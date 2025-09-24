from datetime import datetime, timedelta, timezone
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, EmailStr
from jose import JWTError, jwt
from app.db.session import get_session
from app.schemas.user import UserOut, UserUpdate, UserChangePassword
from app.crud import user as user_crud
from app.services.security import verify_password
from app.core.config import settings

router = APIRouter(tags=["authentication"])
security = HTTPBearer()

# ============================================================================
# PYDANTIC SCHEMAS
# ============================================================================

class LoginRequest(BaseModel):
    """For the login endpoint"""
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    """Token response model"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserOut

class RefreshTokenRequest(BaseModel):
    """For the refresh token"""
    refresh_token: str

# ============================================================================
# JWT HELPER FUNCTIONS
# ============================================================================

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create access token"""
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "type": "access"
    })

    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_refresh_token(user_id: int) -> str:
    """Create refresh token"""
    expire = datetime.now(timezone.utc) + timedelta(days=7)
    to_encode = {
        "sub": str(user_id),
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "type": "refresh"
    }

    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def verify_token(token: str) -> dict:
    """Verify the token"""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])

        # Expiry check
        exp = payload.get("exp")
        if exp and datetime.fromtimestamp(exp, timezone.utc) < datetime.now(timezone.utc):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired"
            )

        return payload

    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )


# ============================================================================
# DEPENDENCIES
# ============================================================================

async def get_current_user(
        credentials: HTTPAuthorizationCredentials = Depends(security),
        db: AsyncSession = Depends(get_session)
) -> UserOut:
    """Current user dependency"""

    token = credentials.credentials
    payload = verify_token(token)

    # Token type check
    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type"
        )

    # User ID extract
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload"
        )

    # User fetch from database
    user = await user_crud.get_by_id(db, int(user_id))
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )

    return UserOut.model_validate(user)


async def get_current_active_user(
    current_user: UserOut = Depends(get_current_user)
) -> UserOut:
    """Active user dependency"""
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

# ============================================================================
# AUTH ENDPOINTS
# ============================================================================

@router.post("/login", response_model=TokenResponse)
async def login(
        login_data: LoginRequest,
        db: AsyncSession = Depends(get_session)
):
    """User login - returns JWT token"""

    # Find user with email
    user = await user_crud.get_by_email(db, login_data.email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    # Password verify
    if not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    # Create token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id)},
        expires_delta=access_token_expires
    )

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,  # seconds
        user=UserOut.model_validate(user)
    )

@router.post("/refresh", response_model=TokenResponse)
async def refresh_access_token(
        refresh_data: RefreshTokenRequest,
        db: AsyncSession = Depends(get_session)
):
    """Get the new access token with a refresh token"""

    payload = verify_token(refresh_data.refresh_token)

    # Token type check
    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type"
        )

    # User fetch
    user_id = int(payload.get("sub"))
    user = await user_crud.get_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )

    # New access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id)},
        expires_delta=access_token_expires
    )

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=UserOut.model_validate(user)
    )

@router.get("/me", response_model=UserOut)
async def get_current_user_info(
        current_user: UserOut = Depends(get_current_active_user)
):
    """Get current user information"""
    return current_user

@router.post("/logout")
async def logout():
    """Logout - delete client-side token"""
    return {"message": "Successfully logged out"}

# ============================================================================
# PROTECTED ROUTES EXAMPLE
# ============================================================================

@router.get("/protected")
async def protected_route(
        current_user: UserOut = Depends(get_current_active_user)
):
    """Protected route example"""
    return {
        "message": f"Hello {current_user.username}, this is protected!",
        "user_id": current_user.id,
        "timestamp": datetime.now(timezone.utc)
    }

@router.put("/change-password")
async def change_password(
        passwords: UserChangePassword,
        current_user: UserOut = Depends(get_current_active_user),
        db: AsyncSession = Depends(get_session)
):
    """Change password"""

    # Current user fetch (full data)
    user = await user_crud.get_by_id(db, current_user.id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Old password verify
    if not verify_password(passwords.old_password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid current password"
        )

    # Password update
    await user_crud.patch(db, user, UserUpdate(username=user.username,password=passwords.new_password))

    return {"message": "Password changed successfully"}