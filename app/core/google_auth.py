from typing import Optional
import os
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request as GoogleRequest
from google.oauth2 import id_token
import google.auth.transport.requests
from app.core.config import settings
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
import httpx

from app.core.security import create_access_token
from app.db.session import get_db
from app.models.user import User
from app.crud.crud_user import user as crud_user
from app.schemas.user import UserCreate

router = APIRouter()

SCOPES = [
    "https://www.googleapis.com/auth/userinfo.profile",
    "https://www.googleapis.com/auth/userinfo.email",
    "openid"
]

CLIENT_SECRETS_FILE = os.path.join(os.path.dirname(__file__), "client_secrets.json")

GOOGLE_CLIENT_ID = settings.GOOGLE_CLIENT_ID
GOOGLE_CLIENT_SECRET = settings.GOOGLE_CLIENT_SECRET
GOOGLE_REDIRECT_URI = settings.GOOGLE_REDIRECT_URI

def create_flow(redirect_uri: str) -> Flow:
    """Create a Google OAuth2 flow instance."""
    try:
        flow = Flow.from_client_secrets_file(
            CLIENT_SECRETS_FILE,
            scopes=SCOPES,
            redirect_uri=redirect_uri
        )
        return flow
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error creating Google OAuth flow: {str(e)}"
        )

async def get_google_token(code: str) -> Optional[dict]:
    """Exchange authorization code for access token."""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "client_id": settings.GOOGLE_CLIENT_ID,
                    "client_secret": settings.GOOGLE_CLIENT_SECRET,
                    "code": code,
                    "grant_type": "authorization_code",
                    "redirect_uri": settings.GOOGLE_REDIRECT_URI,
                }
            )
            return response.json() if response.status_code == 200 else None
        except httpx.RequestError:
            return None

async def get_google_user_info(access_token: str) -> Optional[dict]:
    """Get user info from Google using access token."""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                "https://www.googleapis.com/oauth2/v1/userinfo",
                headers={"Authorization": f"Bearer {access_token}"}
            )
            return response.json() if response.status_code == 200 else None
        except httpx.RequestError:
            return None

@router.get("/login/google")
async def google_login():
    auth_url = f"https://accounts.google.com/o/oauth2/v2/auth"
    params = {
        "client_id": GOOGLE_CLIENT_ID,
        "redirect_uri": GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": "email profile",
    }
    return Response(status_code=302, headers={"Location": f"{auth_url}?{'&'.join(f'{k}={v}' for k, v in params.items())}"})

@router.get("/login/google/callback")
async def google_callback(request: Request, code: str, db: Session = Depends(get_db)):
    token_url = "https://oauth2.googleapis.com/token"
    async with httpx.AsyncClient() as client:
        token_response = await client.post(
            token_url,
            data={
                "client_id": GOOGLE_CLIENT_ID,
                "client_secret": GOOGLE_CLIENT_SECRET,
                "code": code,
                "grant_type": "authorization_code",
                "redirect_uri": GOOGLE_REDIRECT_URI,
            },
        )
        
        if token_response.status_code != 200:
            raise HTTPException(status_code=400, detail="Could not validate Google credentials")
        
        token_data = token_response.json()
        user_info_response = await client.get(
            "https://www.googleapis.com/oauth2/v2/userinfo",
            headers={"Authorization": f"Bearer {token_data['access_token']}"},
        )
        
        if user_info_response.status_code != 200:
            raise HTTPException(status_code=400, detail="Could not get user info from Google")
        
        user_info = user_info_response.json()
        
        # Check if user exists by google_id
        db_user = crud_user.get_by_google_id(db, google_id=user_info["id"])
        
        if not db_user:
            # Check if user exists by email
            db_user = crud_user.get_by_email(db, email=user_info["email"])
            
            if db_user:
                # Update existing user with google_id
                db_user = crud_user.update(db, db_obj=db_user, obj_in={"google_id": user_info["id"]})
            else:
                # Create new user
                user_in = UserCreate(
                    email=user_info["email"],
                    full_name=user_info["name"],
                    google_id=user_info["id"],
                    is_active=True,
                )
                db_user = crud_user.create(db, obj_in=user_in)
        
        response = Response(status_code=302, headers={"Location": "/"})
        access_token = create_access_token(subject=db_user.id)
        response.set_cookie(
            key="access_token",
            value=f"Bearer {access_token}",
            httponly=True,
            max_age=1800,
            expires=1800,
        )
        return response 