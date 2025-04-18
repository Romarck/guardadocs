import google.oauth2.credentials
import os
from flask import Flask, render_template, request, redirect, url_for, send_from_directory, flash, abort
from werkzeug.utils import secure_filename
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user
from flask_mail import Mail, Message, email_dispatched
from itsdangerous import URLSafeTimedSerializer
from werkzeug.security import generate_password_hash, check_password_hash
import uuid
import logging
from flask_login import current_user
from sqlalchemy.exc import SQLAlchemyError
from google_auth_oauthlib.flow import Flow
from google.oauth2 import id_token
from google.auth.transport import requests
import json
from functools import wraps

UPLOAD_FOLDER = 'Upload'
ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx'}

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your_default_secret_key')
app.config['SECURITY_PASSWORD_SALT'] = os.environ.get('SECURITY_PASSWORD_SALT', 'your_default_security_salt')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
# Configurações do Flask-Mail
app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', 587))
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER')

# Carrega as credenciais do cliente OAuth do Google a partir de um arquivo JSON
try:
    with open("client_secret.json", "r") as f:
        credentials_data = json.load(f)
        GOOGLE_CLIENT_ID = credentials_data["web"]["client_id"]
        GOOGLE_CLIENT_SECRET = credentials_data["web"]["client_secret"]
        GOOGLE_PROJECT_ID = credentials_data["web"]["project_id"]
except FileNotFoundError:
    print("Erro: Arquivo client_secret.json não encontrado.")
    exit(1)
except json.JSONDecodeError:
    print("Erro: O arquivo client_secret.json não é um JSON válido.")
    exit(1)

app.config["GOOGLE_CLIENT_ID"] = GOOGLE_CLIENT_ID

# Configuração do SQLAlchemy
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'postgresql://usuario:senha@host/nome_do_banco')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # Desabilita avisos de modificação

db = SQLAlchemy(app)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

