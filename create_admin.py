from app.db.session import get_db
from app.models.user import User
from app.core.hashing import get_password_hash
from app.core.config import settings

def create_admin():
    # Obtém a sessão do banco de dados
    db = next(get_db())
    
    try:
        # Verifica se o usuário já existe
        admin = db.query(User).filter(User.email == 'romarck@gmail.com').first()
        
        if admin:
            # Se o usuário existe, apenas atualiza para admin
            admin.is_admin = True
            admin.hashed_password = get_password_hash('admin')
            admin.is_active = True
            print("Usuário administrador atualizado com sucesso!")
        else:
            # Se não existe, cria um novo usuário admin
            admin = User(
                email='romarck@gmail.com',
                full_name='Administrador',
                hashed_password=get_password_hash('admin'),
                is_admin=True,
                is_active=True
            )
            db.add(admin)
            print("Novo usuário administrador criado com sucesso!")
        
        db.commit()
        
    except Exception as e:
        print(f"Erro ao criar/atualizar administrador: {str(e)}")
        db.rollback()
    finally:
        db.close()

if __name__ == '__main__':
    create_admin() 