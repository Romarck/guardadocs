# GuardaDocs v1.0

Sistema de Gerenciamento de Documentos com autenticação e armazenamento seguro.

## Características

- Autenticação de usuários (Email/Senha e Google)
- Upload e download de documentos
- Armazenamento seguro com Supabase
- Interface administrativa
- Controle de acesso baseado em funções
- Interface responsiva e moderna

## Requisitos

- Python 3.8+
- PostgreSQL ou SQLite
- Conta no Supabase para armazenamento
- Credenciais do Google OAuth (opcional)

## Instalação

1. Clone o repositório:
```bash
git clone https://github.com/seu-usuario/GuardaDocs.git
cd GuardaDocs
```

2. Crie e ative um ambiente virtual:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
.\venv\Scripts\activate  # Windows
```

3. Instale as dependências:
```bash
pip install -r requirements.txt
```

4. Configure as variáveis de ambiente:
```bash
cp .env.example .env
```
Edite o arquivo `.env` com suas configurações.

5. Execute as migrações do banco de dados:
```bash
alembic upgrade head
```

## Configuração

### Variáveis de Ambiente Necessárias:

- `DATABASE_URL`: URL de conexão com o banco de dados
- `SECRET_KEY`: Chave secreta para JWT
- `SUPABASE_URL`: URL do seu projeto Supabase
- `SUPABASE_KEY`: Chave de API do Supabase
- `GOOGLE_CLIENT_ID`: ID do cliente OAuth do Google (opcional)
- `GOOGLE_CLIENT_SECRET`: Chave secreta do cliente OAuth do Google (opcional)

## Execução

### Desenvolvimento

```bash
python -m hypercorn app.main:app --bind 0.0.0.0:8000 --reload
```

### Produção

```bash
python -m hypercorn app.main:app --bind 0.0.0.0:8000 --workers 4
```

Ou use o Docker:

```bash
docker-compose up -d
```

## Estrutura do Projeto

```
GuardaDocs/
├── alembic/            # Migrações do banco de dados
├── app/
│   ├── core/          # Configurações e funcionalidades principais
│   ├── db/            # Configuração do banco de dados
│   ├── models/        # Modelos do banco de dados
│   ├── static/        # Arquivos estáticos
│   ├── templates/     # Templates HTML
│   └── main.py        # Aplicação principal
├── scripts/           # Scripts utilitários
└── uploads/          # Diretório temporário de uploads
```

## Segurança

- Todas as senhas são hasheadas usando bcrypt
- Autenticação via JWT
- Uploads de arquivos são validados e armazenados de forma segura
- Controle de acesso granular

## Licença

Este projeto está licenciado sob a licença MIT. # guardadocs
# guardadocs
# guardadocs
