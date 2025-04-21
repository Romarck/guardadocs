# GuardaDocs

Sistema de gerenciamento de documentos desenvolvido com FastAPI e SQLite.

## Características

- ✨ Interface moderna e responsiva com Bootstrap 5
- 🔒 Autenticação de usuários com JWT
- 📁 Upload e gerenciamento de documentos
- 👥 Gerenciamento de usuários (admin)
- 💾 Armazenamento local de arquivos
- 🎯 Validações de tamanho e tipo de arquivo
- 📱 Design responsivo para mobile
- 🚀 Suporte para deploy local e em VPS

## Requisitos

- Python 3.8+
- pip (gerenciador de pacotes Python)
- SQLite 3
- Supervisor (para produção)
- Nginx (para produção)

## Instalação Local

1. Clone o repositório:
```bash
git clone https://github.com/seu-usuario/GuardaDocs.git
cd GuardaDocs
```

2. Crie um ambiente virtual e ative-o:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows
```

3. Instale as dependências:
```bash
pip install -r requirements.txt
```

4. Configure as variáveis de ambiente:
- Copie o arquivo `.env.example` para `.env`
- Ajuste as configurações conforme necessário:
  ```
  # Configurações do Projeto
  PROJECT_NAME=GuardaDocs
  VERSION=1.0.0
  API_V1_STR=/api/v1

  # Segurança
  SECRET_KEY=sua-chave-secreta-aqui
  ACCESS_TOKEN_EXPIRE_MINUTES=11520

  # Banco de Dados
  DATABASE_URL=sqlite:///./guarda_docs.db

  # Armazenamento
  UPLOAD_FOLDER=uploads
  MAX_UPLOAD_SIZE=10485760  # 10MB
  ```

5. Execute as migrações do banco de dados:
```bash
alembic upgrade head
```

6. Crie o usuário administrador:
```bash
python create_admin.py
```

7. Para desenvolvimento local, inicie o servidor:
```bash
uvicorn app.main:app --reload
```

O sistema estará disponível em `http://localhost:8000`

## Deploy em VPS

### 1. Preparação do Servidor

```bash
# Atualizar o sistema
sudo apt update && sudo apt upgrade -y

# Instalar dependências
sudo apt install python3-pip python3-venv nginx supervisor sqlite3 -y
```

### 2. Configuração do Projeto

```bash
# Criar diretório da aplicação
sudo mkdir -p /opt/guardadocs
sudo chown -R $USER:$USER /opt/guardadocs

# Clonar o repositório
git clone https://github.com/seu-usuario/GuardaDocs.git /opt/guardadocs
cd /opt/guardadocs

# Criar e ativar ambiente virtual
python3 -m venv venv
source venv/bin/activate

# Instalar dependências
pip install -r requirements.txt
pip install gunicorn

# Configurar variáveis de ambiente
cp .env.example .env
# Edite o arquivo .env com suas configurações de produção
```

### 3. Configuração do Supervisor

Crie o arquivo `/etc/supervisor/conf.d/guardadocs.conf`:

```ini
[program:guardadocs]
directory=/opt/guardadocs
command=/opt/guardadocs/venv/bin/gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker -b unix:/tmp/guardadocs.sock
user=www-data
autostart=true
autorestart=true
stderr_logfile=/var/log/guardadocs/err.log
stdout_logfile=/var/log/guardadocs/out.log
```

### 4. Configuração do Nginx

Crie o arquivo `/etc/nginx/sites-available/guardadocs`:

```nginx
server {
    listen 80;
    server_name seu-dominio.com;

    location / {
        proxy_pass http://unix:/tmp/guardadocs.sock;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }

    location /static {
        alias /opt/guardadocs/app/static;
    }

    location /uploads {
        alias /opt/guardadocs/uploads;
        internal;
    }

    client_max_body_size 10M;
}
```

### 5. Iniciar os Serviços

```bash
# Criar diretórios de log
sudo mkdir -p /var/log/guardadocs
sudo chown -R www-data:www-data /var/log/guardadocs

# Configurar Nginx
sudo ln -s /etc/nginx/sites-available/guardadocs /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx

# Iniciar Supervisor
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start guardadocs
```

### 6. Configuração do Firewall (opcional)

```bash
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
```

### 7. SSL/HTTPS (recomendado)

Para configurar HTTPS gratuito com Let's Encrypt:

```bash
sudo apt install certbot python3-certbot-nginx -y
sudo certbot --nginx -d seu-dominio.com
```

## Manutenção em Produção

### Atualização do Sistema

```bash
cd /opt/guardadocs
git pull
source venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
sudo supervisorctl restart guardadocs
```

### Backup do Banco de Dados

```bash
# Backup
sqlite3 guarda_docs.db ".backup 'backup.db'"

# Restauração (se necessário)
sqlite3 guarda_docs.db ".restore 'backup.db'"
```

## Estrutura do Projeto

```
GuardaDocs/
├── alembic/              # Migrações do banco de dados
├── app/
│   ├── core/            # Configurações e funcionalidades principais
│   ├── db/             # Configuração do banco de dados
│   ├── models/         # Modelos SQLAlchemy
│   ├── schemas/        # Schemas Pydantic
│   ├── static/         # Arquivos estáticos (CSS, JS)
│   ├── templates/      # Templates Jinja2
│   └── main.py         # Aplicação principal
├── uploads/            # Pasta para armazenamento de arquivos
├── .env               # Variáveis de ambiente
└── requirements.txt   # Dependências do projeto
```

## Funcionalidades

### Usuários
- Registro e login de usuários
- Perfil do usuário com informações básicas
- Edição de dados do perfil
- Alteração de senha

### Documentos
- Upload de documentos com título e descrição
- Visualização em lista ou grade
- Download de documentos
- Edição de informações do documento
- Exclusão de documentos

### Área Administrativa
- Gerenciamento de usuários
- Visualização de todos os documentos
- Ativação/desativação de usuários
- Promoção de usuários a administradores

## Segurança

- Senhas criptografadas com Bcrypt
- Autenticação via JWT (JSON Web Tokens)
- Proteção contra CSRF
- Validação de uploads de arquivos
- Controle de acesso baseado em funções

## Desenvolvimento

Para contribuir com o projeto:

1. Crie um fork do repositório
2. Crie uma branch para sua feature (`git checkout -b feature/nome-da-feature`)
3. Faça commit das mudanças (`git commit -am 'Adiciona nova feature'`)
4. Push para a branch (`git push origin feature/nome-da-feature`)
5. Crie um Pull Request

## Licença

Este projeto está licenciado sob a licença MIT - veja o arquivo [LICENSE](LICENSE) para mais detalhes.
