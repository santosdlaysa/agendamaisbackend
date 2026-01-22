"""
Testes para o servico de notificacoes unificado (NotificationService)
"""
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, date, time, timedelta
import json


class TestNotificationMessages:
    """Testes para funcoes de criacao de mensagens"""

    def test_create_new_client_message(self):
        """Testar criacao de mensagem de boas-vindas para novo cliente"""
        from src.services.notification_service import create_new_client_message

        message = create_new_client_message(
            client_name='Maria Silva',
            business_name='Salao Exemplo',
            booking_url='https://agendarmais.com/agendar/salao-exemplo'
        )

        assert 'Maria Silva' in message
        assert 'Salao Exemplo' in message
        assert 'https://agendarmais.com/agendar/salao-exemplo' in message
        assert 'cadastro' in message.lower()

    def test_create_new_client_message_without_url(self):
        """Testar mensagem de boas-vindas sem URL"""
        from src.services.notification_service import create_new_client_message

        message = create_new_client_message(
            client_name='Joao Santos',
            business_name='Barbearia Top'
        )

        assert 'Joao Santos' in message
        assert 'Barbearia Top' in message

    def test_create_appointment_created_message(self):
        """Testar criacao de mensagem de agendamento criado"""
        from src.services.notification_service import create_appointment_created_message

        message = create_appointment_created_message(
            client_name='Maria Silva',
            appointment_date='15/01/2024',
            appointment_time='10:00',
            service_name='Corte de Cabelo',
            professional_name='Carlos',
            business_name='Salao Exemplo',
            booking_code='ABC12345',
            price=50.00
        )

        assert 'Maria Silva' in message
        assert '15/01/2024' in message
        assert '10:00' in message
        assert 'Corte de Cabelo' in message
        assert 'Carlos' in message
        assert 'ABC12345' in message
        assert '50.00' in message

    def test_create_appointment_confirmed_message(self):
        """Testar criacao de mensagem de agendamento confirmado"""
        from src.services.notification_service import create_appointment_confirmed_message

        message = create_appointment_confirmed_message(
            client_name='Joao Santos',
            appointment_date='20/01/2024',
            appointment_time='14:30',
            service_name='Barba',
            business_name='Barbearia Top'
        )

        assert 'Joao Santos' in message
        assert '20/01/2024' in message
        assert '14:30' in message
        assert 'Barba' in message
        assert 'Confirmado' in message

    def test_create_appointment_cancelled_message(self):
        """Testar criacao de mensagem de agendamento cancelado"""
        from src.services.notification_service import create_appointment_cancelled_message

        message = create_appointment_cancelled_message(
            client_name='Ana Costa',
            appointment_date='25/01/2024',
            appointment_time='09:00',
            service_name='Manicure',
            business_name='Salao Beleza',
            reason='Cliente solicitou cancelamento'
        )

        assert 'Ana Costa' in message
        assert '25/01/2024' in message
        assert '09:00' in message
        assert 'cancelado' in message.lower()
        assert 'Cliente solicitou cancelamento' in message

    def test_create_appointment_cancelled_message_without_reason(self):
        """Testar mensagem de cancelamento sem motivo"""
        from src.services.notification_service import create_appointment_cancelled_message

        message = create_appointment_cancelled_message(
            client_name='Ana Costa',
            appointment_date='25/01/2024',
            appointment_time='09:00',
            service_name='Manicure',
            business_name='Salao Beleza'
        )

        assert 'Ana Costa' in message
        assert 'cancelado' in message.lower()

    def test_create_appointment_rescheduled_message(self):
        """Testar criacao de mensagem de agendamento reagendado"""
        from src.services.notification_service import create_appointment_rescheduled_message

        message = create_appointment_rescheduled_message(
            client_name='Pedro Lima',
            old_date='10/01/2024',
            old_time='15:00',
            new_date='12/01/2024',
            new_time='16:00',
            service_name='Corte Masculino',
            professional_name='Marcos',
            business_name='Barbearia'
        )

        assert 'Pedro Lima' in message
        assert '10/01/2024' in message
        assert '15:00' in message
        assert '12/01/2024' in message
        assert '16:00' in message
        assert 'Reagendado' in message

    def test_create_appointment_completed_message(self):
        """Testar criacao de mensagem de agendamento concluido"""
        from src.services.notification_service import create_appointment_completed_message

        message = create_appointment_completed_message(
            client_name='Julia Ferreira',
            service_name='Escova',
            professional_name='Carla',
            business_name='Salao Premium',
            price=80.00
        )

        assert 'Julia Ferreira' in message
        assert 'Escova' in message
        assert 'Carla' in message
        assert '80.00' in message
        assert 'Obrigado' in message


