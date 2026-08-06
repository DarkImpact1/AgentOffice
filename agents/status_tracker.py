import json
from datetime import datetime, timedelta
from typing import Any, Optional, List, Dict
from core.base_agent import BaseAgent, AgentResponse


class StatusTrackerAgent(BaseAgent):
    name = "status_tracker"
    description = "Tracks daily productivity and generates reports"
    avatar = "📊"
    color = "#f59e0b"

    async def _get_daily_stats(self) -> Dict:
        if not self.db:
            return {}

        today = datetime.now().date().isoformat()
        yesterday = (datetime.now() - timedelta(days=1)).date().isoformat()

        tasks = await self.db.fetch_all(
            "SELECT * FROM tasks WHERE DATE(created_at) = ?", (today,)
        )
        completed_tasks = [t for t in tasks if t["status"] == "completed"]

        token_stats = await self.db.get_token_stats()

        applications = await self.db.fetch_all(
            "SELECT * FROM job_applications WHERE DATE(created_at) = ?", (today,)
        )
        approved = [a for a in applications if a["status"] == "approved"]

        platforms = await self.db.get_latest_platform_status()

        agent_states = await self.db.fetch_all("SELECT * FROM agent_states")

        return {
            "date": today,
            "tasks": {
                "total": len(tasks),
                "completed": len(completed_tasks),
                "pending": len(tasks) - len(completed_tasks),
            },
            "emails": {
                "processed": len([t for t in tasks if t["source_agent"] == "email"]),
            },
            "freelance": {
                "jobs_found": len(applications),
                "proposals_sent": len(approved),
                "platforms_checked": len(set(a["platform"] for a in applications)),
            },
            "ai_platforms": {
                "monitored": len(platforms),
                "active": len([p for p in platforms if p["status"] not in ["error", "unknown"]]),
                "total_earnings": sum(
                    float(p["earnings"].replace("$", "").replace(",", "") or 0)
                    for p in platforms
                    if p["earnings"] and p["earnings"].replace("$", "").replace(",", "").replace(".", "").isdigit()
                ),
            },
            "tokens": token_stats,
            "agents": {
                a["agent_name"]: a["status"]
                for a in agent_states
            },
        }

    async def _generate_report(self, stats: Dict) -> str:
        # Always use basic report - LLM is optional
        return self._format_basic_report(stats)

    def _format_basic_report(self, stats: Dict) -> str:
        return f"""📊 Daily Report - {stats['date']}

📧 Emails: {stats['emails']['processed']} processed
✅ Tasks: {stats['tasks']['completed']}/{stats['tasks']['total']} completed
💼 Freelance: {stats['freelance']['jobs_found']} jobs, {stats['freelance']['proposals_sent']} proposals
🤖 AI Platforms: {stats['ai_platforms']['active']}/{stats['ai_platforms']['monitored']} active
💰 Platform Earnings: ${stats['ai_platforms']['total_earnings']:.2f}
🎫 Tokens Used: {stats['tokens']['input_tokens'] + stats['tokens']['output_tokens']} total"""

    async def execute(self, task: str = "") -> AgentResponse:
        if not self.db:
            return AgentResponse(success=False, message="Database not connected")

        stats = await self._get_daily_stats()

        if "report" in task.lower() or not task:
            report = await self._generate_report(stats)
        else:
            report = self._format_basic_report(stats)

        return AgentResponse(
            success=True,
            message=report,
            data=stats,
        )

    async def get_weekly_summary(self) -> Dict:
        if not self.db:
            return {}

        week_ago = (datetime.now() - timedelta(days=7)).isoformat()

        tasks = await self.db.fetch_all(
            "SELECT * FROM tasks WHERE created_at >= ?", (week_ago,)
        )
        applications = await self.db.fetch_all(
            "SELECT * FROM job_applications WHERE created_at >= ?", (week_ago,)
        )
        token_usage = await self.db.fetch_all(
            "SELECT SUM(input_tokens) as input, SUM(output_tokens) as output FROM token_usage WHERE timestamp >= ?",
            (week_ago,),
        )

        return {
            "period": "7 days",
            "tasks_created": len(tasks),
            "tasks_completed": len([t for t in tasks if t["status"] == "completed"]),
            "jobs_found": len(applications),
            "proposals_approved": len([a for a in applications if a["status"] == "approved"]),
            "total_tokens": (token_usage[0]["input"] or 0) + (token_usage[0]["output"] or 0) if token_usage else 0,
        }
