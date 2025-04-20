from supabase import create_client
import os
from dotenv import load_dotenv

# Carrega as variáveis de ambiente
load_dotenv()

# Inicializa o cliente Supabase com a chave de serviço
supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_SERVICE_KEY")  # Use a chave de serviço aqui
)

def create_bucket_and_policies():
    try:
        # Cria o bucket se não existir
        bucket_id = "documents"
        try:
            supabase.storage.create_bucket(
                id=bucket_id,
                options={"public": False}  # Bucket privado por padrão
            )
            print(f"Bucket '{bucket_id}' criado com sucesso!")
        except Exception as e:
            if "already exists" in str(e):
                print(f"Bucket '{bucket_id}' já existe.")
            else:
                raise e

        # Configura as políticas de acesso
        policies = [
            {
                "name": "Permitir upload para usuários autenticados",
                "definition": """
                    (role() = 'authenticated' AND 
                     auth.uid()::text = (storage.foldername)[1])
                """,
                "operation": "INSERT"
            },
            {
                "name": "Permitir download para usuários autenticados",
                "definition": """
                    (role() = 'authenticated' AND 
                     auth.uid()::text = (storage.foldername)[1])
                """,
                "operation": "SELECT"
            },
            {
                "name": "Permitir deleção apenas para o dono do arquivo",
                "definition": """
                    (role() = 'authenticated' AND 
                     auth.uid()::text = (storage.foldername)[1])
                """,
                "operation": "DELETE"
            }
        ]

        # Aplica as políticas
        for policy in policies:
            try:
                supabase.storage.create_policy(
                    bucket=bucket_id,
                    name=policy["name"],
                    definition=policy["definition"],
                    operation=policy["operation"]
                )
                print(f"Política '{policy['name']}' criada com sucesso!")
            except Exception as e:
                print(f"Erro ao criar política '{policy['name']}': {str(e)}")

    except Exception as e:
        print(f"Erro: {str(e)}")

if __name__ == "__main__":
    create_bucket_and_policies() 