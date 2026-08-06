from typing import Any, Callable, Coroutine, Dict, List, Optional
from .base_agent import BaseAgent, AgentStatus, AgentResponse
from .database import Database
from .llm_client import LLMClient


class Orchestrator:
    def __init__(self, db: Database, llm: LLMClient):
        self.db = db
        self.llm = llm
        self._agents: Dict[str, BaseAgent] = {}
        self._ws_callbacks: List[Callable[[str, str, Any], Coroutine[Any, Any, None]]] = []

    def register(self, agent: BaseAgent) -> None:
        agent.db = self.db
        agent.llm = self.llm
        agent.on_status_change(self._on_agent_status_change)
        self._agents[agent.name] = agent

    def get_agent(self, name: str) -> Optional[BaseAgent]:
        return self._agents.get(name)

    def list_agents(self) -> List[str]:
        return list(self._agents.keys())

    async def get_all_status(self) -> List[Dict]:
        return [await agent.get_status_info() for agent in self._agents.values()]

    def on_event(self, callback: Callable[[str, str, Any], Coroutine[Any, Any, None]]) -> None:
        self._ws_callbacks.append(callback)

    async def _on_agent_status_change(self, agent_name: str, status: AgentStatus) -> None:
        for callback in self._ws_callbacks:
            await callback("agent_status", agent_name, {"status": status.value})

    async def _emit(self, event: str, agent: str, data: Any) -> None:
        for callback in self._ws_callbacks:
            await callback(event, agent, data)

    async def execute(self, agent_name: str, task: str = "") -> AgentResponse:
        agent = self.get_agent(agent_name)
        if not agent:
            return AgentResponse(success=False, message=f"Agent '{agent_name}' not found")

        await self._emit("task_started", agent_name, {"task": task})
        result = await agent.run(task)
        await self._emit("task_completed", agent_name, {"result": result.message, "success": result.success})
        return result

    async def execute_all(self) -> dict[str, AgentResponse]:
        results = {}
        for name in self._agents:
            results[name] = await self.execute(name)
        return results

    async def route_task(self, task: str) -> AgentResponse:
        task_lower = task.lower()
        routing: Dict[str, List[str]] = {
            "email": ["email", "mail", "inbox", "gmail"],
            "tab_monitor": ["tab", "chrome", "browser", "outlier", "scale", "remotasks", "training"],
            "freelance_hunter": ["freelance", "job", "upwork", "fiverr", "proposal", "gig"],
            "status_tracker": ["status", "report", "summary", "productivity", "daily"],
        }
        for agent_name, keywords in routing.items():
            if any(kw in task_lower for kw in keywords):
                return await self.execute(agent_name, task)
        return AgentResponse(success=False, message="Could not route task to any agent")
