from datetime import datetime, timedelta
from typing import Any, Union, Optional
from jose import jwt, JWTError
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db
from app.models import User
from app.core.hashing import verify_password, get_password_hash
from app.schemas import User as UserSchema

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login")

def create_access_token(*, subject: Union[str, int], expires_delta: Optional[timedelta] = None) -> str:
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> UserSchema:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise credentials_exception
        
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Inactive user"
        )
        
    return UserSchema.model_validate(user)

async def get_current_user_from_request(request: Request, db: Session) -> Optional[User]:
    try:
        # Tenta pegar o token do cookie
        token = request.cookies.get("access_token")
        if not token:
            # Tenta pegar o token do header de autorização
            auth_header = request.headers.get("Authorization")
            if auth_header and auth_header.startswith("Bearer "):
                token = auth_header.split(" ")[1]
            else:
                return None

        # Remove o prefixo "Bearer " se existir
        if token.startswith("Bearer "):
            token = token.split(" ")[1]

        try:
            payload = jwt.decode(
                token,
                settings.SECRET_KEY,
                algorithms=[settings.ALGORITHM]
            )
            email = payload.get("sub")
            if email is None:
                return None
        except JWTError:
            return None

        user = db.query(User).filter(User.email == email).first()
        if user is None:
            return None
            
        if not user.is_active:
            return None

        return user
    except Exception as e:
        print(f"Erro ao verificar usuário: {str(e)}")
        return None 