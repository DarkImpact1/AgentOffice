import re
import json
import base64
from datetime import datetime, timedelta
from typing import Any, Optional, List, Dict
from email.utils import parsedate_to_datetime
from core.base_agent import BaseAgent, AgentResponse
from core.config import settings

try:
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    GOOGLE_AVAILABLE = True
except ImportError:
    GOOGLE_AVAILABLE = False

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]
PRIORITY_SENDERS = ["@github.com", "@linkedin.com", "noreply@", "important"]
PRIORITY_KEYWORDS = ["urgent", "deadline", "asap", "meeting", "review", "action required", "invoice"]


class EmailAgent(BaseAgent):
    name = "email"
    description = "Monitors Gmail and extracts actionable tasks"
    avatar = "📧"
    color = "#ef4444"

    def __init__(self, db: Any = None, llm: Any = None):
        super().__init__(db, llm)
        self._service = None

    def _get_gmail_service(self) -> Any:
        if not GOOGLE_AVAILABLE:
            return None
        creds = None
        token_path = settings.google_credentials_path.parent / "token.json"
        if token_path.exists():
            creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not settings.google_credentials_path.exists():
                    return None
                flow = InstalledAppFlow.from_client_secrets_file(str(settings.google_credentials_path), SCOPES)
                creds = flow.run_local_server(port=0)
            with open(token_path, "w") as f:
                f.write(creds.to_json())
        return build("gmail", "v1", credentials=creds)

    def _extract_body(self, payload: dict) -> str:
        if "body" in payload and payload["body"].get("data"):
            return base64.urlsafe_b64decode(payload["body"]["data"]).decode("utf-8", errors="ignore")
        if "parts" in payload:
            for part in payload["parts"]:
                if part["mimeType"] == "text/plain":
                    if part["body"].get("data"):
                        return base64.urlsafe_b64decode(part["body"]["data"]).decode("utf-8", errors="ignore")
        return ""

    def _is_high_priority(self, sender: str, subject: str, body: str) -> bool:
        text = f"{sender} {subject} {body}".lower()
        if any(s in sender.lower() for s in PRIORITY_SENDERS):
            return True
        return any(kw in text for kw in PRIORITY_KEYWORDS)

    def _local_extract_tasks(self, emails: List[Dict]) -> List[Dict]:
        tasks = []
        date_pattern = re.compile(r"\b(\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{4}[/-]\d{2}[/-]\d{2})\b")
        for email in emails:
            text = f"{email['subject']} {email['body'][:500]}"
            due_date = None
            date_match = date_pattern.search(text)
            if date_match:
                due_date = date_match.group(1)
            if email["high_priority"] or any(kw in text.lower() for kw in ["please", "need", "request", "confirm"]):
                tasks.append({
                    "title": email["subject"][:100],
                    "description": f"From: {email['sender']}\n{email['body'][:200]}",
                    "due_date": due_date,
                    "priority": 2 if email["high_priority"] else 1,
                    "email_id": email["id"],
                })
        return tasks

    async def _llm_extract_tasks(self, emails: List[Dict]) -> List[Dict]:
        if not self.llm or not emails:
            return []
        email_summaries = [
            f"From: {e['sender']}\nSubject: {e['subject']}\nBody: {e['body'][:300]}"
            for e in emails[:5]
        ]
        prompt = f"""Extract actionable tasks from these emails. Return JSON array with objects containing: title, description, due_date (YYYY-MM-DD or null), priority (1-3).

Emails:
{chr(10).join(email_summaries)}

Return only the JSON array."""

        result = await self.llm.complete_json(
            prompt,
            agent_name=self.name,
            system="Extract tasks from emails. Return valid JSON array only.",
            max_tokens=512,
        )
        return result if isinstance(result, list) else []

    async def execute(self, task: str = "") -> AgentResponse:
        if not GOOGLE_AVAILABLE:
            return AgentResponse(success=False, message="Google API not available. Install google packages.")

        service = self._get_gmail_service()
        if not service:
            return AgentResponse(success=False, message="Gmail not configured. Run OAuth flow first.")

        after_date = (datetime.now() - timedelta(days=1)).strftime("%Y/%m/%d")
        query = f"is:unread after:{after_date}"

        try:
            results = service.users().messages().list(userId="me", q=query, maxResults=20).execute()
            messages = results.get("messages", [])
        except Exception as e:
            return AgentResponse(success=False, message=f"Gmail API error: {e}")

        if not messages:
            return AgentResponse(success=True, message="No new unread emails", data={"emails": 0, "tasks": 0})

        emails = []
        for msg in messages:
            full = service.users().messages().get(userId="me", id=msg["id"], format="full").execute()
            headers = {h["name"]: h["value"] for h in full["payload"]["headers"]}
            body = self._extract_body(full["payload"])
            email_data = {
                "id": msg["id"],
                "sender": headers.get("From", ""),
                "subject": headers.get("Subject", ""),
                "date": headers.get("Date", ""),
                "body": body,
                "high_priority": self._is_high_priority(headers.get("From", ""), headers.get("Subject", ""), body),
            }
            emails.append(email_data)

        high_priority = [e for e in emails if e["high_priority"]]
        low_priority = [e for e in emails if not e["high_priority"]]

        tasks = self._local_extract_tasks(high_priority)
        
        # Only use LLM if API key is configured
        if low_priority and self.llm and hasattr(self.llm, 'client') and self.llm.client.api_key:
            try:
                llm_tasks = await self._llm_extract_tasks(low_priority)
                tasks.extend(llm_tasks)
            except Exception:
                # LLM failed, use local extraction for low priority too
                tasks.extend(self._local_extract_tasks(low_priority))

        tasks_created = 0
        if self.db:
            for t in tasks:
                await self.db.add_task(
                    title=t.get("title", "Email task"),
                    source_agent=self.name,
                    description=t.get("description", ""),
                    priority=t.get("priority", 1),
                    due_date=t.get("due_date"),
                    metadata=json.dumps({"email_id": t.get("email_id", "")}),
                )
                tasks_created += 1

        return AgentResponse(
            success=True,
            message=f"Processed {len(emails)} emails, created {tasks_created} tasks",
            data={"emails": len(emails), "tasks": tasks_created, "high_priority": len(high_priority)},
            tasks_created=tasks_created,
        )