class TestNotificationResult:
    """Testes para a classe NotificationResult"""

    def test_notification_result_success(self):
        """Testar resultado de notificacao bem-sucedida"""
        from src.services.notification_service import NotificationResult

        result = NotificationResult(
            success=True,
            channel='email',
            message_id='msg_123'
        )

        assert result.success is True
        assert result.channel == 'email'
        assert result.message_id == 'msg_123'
        assert result.error is None

    def test_notification_result_failure(self):
        """Testar resultado de notificacao com falha"""
        from src.services.notification_service import NotificationResult

        result = NotificationResult(
            success=False,
            channel='whatsapp',
            error='Numero invalido'
        )

        assert result.success is False
        assert result.channel == 'whatsapp'
        assert result.message_id is None
        assert result.error == 'Numero invalido'

    def test_notification_result_to_dict(self):
        """Testar conversao para dicionario"""
        from src.services.notification_service import NotificationResult

        result = NotificationResult(
            success=True,
            channel='sms',
            message_id='sms_456'
        )

        result_dict = result.to_dict()

        assert result_dict['success'] is True
        assert result_dict['channel'] == 'sms'
        assert result_dict['message_id'] == 'sms_456'
        assert result_dict['error'] is None


class TestNotificationServiceNewClient:
    """Testes para notificacoes de novo cliente"""

    @patch('src.services.notification_service.send_email')
    def test_send_new_client_notification_email_success(self, mock_send_email):
        """Testar envio de notificacao por email com sucesso"""
        from src.services.notification_service import NotificationService

        mock_send_email.return_value = (True, 'Email enviado')

        # Mock do cliente
        mock_client = MagicMock()
        mock_client.name = 'Maria Silva'
        mock_client.email = 'maria@email.com'
        mock_client.phone = None

        results = NotificationService.send_new_client_notification(
            client=mock_client,
            business_name='Salao Exemplo',
            channels=['email']
        )

        assert 'email' in results
        assert results['email'].success is True
        mock_send_email.assert_called_once()

    @patch('src.services.notification_service.send_whatsapp')
    @patch('src.services.notification_service.is_twilio_configured')
    def test_send_new_client_notification_whatsapp_success(self, mock_twilio_config, mock_send_whatsapp):
        """Testar envio de notificacao por WhatsApp com sucesso"""
        from src.services.notification_service import NotificationService

        mock_twilio_config.return_value = True
        mock_send_whatsapp.return_value = (True, 'msg_sid_123')

        mock_client = MagicMock()
        mock_client.name = 'Joao Santos'
        mock_client.email = None
        mock_client.phone = '+5511999999999'

        results = NotificationService.send_new_client_notification(
            client=mock_client,
            business_name='Barbearia Top',
            channels=['whatsapp']
        )

        assert 'whatsapp' in results
        assert results['whatsapp'].success is True
        assert results['whatsapp'].message_id == 'msg_sid_123'

    @patch('src.services.notification_service.send_email')
    @patch('src.services.notification_service.send_whatsapp')
    @patch('src.services.notification_service.is_twilio_configured')
    def test_send_new_client_notification_multiple_channels(self, mock_twilio_config, mock_send_whatsapp, mock_send_email):
        """Testar envio de notificacao por multiplos canais"""
        from src.services.notification_service import NotificationService

        mock_twilio_config.return_value = True
        mock_send_email.return_value = (True, 'Email OK')
        mock_send_whatsapp.return_value = (True, 'msg_123')

        mock_client = MagicMock()
        mock_client.name = 'Ana Costa'
        mock_client.email = 'ana@email.com'
        mock_client.phone = '+5511988888888'

        results = NotificationService.send_new_client_notification(
            client=mock_client,
            business_name='Salao Beleza',
            channels=['email', 'whatsapp']
        )

        assert 'email' in results
        assert 'whatsapp' in results
        assert results['email'].success is True
        assert results['whatsapp'].success is True

    @patch('src.services.notification_service.send_email')
    def test_send_new_client_notification_email_failure(self, mock_send_email):
        """Testar falha no envio de email"""
        from src.services.notification_service import NotificationService

        mock_send_email.return_value = (False, 'Erro de conexao')

        mock_client = MagicMock()
        mock_client.name = 'Pedro Lima'
        mock_client.email = 'pedro@email.com'
        mock_client.phone = None

        results = NotificationService.send_new_client_notification(
            client=mock_client,
            business_name='Salao X',
            channels=['email']
        )

        assert 'email' in results
        assert results['email'].success is False
        assert results['email'].error == 'Erro de conexao'

    def test_send_new_client_notification_no_contact(self):
        """Testar quando cliente nao tem contato"""
        from src.services.notification_service import NotificationService

        mock_client = MagicMock()
        mock_client.name = 'Sem Contato'
        mock_client.email = None
        mock_client.phone = None

        results = NotificationService.send_new_client_notification(
            client=mock_client,
            business_name='Salao Y',
            channels=['email', 'whatsapp']
        )

        # Nenhum canal deve ter resultado pois cliente nao tem contato
        assert 'email' not in results
        assert 'whatsapp' not in results


