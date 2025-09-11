import sqlite3
import os

# Conectar ao banco de dados SQLite
db_path = 'instance/agendamento.db'
if not os.path.exists('instance'):
    os.makedirs('instance')

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

try:
    # Verificar se a coluna já existe
    cursor.execute("PRAGMA table_info(appointments)")
    columns = [column[1] for column in cursor.fetchall()]
    
    if 'payment_method' not in columns:
        # Adicionar a nova coluna
        cursor.execute("ALTER TABLE appointments ADD COLUMN payment_method VARCHAR(50)")
        print("Coluna 'payment_method' adicionada com sucesso!")
    else:
        print("Coluna 'payment_method' ja existe")
    
    conn.commit()
    
except sqlite3.Error as e:
    print(f"Erro ao adicionar coluna: {e}")
    
finally:
    conn.close()
    print("Migracao concluida!")