from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ..deps import get_current_user, get_db
from ..schemas import QueryCreateIn, QueryOut, QueryListOut
from ..models import User, UserQuery
from ..kafka_producer import producer
from ..config import settings
from uuid import uuid4
from datetime import datetime, timezone

router = APIRouter(prefix="/queries", tags=["queries"])

@router.post("", response_model=QueryOut, status_code=201)
async def create_query(
    payload: QueryCreateIn,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    # Check for duplicate queries
    existing_query = await session.execute(
        select(UserQuery).where(
            UserQuery.user_id == user.id,
            UserQuery.original_query == payload.original_query
        )
    )
    if existing_query.scalars().first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A query with this original_query already exists for this user"
        )
    
    # Check for duplicate in enhanced_query column (if it exists)
    existing_enhanced_query = await session.execute(
        select(UserQuery).where(
            UserQuery.user_id == user.id,
            UserQuery.enhanced_query.isnot(None),
            UserQuery.enhanced_query["original_query"].astext == payload.original_query
        )
    )
    if existing_enhanced_query.scalars().first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A query with this original_query already exists in enhanced_query for this user"
        )

    # Create DB row
    q = UserQuery(
        user_id=user.id,
        original_query=payload.original_query,
        is_active=payload.is_active,
    )
    session.add(q)
    await session.commit()
    await session.refresh(q)

    # Produce to Kafka
    event = {
        "event_id": str(uuid4()),
        "type": "query.created",
        "occurred_at": datetime.now(tz=timezone.utc).isoformat(),
        "data": {
            "query_id": str(q.id),
            "user_id": str(user.id),
            "email": user.email,
            "original_query": q.original_query,
            "is_active": q.is_active,
        },
    }
    await producer.send(settings.kafka_topic, key=str(q.id), value=event)

    return QueryOut(id=q.id, original_query=q.original_query, is_active=q.is_active, created_at=q.created_at)

@router.get("", response_model=QueryListOut)
async def list_my_queries(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    result = await session.execute(select(UserQuery).where(UserQuery.user_id == user.id).order_by(UserQuery.created_at.desc()))
    items = [
        QueryOut(
            id=row.id,
            original_query=row.original_query,
            is_active=row.is_active,
            created_at=row.created_at,
        )
        for row in result.scalars().all()
    ]
    return QueryListOut(items=items)
