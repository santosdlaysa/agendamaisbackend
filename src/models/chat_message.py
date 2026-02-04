"""
Modelo de Mensagem de Chat de Suporte para o sistema AgendaMais
"""
from src.config.database import db
from datetime import datetime


class ChatMessage(db.Model):
    """Mensagem individual dentro de uma conversa de suporte"""
    __tablename__ = 'chat_messages'

    id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(db.Integer, db.ForeignKey('chat_conversations.id'), nullable=False)
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    sender_role = db.Column(db.String(20), nullable=False)  # 'user' ou 'superadmin'

    # Conteudo
    message = db.Column(db.Text, nullable=False)

    # Status de leitura
    read = db.Column(db.Boolean, default=False)
    read_at = db.Column(db.DateTime, nullable=True)

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relacionamentos
    sender = db.relationship('User', backref=db.backref('chat_messages_sent', lazy='dynamic'))

    def to_dict(self):
        """Converte para dicionario"""
        return {
            'id': self.id,
            'conversation_id': self.conversation_id,
            'sender_id': self.sender_id,
            'sender_role': self.sender_role,
            'sender_name': self.sender.name if self.sender else None,
            'message': self.message,
            'read': self.read,
            'read_at': self.read_at.isoformat() if self.read_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
