import re
import json
from typing import Any, Optional, List, Dict
from dataclasses import dataclass
from core.base_agent import BaseAgent, AgentResponse
from core.config import settings

try:
    from playwright.async_api import async_playwright, Browser, Page
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    Browser = Any
    Page = Any


@dataclass
class PlatformConfig:
    name: str
    url: str
    dashboard_url: str
    status_selector: str
    earnings_selector: str
    tasks_selector: str


PLATFORMS = [
    PlatformConfig(
        name="Outlier",
        url="https://outlier.ai",
        dashboard_url="https://app.outlier.ai/en/expert/dashboard",
        status_selector=".project-status, .status-badge, [data-testid='status']",
        earnings_selector=".earnings, .balance, [data-testid='earnings']",
        tasks_selector=".available-tasks, .task-count, [data-testid='tasks']",
    ),
    PlatformConfig(
        name="Scale AI",
        url="https://scale.com",
        dashboard_url="https://dashboard.scale.com/",
        status_selector=".status, .application-status",
        earnings_selector=".earnings, .payout",
        tasks_selector=".tasks-available, .queue-count",
    ),
    PlatformConfig(
        name="Remotasks",
        url="https://remotasks.com",
        dashboard_url="https://www.remotasks.com/en/tasker",
        status_selector=".account-status, .worker-status",
        earnings_selector=".balance, .earnings-amount",
        tasks_selector=".available-tasks, .task-queue",
    ),
    PlatformConfig(
        name="Alignerr",
        url="https://alignerr.com",
        dashboard_url="https://app.alignerr.com/dashboard",
        status_selector=".status, .account-state",
        earnings_selector=".earnings, .balance",
        tasks_selector=".tasks, .available",
    ),
    PlatformConfig(
        name="DataAnnotation",
        url="https://dataannotation.tech",
        dashboard_url="https://app.dataannotation.tech/workers/projects",
        status_selector=".status, .worker-status",
        earnings_selector=".earnings, .payout-amount",
        tasks_selector=".projects-available, .task-list",
    ),
]


class TabMonitorAgent(BaseAgent):
    name = "tab_monitor"
    description = "Monitors AI training platform statuses"
    avatar = "🔍"
    color = "#8b5cf6"

    def __init__(self, db: Any = None, llm: Any = None):
        super().__init__(db, llm)
        self._browser: Optional[Browser] = None

    async def _get_browser(self) -> Optional[Browser]:
        if not PLAYWRIGHT_AVAILABLE:
            return None
        pw = await async_playwright().start()
        browser_args = {}
        if settings.chrome_profile_path:
            browser_args["user_data_dir"] = settings.chrome_profile_path
        try:
            browser = await pw.chromium.launch_persistent_context(
                settings.chrome_profile_path or "",
                headless=True,
                **({} if not settings.chrome_profile_path else {}),
            )
            return browser
        except Exception:
            return await pw.chromium.launch(headless=True)

    def _extract_text(self, page_content: str, selectors: List[str]) -> str:
        for pattern in [r'class="[^"]*status[^"]*"[^>]*>([^<]+)', r'earnings[^>]*>([^<]+)', r'\$[\d,]+\.?\d*']:
            match = re.search(pattern, page_content, re.IGNORECASE)
            if match:
                return match.group(1) if match.lastindex else match.group(0)
        return "unknown"

    async def _check_platform(self, page: Page, platform: PlatformConfig) -> Dict:
        result = {
            "platform": platform.name,
            "status": "unknown",
            "earnings": "",
            "available_tasks": 0,
            "details": "",
            "error": None,
        }
        try:
            await page.goto(platform.dashboard_url, timeout=30000, wait_until="domcontentloaded")
            await page.wait_for_timeout(2000)

            content = await page.content()

            try:
                status_el = await page.query_selector(platform.status_selector)
                if status_el:
                    result["status"] = (await status_el.text_content() or "").strip()
            except Exception:
                result["status"] = self._extract_text(content, [platform.status_selector])

            try:
                earnings_el = await page.query_selector(platform.earnings_selector)
                if earnings_el:
                    result["earnings"] = (await earnings_el.text_content() or "").strip()
            except Exception:
                earnings_match = re.search(r'\$[\d,]+\.?\d*', content)
                if earnings_match:
                    result["earnings"] = earnings_match.group(0)

            try:
                tasks_el = await page.query_selector(platform.tasks_selector)
                if tasks_el:
                    tasks_text = await tasks_el.text_content() or "0"
                    nums = re.findall(r'\d+', tasks_text)
                    result["available_tasks"] = int(nums[0]) if nums else 0
            except Exception:
                pass

            if result["status"] == "unknown" and self.llm:
                snippet = content[:2000]
                prompt = f"Extract status from this page content for {platform.name}. Return JSON: {{status, earnings, tasks}}.\n\n{snippet}"
                llm_result = await self.llm.complete_json(prompt, agent_name=self.name, max_tokens=256)
                if isinstance(llm_result, dict) and "status" in llm_result:
                    result["status"] = llm_result.get("status", "unknown")
                    result["earnings"] = llm_result.get("earnings", "")
                    result["available_tasks"] = llm_result.get("tasks", 0)

        except Exception as e:
            result["error"] = str(e)
            result["status"] = "error"

        return result

    async def execute(self, task: str = "") -> AgentResponse:
        if not PLAYWRIGHT_AVAILABLE:
            return AgentResponse(success=False, message="Playwright not installed. Run: playwright install")

        browser = await self._get_browser()
        if not browser:
            return AgentResponse(success=False, message="Could not launch browser")

        results = []
        try:
            page = await browser.new_page()
            for platform in PLATFORMS:
                status = await self._check_platform(page, platform)
                results.append(status)
                if self.db:
                    await self.db.add_platform_status(
                        platform=status["platform"],
                        status=status["status"],
                        earnings=status["earnings"],
                        available_tasks=status["available_tasks"],
                        details=json.dumps({"error": status.get("error")}),
                    )
            await page.close()
        finally:
            await browser.close()

        successful = [r for r in results if r["status"] != "error"]
        summary = "\n".join([
            f"• {r['platform']}: {r['status']} | ${r['earnings'] or 'N/A'} | {r['available_tasks']} tasks"
            for r in results
        ])

        return AgentResponse(
            success=len(successful) > 0,
            message=f"Checked {len(results)} platforms:\n{summary}",
            data={"platforms": results, "successful": len(successful)},
        )
