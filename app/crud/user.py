from typing import Optional, Sequence
from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import EmailStr

from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate
from app.services.security import hash_password

# ============================================================================
# READ Operations
# ============================================================================

async def get_by_id(db: AsyncSession, user_id: int) -> Optional[User]:
    """Get user by ID"""
    res = await db.execute(select(User).where(User.id == user_id))
    return res.scalar_one_or_none()

async def get_by_email(db: AsyncSession, email: EmailStr) -> Optional[User]:
    """Get user by email"""
    res = await db.execute(select(User).where(User.email == email))
    return res.scalar_one_or_none()

async def get_by_username(db: AsyncSession, username: str) -> Optional[User]:
    """Get user by username"""
    res = await db.execute(select(User).where(User.username == username))
    return res.scalar_one_or_none()

async def list_users(db: AsyncSession, limit: int = 50, offset: int = 0) -> Sequence[User]:
    """List users with pagination"""
    res = await db.execute(
        select(User)
        .order_by(User.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    return res.scalars().all()

# ============================================================================
# CREATE Operation
# ============================================================================

async def create(db: AsyncSession, data: UserCreate) -> User:
    """Create a new user"""
    user = User(
        email=str(data.email),
        username=data.username,
        hashed_password=hash_password(data.password),
        is_active=data.is_active
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user

# ============================================================================
# UPDATE Operation
# ============================================================================

async def patch(db: AsyncSession, user: User, data: UserUpdate) -> User:
    """Update user information"""
    if data.email is not None:
        user.email = str(data.email)
    if data.username is not None:
        user.username = data.username
    if data.password is not None:
        user.hashed_password = hash_password(data.password)
    if data.is_active is not None:
        user.is_active = data.is_active

    await db.commit()
    await db.refresh(user)
    return user

# ============================================================================
# DELETE Operation
# ============================================================================

async def remove(db: AsyncSession, user: User) -> None:
    """Delete a user"""
    await db.delete(user)
    await db.commit()