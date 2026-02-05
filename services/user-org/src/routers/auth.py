from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import IntegrityError
from pydantic import BaseModel, EmailStr
from typing import Optional
import uuid

from src.database import get_db
from src.models import User, Organization, Membership
from src.auth import get_password_hash, verify_password, create_access_token
from src.config import settings

router = APIRouter(prefix="/auth", tags=["auth"])

# Pydantic Models
class UserSignup(BaseModel):
    email: EmailStr
    password: str
    name: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class UserResponse(BaseModel):
    id: uuid.UUID
    email: str
    name: str
    organization_id: Optional[uuid.UUID]
    organization_name: Optional[str]
    role: Optional[str]

    class Config:
        from_attributes = True

@router.post("/signup", response_model=Token)
async def signup(user_data: UserSignup, db: AsyncSession = Depends(get_db)):
    # 1. Check if user exists
    result = await db.execute(select(User).where(User.email == user_data.email))
    if result.scalars().first():
        raise HTTPException(status_code=400, detail="Email already registered")

    # 2. Extract domain
    domain = user_data.email.split("@")[1]
    
    # 3. Check/Create Organization
    result = await db.execute(select(Organization).where(Organization.domain == domain))
    org = result.scalars().first()
    
    is_new_org = False
    if not org:
        # Create new Org
        org_name = domain.split(".")[0].capitalize() # e.g. google.com -> Google
        org = Organization(name=org_name, domain=domain)
        db.add(org)
        await db.flush() # Get ID
        is_new_org = True
    
    # 4. Create User
    hashed_password = get_password_hash(user_data.password)
    new_user = User(
        email=user_data.email,
        name=user_data.name,
        password_hash=hashed_password
    )
    db.add(new_user)
    await db.flush()
    
    # 5. Create Membership
    # Role: admin if new org, else member
    role = "admin" if is_new_org else "member"
    membership = Membership(
        user_id=new_user.id,
        organization_id=org.id,
        role=role
    )
    db.add(membership)
    
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=400, detail="Registration failed")
        
    # 6. Create Token
    access_token = create_access_token(data={"sub": str(new_user.id), "org_id": str(org.id), "role": role})
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/login", response_model=Token)
async def login(login_data: UserLogin, db: AsyncSession = Depends(get_db)):
    # 1. Find User
    result = await db.execute(select(User).where(User.email == login_data.email))
    user = result.scalars().first()
    
    if not user or not verify_password(login_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    # 2. Get Membership (assume single org for now)
    result = await db.execute(select(Membership).where(Membership.user_id == user.id))
    membership = result.scalars().first()
    
    if not membership:
        raise HTTPException(status_code=400, detail="User has no organization membership")
        
    # 3. Create Token
    access_token = create_access_token(
        data={
            "sub": str(user.id), 
            "org_id": str(membership.organization_id), 
            "role": membership.role
        }
    )
    return {"access_token": access_token, "token_type": "bearer"}

from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

async def get_current_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
        
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalars().first()
    if user is None:
        raise credentials_exception
    return user

class SetupPasswordRequest(BaseModel):
    token: str
    password: str

class TokenValidationResponse(BaseModel):
    valid: bool
    email: Optional[str] = None
    name: Optional[str] = None

@router.post("/validate-token", response_model=TokenValidationResponse)
async def validate_invitation_token(token: str, db: AsyncSession = Depends(get_db)):
    """Validate an invitation token without setting password"""
    from datetime import datetime
    
    result = await db.execute(select(User).where(User.invitation_token == token))
    user = result.scalars().first()
    
    if not user:
        return {"valid": False}
    
    # Check if token is expired
    if user.invitation_expires and user.invitation_expires < datetime.utcnow():
        return {"valid": False}
    
    return {
        "valid": True,
        "email": user.email,
        "name": user.name
    }

@router.post("/setup-password", response_model=Token)
async def setup_password(setup_data: SetupPasswordRequest, db: AsyncSession = Depends(get_db)):
    """Set password for invited user using invitation token"""
    from datetime import datetime
    
    # Find user by invitation token
    result = await db.execute(select(User).where(User.invitation_token == setup_data.token))
    user = result.scalars().first()
    
    if not user:
        raise HTTPException(status_code=400, detail="Invalid invitation token")
    
    # Check if token is expired
    if user.invitation_expires and user.invitation_expires < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Invitation token has expired")
    
    # Set password and clear invitation token
    user.password_hash = get_password_hash(setup_data.password)
    user.invitation_token = None
    user.invitation_expires = None
    
    await db.commit()
    
    # Get membership for token generation
    result = await db.execute(select(Membership).where(Membership.user_id == user.id))
    membership = result.scalars().first()
    
    if not membership:
        raise HTTPException(status_code=400, detail="User has no organization membership")
    
    # Create access token
    access_token = create_access_token(
        data={
            "sub": str(user.id),
            "org_id": str(membership.organization_id),
            "role": membership.role
        }
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=UserResponse)
async def read_users_me(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    # Fetch membership and org info
    result = await db.execute(select(Membership).where(Membership.user_id == current_user.id))
    membership = result.scalars().first()
    
    org_name = None
    org_id = None
    role = None
    
    if membership:
        result = await db.execute(select(Organization).where(Organization.id == membership.organization_id))
        org = result.scalars().first()
        if org:
            org_name = org.name
            org_id = org.id
        role = membership.role

    return {
        "id": current_user.id,
        "email": current_user.email,
        "name": current_user.name,
        "organization_id": org_id,
        "organization_name": org_name,
        "role": role
    }

