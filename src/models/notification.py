"""
Modelo de Notificacoes In-App para o sistema AgendaMais
"""
from src.config.database import db
from datetime import datetime


class Notification(db.Model):
    """Modelo para notificacoes in-app que aparecem no dashboard"""
    __tablename__ = 'notifications'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    # Tipo de notificacao
    type = db.Column(db.String(50), nullable=False)  # new_appointment, new_client, appointment_completed, appointment_cancelled, etc.

    # Titulo e mensagem
    title = db.Column(db.String(255), nullable=False)
    message = db.Column(db.Text, nullable=False)

    # Dados relacionados (JSON para flexibilidade)
    data = db.Column(db.JSON, nullable=True)  # {appointment_id: 1, client_id: 2, etc.}

    # Status
    read = db.Column(db.Boolean, default=False)
    read_at = db.Column(db.DateTime, nullable=True)

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relacionamento com usuario
    user = db.relationship('User', backref=db.backref('notifications', lazy='dynamic'))

    # Tipos de notificacao disponiveis
    TYPES = {
        'new_appointment': 'Novo Agendamento',
        'new_client': 'Novo Cliente',
        'appointment_confirmed': 'Agendamento Confirmado',
        'appointment_completed': 'Agendamento Concluido',
        'appointment_cancelled': 'Agendamento Cancelado',
        'appointment_rescheduled': 'Agendamento Reagendado',
        'appointment_reminder': 'Lembrete de Agendamento',
        'system': 'Sistema'
    }

    def to_dict(self):
        """Converte para dicionario"""
        return {
            'id': self.id,
            'type': self.type,
            'type_label': self.TYPES.get(self.type, self.type),
            'title': self.title,
            'message': self.message,
            'data': self.data,
            'read': self.read,
            'read_at': self.read_at.isoformat() if self.read_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

    def mark_as_read(self):
        """Marca notificacao como lida"""
        if not self.read:
            self.read = True
            self.read_at = datetime.utcnow()

    @staticmethod
    def create_notification(user_id, notification_type, title, message, data=None):
        """Cria uma nova notificacao"""
        notification = Notification(
            user_id=user_id,
            type=notification_type,
            title=title,
            message=message,
            data=data
        )
        db.session.add(notification)
        return notification

    @staticmethod
    def get_unread_count(user_id):
        """Retorna contagem de notificacoes nao lidas"""
        return Notification.query.filter_by(user_id=user_id, read=False).count()

    @staticmethod
    def get_notifications(user_id, page=1, per_page=20, unread_only=False):
        """Retorna notificacoes do usuario com paginacao"""
        query = Notification.query.filter_by(user_id=user_id)

        if unread_only:
            query = query.filter_by(read=False)

        return query.order_by(Notification.created_at.desc()).paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )

    @staticmethod
    def mark_all_as_read(user_id):
        """Marca todas as notificacoes do usuario como lidas"""
        Notification.query.filter_by(user_id=user_id, read=False).update({
            'read': True,
            'read_at': datetime.utcnow()
        })
        db.session.commit()

    # Metodos de fabrica para criar notificacoes especificas
    @classmethod
    def notify_new_appointment(cls, user_id, appointment, client, service, professional):
        """Cria notificacao de novo agendamento"""
        date_str = appointment.appointment_date.strftime('%d/%m/%Y')
        time_str = appointment.start_time.strftime('%H:%M') if hasattr(appointment.start_time, 'strftime') else str(appointment.start_time)[:5]

        return cls.create_notification(
            user_id=user_id,
            notification_type='new_appointment',
            title='Novo Agendamento',
            message=f'{client.name} agendou {service.name} para {date_str} as {time_str}',
            data={
                'appointment_id': appointment.id,
                'client_id': client.id,
                'client_name': client.name,
                'service_id': service.id,
                'service_name': service.name,
                'professional_id': professional.id,
                'professional_name': professional.name,
                'date': date_str,
                'time': time_str,
                'booking_code': appointment.booking_code
            }
        )

    @classmethod
    def notify_new_client(cls, user_id, client):
        """Cria notificacao de novo cliente"""
        return cls.create_notification(
            user_id=user_id,
            notification_type='new_client',
            title='Novo Cliente',
            message=f'{client.name} foi cadastrado no sistema',
            data={
                'client_id': client.id,
                'client_name': client.name,
                'client_phone': client.phone,
                'client_email': client.email
            }
        )

    @classmethod
    def notify_appointment_confirmed(cls, user_id, appointment, client):
        """Cria notificacao de agendamento confirmado"""
        date_str = appointment.appointment_date.strftime('%d/%m/%Y')
        time_str = appointment.start_time.strftime('%H:%M') if hasattr(appointment.start_time, 'strftime') else str(appointment.start_time)[:5]

        return cls.create_notification(
            user_id=user_id,
            notification_type='appointment_confirmed',
            title='Agendamento Confirmado',
            message=f'{client.name} confirmou o agendamento de {date_str} as {time_str}',
            data={
                'appointment_id': appointment.id,
                'client_id': client.id,
                'client_name': client.name,
                'date': date_str,
                'time': time_str,
                'booking_code': appointment.booking_code
            }
        )

    @classmethod
    def notify_appointment_completed(cls, user_id, appointment, client, service):
        """Cria notificacao de agendamento concluido"""
        price_str = f"R$ {float(appointment.price):.2f}" if appointment.price else ""

        return cls.create_notification(
            user_id=user_id,
            notification_type='appointment_completed',
            title='Agendamento Concluido',
            message=f'Atendimento de {client.name} ({service.name}) foi concluido. {price_str}',
            data={
                'appointment_id': appointment.id,
                'client_id': client.id,
                'client_name': client.name,
                'service_name': service.name,
                'price': float(appointment.price) if appointment.price else None
            }
        )

    @classmethod
    def notify_appointment_cancelled(cls, user_id, appointment, client, reason=None):
        """Cria notificacao de agendamento cancelado"""
        date_str = appointment.appointment_date.strftime('%d/%m/%Y')
        time_str = appointment.start_time.strftime('%H:%M') if hasattr(appointment.start_time, 'strftime') else str(appointment.start_time)[:5]

        message = f'{client.name} cancelou o agendamento de {date_str} as {time_str}'
        if reason:
            message += f'. Motivo: {reason}'

        return cls.create_notification(
            user_id=user_id,
            notification_type='appointment_cancelled',
            title='Agendamento Cancelado',
            message=message,
            data={
                'appointment_id': appointment.id,
                'client_id': client.id,
                'client_name': client.name,
                'date': date_str,
                'time': time_str,
                'reason': reason
            }
        )

    @classmethod
    def notify_appointment_rescheduled(cls, user_id, appointment, client, old_date, old_time):
        """Cria notificacao de agendamento reagendado"""
        new_date_str = appointment.appointment_date.strftime('%d/%m/%Y')
        new_time_str = appointment.start_time.strftime('%H:%M') if hasattr(appointment.start_time, 'strftime') else str(appointment.start_time)[:5]
        old_date_str = old_date.strftime('%d/%m/%Y') if hasattr(old_date, 'strftime') else str(old_date)
        old_time_str = old_time.strftime('%H:%M') if hasattr(old_time, 'strftime') else str(old_time)[:5]

        return cls.create_notification(
            user_id=user_id,
            notification_type='appointment_rescheduled',
            title='Agendamento Reagendado',
            message=f'{client.name} reagendou de {old_date_str} {old_time_str} para {new_date_str} {new_time_str}',
            data={
                'appointment_id': appointment.id,
                'client_id': client.id,
                'client_name': client.name,
                'old_date': old_date_str,
                'old_time': old_time_str,
                'new_date': new_date_str,
                'new_time': new_time_str
            }
        )
