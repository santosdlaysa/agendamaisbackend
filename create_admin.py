"""
Script para criar (ou promover) um usuário admin.
Uso: python create_admin.py <email> <senha> [nome]
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from src.models.user import User, db


def create_admin(email, password, name=None):
    app = create_app()

    with app.app_context():
        user = User.query.filter_by(email=email).first()

        if user:
            user.role = 'admin'
            user.set_password(password)
            user.active = True
            user.email_verified = True
            db.session.commit()
            print(f"Usuário existente '{user.email}' atualizado para admin e senha redefinida.")
            return True

        user = User(
            name=name or email.split('@')[0],
            email=email,
            role='admin',
            active=True,
            email_verified=True,
        )
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        print(f"Admin criado com sucesso: {user.email} (id={user.id})")
        return True


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Uso: python create_admin.py <email> <senha> [nome]")
        sys.exit(1)

    email = sys.argv[1]
    password = sys.argv[2]
    name = sys.argv[3] if len(sys.argv) > 3 else None
    create_admin(email, password, name)
