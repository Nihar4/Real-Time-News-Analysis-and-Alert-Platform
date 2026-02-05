from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import or_, desc
from pydantic import BaseModel
from typing import List, Optional
import uuid
from datetime import datetime

from src.database import get_db
from src.models import User, Organization, Membership, Company, OrganizationCompany, OrganizationEvent, Event
from src.routers.auth import get_current_user

router = APIRouter(tags=["companies"])

# Pydantic Models
class CompanyResponse(BaseModel):
    id: uuid.UUID
    slug: str
    display_name: str
    last_event_headline: Optional[str] = None
    last_event_time: Optional[datetime] = None

    class Config:
        from_attributes = True

class SubscribeRequest(BaseModel):
    company_id: uuid.UUID

@router.get("/companies", response_model=List[CompanyResponse])
async def search_companies(
    query: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Search by slug or display_name
    result = await db.execute(
        select(Company).where(
            or_(
                Company.slug.ilike(f"%{query}%"),
                Company.display_name.ilike(f"%{query}%")
            )
        ).limit(20)
    )
    return result.scalars().all()

@router.get("/org/{org_id}/companies", response_model=List[CompanyResponse])
async def get_subscribed_companies(
    org_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Verify membership
    result = await db.execute(select(Membership).where(
        Membership.user_id == current_user.id,
        Membership.organization_id == org_id
    ))
    if not result.scalars().first():
        raise HTTPException(status_code=403, detail="Not a member of this organization")
    
    # Fetch subscribed companies
    result = await db.execute(
        select(Company)
        .join(OrganizationCompany, Company.id == OrganizationCompany.company_id)
        .where(OrganizationCompany.organization_id == org_id)
    )
    companies = result.scalars().all()
    
    # Enrich with last event (MVP approach: N+1 queries)
    enriched_companies = []
    for company in companies:
        # Find latest event for this company mapped to this org
        event_result = await db.execute(
            select(Event)
            .join(OrganizationEvent, Event.id == OrganizationEvent.event_id)
            .where(
                OrganizationEvent.organization_id == org_id,
                Event.primary_company_id == company.id
            )
            .order_by(desc(Event.created_at))
            .limit(1)
        )
        last_event = event_result.scalars().first()
        
        company_data = CompanyResponse(
            id=company.id,
            slug=company.slug,
            display_name=company.display_name,
            last_event_headline=last_event.headline_summary if last_event else None,
            last_event_time=last_event.created_at if last_event else None
        )
        enriched_companies.append(company_data)
        
    return enriched_companies

@router.post("/org/{org_id}/companies/subscribe")
async def subscribe_company(
    org_id: uuid.UUID,
    request: SubscribeRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Verify Admin
    result = await db.execute(select(Membership).where(
        Membership.user_id == current_user.id,
        Membership.organization_id == org_id
    ))
    membership = result.scalars().first()
    if not membership:
        raise HTTPException(status_code=403, detail="Not a member")
    if membership.role != "admin":
        raise HTTPException(status_code=403, detail="Only admins can subscribe")
    
    # Check if already subscribed
    result = await db.execute(select(OrganizationCompany).where(
        OrganizationCompany.organization_id == org_id,
        OrganizationCompany.company_id == request.company_id
    ))
    if result.scalars().first():
        return {"status": "already_subscribed"}
    
    # Subscribe
    sub = OrganizationCompany(organization_id=org_id, company_id=request.company_id)
    db.add(sub)
    
    # Backfill existing events for this company
    # Find all events for this company
    events_result = await db.execute(select(Event).where(Event.primary_company_id == request.company_id))
    existing_events = events_result.scalars().all()
    
    # Create OrganizationEvent entries
    for event in existing_events:
        # Check if already exists (sanity check, though unlikely for new sub)
        check = await db.execute(select(OrganizationEvent).where(
            OrganizationEvent.organization_id == org_id,
            OrganizationEvent.event_id == event.id
        ))
        if not check.scalars().first():
            org_event = OrganizationEvent(
                organization_id=org_id,
                event_id=event.id,
                created_at=event.created_at # Preserve original event time
            )
            db.add(org_event)

    await db.commit()
    return {"status": "subscribed", "backfilled_events": len(existing_events)}

@router.delete("/org/{org_id}/companies/{company_id}")
async def unsubscribe_company(
    org_id: uuid.UUID,
    company_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Verify Admin
    result = await db.execute(select(Membership).where(
        Membership.user_id == current_user.id,
        Membership.organization_id == org_id
    ))
    membership = result.scalars().first()
    if not membership:
        raise HTTPException(status_code=403, detail="Not a member")
    if membership.role != "admin":
        raise HTTPException(status_code=403, detail="Only admins can unsubscribe")
    
    # Unsubscribe
    result = await db.execute(select(OrganizationCompany).where(
        OrganizationCompany.organization_id == org_id,
        OrganizationCompany.company_id == company_id
    ))
    sub = result.scalars().first()
    if sub:
        await db.delete(sub)
        await db.commit()
    
    return {"status": "unsubscribed"}
