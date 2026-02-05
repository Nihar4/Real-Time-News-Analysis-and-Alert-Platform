from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from ..schemas import SignUpIn, LoginIn, TokenOut, UserOut
from ..models import User
from ..db import get_session
from ..auth import hash_password, verify_password, create_access_token

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/signup", response_model=UserOut, status_code=201)
async def signup(payload: SignUpIn, session: AsyncSession = Depends(get_session)):
    # Check if email exists (case-insensitive)
    result = await session.execute(
        select(User).where(func.lower(User.email) == func.lower(payload.email))
    )
    existing = result.scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=409, detail="Email already registered")

    user = User(email=payload.email, password_hash=hash_password(payload.password))
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return UserOut(id=user.id, email=user.email, created_at=user.created_at)

@router.post("/login", response_model=TokenOut)
async def login(payload: LoginIn, session: AsyncSession = Depends(get_session)):
    result = await session.execute(
        select(User).where(func.lower(User.email) == func.lower(payload.email))
    )
    user = result.scalar_one_or_none()
    if not user or not verify_password(user.password_hash, payload.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    token, hours = create_access_token(user.id, user.email)
    return TokenOut(access_token=token, expires_in_hours=hours)
