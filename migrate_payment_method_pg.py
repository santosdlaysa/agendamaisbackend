import os
from app import create_app
from src.config.database import db

# Create app context
app = create_app()

with app.app_context():
    try:
        # Check if column exists
        result = db.engine.execute("SELECT column_name FROM information_schema.columns WHERE table_name='appointments' AND column_name='payment_method'")
        columns = result.fetchall()
        
        if not columns:
            # Add the column
            db.engine.execute("ALTER TABLE appointments ADD COLUMN payment_method VARCHAR(50)")
            print("Coluna 'payment_method' adicionada com sucesso!")
        else:
            print("Coluna 'payment_method' ja existe")
        
    except Exception as e:
        print(f"Erro ao adicionar coluna: {e}")
    
    print("Migracao PostgreSQL concluida!")