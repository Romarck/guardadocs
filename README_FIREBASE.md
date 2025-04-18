# Implantando o Guarda Docs no Firebase

Este guia explica como implantar o aplicativo Guarda Docs no Firebase.

## Pré-requisitos

1. Conta no Google Cloud Platform
2. Node.js e npm instalados
3. Firebase CLI instalado (`npm install -g firebase-tools`)

## Passos para implantação

### 1. Configurar o projeto no Firebase Console

1. Acesse o [Firebase Console](https://console.firebase.google.com/)
2. Crie um novo projeto ou selecione um existente
3. Ative os seguintes serviços:
   - Authentication (com provedor de email/senha e Google)
   - Firestore Database
   - Storage
   - Hosting

### 2. Obter as credenciais do Firebase

1. No console do Firebase, vá para Configurações do Projeto > Contas de serviço
2. Clique em "Gerar nova chave privada"
3. Salve o arquivo JSON como `serviceAccountKey.json` na raiz do projeto

### 3. Configurar o arquivo firebase_config.py

Edite o arquivo `firebase_config.py` para incluir o caminho correto para o arquivo de credenciais e o ID do seu projeto:

```python
import firebase_admin
from firebase_admin import credentials, firestore, storage, auth

# Inicializar o Firebase Admin SDK
cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred, {
    'storageBucket': 'seu-projeto-id.appspot.com'
})

# Referências para os serviços
db = firestore.client()
bucket = storage.bucket()
```

### 4. Preparar o aplicativo para implantação

1. Instale as dependências necessárias:
   ```
   pip install firebase-admin gunicorn
   ```

2. Crie um arquivo `requirements.txt` atualizado:
   ```
   pip freeze > requirements.txt
   ```

3. Crie um arquivo `app.yaml` para o Google App Engine:
   ```yaml
   runtime: python39
   entrypoint: gunicorn -b :$PORT main:app
   
   env_variables:
     GOOGLE_APPLICATION_CREDENTIALS: "serviceAccountKey.json"
   ```

### 5. Implantar no Firebase Hosting

1. Faça login no Firebase CLI:
   ```
   firebase login
   ```

2. Inicialize o projeto Firebase:
   ```
   firebase init
   ```
   - Selecione Hosting, Firestore e Storage
   - Escolha seu projeto
   - Use "public" como diretório público
   - Configure como aplicativo de página única

3. Construa o aplicativo:
   ```
   python -m pip install -r requirements.txt
   ```

4. Implante o aplicativo:
   ```
   firebase deploy
   ```

## Alternativa: Implantar no Google App Engine

Se preferir usar o Google App Engine em vez do Firebase Hosting:

1. Instale o Google Cloud SDK
2. Faça login:
   ```
   gcloud auth login
   ```
3. Configure o projeto:
   ```
   gcloud config set project seu-projeto-id
   ```
4. Implante o aplicativo:
   ```
   gcloud app deploy
   ```

## Migração de dados

Para migrar os dados do PostgreSQL para o Firestore:

1. Exporte os dados do PostgreSQL:
   ```
   pg_dump -U tccmvp -d tccmvpdb > backup.sql
   ```

2. Use um script de migração para importar os dados para o Firestore (exemplo básico):
   ```python
   import psycopg2
   from firebase_config import db
   
   # Conectar ao PostgreSQL
   conn = psycopg2.connect("dbname=tccmvpdb user=tccmvp password=tccmvpdb1969 host=localhost")
   cur = conn.cursor()
   
   # Migrar usuários
   cur.execute("SELECT id, name, email, phone, is_admin, confirmed FROM users")
   for row in cur.fetchall():
       user_id, name, email, phone, is_admin, confirmed = row
       db.collection('users').document(str(user_id)).set({
           'name': name,
           'email': email,
           'phone': phone,
           'is_admin': is_admin,
           'confirmed': confirmed
       })
   
   # Migrar documentos
   cur.execute("SELECT id, title, description, filename, filepath, user_id FROM documents")
   for row in cur.fetchall():
       doc_id, title, description, filename, filepath, user_id = row
       db.collection('documents').document(str(doc_id)).set({
           'title': title,
           'description': description,
           'filename': filename,
           'filepath': filepath,
           'user_id': str(user_id)
       })
   
   conn.close()
   ```

## Solução de problemas

- **Erro de permissão**: Verifique se as regras de segurança do Firestore e Storage estão configuradas corretamente
- **Erro de autenticação**: Verifique se o arquivo de credenciais está no local correto e tem as permissões adequadas
- **Erro de CORS**: Configure as regras de CORS no Firebase Storage se necessário 