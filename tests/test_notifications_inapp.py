"""
Testes para notificacoes in-app (dashboard)
"""
import pytest
from unittest.mock import MagicMock
from datetime import datetime, date, time, timedelta
import json


class TestNotificationModel:
    """Testes para o modelo Notification"""

    def test_create_notification(self, app, db_session):
        """Testar criacao de notificacao"""
        from src.models.notification import Notification
        from src.models.user import User

        with app.app_context():
            # Criar usuario
            user = User(
                name='Test User',
                email='testnotif@example.com',
                password_hash='hashed'
            )
            db_session.add(user)
            db_session.flush()

            # Criar notificacao
            notification = Notification.create_notification(
                user_id=user.id,
                notification_type='new_appointment',
                title='Novo Agendamento',
                message='Cliente X agendou servico Y',
                data={'appointment_id': 1}
            )
            db_session.commit()

            assert notification.id is not None
            assert notification.user_id == user.id
            assert notification.type == 'new_appointment'
            assert notification.title == 'Novo Agendamento'
            assert notification.read is False

    def test_notification_to_dict(self, app, db_session):
        """Testar conversao para dicionario"""
        from src.models.notification import Notification
        from src.models.user import User

        with app.app_context():
            user = User(
                name='Test User 2',
                email='testnotif2@example.com',
                password_hash='hashed'
            )
            db_session.add(user)
            db_session.flush()

            notification = Notification.create_notification(
                user_id=user.id,
                notification_type='new_client',
                title='Novo Cliente',
                message='Cliente Z foi cadastrado',
                data={'client_id': 5}
            )
            db_session.commit()

            result = notification.to_dict()

            assert 'id' in result
            assert result['type'] == 'new_client'
            assert result['title'] == 'Novo Cliente'
            assert result['read'] is False
            assert result['data']['client_id'] == 5

    def test_mark_as_read(self, app, db_session):
        """Testar marcar como lida"""
        from src.models.notification import Notification
        from src.models.user import User

        with app.app_context():
            user = User(
                name='Test User 3',
                email='testnotif3@example.com',
                password_hash='hashed'
            )
            db_session.add(user)
            db_session.flush()

            notification = Notification.create_notification(
                user_id=user.id,
                notification_type='system',
                title='Aviso',
                message='Mensagem do sistema'
            )
            db_session.commit()

            assert notification.read is False
            assert notification.read_at is None

            notification.mark_as_read()
            db_session.commit()

            assert notification.read is True
            assert notification.read_at is not None

    def test_get_unread_count(self, app, db_session):
        """Testar contagem de nao lidas"""
        from src.models.notification import Notification
        from src.models.user import User

        with app.app_context():
            user = User(
                name='Test User 4',
                email='testnotif4@example.com',
                password_hash='hashed'
            )
            db_session.add(user)
            db_session.flush()

            # Criar 3 notificacoes
            for i in range(3):
                Notification.create_notification(
                    user_id=user.id,
                    notification_type='new_appointment',
                    title=f'Notificacao {i}',
                    message=f'Mensagem {i}'
                )
            db_session.commit()

            count = Notification.get_unread_count(user.id)
            assert count == 3

    def test_mark_all_as_read(self, app, db_session):
        """Testar marcar todas como lidas"""
        from src.models.notification import Notification
        from src.models.user import User

        with app.app_context():
            user = User(
                name='Test User 5',
                email='testnotif5@example.com',
                password_hash='hashed'
            )
            db_session.add(user)
            db_session.flush()

            # Criar 5 notificacoes
            for i in range(5):
                Notification.create_notification(
                    user_id=user.id,
                    notification_type='new_appointment',
                    title=f'Notificacao {i}',
                    message=f'Mensagem {i}'
                )
            db_session.commit()

            assert Notification.get_unread_count(user.id) == 5

            Notification.mark_all_as_read(user.id)

            assert Notification.get_unread_count(user.id) == 0


