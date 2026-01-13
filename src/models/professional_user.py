from src.config.database import db
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash


class ProfessionalUser(db.Model):
    """Modelo para autenticacao de profissionais no portal"""
    __tablename__ = 'professional_users'

    id = db.Column(db.Integer, primary_key=True)
    professional_id = db.Column(db.Integer, db.ForeignKey('professionals.id', ondelete='CASCADE'), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255))
    invite_token = db.Column(db.String(255), index=True)
    invite_expires_at = db.Column(db.DateTime)
    reset_token = db.Column(db.String(255), index=True)
    reset_expires_at = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=False)
    last_login = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relacionamento
    professional = db.relationship('Professional', backref=db.backref('user_account', uselist=False))

    def set_password(self, password):
        """Define a senha do usuario"""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Verifica se a senha esta correta"""
        if not self.password_hash:
            return False
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        """Converte o objeto para dicionario"""
        return {
            'id': self.id,
            'professional_id': self.professional_id,
            'email': self.email,
            'is_active': self.is_active,
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'professional': self.professional.to_dict() if self.professional else None
        }

    def to_dict_simple(self):
        """Converte para dicionario sem relacionamentos"""
        return {
            'id': self.id,
            'professional_id': self.professional_id,
            'email': self.email,
            'is_active': self.is_active,
            'last_login': self.last_login.isoformat() if self.last_login else None
        }
