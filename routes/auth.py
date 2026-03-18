from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import warnings

from database.connection import get_db
from database import models, schemas
from utils.authentication import hash_password, verify_password, generate_session_token, get_current_user

warnings.filterwarnings("ignore")

router = APIRouter(
    prefix="/User-Authentication",
    tags=["User Authentication"]
)

@router.post("/register", response_model=schemas.UserResponse)
async def register(
    user: schemas.UserCreate,
    db: AsyncSession = Depends(get_db)
):

    # Check if user already exists
    result = await db.execute(
        select(models.User).where(
            (models.User.name == user.name) | (models.User.email == user.email)
        )
    )
    existing_user = result.scalar_one_or_none()
    
    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="User with this name or email already exists"
        )
    
    # Hash password before storing
    hashed_password = hash_password(user.password)
    
    # Create new user
    new_user = models.User(
        name=user.name,
        password=hashed_password,
        email=user.email
    )
    
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    
    return new_user


@router.post('/login', response_model=schemas.TokenResponse)
async def login(
    user: schemas.LoginUser,
    db: AsyncSession = Depends(get_db)
):
    # Find user by name
    result = await db.execute(
        select(models.User).where(models.User.name == user.name)
    )
    user_record = result.scalar_one_or_none()
    
    if not user_record:
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password"
        )
    
    # Verify password
    if not verify_password(user.password, user_record.password):
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password"
        )
    
    # Generate and store session token
    token = generate_session_token()
    user_record.session_token = token
    
    await db.commit()
    await db.refresh(user_record)
    
    return {"access_token": token, "token_type": "simple"}


@router.post('/logout')
async def logout(
    current_user: models.User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Logout the current user by clearing their session token."""
    current_user.session_token = None
    
    await db.commit()
    
    return {"message": "Successfully logged out"}
