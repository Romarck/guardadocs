from sqlalchemy import create_engine, text
from app.core.config import settings
from datetime import datetime
import os

def run_migration():
    engine = create_engine(settings.DATABASE_URL)
    
    with engine.connect() as conn:
        # Buscar todos os documentos
        result = conn.execute(text("SELECT id, storage_filename, original_filename FROM documents"))
        documents = result.fetchall()
        
        for doc in documents:
            # Gerar novo nome de arquivo
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            extension = os.path.splitext(doc.original_filename)[1].lower()
            new_filename = f"{timestamp}_{doc.id}{extension}"
            
            # Atualizar o registro
            conn.execute(
                text("UPDATE documents SET storage_filename = :new_filename WHERE id = :id"),
                {"new_filename": new_filename, "id": doc.id}
            )
            
            print(f"Atualizado documento {doc.id}:")
            print(f"  De: {doc.storage_filename}")
            print(f"Para: {new_filename}")
            
        conn.commit()
        print("\nMigração concluída com sucesso!")

if __name__ == "__main__":
    run_migration() 