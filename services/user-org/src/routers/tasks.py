from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import uuid

from src.database import get_db
from src.models import Task, TaskComment, User, OrganizationEvent, Membership
from src.routers.auth import oauth2_scheme
from src.config import settings
from jose import JWTError, jwt

router = APIRouter(prefix="/tasks", tags=["tasks"])

# ==================== Pydantic Schemas ====================

class TaskCreate(BaseModel):
    event_id: Optional[uuid.UUID] = None
    title: str
    description: Optional[str] = None
    priority: str = "medium"  # low, medium, high
    due_date: Optional[datetime] = None
    assigned_to: Optional[uuid.UUID] = None

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None  # todo, in_progress, done
    priority: Optional[str] = None
    due_date: Optional[datetime] = None
    assigned_to: Optional[uuid.UUID] = None

class CommentCreate(BaseModel):
    text: str

class CommentResponse(BaseModel):
    id: uuid.UUID
    task_id: uuid.UUID
    user_id: uuid.UUID
    text: str
    created_at: datetime

    class Config:
        from_attributes = True

class TaskResponse(BaseModel):
    id: uuid.UUID
    organization_id: uuid.UUID
    event_id: Optional[uuid.UUID]
    title: str
    description: Optional[str]
    status: str
    priority: str
    due_date: Optional[datetime]
    created_by: uuid.UUID
    assigned_to: Optional[uuid.UUID]
    created_at: datetime
    updated_at: datetime
    comments: Optional[List[CommentResponse]] = None

    class Config:
        from_attributes = True

# ==================== Auth Dependency ====================

