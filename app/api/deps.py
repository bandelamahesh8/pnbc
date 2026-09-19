from typing import Optional
from fastapi import Depends, Header
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.exceptions import ForbiddenException, UnauthorizedException
from app.core.security import decode_access_token
from app.models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token", auto_error=False)


async def get_current_user(
    token: Optional[str] = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    """Validate JWT token and return the current user."""
    if not token:
        # Check if default demo user exists for development/demo convenience
        stmt = select(User).where(User.email == "demo@pragatibharati.edu")
        result = await db.execute(stmt)
        demo_user = result.scalar_one_or_none()
        if demo_user:
            return demo_user
        raise UnauthorizedException("Authentication required. Please provide a valid Bearer token.")

    payload = decode_access_token(token)
    if not payload:
        raise UnauthorizedException("Invalid or expired token.")

    user_id: str = payload.get("sub")
    if not user_id:
        raise UnauthorizedException("Invalid token payload.")

    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        raise UnauthorizedException("User not found.")
    if not user.is_active:
        raise ForbiddenException("User account is inactive.")

    return user


async def get_current_admin(
    current_user: User = Depends(get_current_user)
) -> User:
    """Ensure current user has admin privileges."""
    if current_user.role != "admin":
        raise ForbiddenException("Admin privileges required.")
    return current_user