class TestNotificationServiceAppointment:
    """Testes para notificacoes de agendamento"""

    @patch('src.services.notification_service.send_email')
    def test_send_appointment_created_notification(self, mock_send_email):
        """Testar notificacao de agendamento criado"""
        from src.services.notification_service import NotificationService

        mock_send_email.return_value = (True, 'Email enviado')

        # Mocks
        mock_appointment = MagicMock()
        mock_appointment.appointment_date = date(2024, 1, 15)
        mock_appointment.start_time = time(10, 0)
        mock_appointment.price = 50.00
        mock_appointment.booking_code = 'ABC123'

        mock_client = MagicMock()
        mock_client.name = 'Maria Silva'
        mock_client.email = 'maria@email.com'
        mock_client.phone = None

        mock_professional = MagicMock()
        mock_professional.name = 'Carlos'

        mock_service = MagicMock()
        mock_service.name = 'Corte'
        mock_service.price = 50.00

        results = NotificationService.send_appointment_created_notification(
            appointment=mock_appointment,
            client=mock_client,
            professional=mock_professional,
            service=mock_service,
            business_name='Salao X',
            booking_code='ABC123',
            channels=['email']
        )

        assert 'email' in results
        assert results['email'].success is True

    @patch('src.services.notification_service.send_email')
    def test_send_appointment_confirmed_notification(self, mock_send_email):
        """Testar notificacao de agendamento confirmado"""
        from src.services.notification_service import NotificationService

        mock_send_email.return_value = (True, 'OK')

        mock_appointment = MagicMock()
        mock_appointment.appointment_date = date(2024, 1, 20)
        mock_appointment.start_time = time(14, 30)

        mock_client = MagicMock()
        mock_client.name = 'Joao'
        mock_client.email = 'joao@email.com'
        mock_client.phone = None

        mock_professional = MagicMock()
        mock_professional.name = 'Ana'

        mock_service = MagicMock()
        mock_service.name = 'Barba'

        results = NotificationService.send_appointment_confirmed_notification(
            appointment=mock_appointment,
            client=mock_client,
            professional=mock_professional,
            service=mock_service,
            business_name='Barbearia',
            channels=['email']
        )

        assert 'email' in results
        assert results['email'].success is True

    @patch('src.services.notification_service.send_email')
    def test_send_appointment_cancelled_notification(self, mock_send_email):
        """Testar notificacao de agendamento cancelado"""
        from src.services.notification_service import NotificationService

        mock_send_email.return_value = (True, 'OK')

        mock_appointment = MagicMock()
        mock_appointment.appointment_date = date(2024, 1, 25)
        mock_appointment.start_time = time(9, 0)

        mock_client = MagicMock()
        mock_client.name = 'Ana'
        mock_client.email = 'ana@email.com'
        mock_client.phone = None

        mock_service = MagicMock()
        mock_service.name = 'Manicure'

        results = NotificationService.send_appointment_cancelled_notification(
            appointment=mock_appointment,
            client=mock_client,
            service=mock_service,
            business_name='Salao Y',
            reason='Cliente solicitou',
            channels=['email']
        )

        assert 'email' in results
        assert results['email'].success is True

    @patch('src.services.notification_service.send_email')
    def test_send_appointment_rescheduled_notification(self, mock_send_email):
        """Testar notificacao de agendamento reagendado"""
        from src.services.notification_service import NotificationService

        mock_send_email.return_value = (True, 'OK')

        mock_appointment = MagicMock()
        mock_appointment.appointment_date = date(2024, 1, 30)
        mock_appointment.start_time = time(16, 0)

        mock_client = MagicMock()
        mock_client.name = 'Pedro'
        mock_client.email = 'pedro@email.com'
        mock_client.phone = None

        mock_professional = MagicMock()
        mock_professional.name = 'Lucas'

        mock_service = MagicMock()
        mock_service.name = 'Corte'

        results = NotificationService.send_appointment_rescheduled_notification(
            appointment=mock_appointment,
            client=mock_client,
            professional=mock_professional,
            service=mock_service,
            business_name='Barbearia Z',
            old_date=date(2024, 1, 28),
            old_time=time(14, 0),
            channels=['email']
        )

        assert 'email' in results
        assert results['email'].success is True

    @patch('src.services.notification_service.send_email')
    def test_send_appointment_completed_notification(self, mock_send_email):
        """Testar notificacao de agendamento concluido"""
        from src.services.notification_service import NotificationService

        mock_send_email.return_value = (True, 'OK')

        mock_appointment = MagicMock()
        mock_appointment.appointment_date = date(2024, 1, 15)
        mock_appointment.price = 80.00
        mock_appointment.payment_method = 'pix'

        mock_client = MagicMock()
        mock_client.name = 'Julia'
        mock_client.email = 'julia@email.com'
        mock_client.phone = None

        mock_professional = MagicMock()
        mock_professional.name = 'Carla'

        mock_service = MagicMock()
        mock_service.name = 'Escova'

        results = NotificationService.send_appointment_completed_notification(
            appointment=mock_appointment,
            client=mock_client,
            professional=mock_professional,
            service=mock_service,
            business_name='Salao Premium',
            price=80.00,
            payment_method='pix',
            channels=['email']
        )

        assert 'email' in results
        assert results['email'].success is True