async def get_current_user_with_org(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
):
    """Extract user and org info from JWT token"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        user_id_str: str = payload.get("sub")
        org_id_str: str = payload.get("org_id")
        
        if user_id_str is None or org_id_str is None:
            raise credentials_exception
            
        user_id = uuid.UUID(user_id_str)
        org_id = uuid.UUID(org_id_str)
        
    except (JWTError, ValueError):
        raise credentials_exception
    
    # Verify user exists
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalars().first()
    if user is None:
        raise credentials_exception
    
    return {"user_id": user_id, "org_id": org_id, "user": user}

# ==================== Endpoints ====================

@router.post("/org/{org_id}/tasks", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(
    org_id: uuid.UUID,
    task_data: TaskCreate,
    auth_data: dict = Depends(get_current_user_with_org),
    db: AsyncSession = Depends(get_db)
):
    """Create a new task"""
    # Verify user belongs to the organization
    if auth_data["org_id"] != org_id:
        raise HTTPException(status_code=403, detail="User does not belong to this organization")
    
    # If event_id is provided, verify it belongs to this org
    if task_data.event_id:
        result = await db.execute(
            select(OrganizationEvent).where(
                OrganizationEvent.organization_id == org_id,
                OrganizationEvent.event_id == task_data.event_id
            )
        )
        if not result.scalars().first():
            raise HTTPException(status_code=404, detail="Event not found or does not belong to this organization")
    
    # If assigned_to is provided, verify they belong to this org
    if task_data.assigned_to:
        result = await db.execute(
            select(Membership).where(
                Membership.user_id == task_data.assigned_to,
                Membership.organization_id == org_id
            )
        )
        if not result.scalars().first():
            raise HTTPException(status_code=404, detail="Assigned user not found in this organization")
    
    # Create task
    new_task = Task(
        organization_id=org_id,
        event_id=task_data.event_id,
        title=task_data.title,
        description=task_data.description,
        priority=task_data.priority,
        due_date=task_data.due_date,
        created_by=auth_data["user_id"],
        assigned_to=task_data.assigned_to,
        status="todo"
    )
    
    db.add(new_task)
    await db.commit()
    
    # Re-fetch with eager loading to satisfy Pydantic response model
    result = await db.execute(
        select(Task)
        .options(selectinload(Task.comments))
        .where(Task.id == new_task.id)
    )
    created_task = result.scalars().first()
    
    return created_task

@router.get("/org/{org_id}/tasks", response_model=List[TaskResponse])
async def list_tasks(
    org_id: uuid.UUID,
    status_filter: Optional[str] = Query(None, alias="status"),
    assigned_to: Optional[uuid.UUID] = None,
    event_id: Optional[uuid.UUID] = None,
    auth_data: dict = Depends(get_current_user_with_org),
    db: AsyncSession = Depends(get_db)
):
    """List all tasks for an organization with optional filters.
    Users only see tasks they created OR are assigned to."""
    # Verify user belongs to the organization
    if auth_data["org_id"] != org_id:
        raise HTTPException(status_code=403, detail="User does not belong to this organization")
    
    current_user_id = auth_data["user_id"]
    
    # Build query - filter by current user (created_by OR assigned_to)
    query = (
        select(Task)
        .options(selectinload(Task.comments))
        .where(
            Task.organization_id == org_id,
            (Task.created_by == current_user_id) | (Task.assigned_to == current_user_id)
        )
    )
    
    if status_filter:
        query = query.where(Task.status == status_filter)
    if assigned_to:
        query = query.where(Task.assigned_to == assigned_to)
    if event_id:
        query = query.where(Task.event_id == event_id)
    
    query = query.order_by(Task.created_at.desc())
    
    result = await db.execute(query)
    tasks = result.scalars().all()
    
    return tasks

@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: uuid.UUID,
    auth_data: dict = Depends(get_current_user_with_org),
    db: AsyncSession = Depends(get_db)
):
    """Get task detail with comments"""
    # Fetch task with comments
    result = await db.execute(
        select(Task)
        .options(selectinload(Task.comments))
        .where(Task.id == task_id)
    )
    task = result.scalars().first()
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Verify task belongs to user's organization
    if task.organization_id != auth_data["org_id"]:
        raise HTTPException(status_code=403, detail="Task does not belong to your organization")
    
    return task

@router.patch("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: uuid.UUID,
    task_update: TaskUpdate,
    auth_data: dict = Depends(get_current_user_with_org),
    db: AsyncSession = Depends(get_db)
):
    """Update a task"""
    # Fetch task
    result = await db.execute(select(Task).where(Task.id == task_id))
    task = result.scalars().first()
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Verify task belongs to user's organization
    if task.organization_id != auth_data["org_id"]:
        raise HTTPException(status_code=403, detail="Task does not belong to your organization")
    
    # Update fields
    if task_update.title is not None:
        task.title = task_update.title
    if task_update.description is not None:
        task.description = task_update.description
    if task_update.status is not None:
        task.status = task_update.status
    if task_update.priority is not None:
        task.priority = task_update.priority
    if task_update.due_date is not None:
        task.due_date = task_update.due_date
    if task_update.assigned_to is not None:
        # Verify assigned user belongs to org
        result = await db.execute(
            select(Membership).where(
                Membership.user_id == task_update.assigned_to,
                Membership.organization_id == auth_data["org_id"]
            )
        )
        if not result.scalars().first():
            raise HTTPException(status_code=404, detail="Assigned user not found in this organization")
        task.assigned_to = task_update.assigned_to
    
    task.updated_at = datetime.utcnow()
    
    await db.commit()
    
    # Re-fetch with eager loading
    result = await db.execute(
        select(Task)
        .options(selectinload(Task.comments))
        .where(Task.id == task_id)
    )
    updated_task = result.scalars().first()
    
    return updated_task

@router.post("/{task_id}/comments", response_model=CommentResponse, status_code=status.HTTP_201_CREATED)
async def add_comment(
    task_id: uuid.UUID,
    comment_data: CommentCreate,
    auth_data: dict = Depends(get_current_user_with_org),
    db: AsyncSession = Depends(get_db)
):
    """Add a comment to a task"""
    # Fetch task
    result = await db.execute(select(Task).where(Task.id == task_id))
    task = result.scalars().first()
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Verify task belongs to user's organization
    if task.organization_id != auth_data["org_id"]:
        raise HTTPException(status_code=403, detail="Task does not belong to your organization")
    
    # Create comment
    new_comment = TaskComment(
        task_id=task_id,
        user_id=auth_data["user_id"],
        text=comment_data.text
    )
    
    db.add(new_comment)
    await db.commit()
    await db.refresh(new_comment)
    
    return new_comment
