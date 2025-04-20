from fastapi import FastAPI, Request, Depends, HTTPException, status, File, UploadFile, Form, Body
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Annotated
import os
import uuid
from jose import JWTError, jwt
from fastapi.middleware.cors import CORSMiddleware
from starlette.templating import _TemplateResponse
from starlette.middleware.sessions import SessionMiddleware

from app.db.session import get_db
from app.core.security import create_access_token, get_current_user, get_current_user_from_request
from app.core.hashing import get_password_hash, verify_password
from app.models import User as UserModel, Document
from app.schemas import UserCreate, DocumentCreate, User as UserSchema
from app.core.config import settings
from app.core.storage import upload_file, delete_file, get_file_url
from app.core.google_auth import google_login, google_callback

app = FastAPI(title="GuardaDocs")

# Configuração de templates e arquivos estáticos
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

# Configuração do CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Adiciona o middleware de sessão
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.SECRET_KEY,
    max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
)

# Middleware para adicionar o usuário atual ao contexto dos templates
@app.middleware("http")
async def add_user_to_template(request: Request, call_next):
    try:
        response = await call_next(request)
        if isinstance(response, _TemplateResponse):
            response.context["user"] = await get_current_user_from_request(request, next(get_db()))
        return response
    except Exception as e:
        print(f"Erro no middleware: {str(e)}")
        return await call_next(request)

# Dependência para o banco de dados
def get_db_dependency():
    db = next(get_db())
    try:
        yield db
    finally:
        db.close()

# Rotas da interface web
@app.get("/", response_class=HTMLResponse)
async def home(
    request: Request,
    db: Annotated[Session, Depends(get_db_dependency)]
):
    print("Iniciando rota principal")
    try:
        user = await get_current_user_from_request(request, db)
        print(f"Usuário: {user}")
        if not user:
            print("Usuário não autenticado, mostrando página inicial")
            return templates.TemplateResponse(
                "index.html",
                {"request": request, "user": None}
            )
        
        try:
            print("Buscando documentos do usuário")
            documents = db.query(Document).filter(Document.user_id == user.id).all()
            print(f"Documentos encontrados: {len(documents)}")
            return templates.TemplateResponse(
                "home.html",
                {
                    "request": request,
                    "documents": documents,
                    "user": user,
                    "settings": settings
                }
            )
        except Exception as e:
            print(f"Erro ao carregar documentos: {str(e)}")
            return templates.TemplateResponse(
                "home.html",
                {
                    "request": request,
                    "documents": [],
                    "user": user,
                    "settings": settings,
                    "error": "Erro ao carregar documentos"
                }
            )
    except Exception as e:
        print(f"Erro na rota principal: {str(e)}")
        return templates.TemplateResponse(
            "error.html",
            {
                "request": request,
                "error": f"Erro interno: {str(e)}",
                "user": None
            }
        )

@app.get("/login", response_class=HTMLResponse)
async def login_page(
    request: Request,
    db: Annotated[Session, Depends(get_db_dependency)]
):
    user = await get_current_user_from_request(request, db)
    if user:
        return RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
    return templates.TemplateResponse("login.html", {"request": request, "user": None})

@app.post("/login")
async def login(
    request: Request,
    db: Session = Depends(get_db_dependency),
    email: str = Form(...),
    password: str = Form(...)
):
    try:
        user = db.query(UserModel).filter(UserModel.email == email).first()
        if not user or not verify_password(password, user.hashed_password):
            return templates.TemplateResponse(
                "login.html",
                {"request": request, "error": "Email ou senha inválidos", "user": None}
            )
        
        if not user.is_active:
            return templates.TemplateResponse(
                "login.html",
                {"request": request, "error": "Usuário inativo", "user": None}
            )
            
        access_token = create_access_token(subject=user.email)
        response = RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
        response.set_cookie(
            key="access_token",
            value=f"Bearer {access_token}",
            httponly=True,
            max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            expires=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            path="/",
            samesite="lax",
            secure=False  # Definir como True em produção com HTTPS
        )
        return response
    except Exception as e:
        print(f"Erro no login: {str(e)}")
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": "Erro ao fazer login", "user": None}
        )

@app.get("/register", response_class=HTMLResponse)
async def register_page(
    request: Request,
    db: Annotated[Session, Depends(get_db_dependency)]
):
    user = await get_current_user_from_request(request, db)
    if user:
        return RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
    return templates.TemplateResponse("register.html", {"request": request, "user": None})

