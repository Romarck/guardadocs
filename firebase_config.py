import firebase_admin
from firebase_admin import credentials, firestore, storage, auth

# Inicializar o Firebase Admin SDK
cred = credentials.Certificate("path/to/your/serviceAccountKey.json")
firebase_admin.initialize_app(cred, {
    'storageBucket': 'your-project-id.appspot.com'
})

# Referências para os serviços
db = firestore.client()
bucket = storage.bucket() 