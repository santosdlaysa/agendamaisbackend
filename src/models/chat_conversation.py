"""
Modelo de Conversa de Chat de Suporte para o sistema AgendaMais
"""
from src.config.database import db
from datetime import datetime


class ChatConversation(db.Model):
    """Conversa de suporte entre usuario (dono de empresa) e super admin"""
    __tablename__ = 'chat_conversations'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)

    # Status da conversa
    status = db.Column(db.String(20), default='active', nullable=False)  # active, closed

    # Contadores desnormalizados para performance
    user_unread_count = db.Column(db.Integer, default=0, nullable=False)
    admin_unread_count = db.Column(db.Integer, default=0, nullable=False)

    # Preview da ultima mensagem
    last_message_text = db.Column(db.Text, nullable=True)
    last_message_at = db.Column(db.DateTime, nullable=True)
    last_message_sender_role = db.Column(db.String(20), nullable=True)

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relacionamentos
    user = db.relationship('User', backref=db.backref('chat_conversation', uselist=False))
    messages = db.relationship('ChatMessage', backref='conversation', lazy='dynamic',
                               order_by='ChatMessage.created_at.desc()')

    def to_dict(self):
        """Converte para dicionario"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'user_name': self.user.name if self.user else None,
            'user_email': self.user.email if self.user else None,
            'user_business_name': self.user.business_name if self.user else None,
            'status': self.status,
            'user_unread_count': self.user_unread_count,
            'admin_unread_count': self.admin_unread_count,
            'last_message_text': self.last_message_text,
            'last_message_at': self.last_message_at.isoformat() if self.last_message_at else None,
            'last_message_sender_role': self.last_message_sender_role,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
