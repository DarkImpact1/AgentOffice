import asyncio
import json
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from core.config import settings
from core.database import Database
from core.llm_client import LLMClient
from core.orchestrator import Orchestrator
from agents import EmailAgent, TabMonitorAgent, FreelanceHunterAgent, StatusTrackerAgent
from .routes import agents_router, tasks_router

db = Database(settings.database_path)
llm = LLMClient(db)
orchestrator = Orchestrator(db, llm)


class ConnectionManager:
    def __init__(self):
        self.connections: list[WebSocket] = []

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self.connections.append(ws)

    def disconnect(self, ws: WebSocket):
        if ws in self.connections:
            self.connections.remove(ws)

    async def broadcast(self, event: str, agent: str, data: dict):
        message = json.dumps({"event": event, "agent": agent, "data": data})
        for conn in self.connections:
            try:
                await conn.send_text(message)
            except Exception:
                self.disconnect(conn)


ws_manager = ConnectionManager()


async def on_agent_event(event: str, agent: str, data: dict):
    await ws_manager.broadcast(event, agent, data)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings.ensure_data_dir()
    await db.connect()
    llm.set_db(db)

    orchestrator.register(EmailAgent())
    orchestrator.register(TabMonitorAgent())
    orchestrator.register(FreelanceHunterAgent())
    orchestrator.register(StatusTrackerAgent())
    orchestrator.on_event(on_agent_event)

    app.state.db = db
    app.state.llm = llm
    app.state.orchestrator = orchestrator
    app.state.ws_manager = ws_manager

    yield

    await db.close()


app = FastAPI(
    title="AgentOffice API",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(agents_router, prefix="/agents", tags=["agents"])
app.include_router(tasks_router, prefix="/tasks", tags=["tasks"])


@app.get("/")
async def root():
    return {"status": "ok", "name": "AgentOffice", "version": "0.1.0"}


@app.get("/stats")
async def get_stats():
    token_stats = await llm.get_stats()
    agents = await orchestrator.get_all_status()
    return {
        "tokens": token_stats,
        "agents": len(agents),
        "agents_status": {a["name"]: a["status"] for a in agents},
    }


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await ws_manager.connect(websocket)
    try:
        agents = await orchestrator.get_all_status()
        await websocket.send_text(json.dumps({
            "event": "connected",
            "agent": "system",
            "data": {"agents": agents},
        }))

        while True:
            data = await websocket.receive_text()
            try:
                msg = json.loads(data)
                cmd = msg.get("command")
                if cmd == "execute":
                    agent_name = msg.get("agent")
                    task = msg.get("task", "")
                    result = await orchestrator.execute(agent_name, task)
                    await websocket.send_text(json.dumps({
                        "event": "result",
                        "agent": agent_name,
                        "data": {"success": result.success, "message": result.message},
                    }))
                elif cmd == "status":
                    agents = await orchestrator.get_all_status()
                    await websocket.send_text(json.dumps({
                        "event": "status",
                        "agent": "system",
                        "data": {"agents": agents},
                    }))
            except json.JSONDecodeError:
                pass
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
