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
class FreelancePlatform:
    name: str
    search_url: str
    job_selector: str
    title_selector: str
    budget_selector: str
    description_selector: str
    link_selector: str


PLATFORMS = [
    FreelancePlatform(
        name="Upwork",
        search_url="https://www.upwork.com/nx/search/jobs/?q={query}&sort=recency",
        job_selector="article[data-test='JobTile'], .job-tile",
        title_selector="h2 a, .job-title a",
        budget_selector=".budget, [data-test='budget']",
        description_selector=".description, [data-test='description']",
        link_selector="h2 a, .job-title a",
    ),
    FreelancePlatform(
        name="Freelancer",
        search_url="https://www.freelancer.com/jobs/?keyword={query}",
        job_selector=".JobSearchCard-item, .project-card",
        title_selector=".JobSearchCard-primary-heading a, .project-title",
        budget_selector=".JobSearchCard-secondary-price, .budget",
        description_selector=".JobSearchCard-primary-description, .description",
        link_selector=".JobSearchCard-primary-heading a, .project-title a",
    ),
    FreelancePlatform(
        name="Fiverr",
        search_url="https://www.fiverr.com/search/gigs?query={query}",
        job_selector=".gig-card-layout, .gig-wrapper",
        title_selector=".gig-title, h3",
        budget_selector=".price, .gig-price",
        description_selector=".gig-description",
        link_selector="a.gig-link, .gig-title a",
    ),
]

SKILLS = ["python", "react", "devops", "ai", "machine learning", "full stack", "backend", "api"]
PROPOSAL_TEMPLATE = """Hi,

I'm interested in your {job_type} project. With my experience in {skills}, I can help you achieve {goal}.

Key points:
- {point1}
- {point2}
- {point3}

I'd love to discuss this further. When would be a good time to chat?

Best regards"""


class FreelanceHunterAgent(BaseAgent):
    name = "freelance_hunter"
    description = "Finds freelance jobs and drafts proposals"
    avatar = "💼"
    color = "#10b981"

    def __init__(self, db: Any = None, llm: Any = None):
        super().__init__(db, llm)
        self._browser: Optional[Browser] = None

    async def _get_browser(self) -> Optional[Browser]:
        if not PLAYWRIGHT_AVAILABLE:
            return None
        pw = await async_playwright().start()
        try:
            if settings.chrome_profile_path:
                return await pw.chromium.launch_persistent_context(
                    settings.chrome_profile_path,
                    headless=True,
                )
            return await pw.chromium.launch(headless=True)
        except Exception:
            return await pw.chromium.launch(headless=True)

    def _matches_skills(self, text: str) -> bool:
        text_lower = text.lower()
        return any(skill in text_lower for skill in SKILLS)

    def _extract_budget(self, text: str) -> str:
        patterns = [r'\$[\d,]+(?:\s*-\s*\$[\d,]+)?', r'[\d,]+\s*(?:USD|EUR|GBP)', r'Budget:\s*([^\n]+)']
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(0)
        return "Not specified"

    async def _scrape_platform(self, page: Page, platform: FreelancePlatform, query: str) -> List[Dict]:
        jobs = []
        url = platform.search_url.format(query=query.replace(" ", "+"))

        try:
            await page.goto(url, timeout=30000, wait_until="domcontentloaded")
            await page.wait_for_timeout(3000)

            job_elements = await page.query_selector_all(platform.job_selector)

            for i, job_el in enumerate(job_elements[:10]):
                try:
                    title_el = await job_el.query_selector(platform.title_selector)
                    title = await title_el.text_content() if title_el else "Unknown"

                    desc_el = await job_el.query_selector(platform.description_selector)
                    description = await desc_el.text_content() if desc_el else ""

                    budget_el = await job_el.query_selector(platform.budget_selector)
                    budget_text = await budget_el.text_content() if budget_el else ""
                    budget = self._extract_budget(budget_text) if budget_text else "Not specified"

                    link_el = await job_el.query_selector(platform.link_selector)
                    link = await link_el.get_attribute("href") if link_el else ""
                    if link and not link.startswith("http"):
                        link = f"https://{platform.name.lower()}.com{link}"

                    if self._matches_skills(f"{title} {description}"):
                        jobs.append({
                            "platform": platform.name,
                            "title": (title or "").strip()[:200],
                            "description": (description or "").strip()[:500],
                            "budget": budget,
                            "url": link,
                        })
                except Exception:
                    continue

        except Exception as e:
            pass

        return jobs

    async def _generate_proposal(self, job: dict) -> str:
        if not self.llm:
            return PROPOSAL_TEMPLATE.format(
                job_type=job.get("title", "development"),
                skills="Python, React, and DevOps",
                goal="deliver a high-quality solution",
                point1="5+ years of relevant experience",
                point2="Quick turnaround time",
                point3="Clear communication throughout",
            )

        prompt = f"""Write a brief, professional freelance proposal for this job. Keep it under 150 words.

Job Title: {job['title']}
Description: {job['description'][:300]}

Return only the proposal text, no JSON."""

        result = await self.llm.complete(
            prompt,
            agent_name=self.name,
            system="Write concise freelance proposals. Be professional but friendly. No fluff.",
            max_tokens=300,
        )
        return result.strip()

    async def execute(self, task: str = "") -> AgentResponse:
        if not PLAYWRIGHT_AVAILABLE:
            return AgentResponse(success=False, message="Playwright not installed")

        browser = await self._get_browser()
        if not browser:
            return AgentResponse(success=False, message="Could not launch browser")

        query = task if task else "python developer"
        all_jobs: List[Dict] = []

        try:
            page = await browser.new_page()
            for platform in PLATFORMS:
                jobs = await self._scrape_platform(page, platform, query)
                all_jobs.extend(jobs)
            await page.close()
        finally:
            await browser.close()

        if not all_jobs:
            return AgentResponse(
                success=True,
                message="No matching jobs found",
                data={"jobs": 0, "proposals": 0},
            )

        proposals_created = 0
        for job in all_jobs[:5]:
            proposal = await self._generate_proposal(job)
            job["proposal"] = proposal

            if self.db:
                await self.db.add_job_application(
                    platform=job["platform"],
                    job_title=job["title"],
                    job_url=job.get("url", ""),
                    budget=job["budget"],
                    proposal=proposal,
                )
                proposals_created += 1

        summary = "\n".join([
            f"• [{j['platform']}] {j['title'][:50]} - {j['budget']}"
            for j in all_jobs[:5]
        ])

        return AgentResponse(
            success=True,
            message=f"Found {len(all_jobs)} jobs, created {proposals_created} proposals:\n{summary}",
            data={"jobs": len(all_jobs), "proposals": proposals_created, "details": all_jobs[:5]},
            tasks_created=proposals_created,
        )
