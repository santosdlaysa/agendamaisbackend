from src.config.database import db
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import secrets

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), nullable=False, unique=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), nullable=False, default='admin')
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Dados do estabelecimento para agendamento online
    slug = db.Column(db.String(100), unique=True, nullable=True)
    business_name = db.Column(db.String(255), nullable=True)
    business_phone = db.Column(db.String(20), nullable=True)
    business_address = db.Column(db.String(500), nullable=True)
    business_logo = db.Column(db.String(500), nullable=True)
    online_booking_enabled = db.Column(db.Boolean, default=True)

    # Configurações de agendamento online
    booking_min_advance_hours = db.Column(db.Integer, default=2)  # Antecedência mínima em horas
    booking_max_advance_days = db.Column(db.Integer, default=30)  # Antecedência máxima em dias
    booking_slot_interval = db.Column(db.Integer, default=30)  # Intervalo de slots em minutos
    booking_start_hour = db.Column(db.Integer, default=8)  # Hora de início
    booking_end_hour = db.Column(db.Integer, default=18)  # Hora de término
    booking_require_confirmation = db.Column(db.Boolean, default=False)  # Exigir confirmação por token
    booking_allow_cancellation = db.Column(db.Boolean, default=True)  # Permitir cancelamento online
    booking_cancellation_min_hours = db.Column(db.Integer, default=2)  # Antecedência mínima para cancelar

    # Verificação de email
    email_verified = db.Column(db.Boolean, default=False)
    email_verification_token = db.Column(db.String(64), nullable=True)
    email_verification_expires = db.Column(db.DateTime, nullable=True)
    email_verified_at = db.Column(db.DateTime, nullable=True)

    def set_password(self, password):
        """Define a senha do usuário usando hash"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Verifica se a senha fornecida está correta"""
        return check_password_hash(self.password_hash, password)

    def generate_email_verification_token(self, expires_hours=24):
        """Gera token de verificação de email"""
        self.email_verification_token = secrets.token_urlsafe(32)
        self.email_verification_expires = datetime.utcnow() + timedelta(hours=expires_hours)
        return self.email_verification_token

    def verify_email(self, token):
        """Verifica o email com o token fornecido"""
        if not self.email_verification_token:
            return False, 'Nenhum token de verificação pendente'
        if self.email_verification_token != token:
            return False, 'Token inválido'
        if self.email_verification_expires and datetime.utcnow() > self.email_verification_expires:
            return False, 'Token expirado'

        self.email_verified = True
        self.email_verified_at = datetime.utcnow()
        self.email_verification_token = None
        self.email_verification_expires = None
        return True, 'Email verificado com sucesso'

    @staticmethod
    def find_by_verification_token(token):
        """Busca usuário pelo token de verificação"""
        return User.query.filter_by(email_verification_token=token).first()

    def to_dict(self):
        """Converte o objeto para dicionário"""
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'role': self.role,
            'active': self.active,
            'email_verified': self.email_verified,
            'slug': self.slug,
            'business_name': self.business_name,
            'business_phone': self.business_phone,
            'business_address': self.business_address,
            'business_logo': self.business_logo,
            'online_booking_enabled': self.online_booking_enabled,
            'booking_settings': {
                'min_advance_hours': self.booking_min_advance_hours,
                'max_advance_days': self.booking_max_advance_days,
                'slot_interval': self.booking_slot_interval,
                'start_hour': self.booking_start_hour,
                'end_hour': self.booking_end_hour,
                'require_confirmation': self.booking_require_confirmation,
                'allow_cancellation': self.booking_allow_cancellation,
                'cancellation_min_hours': self.booking_cancellation_min_hours
            },
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    def to_public_dict(self):
        """Dados públicos do estabelecimento para agendamento online"""
        return {
            'slug': self.slug,
            'business_name': self.business_name or self.name,
            'business_phone': self.business_phone,
            'business_address': self.business_address,
            'business_logo': self.business_logo,
            'online_booking_enabled': self.online_booking_enabled,
            'booking_settings': {
                'min_advance_hours': self.booking_min_advance_hours,
                'max_advance_days': self.booking_max_advance_days,
                'slot_interval': self.booking_slot_interval,
                'start_hour': self.booking_start_hour,
                'end_hour': self.booking_end_hour,
                'allow_cancellation': self.booking_allow_cancellation,
                'cancellation_min_hours': self.booking_cancellation_min_hours
            }
        }