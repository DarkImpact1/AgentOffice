from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
from typing import Any, Optional, List, Dict


class AgentStatus(str, Enum):
    IDLE = "idle"
    WALKING = "walking"
    WORKING = "working"
    REPORTING = "reporting"
    ERROR = "error"


@dataclass
class AgentResponse:
    success: bool
    message: str
    data: Dict = field(default_factory=dict)
    tasks_created: int = 0
    tokens_used: int = 0


class BaseAgent(ABC):
    name: str = "base"
    description: str = "Base agent"
    avatar: str = "👤"
    color: str = "#6366f1"

    def __init__(self, db: Any = None, llm: Any = None):
        self.db = db
        self.llm = llm
        self._status = AgentStatus.IDLE
        self._last_run: Optional[datetime] = None
        self._callbacks: List[Any] = []

    @property
    def status(self) -> AgentStatus:
        return self._status

    async def set_status(self, status: AgentStatus) -> None:
        self._status = status
        for callback in self._callbacks:
            await callback(self.name, status)

    def on_status_change(self, callback: Any) -> None:
        self._callbacks.append(callback)

    @abstractmethod
    async def execute(self, task: str = "") -> AgentResponse:
        pass

    async def get_status_info(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "avatar": self.avatar,
            "color": self.color,
            "status": self._status.value,
            "last_run": self._last_run.isoformat() if self._last_run else None,
        }

    async def run(self, task: str = "") -> AgentResponse:
        await self.set_status(AgentStatus.WALKING)
        await self.set_status(AgentStatus.WORKING)
        try:
            result = await self.execute(task)
            self._last_run = datetime.now()
            await self.set_status(AgentStatus.REPORTING)
            if self.db:
                await self.db.update_agent_state(self.name, "idle", result.message)
            await self.set_status(AgentStatus.IDLE)
            return result
        except Exception as e:
            await self.set_status(AgentStatus.ERROR)
            if self.db:
                await self.db.update_agent_state(self.name, "error", str(e))
            return AgentResponse(success=False, message=str(e))
