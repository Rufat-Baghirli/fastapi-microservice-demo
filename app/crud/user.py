from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import EmailStr

from app.crud.base import CRUDBase
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate
from app.services.security import hash_password

class CRUDUser(CRUDBase[User, UserCreate, UserUpdate]):
    async def create(self, db: AsyncSession, *, obj_in: UserCreate) -> User:
        """Override the create method to hash the password."""
        create_data = obj_in.model_dump()
        create_data.pop("password")
        db_obj = User(**create_data, hashed_password=hash_password(obj_in.password))
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def get_by_email(self, db: AsyncSession, *, email: EmailStr) -> Optional[User]:
        """Get user by email (user-specific method)."""
        res = await db.execute(select(User).where(User.email == email))
        return res.scalar_one_or_none()

    async def get_by_username(self, db: AsyncSession, *, username: str) -> Optional[User]:
        """Get user by username (user-specific method)."""
        res = await db.execute(select(User).where(User.username == username))
        return res.scalar_one_or_none()

# Create a single instance of the CRUDUser class
user = CRUDUser(User)