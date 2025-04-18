from main import app, db
from sqlalchemy import text

def migrate_database():
    with app.app_context():
        # Adiciona a coluna is_admin se ela não existir
        with db.engine.connect() as conn:
            conn.execute(text("""
                DO $$
                BEGIN
                    IF NOT EXISTS (
                        SELECT 1 
                        FROM information_schema.columns 
                        WHERE table_name='users' AND column_name='is_admin'
                    ) THEN
                        ALTER TABLE users ADD COLUMN is_admin BOOLEAN DEFAULT FALSE;
                    END IF;
                END $$;
            """))
            conn.commit()
        print("Migração concluída com sucesso!")

if __name__ == '__main__':
    migrate_database() 