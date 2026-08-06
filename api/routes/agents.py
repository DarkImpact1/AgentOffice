from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel

router = APIRouter()


class ExecuteRequest(BaseModel):
    task: str = ""


@router.get("")
async def list_agents(request: Request):
    orchestrator = request.app.state.orchestrator
    return await orchestrator.get_all_status()


@router.get("/{name}")
async def get_agent(name: str, request: Request):
    orchestrator = request.app.state.orchestrator
    agent = orchestrator.get_agent(name)
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent '{name}' not found")
    return await agent.get_status_info()


@router.post("/{name}/execute")
async def execute_agent(name: str, request: Request, body: ExecuteRequest = ExecuteRequest()):
    orchestrator = request.app.state.orchestrator
    result = await orchestrator.execute(name, body.task)
    return {
        "success": result.success,
        "message": result.message,
        "data": result.data,
        "tasks_created": result.tasks_created,
    }


@router.post("/route")
async def route_task(request: Request, body: ExecuteRequest):
    orchestrator = request.app.state.orchestrator
    result = await orchestrator.route_task(body.task)
    return {
        "success": result.success,
        "message": result.message,
        "data": result.data,
    }