@app.post("/register")
async def register(
    request: Request,
    db: Annotated[Session, Depends(get_db_dependency)],
    full_name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...)
):
    try:
        if db.query(UserModel).filter(UserModel.email == email).first():
            return templates.TemplateResponse(
                "register.html",
                {"request": request, "error": "Email já registrado", "user": None}
            )
            
        user = UserModel(
            full_name=full_name,
            email=email,
            hashed_password=get_password_hash(password)
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        
        access_token = create_access_token(subject=user.email)
        response = RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
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
        print(f"Erro no registro: {str(e)}")
        return templates.TemplateResponse(
            "register.html",
            {"request": request, "error": "Erro ao criar conta", "user": None}
        )

@app.get("/logout")
async def logout():
    response = RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    response.delete_cookie(key="access_token", path="/")
    response.delete_cookie(key="access_token")  # Tenta deletar também sem o path
    return response

@app.get("/documents", response_class=HTMLResponse)
async def documents_page(
    request: Request,
    db: Session = Depends(get_db_dependency)
):
    user = await get_current_user_from_request(request, db)
    if not user:
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": "Faça login para acessar seus documentos", "user": None}
        )
    
    try:
        documents = db.query(Document).filter(Document.user_id == user.id).all()
        return templates.TemplateResponse(
            "home.html",
            {"request": request, "documents": documents, "user": user}
        )
    except Exception as e:
        print(f"Erro ao carregar documentos: {str(e)}")
        return templates.TemplateResponse(
            "error.html",
            {"request": request, "error": "Erro ao carregar documentos", "user": user}
        )

@app.post("/api/v1/documents/")
async def upload_document(
    request: Request,
    title: str = Form(...),
    description: str = Form(None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db_dependency)
):
    user = await get_current_user_from_request(request, db)
    if not user:
        raise HTTPException(status_code=401, detail="Não autorizado")
    
    # Verifica o tamanho do arquivo
    content = await file.read()
    if len(content) > settings.MAX_UPLOAD_SIZE:
        raise HTTPException(status_code=400, detail="Arquivo muito grande")
    
    # Gera um nome único para o arquivo
    file_ext = os.path.splitext(file.filename)[1]
    storage_filename = f"{uuid.uuid4()}{file_ext}"
    
    try:
        # Faz upload do arquivo
        await upload_file(content, storage_filename)
        
        # Cria o documento no banco
        document = Document(
            original_filename=file.filename,
            storage_filename=storage_filename,
            title=title,
            description=description,
            content_type=file.content_type,
            file_size=len(content),
            user_id=user.id
        )
        db.add(document)
        db.commit()
        db.refresh(document)
        
        # Redireciona para a página de documentos
        return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
        
    except Exception as e:
        # Se houver erro, tenta deletar o arquivo do storage
        try:
            await delete_file(storage_filename)
        except:
            pass
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/documents/{document_id}/download")
async def download_document(
    request: Request,
    document_id: int,
    db: Session = Depends(get_db_dependency)
):
    user = await get_current_user_from_request(request, db)
    if not user:
        raise HTTPException(status_code=401, detail="Não autorizado")
    
    print(f"Buscando documento com ID: {document_id} para o usuário: {user.id}")
    document = db.query(Document).filter(
        Document.id == document_id,
        Document.user_id == user.id
    ).first()
    
    if not document:
        print(f"Documento não encontrado: {document_id}")
        raise HTTPException(status_code=404, detail="Documento não encontrado")
    
    print(f"Documento encontrado: {document.original_filename}, storage_filename: {document.storage_filename}")
    
    try:
        url = await get_file_url(document.storage_filename)
        print(f"URL gerada com sucesso: {url}")
        return RedirectResponse(url=url)
    except Exception as e:
        print(f"Erro ao gerar URL: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/v1/documents/{document_id}")
