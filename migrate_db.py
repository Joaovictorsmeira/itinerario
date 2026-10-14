from sqlalchemy import text
from database import engine

def migrate():
    with engine.connect() as conn:
        print("Aumentando tamanho de status para VARCHAR(50)...")
        conn.execute(text("ALTER TABLE voluntarios ALTER COLUMN status TYPE VARCHAR(50);"))
        print("Adicionando coluna 'recado_organizacao' se não existir...")
        conn.execute(text("ALTER TABLE voluntarios ADD COLUMN IF NOT EXISTS recado_organizacao TEXT;"))
        conn.execute(text("UPDATE voluntarios SET status = 'recebido' WHERE status = 'novo';"))
        conn.execute(text("UPDATE voluntarios SET status = 'contato_realizado' WHERE status = 'contatado';"))
        conn.execute(text("UPDATE voluntarios SET status = 'participacao_confirmada' WHERE status = 'ativo';"))
        conn.commit()
        print("Migração executada com sucesso no PostgreSQL do Supabase!")

if __name__ == "__main__":
    migrate()
