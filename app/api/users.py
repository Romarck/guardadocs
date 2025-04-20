from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models import User
from app.schemas import user
from app.core import security

router = APIRouter(prefix="/users", tags=["users"])

@router.get("/", response_model=List[user.User])
async def read_users(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """
    Retrieve users.
    """
    users = db.query(User).offset(skip).limit(limit).all()
    return users

@router.get("/{user_id}", response_model=user.User)
async def read_user(
    *,
    db: Session = Depends(get_db),
    user_id: int,
) -> Any:
    """
    Get user by ID.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user

@router.put("/{user_id}", response_model=user.User)
async def update_user(
    *,
    db: Session = Depends(get_db),
    user_id: int,
    user_in: user.UserUpdate,
) -> Any:
    """
    Update user.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    for field, value in user_in.dict(exclude_unset=True).items():
        if field == "password" and value:
            value = security.get_password_hash(value)
        setattr(user, field, value)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@router.delete("/{user_id}", response_model=user.User)
async def delete_user(
    *,
    db: Session = Depends(get_db),
    user_id: int,
) -> Any:
    """
    Delete user.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    db.delete(user)
    db.commit()
    return user

@router.post("/", response_model=user.User)
async def create_user(
    *,
    db: Session = Depends(get_db),
    user_in: user.UserCreate,
) -> Any:
    """
    Create new user.
    """
    user = db.query(User).filter(User.email == user_in.email).first()
    if user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    user = User(
        email=user_in.email,
        hashed_password=security.get_password_hash(user_in.password),
        full_name=user_in.full_name
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user 