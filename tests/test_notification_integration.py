"""
Testes de integracao para notificacoes nos endpoints de cliente e agendamento
"""
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, date, time, timedelta
import json


class TestClientNotificationIntegration:
    """Testes de integracao para notificacoes de cliente"""

    @patch('src.app.main.client.clients.NotificationService.send_new_client_notification')
    def test_create_client_sends_notification(self, mock_send_notification, client, auth_headers, app, db_session):
        """Testar que criar cliente envia notificacao"""
        from src.services.notification_service import NotificationResult

        # Mock do retorno de notificacao
        mock_send_notification.return_value = {
            'email': NotificationResult(success=True, channel='email', message_id='email_123')
        }

        with app.app_context():
            response = client.post(
                '/api/clients',
                headers=auth_headers,
                json={
                    'name': 'Cliente Teste',
                    'email': 'cliente.teste@email.com',
                    'phone': '+5511999999999'
                }
            )

        assert response.status_code == 201
        data = json.loads(response.data)
        assert 'client' in data

        # Verificar que notificacao foi chamada
        mock_send_notification.assert_called_once()

    @patch('src.app.main.client.clients.NotificationService.send_new_client_notification')
    def test_create_client_without_notification(self, mock_send_notification, client, auth_headers, app, db_session):
        """Testar criar cliente sem enviar notificacao"""
        with app.app_context():
            response = client.post(
                '/api/clients',
                headers=auth_headers,
                json={
                    'name': 'Cliente Sem Notificacao',
                    'email': 'sem.notif@email.com',
                    'send_notification': False
                }
            )

        assert response.status_code == 201
        mock_send_notification.assert_not_called()

    @patch('src.app.main.client.clients.NotificationService.send_new_client_notification')
    def test_create_client_specific_channels(self, mock_send_notification, client, auth_headers, app, db_session):
        """Testar criar cliente com canais especificos"""
        from src.services.notification_service import NotificationResult

        mock_send_notification.return_value = {
            'email': NotificationResult(success=True, channel='email', message_id='email_456')
        }

        with app.app_context():
            response = client.post(
                '/api/clients',
                headers=auth_headers,
                json={
                    'name': 'Cliente Canais',
                    'email': 'canais@email.com',
                    'notification_channels': ['email']
                }
            )

        assert response.status_code == 201

        # Verificar que foi chamado com canais corretos
        call_args = mock_send_notification.call_args
        assert call_args.kwargs['channels'] == ['email']

    @patch('src.app.main.client.clients.NotificationService.send_new_client_notification')
    def test_create_client_notification_failure_doesnt_break(self, mock_send_notification, client, auth_headers, app, db_session):
        """Testar que falha na notificacao nao impede criacao do cliente"""
        mock_send_notification.side_effect = Exception('Erro de notificacao')

        with app.app_context():
            response = client.post(
                '/api/clients',
                headers=auth_headers,
                json={
                    'name': 'Cliente Erro Notif',
                    'email': 'erro.notif@email.com'
                }
            )

        # Cliente deve ser criado mesmo com erro de notificacao
        assert response.status_code == 201
        data = json.loads(response.data)
        assert 'client' in data


