"""
Script para promover um usuário a admin.
Execute: python promote_admin.py email@exemplo.com
"""
import sys
import os

# Adicionar o diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from src.models.user import User, db

def promote_to_admin(email):
    app = create_app()

    with app.app_context():
        user = User.query.filter_by(email=email).first()

        if not user:
            print(f"Usuário com email '{email}' não encontrado.")
            return False

        if user.role == 'admin':
            print(f"Usuário '{user.name}' já é admin.")
            return True

        old_role = user.role
        user.role = 'admin'
        db.session.commit()

        print(f"Sucesso! Usuário '{user.name}' promovido de '{old_role}' para 'admin'.")
        return True

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Uso: python promote_admin.py email@exemplo.com")
        sys.exit(1)

    email = sys.argv[1]
    promote_to_admin(email)