class TestNotificationServiceSMS:
    """Testes para notificacoes via SMS"""

    @patch('src.services.notification_service.send_sms')
    @patch('src.services.notification_service.is_twilio_configured')
    def test_send_new_client_notification_sms(self, mock_twilio_config, mock_send_sms):
        """Testar envio de SMS para novo cliente"""
        from src.services.notification_service import NotificationService

        mock_twilio_config.return_value = True
        mock_send_sms.return_value = (True, 'sms_123')

        mock_client = MagicMock()
        mock_client.name = 'Carlos'
        mock_client.email = None
        mock_client.phone = '+5511977777777'

        results = NotificationService.send_new_client_notification(
            client=mock_client,
            business_name='Salao ABC',
            channels=['sms']
        )

        assert 'sms' in results
        assert results['sms'].success is True
        assert results['sms'].message_id == 'sms_123'

    @patch('src.services.notification_service.send_sms')
    @patch('src.services.notification_service.is_twilio_configured')
    def test_send_appointment_created_notification_sms(self, mock_twilio_config, mock_send_sms):
        """Testar envio de SMS para agendamento criado"""
        from src.services.notification_service import NotificationService

        mock_twilio_config.return_value = True
        mock_send_sms.return_value = (True, 'sms_456')

        mock_appointment = MagicMock()
        mock_appointment.appointment_date = date(2024, 2, 10)
        mock_appointment.start_time = time(11, 0)
        mock_appointment.price = 60.00
        mock_appointment.booking_code = 'XYZ789'

        mock_client = MagicMock()
        mock_client.name = 'Roberto'
        mock_client.email = None
        mock_client.phone = '+5511966666666'

        mock_professional = MagicMock()
        mock_professional.name = 'Fernando'

        mock_service = MagicMock()
        mock_service.name = 'Barba'
        mock_service.price = 60.00

        results = NotificationService.send_appointment_created_notification(
            appointment=mock_appointment,
            client=mock_client,
            professional=mock_professional,
            service=mock_service,
            business_name='Barbearia XYZ',
            booking_code='XYZ789',
            channels=['sms']
        )

        assert 'sms' in results
        assert results['sms'].success is True


