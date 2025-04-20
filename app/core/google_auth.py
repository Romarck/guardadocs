from authlib.integrations.starlette_client import OAuth
from starlette.requests import Request
from starlette.responses import RedirectResponse
from app.core.config import settings
from app.db.session import get_db
from app.models.user import User
from app.core.security import create_access_token
from sqlalchemy.orm import Session
from fastapi import Depends

oauth = OAuth()

oauth.register(
    name='google',
    client_id=settings.GOOGLE_CLIENT_ID,
    client_secret=settings.GOOGLE_CLIENT_SECRET,
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={
        'scope': 'openid email profile'
    }
)

async def get_google_user(request: Request):
    """Obtém o usuário do Google após autenticação bem-sucedida."""
    try:
        user = await oauth.google.parse_id_token(request)
        return user
    except Exception as e:
        print(f"Erro ao obter usuário do Google: {str(e)}")
        return None

async def google_login(request: Request):
    """Inicia o processo de login com o Google."""
    try:
        redirect_uri = str(request.url_for('google_callback'))
        print(f"Redirect URI: {redirect_uri}")
        return await oauth.google.authorize_redirect(request, redirect_uri)
    except Exception as e:
        print(f"Erro ao iniciar login com Google: {str(e)}")
        return RedirectResponse(url='/login?error=google_auth_failed', status_code=303)

async def google_callback(request: Request, db: Session = Depends(get_db)):
    """Processa o callback do Google após autenticação."""
    try:
        # Obtém o token de acesso
        token = await oauth.google.authorize_access_token(request)
        if not token:
            return RedirectResponse(url='/login?error=no_token', status_code=303)
            
        # Obtém as informações do usuário
        user_info = await oauth.google.parse_id_token(request)
        if not user_info or 'email' not in user_info:
            return RedirectResponse(url='/login?error=no_user_info', status_code=303)
        
        # Verifica se o usuário já existe
        user = db.query(User).filter(User.email == user_info['email']).first()
        
        if not user:
            # Cria um novo usuário
            user = User(
                email=user_info['email'],
                full_name=user_info.get('name', ''),
                is_active=True,
                is_google_user=True
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        
        # Cria o token de acesso
        access_token = create_access_token(subject=user.email)
        
        # Redireciona para a página inicial com o token
        response = RedirectResponse(url='/', status_code=303)
        response.set_cookie(
            key="access_token",
            value=f"Bearer {access_token}",
            httponly=True,
            max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            path="/",
            samesite="lax"
        )
        return response
        
    except Exception as e:
        print(f"Erro na autenticação com Google: {str(e)}")
        return RedirectResponse(url='/login?error=google_auth_failed', status_code=303) 