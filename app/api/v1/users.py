from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_session
from app.schemas.user import UserCreate, UserUpdate, UserOut
from app.crud import user as user_crud

router = APIRouter(tags=["users"])

@router.get("/users", response_model=list[UserOut])
async def list_users(limit: int = 50, offset: int = 0, db: AsyncSession = Depends(get_session)):
    users = await user_crud.list_users(db, limit=limit, offset=offset)
    return users

@router.get("/users/{user_id}", response_model=UserOut)
async def get_user(user_id: int, db: AsyncSession = Depends(get_session)):
    u = await user_crud.get_by_id(db, user_id)
    if not u:
        raise HTTPException(status_code=404, detail="user not found")
    return u

@router.post("/users", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def create_user(payload: UserCreate, db: AsyncSession = Depends(get_session)):
    """
    Create a new user.
    Senior approach:
    - Validation handled by Pydantic (UserCreate)
    - Email type conversion handled in CRUD layer
    - Endpoint only handles business logic (existence check + HTTP response)
    """

    # 1. Check if email already exists
    existing_user = await user_crud.get_by_email(db, str(payload.email))
    if existing_user:
        raise HTTPException(status_code=409, detail="Email already registered")

    # 2. Create user (CRUD handles hashing and type conversion)
    new_user = await user_crud.create(db, payload)

    # 3. Return user output
    return new_user
@router.patch("/users/{user_id}", response_model=UserOut)
async def update_user(user_id: int, payload: UserUpdate, db: AsyncSession = Depends(get_session)):
    u = await user_crud.get_by_id(db, user_id)
    if not u:
        raise HTTPException(status_code=404, detail="user not found")
    u = await user_crud.patch(db, u, payload)
    return u

@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user_id: int, db: AsyncSession = Depends(get_session)):
    u = await user_crud.get_by_id(db, user_id)
    if not u:
        raise HTTPException(status_code=404, detail="user not found")
    await user_crud.remove(db, u)
    return None
