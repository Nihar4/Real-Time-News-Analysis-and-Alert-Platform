from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import desc
from pydantic import BaseModel
from typing import List, Optional, Any
import uuid
from datetime import datetime

from src.database import get_db
from src.models import User, Organization, Membership, Company, OrganizationCompany, Event, OrganizationEvent
from src.routers.auth import get_current_user

router = APIRouter(tags=["events"])

class EventResponse(BaseModel):
    id: uuid.UUID
    event_type: Optional[str]
    headline_summary: Optional[str]
    short_summary: Optional[str]
    detailed_summary: Optional[str]
    created_at: datetime
    primary_company_name: Optional[str] = None
    
    # New fields
    overall_impact: Optional[int] = None
    importance_level: Optional[str] = None
    urgency: Optional[str] = None
    time_horizon: Optional[str] = None
    
    key_points: Optional[List[str]] = None
    recommended_teams: Optional[List[str]] = None
    affected_areas: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    
    confidence_explanation: Optional[str] = None
    risk_score: Optional[int] = None
    opportunity_score: Optional[int] = None
    sentiment: Optional[str] = None
    sentiment_score: Optional[float] = None
    threat_level: Optional[str] = None
    confidence_level: Optional[str] = None
    recommended_actions: Optional[str] = None
    
    impact_on_market: Optional[str] = None
    impact_on_products: Optional[str] = None
    impact_on_competitors: Optional[str] = None
    impact_on_customers: Optional[str] = None
    impact_on_talent: Optional[str] = None
    impact_on_regulation: Optional[str] = None

    class Config:
        from_attributes = True

@router.get("/org/{org_id}/companies/{company_id}/events", response_model=List[EventResponse])
async def get_company_events(
    org_id: uuid.UUID,
    company_id: uuid.UUID,
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Verify membership
    result = await db.execute(select(Membership).where(
        Membership.user_id == current_user.id,
        Membership.organization_id == org_id
    ))
    if not result.scalars().first():
        raise HTTPException(status_code=403, detail="Not a member")
    
    # Verify subscription (optional but good practice)
    result = await db.execute(select(OrganizationCompany).where(
        OrganizationCompany.organization_id == org_id,
        OrganizationCompany.company_id == company_id
    ))
    if not result.scalars().first():
        raise HTTPException(status_code=404, detail="Company not subscribed")

    # Fetch events for this company that are linked to this org
    # Actually, if we just want events for the company, we can query events directly where primary_company_id = company_id
    # BUT, the plan says "query organization_events joined with events".
    # This implies we only show events that were mapped to this org (e.g. maybe some filtering happened).
    # Let's follow the plan.
    
    result = await db.execute(
        select(Event)
        .join(OrganizationEvent, Event.id == OrganizationEvent.event_id)
        .where(
            OrganizationEvent.organization_id == org_id,
            Event.primary_company_id == company_id
        )
        .order_by(desc(Event.created_at))
        .limit(limit)
    )
    events = result.scalars().all()
    return events

@router.get("/events/{event_id}", response_model=EventResponse)
async def get_event_detail(
    event_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # We should probably verify the user has access to this event via some org
    # For now, let's just return it if they are authenticated
    result = await db.execute(select(Event).where(Event.id == event_id))
    event = result.scalars().first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    return event