class TestNotificationServiceTwilioNotConfigured:
    """Testes quando Twilio nao esta configurado"""

    @patch('src.services.notification_service.is_twilio_configured')
    def test_whatsapp_not_sent_when_twilio_not_configured(self, mock_twilio_config):
        """Testar que WhatsApp nao e enviado quando Twilio nao esta configurado"""
        from src.services.notification_service import NotificationService

        mock_twilio_config.return_value = False

        mock_client = MagicMock()
        mock_client.name = 'Test'
        mock_client.email = None
        mock_client.phone = '+5511999999999'

        results = NotificationService.send_new_client_notification(
            client=mock_client,
            business_name='Test',
            channels=['whatsapp']
        )

        # WhatsApp nao deve estar nos resultados pois Twilio nao esta configurado
        assert 'whatsapp' not in results

    @patch('src.services.notification_service.is_twilio_configured')
    def test_sms_not_sent_when_twilio_not_configured(self, mock_twilio_config):
        """Testar que SMS nao e enviado quando Twilio nao esta configurado"""
        from src.services.notification_service import NotificationService

        mock_twilio_config.return_value = False

        mock_client = MagicMock()
        mock_client.name = 'Test'
        mock_client.email = None
        mock_client.phone = '+5511999999999'

        results = NotificationService.send_new_client_notification(
            client=mock_client,
            business_name='Test',
            channels=['sms']
        )

        assert 'sms' not in results


class TestNotificationServiceException:
    """Testes para tratamento de excecoes"""

    @patch('src.services.notification_service.send_email')
    def test_email_exception_handled(self, mock_send_email):
        """Testar que excecoes de email sao tratadas"""
        from src.services.notification_service import NotificationService

        mock_send_email.side_effect = Exception('Erro inesperado')

        mock_client = MagicMock()
        mock_client.name = 'Test'
        mock_client.email = 'test@email.com'
        mock_client.phone = None

        results = NotificationService.send_new_client_notification(
            client=mock_client,
            business_name='Test',
            channels=['email']
        )

        assert 'email' in results
        assert results['email'].success is False
        assert 'Erro inesperado' in results['email'].error

    @patch('src.services.notification_service.send_whatsapp')
    @patch('src.services.notification_service.is_twilio_configured')
    def test_whatsapp_exception_handled(self, mock_twilio_config, mock_send_whatsapp):
        """Testar que excecoes de WhatsApp sao tratadas"""
        from src.services.notification_service import NotificationService

        mock_twilio_config.return_value = True
        mock_send_whatsapp.side_effect = Exception('Twilio error')

        mock_client = MagicMock()
        mock_client.name = 'Test'
        mock_client.email = None
        mock_client.phone = '+5511999999999'

        results = NotificationService.send_new_client_notification(
            client=mock_client,
            business_name='Test',
            channels=['whatsapp']
        )

        assert 'whatsapp' in results
        assert results['whatsapp'].success is False
        assert 'Twilio error' in results['whatsapp'].error


class TestNotificationServiceIntegration:
    """Testes de integracao (requer fixtures do conftest)"""

    def test_notification_service_import(self):
        """Testar que o servico pode ser importado corretamente"""
        from src.services.notification_service import (
            NotificationService,
            NotificationResult,
            NOTIFICATION_TYPES,
            create_new_client_message,
            create_appointment_created_message,
            create_appointment_confirmed_message,
            create_appointment_cancelled_message,
            create_appointment_rescheduled_message,
            create_appointment_completed_message,
            notification_service
        )

        assert NotificationService is not None
        assert NotificationResult is not None
        assert notification_service is not None
        assert len(NOTIFICATION_TYPES) > 0

    def test_notification_types_defined(self):
        """Testar que todos os tipos de notificacao estao definidos"""
        from src.services.notification_service import NOTIFICATION_TYPES

        expected_types = [
            'NEW_CLIENT',
            'APPOINTMENT_CREATED',
            'APPOINTMENT_CONFIRMED',
            'APPOINTMENT_CANCELLED',
            'APPOINTMENT_RESCHEDULED',
            'APPOINTMENT_COMPLETED',
            'APPOINTMENT_REMINDER'
        ]

        for notification_type in expected_types:
            assert notification_type in NOTIFICATION_TYPES
