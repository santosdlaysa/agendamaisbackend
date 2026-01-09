from src.config.database import db
from datetime import datetime


class ReminderSettings(db.Model):
    """Configuracoes de lembretes por usuario - LEGADO (mantido para compatibilidade)"""
    __tablename__ = 'reminder_settings'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)

    # Configuracoes de email
    email_enabled = db.Column(db.Boolean, default=True)
    email_hours_before = db.Column(db.Integer, default=24)

    # Configuracoes de SMS
    sms_enabled = db.Column(db.Boolean, default=False)
    sms_hours_before = db.Column(db.Integer, default=2)

    # Configuracoes de WhatsApp
    whatsapp_enabled = db.Column(db.Boolean, default=False)
    whatsapp_hours_before = db.Column(db.Integer, default=2)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'email_enabled': self.email_enabled,
            'email_hours_before': self.email_hours_before,
            'sms_enabled': self.sms_enabled,
            'sms_hours_before': self.sms_hours_before,
            'whatsapp_enabled': self.whatsapp_enabled,
            'whatsapp_hours_before': self.whatsapp_hours_before
        }


class ProfessionalReminderSettings(db.Model):
    """Configuracoes de lembretes por profissional e tipo"""
    __tablename__ = 'professional_reminder_settings'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    professional_id = db.Column(db.Integer, db.ForeignKey('professionals.id'), nullable=False)
    reminder_type = db.Column(db.String(20), nullable=False)  # 'whatsapp', 'sms', 'email'

    enabled = db.Column(db.Boolean, default=True)
    hours_before = db.Column(db.Integer, default=24)
    custom_message = db.Column(db.Text, nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Constraint para garantir uma config por profissional/tipo
    __table_args__ = (
        db.UniqueConstraint('professional_id', 'reminder_type', name='uq_professional_reminder_type'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'professional_id': self.professional_id,
            'reminder_type': self.reminder_type,
            'enabled': self.enabled,
            'hours_before': self.hours_before,
            'custom_message': self.custom_message
        }
