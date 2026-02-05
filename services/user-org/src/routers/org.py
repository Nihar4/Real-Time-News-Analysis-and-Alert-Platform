from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from pydantic import BaseModel, EmailStr
from typing import List
import uuid

from src.database import get_db
from src.models import User, Organization, Membership
from src.auth import get_password_hash
from src.routers.auth import get_current_user

router = APIRouter(prefix="/org", tags=["org"])

# Pydantic Models
class MemberResponse(BaseModel):
    id: uuid.UUID
    email: str
    name: str
    role: str

    class Config:
        from_attributes = True

class InviteRequest(BaseModel):
    email: EmailStr
    name: str

@router.get("/{org_id}/members", response_model=List[MemberResponse])
async def get_members(
    org_id: uuid.UUID,
    search: str = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # 1. Verify user belongs to this org
    result = await db.execute(select(Membership).where(
        Membership.user_id == current_user.id,
        Membership.organization_id == org_id
    ))
    membership = result.scalars().first()
    if not membership:
        raise HTTPException(status_code=403, detail="Not a member of this organization")
    
    # 2. Fetch members
    # Join User and Membership
    query = (
        select(User, Membership.role)
        .join(Membership, User.id == Membership.user_id)
        .where(Membership.organization_id == org_id)
    )
    
    # Apply search filter if provided
    if search:
        search_param = f"%{search.lower()}%"
        query = query.where(
            (User.name.ilike(search_param)) | (User.email.ilike(search_param))
        )
    
    result = await db.execute(query)
    
    members = []
    for user, role in result:
        members.append(MemberResponse(
            id=user.id,
            email=user.email,
            name=user.name,
            role=role
        ))
    
    return members

@router.post("/{org_id}/invite", response_model=MemberResponse)
async def invite_member(
    org_id: uuid.UUID,
    invite_data: InviteRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    from datetime import datetime, timedelta
    from src.email_service import email_service
    
    # 1. Verify Admin Role
    result = await db.execute(select(Membership).where(
        Membership.user_id == current_user.id,
        Membership.organization_id == org_id
    ))
    membership = result.scalars().first()
    if not membership:
        raise HTTPException(status_code=403, detail="Not a member of this organization")
    
    if membership.role != "admin":
        raise HTTPException(status_code=403, detail="Only admins can invite members")
    
    # Get organization name for email
    result = await db.execute(select(Organization).where(Organization.id == org_id))
    org = result.scalars().first()
    
    # 2. Check if user exists
    result = await db.execute(select(User).where(User.email == invite_data.email))
    existing_user = result.scalars().first()
    
    if existing_user:
        # Check if already a member
        result = await db.execute(select(Membership).where(
            Membership.user_id == existing_user.id,
            Membership.organization_id == org_id
        ))
        if result.scalars().first():
            raise HTTPException(status_code=400, detail="User is already a member")
        
        new_user = existing_user
    else:
        # Validate domain
        user_domain = invite_data.email.split("@")[1]
        if user_domain != org.domain:
             raise HTTPException(status_code=400, detail=f"Email must belong to organization domain: {org.domain}")
        
        # Generate invitation token
        invitation_token = str(uuid.uuid4())
        invitation_expires = datetime.utcnow() + timedelta(hours=48)
        
        # Create new user with invitation token
        new_user = User(
            email=invite_data.email,
            name=invite_data.name,
            password_hash=None,  # No password yet
            invitation_token=invitation_token,
            invitation_expires=invitation_expires
        )
        db.add(new_user)
        await db.flush()
        
        # Send invitation email
        try:
            email_service.send_invitation_email(
                to_email=invite_data.email,
                to_name=invite_data.name,
                org_name=org.name,
                token=invitation_token
            )
        except Exception as e:
            print(f"Failed to send invitation email: {str(e)}")
            # Continue anyway - user can be manually notified
    
    # 3. Create Membership (role=member)
    new_membership = Membership(
        user_id=new_user.id,
        organization_id=org_id,
        role="member"
    )
    db.add(new_membership)
    await db.commit()
    
    return MemberResponse(
        id=new_user.id,
        email=new_user.email,
        name=new_user.name,
        role="member"
    )
