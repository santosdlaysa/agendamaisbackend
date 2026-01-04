from src.config.database import db
from datetime import datetime


class ReminderSettings(db.Model):
    """Configuracoes de lembretes por usuario"""
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
