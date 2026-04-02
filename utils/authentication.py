import uuid
import bcrypt
from typing import Optional
from datetime import datetime, timedelta
from fastapi import Depends, HTTPException, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from database.models import User
from database.connection import get_db
from utils.settings import get_settings

settings = get_settings()


def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(
        plain_password.encode('utf-8'),
        hashed_password.encode('utf-8')
    )


def generate_session_token() -> str:
    return uuid.uuid4().hex


async def get_current_user(
    session_token: Optional[str] = Header(None, alias="session_token"),
    db: AsyncSession = Depends(get_db)
) -> User:

    if not session_token:
        raise HTTPException(
            status_code=401,
            detail="Session token is missing"
        )
    result = await db.execute(
        select(User).where(User.session_token == session_token)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired session token"
        )
    
    return user


async def get_current_user_from_query(
    session_token: str,
    db: AsyncSession = Depends(get_db)
) -> User:
    result = await db.execute(
        select(User).where(User.session_token == session_token)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired session token"
        )
    
    return user


