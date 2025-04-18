from main import app, db, User
from werkzeug.security import generate_password_hash

def create_admin():
    with app.app_context():
        # Verifica se o usuário já existe
        admin = User.query.filter_by(email='romarck@gmail.com').first()
        
        if admin:
            # Se o usuário existe, apenas atualiza para admin
            admin.is_admin = True
            admin.password_hash = generate_password_hash('admin')
            print("Usuário administrador atualizado com sucesso!")
        else:
            # Se não existe, cria um novo usuário admin
            admin = User(
                name='Administrador',
                email='romarck@gmail.com',
                phone='00000000000',
                is_admin=True,
                confirmed=True,
                password_hash=generate_password_hash('admin')
            )
            db.session.add(admin)
            print("Novo usuário administrador criado com sucesso!")
        
        db.session.commit()

if __name__ == '__main__':
    create_admin() 