class TestAppointmentNotificationIntegration:
    """Testes de integracao para notificacoes de agendamento"""

    @patch('src.app.main.appointment.appointments.NotificationService.send_appointment_created_notification')
    def test_create_appointment_sends_notification(self, mock_send_notification, client, auth_headers, app, db_session, test_appointment_with_code):
        """Testar que criar agendamento envia notificacao"""
        from src.services.notification_service import NotificationResult

        mock_send_notification.return_value = {
            'email': NotificationResult(success=True, channel='email', message_id='email_apt_123')
        }

        with app.app_context():
            # Usar dados do fixture
            apt_data = test_appointment_with_code
            user_id = apt_data['user'].id
            client_id = apt_data['client'].id
            professional_id = apt_data['professional'].id
            service_id = apt_data['service'].id

            # Criar token para o usuario correto
            from flask_jwt_extended import create_access_token
            token = create_access_token(identity=user_id)
            headers = {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            }

            response = client.post(
                '/api/appointments',
                headers=headers,
                json={
                    'client_id': client_id,
                    'professional_id': professional_id,
                    'service_id': service_id,
                    'appointment_date': (date.today() + timedelta(days=7)).isoformat(),
                    'start_time': '14:00'
                }
            )

        assert response.status_code == 201

    @patch('src.app.main.appointment.appointments.NotificationService.send_appointment_rescheduled_notification')
    def test_update_appointment_sends_reschedule_notification(self, mock_send_notification, client, auth_headers, app, db_session, test_appointment_with_code):
        """Testar que reagendar envia notificacao"""
        from src.services.notification_service import NotificationResult

        mock_send_notification.return_value = {
            'email': NotificationResult(success=True, channel='email', message_id='email_resched')
        }

        with app.app_context():
            apt_data = test_appointment_with_code
            appointment = apt_data['appointment']
            user_id = apt_data['user'].id
            client_id = apt_data['client'].id
            professional_id = apt_data['professional'].id
            service_id = apt_data['service'].id

            from flask_jwt_extended import create_access_token
            token = create_access_token(identity=user_id)
            headers = {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            }

            # Reagendar para nova data
            new_date = (date.today() + timedelta(days=10)).isoformat()

            response = client.put(
                f'/api/appointments/{appointment.id}',
                headers=headers,
                json={
                    'client_id': client_id,
                    'professional_id': professional_id,
                    'service_id': service_id,
                    'appointment_date': new_date,
                    'start_time': '15:00'
                }
            )

        assert response.status_code == 200

    @patch('src.app.main.appointment.appointments.NotificationService.send_appointment_confirmed_notification')
    def test_confirm_appointment_sends_notification(self, mock_send_notification, client, auth_headers, app, db_session, test_appointment_with_code):
        """Testar que confirmar agendamento envia notificacao"""
        from src.services.notification_service import NotificationResult

        mock_send_notification.return_value = {
            'email': NotificationResult(success=True, channel='email', message_id='email_confirm')
        }

        with app.app_context():
            apt_data = test_appointment_with_code
            appointment = apt_data['appointment']
            user_id = apt_data['user'].id

            from flask_jwt_extended import create_access_token
            token = create_access_token(identity=user_id)
            headers = {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            }

            response = client.put(
                f'/api/appointments/{appointment.id}/status',
                headers=headers,
                json={'status': 'confirmed'}
            )

        assert response.status_code == 200

    @patch('src.app.main.appointment.appointments.NotificationService.send_appointment_cancelled_notification')
    def test_cancel_appointment_sends_notification(self, mock_send_notification, client, auth_headers, app, db_session, test_appointment_with_code):
        """Testar que cancelar agendamento envia notificacao"""
        from src.services.notification_service import NotificationResult

        mock_send_notification.return_value = {
            'email': NotificationResult(success=True, channel='email', message_id='email_cancel')
        }

        with app.app_context():
            apt_data = test_appointment_with_code
            appointment = apt_data['appointment']
            user_id = apt_data['user'].id

            from flask_jwt_extended import create_access_token
            token = create_access_token(identity=user_id)
            headers = {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            }

            response = client.put(
                f'/api/appointments/{appointment.id}/status',
                headers=headers,
                json={
                    'status': 'cancelled',
                    'cancellation_reason': 'Cliente solicitou'
                }
            )

        assert response.status_code == 200

    @patch('src.app.main.appointment.appointments.NotificationService.send_appointment_completed_notification')
    def test_complete_appointment_sends_notification(self, mock_send_notification, client, auth_headers, app, db_session, test_appointment_with_code):
        """Testar que concluir agendamento envia notificacao"""
        from src.services.notification_service import NotificationResult

        mock_send_notification.return_value = {
            'email': NotificationResult(success=True, channel='email', message_id='email_complete')
        }

        with app.app_context():
            apt_data = test_appointment_with_code
            appointment = apt_data['appointment']
            user_id = apt_data['user'].id

            from flask_jwt_extended import create_access_token
            token = create_access_token(identity=user_id)
            headers = {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            }

            response = client.put(
                f'/api/appointments/{appointment.id}/complete',
                headers=headers,
                json={'payment_method': 'pix'}
            )

        assert response.status_code == 200


