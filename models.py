from datetime import datetime
from firebase_admin import auth
from firebase_config import db

class User:
    def __init__(self, uid, name, email, phone, is_admin=False, confirmed=False):
        self.uid = uid
        self.name = name
        self.email = email
        self.phone = phone
        self.is_admin = is_admin
        self.confirmed = confirmed
        self.documents = []
    
    @staticmethod
    def get_by_id(uid):
        user_doc = db.collection('users').document(uid).get()
        if not user_doc.exists:
            return None
        
        user_data = user_doc.to_dict()
        user = User(
            uid=uid,
            name=user_data.get('name', ''),
            email=user_data.get('email', ''),
            phone=user_data.get('phone', ''),
            is_admin=user_data.get('is_admin', False),
            confirmed=user_data.get('confirmed', False)
        )
        
        # Carregar documentos do usuário
        docs = db.collection('documents').where('user_id', '==', uid).get()
        user.documents = [Document.from_dict(doc.id, doc.to_dict()) for doc in docs]
        
        return user
    
    def save(self):
        user_data = {
            'name': self.name,
            'email': self.email,
            'phone': self.phone,
            'is_admin': self.is_admin,
            'confirmed': self.confirmed,
            'updated_at': datetime.now()
        }
        
        db.collection('users').document(self.uid).set(user_data, merge=True)
    
    def set_password(self, password):
        # Atualizar senha no Firebase Authentication
        auth.update_user(self.uid, password=password)
    
    def check_password(self, password):
        # Verificar senha no Firebase Authentication
        try:
            auth.get_user_by_email(self.email)
            return True
        except:
            return False
    
    def is_authenticated(self):
        return True
    
    def is_active(self):
        return True
    
    def is_anonymous(self):
        return False
    
    def get_id(self):
        return str(self.uid)

class Document:
    def __init__(self, doc_id, title, description, filename, filepath, user_id):
        self.id = doc_id
        self.title = title
        self.description = description
        self.filename = filename
        self.filepath = filepath
        self.user_id = user_id
    
    @staticmethod
    def from_dict(doc_id, data):
        return Document(
            doc_id=doc_id,
            title=data.get('title', ''),
            description=data.get('description', ''),
            filename=data.get('filename', ''),
            filepath=data.get('filepath', ''),
            user_id=data.get('user_id', '')
        )
    
    def save(self):
        doc_data = {
            'title': self.title,
            'description': self.description,
            'filename': self.filename,
            'filepath': self.filepath,
            'user_id': self.user_id,
            'updated_at': datetime.now()
        }
        
        if self.id:
            db.collection('documents').document(self.id).set(doc_data, merge=True)
        else:
            doc_ref = db.collection('documents').document()
            doc_ref.set(doc_data)
            self.id = doc_ref.id
    
    def delete(self):
        if self.id:
            db.collection('documents').document(self.id).delete() 