class TestNotificationFactoryMethods:
    """Testes para metodos de fabrica de notificacoes"""

    def test_notify_new_appointment(self, app, db_session):
        """Testar notificacao de novo agendamento"""
        from src.models.notification import Notification
        from src.models.user import User

        with app.app_context():
            user = User(
                name='Business Owner',
                email='owner@example.com',
                password_hash='hashed'
            )
            db_session.add(user)
            db_session.flush()

            # Mock dos objetos
            mock_client = MagicMock()
            mock_client.id = 1
            mock_client.name = 'Maria Silva'

            mock_service = MagicMock()
            mock_service.id = 1
            mock_service.name = 'Corte de Cabelo'

            mock_professional = MagicMock()
            mock_professional.id = 1
            mock_professional.name = 'Carlos'

            mock_appointment = MagicMock()
            mock_appointment.id = 1
            mock_appointment.appointment_date = date.today()
            mock_appointment.start_time = time(10, 0)
            mock_appointment.booking_code = 'ABC123'

            notification = Notification.notify_new_appointment(
                user_id=user.id,
                appointment=mock_appointment,
                client=mock_client,
                service=mock_service,
                professional=mock_professional
            )
            db_session.commit()

            assert notification.type == 'new_appointment'
            assert 'Maria Silva' in notification.message
            assert 'Corte de Cabelo' in notification.message
            assert notification.data['client_name'] == 'Maria Silva'

    def test_notify_new_client(self, app, db_session):
        """Testar notificacao de novo cliente"""
        from src.models.notification import Notification
        from src.models.user import User

        with app.app_context():
            user = User(
                name='Business Owner 2',
                email='owner2@example.com',
                password_hash='hashed'
            )
            db_session.add(user)
            db_session.flush()

            mock_client = MagicMock()
            mock_client.id = 2
            mock_client.name = 'Joao Santos'
            mock_client.phone = '+5511999999999'
            mock_client.email = 'joao@email.com'

            notification = Notification.notify_new_client(
                user_id=user.id,
                client=mock_client
            )
            db_session.commit()

            assert notification.type == 'new_client'
            assert 'Joao Santos' in notification.message
            assert notification.data['client_name'] == 'Joao Santos'

    def test_notify_appointment_cancelled(self, app, db_session):
        """Testar notificacao de agendamento cancelado"""
        from src.models.notification import Notification
        from src.models.user import User

        with app.app_context():
            user = User(
                name='Business Owner 3',
                email='owner3@example.com',
                password_hash='hashed'
            )
            db_session.add(user)
            db_session.flush()

            mock_client = MagicMock()
            mock_client.id = 3
            mock_client.name = 'Ana Costa'

            mock_appointment = MagicMock()
            mock_appointment.id = 2
            mock_appointment.appointment_date = date.today()
            mock_appointment.start_time = time(14, 30)

            notification = Notification.notify_appointment_cancelled(
                user_id=user.id,
                appointment=mock_appointment,
                client=mock_client,
                reason='Cliente solicitou'
            )
            db_session.commit()

            assert notification.type == 'appointment_cancelled'
            assert 'Ana Costa' in notification.message
            assert 'cancelou' in notification.message
            assert notification.data['reason'] == 'Cliente solicitou'


