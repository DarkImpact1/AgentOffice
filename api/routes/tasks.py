from typing import Optional
from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel

router = APIRouter()


class UpdateTaskStatus(BaseModel):
    status: str


@router.get("")
async def list_tasks(request: Request, status: Optional[str] = None, agent: Optional[str] = None):
    db = request.app.state.db
    return await db.get_tasks(status=status, agent=agent)


@router.get("/pending-approvals")
async def get_pending_approvals(request: Request):
    db = request.app.state.db
    return await db.get_pending_applications()


@router.patch("/{task_id}")
async def update_task(task_id: int, request: Request, body: UpdateTaskStatus):
    db = request.app.state.db
    await db.update_task_status(task_id, body.status)
    return {"success": True, "task_id": task_id, "status": body.status}


@router.patch("/approve/{app_id}")
async def approve_application(app_id: int, request: Request):
    db = request.app.state.db
    await db.approve_application(app_id)
    return {"success": True, "application_id": app_id, "status": "approved"}


@router.get("/platforms")
async def get_platform_status(request: Request):
    db = request.app.state.db
    return await db.get_latest_platform_status()
