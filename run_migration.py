"""Script para executar migration de agendamento online"""
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()

DATABASE_URL = os.getenv('DATABASE_URL')
print(f"Conectando ao banco...")

engine = create_engine(DATABASE_URL)

statements = [
    "ALTER TABLE users ADD COLUMN IF NOT EXISTS slug VARCHAR(100)",
    "ALTER TABLE users ADD COLUMN IF NOT EXISTS business_name VARCHAR(255)",
    "ALTER TABLE users ADD COLUMN IF NOT EXISTS business_phone VARCHAR(20)",
    "ALTER TABLE users ADD COLUMN IF NOT EXISTS business_address VARCHAR(500)",
    "ALTER TABLE users ADD COLUMN IF NOT EXISTS business_logo VARCHAR(500)",
    "ALTER TABLE users ADD COLUMN IF NOT EXISTS online_booking_enabled BOOLEAN DEFAULT TRUE",
    "ALTER TABLE appointments ADD COLUMN IF NOT EXISTS booking_code VARCHAR(8)",
    "ALTER TABLE appointments ADD COLUMN IF NOT EXISTS source VARCHAR(20) DEFAULT 'admin'",
    "ALTER TABLE appointments ADD COLUMN IF NOT EXISTS user_id INTEGER REFERENCES users(id)",
    "CREATE INDEX IF NOT EXISTS idx_appointments_source ON appointments(source)",
    "CREATE INDEX IF NOT EXISTS idx_appointments_user_id ON appointments(user_id)",
]

try:
    with engine.connect() as conn:
        for stmt in statements:
            print(f"  > {stmt[:60]}...")
            conn.execute(text(stmt))
        conn.commit()
    print("\nMigration executada com sucesso!")
except Exception as e:
    print(f"\nErro: {e}")