class TestNotificationChannelSelection:
    """Testes para selecao de canais de notificacao"""

    @patch('src.app.main.client.clients.NotificationService.send_new_client_notification')
    def test_email_only_channel(self, mock_send_notification, client, auth_headers, app, db_session):
        """Testar notificacao apenas por email"""
        from src.services.notification_service import NotificationResult

        mock_send_notification.return_value = {
            'email': NotificationResult(success=True, channel='email')
        }

        with app.app_context():
            response = client.post(
                '/api/clients',
                headers=auth_headers,
                json={
                    'name': 'Email Only',
                    'email': 'email.only@test.com',
                    'notification_channels': ['email']
                }
            )

        assert response.status_code == 201
        call_args = mock_send_notification.call_args
        assert call_args.kwargs['channels'] == ['email']

    @patch('src.app.main.client.clients.NotificationService.send_new_client_notification')
    def test_whatsapp_only_channel(self, mock_send_notification, client, auth_headers, app, db_session):
        """Testar notificacao apenas por WhatsApp"""
        from src.services.notification_service import NotificationResult

        mock_send_notification.return_value = {
            'whatsapp': NotificationResult(success=True, channel='whatsapp')
        }

        with app.app_context():
            response = client.post(
                '/api/clients',
                headers=auth_headers,
                json={
                    'name': 'WhatsApp Only',
                    'phone': '+5511999999999',
                    'notification_channels': ['whatsapp']
                }
            )

        assert response.status_code == 201
        call_args = mock_send_notification.call_args
        assert call_args.kwargs['channels'] == ['whatsapp']

    @patch('src.app.main.client.clients.NotificationService.send_new_client_notification')
    def test_multiple_channels(self, mock_send_notification, client, auth_headers, app, db_session):
        """Testar notificacao por multiplos canais"""
        from src.services.notification_service import NotificationResult

        mock_send_notification.return_value = {
            'email': NotificationResult(success=True, channel='email'),
            'whatsapp': NotificationResult(success=True, channel='whatsapp'),
            'sms': NotificationResult(success=True, channel='sms')
        }

        with app.app_context():
            response = client.post(
                '/api/clients',
                headers=auth_headers,
                json={
                    'name': 'Multi Channel',
                    'email': 'multi@test.com',
                    'phone': '+5511999999999',
                    'notification_channels': ['email', 'whatsapp', 'sms']
                }
            )

        assert response.status_code == 201
        call_args = mock_send_notification.call_args
        assert set(call_args.kwargs['channels']) == {'email', 'whatsapp', 'sms'}


class TestNotificationResponseData:
    """Testes para dados de resposta das notificacoes"""

    @patch('src.app.main.client.clients.NotificationService.send_new_client_notification')
    def test_notification_results_in_response(self, mock_send_notification, client, auth_headers, app, db_session):
        """Testar que resultados de notificacao estao na resposta"""
        from src.services.notification_service import NotificationResult

        mock_send_notification.return_value = {
            'email': NotificationResult(success=True, channel='email', message_id='msg_123'),
            'whatsapp': NotificationResult(success=False, channel='whatsapp', error='Numero invalido')
        }

        with app.app_context():
            response = client.post(
                '/api/clients',
                headers=auth_headers,
                json={
                    'name': 'Notification Response',
                    'email': 'notif.response@test.com',
                    'phone': '+5511999999999'
                }
            )

        assert response.status_code == 201
        data = json.loads(response.data)

        # Verificar que notifications esta na resposta
        assert 'notifications' in data
        assert 'email' in data['notifications']
        assert data['notifications']['email']['success'] is True
        assert data['notifications']['email']['message_id'] == 'msg_123'

        assert 'whatsapp' in data['notifications']
        assert data['notifications']['whatsapp']['success'] is False
        assert data['notifications']['whatsapp']['error'] == 'Numero invalido'