mail = Mail(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

s = URLSafeTimedSerializer(app.config['SECRET_KEY'])
# Modelos do banco de dados
class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    password_hash = db.Column(db.String(128))
    confirmed = db.Column(db.Boolean, default=False)
    confirmation_token = db.Column(db.String(100), unique=True)
    reset_token = db.Column(db.String(100), unique=True)
    is_admin = db.Column(db.Boolean, default=False)
    documents = db.relationship('Document', backref='user', lazy=True)
    google_id = db.Column(db.String(255), unique=True, nullable=True)  # Novo campo para ID do Google

    def __repr__(self):
        return f'<User {self.email}>'

    def set_password(self, password):
        """Define a senha do usuário de forma segura usando hash."""
        self.password_hash = generate_password_hash(password)

class Document(db.Model):
    __tablename__ = 'documents'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    filename = db.Column(db.String(200), nullable=False)
    filepath = db.Column(db.String(200), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    def __repr__(self):
        return f'<Document {self.filename}>'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def send_confirmation_email(user_email, token):
    """Envia um e-mail de confirmação de registro para o usuário.

    Args:
        user_email (str): O endereço de e-mail do usuário.
        token (str): O token de confirmação gerado.
    """
    msg = Message('Confirmação de Registro', sender=app.config['MAIL_DEFAULT_SENDER'], recipients=[user_email])
    confirm_url = url_for('confirm_email', token=token, _external=True)
    msg.body = f"Obrigado por se registrar! Por favor, confirme seu e-mail clicando no link: {confirm_url}"
    try:
        mail.send(msg)
    except Exception as e:
        logger.error(f"Erro ao enviar e-mail: {e}")
        abort(500, description="Erro ao enviar e-mail.")

def send_reset_password_email(user_email, token):
    msg = Message('Redefinição de Senha', sender=app.config['MAIL_DEFAULT_SENDER'], recipients=[user_email])
    reset_url = url_for('reset_password', token=token, _external=True)
    msg.body = f"Para redefinir sua senha, por favor, acesse o link: {reset_url}"
    mail.send(msg)
        
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')

@app.route("/google_login")
def google_login():
    flow = Flow.from_client_config(
        client_config= {
            "web": {
                "client_id": app.config["GOOGLE_CLIENT_ID"],
                "client_secret": GOOGLE_CLIENT_SECRET,
                "redirect_uris": [url_for("google_callback", _external=True)],
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://accounts.google.com/o/oauth2/token"
            }
        },
        scopes=["openid", "https://www.googleapis.com/auth/userinfo.profile", "https://www.googleapis.com/auth/userinfo.email"],
        redirect_uri=url_for("google_callback", _external=True),
    )
    authorization_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true',
        prompt='consent'
    )
    return redirect(authorization_url)

@app.route("/google_callback")
def google_callback():
    try:
        code = request.args.get("code")
        flow = Flow.from_client_config(
            client_config={
                "web": {
                    "client_id": app.config["GOOGLE_CLIENT_ID"],
                    "client_secret": GOOGLE_CLIENT_SECRET,
                    "redirect_uris": [url_for("google_callback", _external=True)],
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token"
                }
            },
            scopes=["openid", "https://www.googleapis.com/auth/userinfo.profile", "https://www.googleapis.com/auth/userinfo.email"],
            redirect_uri=url_for("google_callback", _external=True),
        )
        
        try:
            flow.fetch_token(code=code)
        except Warning:
            # Ignore scope change warning
            pass

        credentials = flow.credentials
        request_session = requests.Request()
        id_info = id_token.verify_oauth2_token(
            id_token=credentials.id_token,
            request=request_session,
            audience=app.config["GOOGLE_CLIENT_ID"]
        )
        
        user = User.query.filter_by(email=id_info["email"]).first()
        if not user:
            user = User(
                name=id_info["name"],
                email=id_info["email"],
                google_id=id_info["sub"],
                confirmed=True,
                phone=id_info["sub"]
            )
            db.session.add(user)
            db.session.commit()

        login_user(user)
        return redirect(url_for("dashboard"))

    except Exception as e:
        logger.error(f"Erro ao autenticar com o Google: {e}")
        db.session.rollback()
        flash('Erro ao fazer login com o Google. Por favor, tente novamente.')
        return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email'].lower()  # Convert email to lowercase for consistency
        phone = request.form['phone'].strip()  # Remove leading/trailing whitespace from phone
        password = request.form['password']        
        try:
            if not all([name, email, phone, password]):
                raise ValueError("Todos os campos são obrigatórios.")
            if len(password) < 6:
                raise ValueError("A senha deve ter pelo menos 6 caracteres.")
            
            user = User.query.filter_by(email=email).first()
            if user:
                flash('Este endereço de e-mail já está cadastrado.')
                return redirect(url_for('register'))
            
            token = str(uuid.uuid4())
            new_user = User(name=name, email=email, phone=phone, confirmation_token=token)
            new_user.set_password(password)
            db.session.add(new_user)
            db.session.commit()
            
            send_confirmation_email(email, token)

            flash(f'Um e-mail de confirmação foi enviado para {email}. Por favor, verifique sua caixa de entrada.')
            return redirect(url_for('login'))
        except SQLAlchemyError as e:
            db.session.rollback()
            logger.error(f"Erro ao registrar usuário: {e}")
            abort(500, description="Erro interno ao registrar usuário.")
        except ValueError as e:
            flash(str(e))
            return redirect(url_for('register'))
    return render_template('register.html')

@app.route('/confirm_email/<token>')
def confirm_email(token):
        
    try:
        user = User.query.filter_by(confirmation_token=token).first()
        if user is None:
            abort(404, description='O token é inválido ou expirou!')
        
        user.confirmed = True
        user.confirmation_token = None
        db.session.commit()
        return render_template('confirmation_success.html')
    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error(f"Erro ao confirmar email: {e}")
        abort(500, description="Erro interno ao confirmar email!")
    
    


    


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email'].lower()
        password = request.form['password']        
        try:
            user = User.query.filter_by(email=email).first()        

            if user and check_password_hash(user.password_hash, password):
                if not user.confirmed:
                    flash('Por favor, confirme seu registro primeiro.')
                    return redirect(url_for('login'))  # Redireciona de volta para a página de login
                login_user(user)            
                return redirect(url_for('dashboard')) # Redireciona para o dashboard
            
            # Caso as credenciais estejam incorretas
            flash('Email ou senha inválidos.')
        except SQLAlchemyError as e:
            db.session.rollback()
            logger.error(f"Erro ao fazer login: {e}")
            abort(500, description="Erro interno ao fazer login.")


    return render_template('login.html')


@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form['email'].lower()
        try:
            user = User.query.filter_by(email=email).first()
            if user:
                token = s.dumps(user.email, salt=app.config['SECURITY_PASSWORD_SALT'])
                user.reset_token = token
                db.session.commit()
                send_reset_password_email(user.email, token)
                flash('Um e-mail com instruções para redefinir sua senha foi enviado para o seu endereço de e-mail.')
            else:
                flash('Este endereço de e-mail não está cadastrado.')
            return redirect(url_for('login'))
        except SQLAlchemyError as e:
            db.session.rollback()
            logger.error(f"Erro ao solicitar redefinição de senha: {e}")
            abort(500, description="Erro interno ao solicitar redefinição de senha.")

    return render_template('forgot_password.html')


@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    try:
        email = s.loads(token, salt=app.config['SECURITY_PASSWORD_SALT'], max_age=3600)
        user = User.query.filter_by(email=email).first()
        if not user or user.reset_token != token:
            flash('O token é inválido ou expirou.')
            return redirect(url_for('login'))
    
        if request.method == 'POST':
            password = request.form['password']
            confirm_password = request.form['confirm_password']
    
            if password != confirm_password:
                flash('As senhas não coincidem.')
                return render_template('reset_password.html', token=token)
            
            if len(password) < 6:
                flash("A senha deve ter pelo menos 6 caracteres.")
                return render_template('reset_password.html', token=token)
            user.set_password(password)
            user.reset_token = None
            db.session.commit()
            flash('Sua senha foi redefinida com sucesso. Faça login com sua nova senha.')
            return redirect(url_for('login'))
        
        return render_template('reset_password.html', token=token)
    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error(f"Erro ao redefinir senha: {e}")
        abort(500, description="Erro interno ao redefinir senha.")

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')

@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload_file():
    try:
        if request.method == 'POST':
            if 'file' not in request.files:
                flash('Nenhum arquivo selecionado.')
                return redirect(request.url)
            file = request.files['file']
            title = request.form['title']
            description = request.form['description']
            if file.filename == '':
                flash('Nenhum arquivo selecionado.')
                return redirect(request.url)
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                user_folder = os.path.join(app.config['UPLOAD_FOLDER'], current_user.phone)
                os.makedirs(user_folder, exist_ok=True)
                filepath = os.path.join(user_folder, filename)
                file.save(filepath)
                new_document = Document(title=title, description=description, filename=filename, filepath=filepath, user_id=current_user.id)
                db.session.add(new_document)
                db.session.commit()
                flash('Arquivo enviado com sucesso!')
                return redirect(url_for('dashboard'))
            else:
                flash('Formato de arquivo não permitido.')
                return redirect(request.url)
            
            if file.content_length > 16 * 1024 * 1024:  # 16MB
                flash("Tamanho do arquivo excede o limite permitido de 16MB.")
                return redirect(request.url)
    except SQLAlchemyError as e:
            db.session.rollback()
            logger.error(f"Erro ao fazer upload do arquivo: {e}")
            abort(500, description="Erro interno ao fazer upload do arquivo.")
    except Exception as e:
            logger.error(f"Erro ao fazer upload do arquivo: {e}")
            flash(f"Ocorreu um erro: {e}")
            return redirect(request.url)
    return render_template('upload.html')

@app.route('/list_documents')
@login_required
def list_documents():
    documents = Document.query.filter_by(user_id=current_user.id).all()
    return render_template('list_documents.html', documents=documents)

@app.route('/download/<int:document_id>')
@login_required
def download_document(document_id):    
    try:
        document = Document.query.get_or_404(document_id)
        if document.user_id != current_user.id and not current_user.is_admin:
            flash('Você não tem permissão para baixar este arquivo.')
            return redirect(url_for('list_documents'))
        
        directory, filename = os.path.split(document.filepath)
        return send_from_directory(directory, filename, as_attachment=True)
    except SQLAlchemyError as e:
        logger.error(f"Erro ao fazer download do arquivo: {e}")
        abort(500, description="Erro interno ao fazer download do arquivo.")


@app.route('/edit_document/<int:document_id>', methods=['GET', 'POST'])
@login_required
def edit_document(document_id):
    try:
        document = Document.query.get_or_404(document_id)
        if document.user_id != current_user.id:
            flash('Você não tem permissão para editar este arquivo.')
            return redirect(url_for('list_documents'))
        
        if request.method == 'POST':
            document.title = request.form['title']
            document.description = request.form['description']
            db.session.commit()
            flash('Documento atualizado com sucesso!')
            return redirect(url_for('list_documents'))
        
        return render_template('edit_document.html', document=document)
    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error(f"Erro ao editar documento: {e}")
        abort(500, description="Erro interno ao editar documento.")
    

@app.route('/delete_document/<int:document_id>', methods=['POST'])
@login_required
def delete_document(document_id):
    try:
        document = Document.query.get_or_404(document_id)
        if document.user_id != current_user.id:
            flash('Você não tem permissão para excluir este arquivo.')
            return redirect(url_for('list_documents'))
        
        filepath = document.filepath
        try:
            os.remove(filepath)
        except FileNotFoundError:
            flash('Arquivo não encontrado no sistema de arquivos.')
        except Exception as e:
            flash(f'Erro ao excluir o arquivo: {e}')
            logger.error(f"Erro ao excluir o arquivo: {e}")
            abort(500, description="Erro interno ao excluir arquivo.")
        
        db.session.delete(document)
        db.session.commit()
        flash('Documento excluído com sucesso!')
        return redirect(url_for('list_documents'))
    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error(f"Erro ao excluir documento: {e}")
        abort(500, description="Erro interno ao excluir documento.")

@app.route('/document/<int:document_id>')
@login_required
def view_document(document_id):
    try:
        document = Document.query.get_or_404(document_id)
        if document.user_id != current_user.id:
            flash('Você não tem permissão para visualizar este arquivo.')
            return redirect(url_for('list_documents'))
        
        return render_template('upload.html')
    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error(f"Erro ao visualizar documento: {e}")
        abort(500, description="Erro interno ao visualizar documento.")

# Função para verificar se o usuário é administrador
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('Acesso negado. Apenas administradores podem acessar esta página.', 'danger')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

# Rotas administrativas
@app.route('/admin')
@login_required
@admin_required
def admin_dashboard():
    return render_template('admin/dashboard.html')

@app.route('/admin/users')
@login_required
@admin_required
def admin_users():
    users = User.query.all()
    return render_template('admin/users.html', users=users)

@app.route('/admin/users/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_edit_user(user_id):
    user = User.query.get_or_404(user_id)
    if request.method == 'POST':
        user.name = request.form['name']
        user.email = request.form['email']
        user.phone = request.form['phone']
        if request.form['password']:
            user.set_password(request.form['password'])
        user.confirmed = 'confirmed' in request.form
        db.session.commit()
        flash('Usuário atualizado com sucesso!', 'success')
        return redirect(url_for('admin_users'))
    return render_template('admin/edit_user.html', user=user)

@app.route('/admin/users/<int:user_id>/delete', methods=['POST'])
@login_required
@admin_required
def admin_delete_user(user_id):
    user = User.query.get_or_404(user_id)
    
    if user.is_admin:
        flash('Não é possível excluir um usuário administrador.', 'danger')
        return redirect(url_for('admin_dashboard'))
    
    # Primeiro, excluir todos os documentos do usuário
    documents = Document.query.filter_by(user_id=user.id).all()
    for doc in documents:
        # Excluir o arquivo físico
        try:
            if os.path.exists(doc.filepath):
                os.remove(doc.filepath)
        except Exception as e:
            print(f"Erro ao excluir arquivo {doc.filepath}: {str(e)}")
        
        # Excluir o registro do documento
        db.session.delete(doc)
    
    # Agora podemos excluir o usuário com segurança
    db.session.delete(user)
    db.session.commit()
    
    flash('Usuário excluído com sucesso!', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/users/<int:user_id>/resend-confirmation', methods=['POST'])
@login_required
@admin_required
def admin_resend_confirmation(user_id):
    user = User.query.get_or_404(user_id)
    if not user.confirmed:
        token = str(uuid.uuid4())
        user.confirmation_token = token
        db.session.commit()
        send_confirmation_email(user.email, token)
        flash('Email de confirmação reenviado com sucesso!', 'success')
    return redirect(url_for('admin_users'))

@app.route('/admin/documents')
@login_required
@admin_required
def admin_documents():
    documents = Document.query.all()
    return render_template('admin/documents.html', documents=documents)

@app.route('/admin/documents/<int:document_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_edit_document(document_id):
    document = Document.query.get_or_404(document_id)
    if request.method == 'POST':
        document.title = request.form['title']
        document.description = request.form['description']
        db.session.commit()
        flash('Documento atualizado com sucesso!', 'success')
        return redirect(url_for('admin_documents'))
    return render_template('admin/edit_document.html', document=document)

@app.route('/admin/documents/<int:document_id>/delete', methods=['POST'])
@login_required
@admin_required
def admin_delete_document(document_id):
    document = Document.query.get_or_404(document_id)
    try:
        os.remove(document.filepath)
    except:
        pass
    db.session.delete(document)
    db.session.commit()
    flash('Documento excluído com sucesso!', 'success')
    return redirect(url_for('admin_documents'))

def main():
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=5001, debug=True)

if __name__ == "__main__":
    main()