class TestNotificationRoutes:
    """Testes para as rotas de notificacoes"""

    def test_get_notifications(self, app, client, db_session):
        """Testar listagem de notificacoes"""
        from src.models.notification import Notification
        from src.models.user import User
        from flask_jwt_extended import create_access_token

        with app.app_context():
            user = User(
                name='Route Test User',
                email='routetest@example.com',
                password_hash='hashed'
            )
            db_session.add(user)
            db_session.flush()

            # Criar notificacoes
            for i in range(3):
                Notification.create_notification(
                    user_id=user.id,
                    notification_type='new_appointment',
                    title=f'Notificacao {i}',
                    message=f'Mensagem {i}'
                )
            db_session.commit()

            # Criar token
            token = create_access_token(identity=user.id)
            headers = {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            }

            response = client.get('/api/notifications', headers=headers)

            assert response.status_code == 200
            data = json.loads(response.data)
            assert 'notifications' in data
            assert len(data['notifications']) == 3
            assert 'unread_count' in data
            assert data['unread_count'] == 3

    def test_get_unread_count(self, app, client, db_session):
        """Testar contagem de nao lidas via API"""
        from src.models.notification import Notification
        from src.models.user import User
        from flask_jwt_extended import create_access_token

        with app.app_context():
            user = User(
                name='Count Test User',
                email='counttest@example.com',
                password_hash='hashed'
            )
            db_session.add(user)
            db_session.flush()

            # Criar notificacoes
            for i in range(5):
                Notification.create_notification(
                    user_id=user.id,
                    notification_type='new_client',
                    title=f'Cliente {i}',
                    message=f'Novo cliente {i}'
                )
            db_session.commit()

            token = create_access_token(identity=user.id)
            headers = {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            }

            response = client.get('/api/notifications/count', headers=headers)

            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['unread_count'] == 5

    def test_mark_as_read_api(self, app, client, db_session):
        """Testar marcar como lida via API"""
        from src.models.notification import Notification
        from src.models.user import User
        from flask_jwt_extended import create_access_token

        with app.app_context():
            user = User(
                name='Mark Read Test User',
                email='markread@example.com',
                password_hash='hashed'
            )
            db_session.add(user)
            db_session.flush()

            notification = Notification.create_notification(
                user_id=user.id,
                notification_type='system',
                title='Aviso',
                message='Teste'
            )
            db_session.commit()

            token = create_access_token(identity=user.id)
            headers = {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            }

            response = client.put(
                f'/api/notifications/{notification.id}/read',
                headers=headers
            )

            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['notification']['read'] is True

    def test_mark_all_as_read_api(self, app, client, db_session):
        """Testar marcar todas como lidas via API"""
        from src.models.notification import Notification
        from src.models.user import User
        from flask_jwt_extended import create_access_token

        with app.app_context():
            user = User(
                name='Mark All Test User',
                email='markall@example.com',
                password_hash='hashed'
            )
            db_session.add(user)
            db_session.flush()

            for i in range(4):
                Notification.create_notification(
                    user_id=user.id,
                    notification_type='new_appointment',
                    title=f'Notif {i}',
                    message=f'Msg {i}'
                )
            db_session.commit()

            token = create_access_token(identity=user.id)
            headers = {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            }

            # Verificar que temos 4 nao lidas
            response = client.get('/api/notifications/count', headers=headers)
            data = json.loads(response.data)
            assert data['unread_count'] == 4

            # Marcar todas como lidas
            response = client.put('/api/notifications/read-all', headers=headers)
            assert response.status_code == 200

            # Verificar que agora temos 0 nao lidas
            response = client.get('/api/notifications/count', headers=headers)
            data = json.loads(response.data)
            assert data['unread_count'] == 0

    def test_delete_notification_api(self, app, client, db_session):
        """Testar exclusao de notificacao via API"""
        from src.models.notification import Notification
        from src.models.user import User
        from flask_jwt_extended import create_access_token

        with app.app_context():
            user = User(
                name='Delete Test User',
                email='deletetest@example.com',
                password_hash='hashed'
            )
            db_session.add(user)
            db_session.flush()

            notification = Notification.create_notification(
                user_id=user.id,
                notification_type='system',
                title='Para excluir',
                message='Sera excluida'
            )
            db_session.commit()

            notif_id = notification.id

            token = create_access_token(identity=user.id)
            headers = {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            }

            response = client.delete(
                f'/api/notifications/{notif_id}',
                headers=headers
            )

            assert response.status_code == 200

            # Verificar que foi excluida
            deleted = Notification.query.get(notif_id)
            assert deleted is None
