from sqlalchemy import create_engine, text
from app.core.config import settings

def run_migration():
    engine = create_engine(settings.DATABASE_URL)
    
    with engine.connect() as conn:
        # Criar backup da tabela atual
        conn.execute(text("""
            CREATE TABLE documents_backup AS SELECT * FROM documents;
        """))
        
        # Dropar a tabela atual
        conn.execute(text("DROP TABLE documents;"))
        
        # Criar nova tabela com o schema atualizado
        conn.execute(text("""
            CREATE TABLE documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                original_filename VARCHAR NOT NULL,
                storage_filename VARCHAR NOT NULL,
                file_size INTEGER NOT NULL,
                content_type VARCHAR NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                user_id INTEGER NOT NULL,
                FOREIGN KEY(user_id) REFERENCES users(id)
            );
        """))
        
        # Migrar dados do backup
        conn.execute(text("""
            INSERT INTO documents (
                id, original_filename, storage_filename, file_size, 
                content_type, created_at, updated_at, user_id
            )
            SELECT 
                id, original_filename, filename as storage_filename, file_size,
                content_type, created_at, updated_at, user_id
            FROM documents_backup;
        """))
        
        # Dropar tabela de backup
        conn.execute(text("DROP TABLE documents_backup;"))
        
        conn.commit()

if __name__ == "__main__":
    run_migration() 