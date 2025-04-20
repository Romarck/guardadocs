import bcrypt

def get_password_hash(password: str) -> str:
    # Gera um salt e faz o hash da senha
    salt = bcrypt.gensalt(rounds=12)
    # Converte a senha para bytes antes de fazer o hash
    password_bytes = password.encode('utf-8')
    # Gera o hash
    hashed = bcrypt.hashpw(password_bytes, salt)
    # Retorna o hash como string
    return hashed.decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        # Converte as strings para bytes
        password_bytes = plain_password.encode('utf-8')
        hashed_bytes = hashed_password.encode('utf-8')
        # Verifica o hash
        return bcrypt.checkpw(password_bytes, hashed_bytes)
    except Exception as e:
        print(f"Erro na verificação da senha: {str(e)}")
        return False 