async def delete_document(
    request: Request,
    document_id: int,
    db: Session = Depends(get_db_dependency)
):
    user = await get_current_user_from_request(request, db)
    if not user:
        raise HTTPException(status_code=401, detail="Não autorizado")
    
    document = db.query(Document).filter(
        Document.id == document_id,
        Document.user_id == user.id
    ).first()
    
    if not document:
        raise HTTPException(status_code=404, detail="Documento não encontrado")
    
    try:
        # Deleta o arquivo do storage
        await delete_file(document.storage_filename)
        
        # Deleta o documento do banco
        db.delete(document)
        db.commit()
        
        return {"message": "Documento deletado com sucesso"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# API routes for users
@app.get("/api/v1/users/{user_id}", response_model=UserSchema)
async def get_user(
    user_id: int,
    current_user: UserSchema = Depends(get_current_user),
    db: Session = Depends(get_db_dependency)
):
    user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return UserSchema.model_validate(user)

@app.post("/api/v1/users/", response_model=dict)
async def create_user(
    user_data: UserCreate,
    db: Session = Depends(get_db_dependency)
):
    db_user = db.query(UserModel).filter(UserModel.email == user_data.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email já registrado")
    
    user = UserModel(
        email=user_data.email,
        full_name=user_data.full_name,
        hashed_password=get_password_hash(user_data.password)
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    return {"id": user.id, "message": "Usuário criado com sucesso"}

# API routes for authentication
@app.post("/api/v1/auth/register", response_model=UserSchema)
async def api_register(
    user_data: UserCreate,
    db: Session = Depends(get_db_dependency)
):
    db_user = db.query(UserModel).filter(UserModel.email == user_data.email).first()
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    user = UserModel(
        email=user_data.email,
        full_name=user_data.full_name,
        hashed_password=get_password_hash(user_data.password)
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return UserSchema.model_validate(user)

@app.post("/api/v1/auth/login")
async def api_login(
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db_dependency)
):
    user = db.query(UserModel).filter(UserModel.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        return RedirectResponse(
            url="/login?error=Invalid credentials",
            status_code=303
        )
    
    access_token = create_access_token(subject=user.email)
    response = RedirectResponse(url="/", status_code=303)
    response.set_cookie(
        key="access_token",
        value=f"Bearer {access_token}",
        httponly=True,
        max_age=1800,
        expires=1800,
        path="/",
        samesite="lax",
        secure=False  # Definir como True em produção com HTTPS
    )
    return response

@app.get("/api/v1/auth/me", response_model=UserSchema)
async def read_users_me(
    request: Request,
    db: Session = Depends(get_db_dependency)
):
    current_user = await get_current_user_from_request(request, db)
    if current_user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    return UserSchema.model_validate(current_user)

# Função auxiliar para verificar se o usuário é admin
async def get_current_admin(
    request: Request,
    db: Session = Depends(get_db_dependency)
) -> UserModel:
    current_user = await get_current_user_from_request(request, db)
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough privileges"
        )
    return current_user

# Rotas administrativas
@app.get("/admin", response_class=HTMLResponse)
async def admin_panel(
    request: Request,
    db: Session = Depends(get_db_dependency)
):
    try:
        # Verifica se o usuário é admin
        current_user = await get_current_admin(request, db)
        
        # Busca todos os usuários ordenados por data de criação
        users = db.query(UserModel).order_by(UserModel.created_at.desc()).all()
        
        # Prepara o contexto com todas as informações necessárias
        context = {
            "request": request,
            "user": current_user,  # Usuário atual para o menu
            "users": users,  # Lista de usuários para a tabela
            "error": request.query_params.get("error"),
            "success": request.query_params.get("success")
        }
        
        print(f"Carregando painel administrativo com {len(users)} usuários")
        return templates.TemplateResponse("admin.html", context)
        
    except HTTPException as he:
        # Se for erro de autenticação, redireciona para o login
        if he.status_code == status.HTTP_401_UNAUTHORIZED:
            return RedirectResponse(url="/login", status_code=302)
        # Se for erro de permissão, mostra mensagem de erro
        if he.status_code == status.HTTP_403_FORBIDDEN:
            return templates.TemplateResponse(
                "error.html",
                {
                    "request": request,
                    "user": await get_current_user_from_request(request, db),
                    "error": "Acesso negado. Apenas administradores podem acessar esta área."
                }
            )
        raise he
    except Exception as e:
        print(f"Erro ao carregar painel administrativo: {str(e)}")
        return templates.TemplateResponse(
            "admin.html",
            {
                "request": request,
                "user": current_user,
                "users": [],
                "error": f"Erro ao carregar lista de usuários: {str(e)}"
            }
        )

@app.get("/admin/users/{user_id}/documents", response_class=HTMLResponse)
async def get_user_documents(
    user_id: int,
    request: Request,
    db: Session = Depends(get_db_dependency)
):
    try:
        # Verifica se o usuário é admin
        current_user = await get_current_admin(request, db)
        
        # Busca o usuário alvo
        target_user = db.query(UserModel).filter(UserModel.id == user_id).first()
        if not target_user:
            raise HTTPException(status_code=404, detail="Usuário não encontrado")
        
        # Busca os documentos do usuário
        documents = db.query(Document).filter(Document.user_id == user_id).all()
        
        return templates.TemplateResponse(
            "admin_user_documents.html",
            {
                "request": request,
                "user": current_user,
                "target_user": target_user,
                "documents": documents
            }
        )
    except HTTPException as he:
        if he.status_code == status.HTTP_401_UNAUTHORIZED:
            return RedirectResponse(url="/login", status_code=302)
        if he.status_code == status.HTTP_403_FORBIDDEN:
            return templates.TemplateResponse(
                "error.html",
                {
                    "request": request,
                    "user": await get_current_user_from_request(request, db),
                    "error": "Acesso negado. Apenas administradores podem acessar esta área."
                }
            )
        raise he
    except Exception as e:
        print(f"Erro ao carregar documentos do usuário: {str(e)}")
        return templates.TemplateResponse(
            "error.html",
            {
                "request": request,
                "user": current_user,
                "error": f"Erro ao carregar documentos: {str(e)}"
            }
        )

@app.post("/admin/users/{user_id}/toggle-status")
async def toggle_user_status(
    user_id: int,
    request: Request,
    db: Session = Depends(get_db_dependency)
):
    try:
        # Verifica se o usuário é admin
        await get_current_admin(request, db)
        
        user = db.query(UserModel).filter(UserModel.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="Usuário não encontrado")
        
        if user.is_admin and not user.is_active:
            raise HTTPException(
                status_code=400,
                detail="Não é possível desativar um usuário administrador"
            )
        
        user.is_active = not user.is_active
        db.commit()
        
        status = "ativado" if user.is_active else "desativado"
        return {"message": f"Usuário {status} com sucesso"}
    except HTTPException as he:
        raise he
    except Exception as e:
        print(f"Erro ao alterar status do usuário: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Erro ao alterar status do usuário"
        )

@app.delete("/admin/users/{user_id}")
async def delete_user(
    user_id: int,
    request: Request,
    db: Session = Depends(get_db_dependency)
):
    try:
        # Verifica se o usuário é admin
        await get_current_admin(request, db)
        
        user = db.query(UserModel).filter(UserModel.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="Usuário não encontrado")
        
        if user.is_admin:
            raise HTTPException(
                status_code=400,
                detail="Não é possível excluir um usuário administrador"
            )
        
        # Deletar documentos do usuário
        documents = db.query(Document).filter(Document.user_id == user.id).all()
        for doc in documents:
            try:
                await delete_file(doc.storage_filename)
            except Exception as e:
                print(f"Erro ao deletar arquivo {doc.storage_filename}: {str(e)}")
            db.delete(doc)
        
        db.delete(user)
        db.commit()
        return {"message": "Usuário e seus documentos foram excluídos com sucesso"}
    except HTTPException as he:
        raise he
    except Exception as e:
        print(f"Erro ao excluir usuário: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Erro ao excluir usuário"
        )

@app.get("/admin/documents/{document_id}/download")
async def admin_download_document(
    document_id: int,
    request: Request,
    db: Session = Depends(get_db_dependency)
):
    # Verifica se o usuário é admin
    await get_current_admin(request, db)
    
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Documento não encontrado")
    
    return RedirectResponse(url=document.storage_filename)

@app.delete("/admin/documents/{document_id}")
async def admin_delete_document(
    document_id: int,
    request: Request,
    db: Session = Depends(get_db_dependency)
):
    # Verifica se o usuário é admin
    await get_current_admin(request, db)
    
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Documento não encontrado")
    
    await delete_file(document.storage_filename)
    db.delete(document)
    db.commit()
    return {"message": "Documento excluído com sucesso"}

@app.get("/login/google")
async def google_auth_login(request: Request):
    """Inicia o processo de login com o Google."""
    try:
        # URI de redirecionamento explícito
        redirect_uri = request.url_for('google_callback')
        return await google_login(request)
    except Exception as e:
        print(f"Erro ao iniciar login com Google: {str(e)}")
        return RedirectResponse(url='/login?error=google_auth_failed', status_code=303)

@app.get("/login/google/callback", name="google_callback")
async def google_auth_callback(request: Request, db: Session = Depends(get_db_dependency)):
    """Processa o retorno do login com Google."""
    try:
        return await google_callback(request, db)
    except Exception as e:
        print(f"Erro no callback do Google: {str(e)}")
        return RedirectResponse(url='/login?error=callback_failed', status_code=303)

@app.get("/profile", response_class=HTMLResponse)
async def profile_page(
    request: Request,
    db: Session = Depends(get_db_dependency)
):
    try:
        user = await get_current_user_from_request(request, db)
        if not user:
            return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
        
        # Busca os documentos do usuário
        documents = db.query(Document).filter(Document.user_id == user.id).all()
        
        return templates.TemplateResponse(
            "profile.html",
            {
                "request": request,
                "user": user,
                "documents": documents,
                "settings": settings
            }
        )
    except Exception as e:
        print(f"Erro ao carregar perfil: {str(e)}")
        return templates.TemplateResponse(
            "error.html",
            {
                "request": request,
                "error": f"Erro ao carregar perfil: {str(e)}",
                "user": None
            }
        ) 