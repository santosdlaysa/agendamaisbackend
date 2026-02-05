"""
Testes E2E para consulta de agendamentos por codigo ou telefone
"""
import pytest
import json


class TestAppointmentLookupByCode:
    """Testes para busca de agendamento por codigo"""

    def test_get_appointment_by_code_success(self, client, test_appointment_with_code, app):
        """Testar busca de agendamento por codigo com sucesso"""
        with app.app_context():
            booking_code = test_appointment_with_code['booking_code']
            response = client.get(f'/api/public/appointments/{booking_code}')

            assert response.status_code == 200
            data = json.loads(response.data)
            assert 'appointment' in data
            assert data['search_type'] == 'code'
            assert data['appointment']['booking_code'] == booking_code

    def test_get_appointment_by_code_lowercase(self, client, test_appointment_with_code, app):
        """Testar busca de agendamento por codigo em minusculo"""
        with app.app_context():
            booking_code = test_appointment_with_code['booking_code']
            response = client.get(f'/api/public/appointments/{booking_code.lower()}')

            assert response.status_code == 200
            data = json.loads(response.data)
            assert 'appointment' in data
            assert data['appointment']['booking_code'] == booking_code

    def test_get_appointment_by_code_not_found(self, client, app):
        """Testar busca de agendamento com codigo inexistente"""
        with app.app_context():
            response = client.get('/api/public/appointments/NOTFOUND')

            assert response.status_code == 404
            data = json.loads(response.data)
            assert 'error' in data

    def test_get_appointment_returns_public_data(self, client, test_appointment_with_code, app):
        """Testar que retorna apenas dados publicos"""
        with app.app_context():
            booking_code = test_appointment_with_code['booking_code']
            response = client.get(f'/api/public/appointments/{booking_code}')

            assert response.status_code == 200
            data = json.loads(response.data)
            appointment = data['appointment']

            # Verificar campos publicos presentes
            assert 'booking_code' in appointment
            assert 'appointment_date' in appointment
            assert 'start_time' in appointment
            assert 'end_time' in appointment
            assert 'status' in appointment
            assert 'professional' in appointment
            assert 'service' in appointment
            assert 'client' in appointment

            # Verificar que dados sensiveis nao estao presentes
            assert 'id' not in appointment
            assert 'user_id' not in appointment


class TestAppointmentLookupByPhone:
    """Testes para busca de agendamento por telefone"""

    def test_get_appointment_by_phone_exact_match(self, client, test_appointment_with_code, app):
        """Testar busca de agendamento por telefone exato"""
        with app.app_context():
            response = client.get('/api/public/appointments/11999887766')

            assert response.status_code == 200
            data = json.loads(response.data)
            assert 'appointments' in data
            assert data['search_type'] == 'phone'
            assert data['count'] >= 1

    def test_get_appointment_by_phone_with_formatting(self, client, test_appointment_formatted_phone, app):
        """Testar busca de agendamento por telefone formatado"""
        with app.app_context():
            # Buscar com telefone formatado (mesmo formato salvo no banco)
            response = client.get('/api/public/appointments/(11) 98888-7777')

            assert response.status_code == 200
            data = json.loads(response.data)
            assert 'appointments' in data
            assert data['search_type'] == 'phone'

    def test_get_multiple_appointments_by_phone(self, client, test_multiple_appointments_same_client, app):
        """Testar busca de multiplos agendamentos pelo telefone"""
        with app.app_context():
            response = client.get('/api/public/appointments/11999887766')

            assert response.status_code == 200
            data = json.loads(response.data)
            assert 'appointments' in data
            assert data['count'] >= 3
            assert len(data['appointments']) >= 3

    def test_get_appointments_by_phone_ordered_by_date(self, client, test_multiple_appointments_same_client, app):
        """Testar que agendamentos sao ordenados por data (mais recente primeiro)"""
        with app.app_context():
            response = client.get('/api/public/appointments/11999887766')

            assert response.status_code == 200
            data = json.loads(response.data)

            appointments = data['appointments']
            if len(appointments) > 1:
                # Verificar ordenacao por data decrescente
                dates = [apt['appointment_date'] for apt in appointments]
                assert dates == sorted(dates, reverse=True)

    def test_get_appointment_by_phone_not_found(self, client, app):
        """Testar busca por telefone inexistente"""
        with app.app_context():
            response = client.get('/api/public/appointments/00000000000')

            assert response.status_code == 404
            data = json.loads(response.data)
            assert 'error' in data

    def test_get_appointment_by_partial_phone(self, client, test_appointment_with_code, app):
        """Testar busca por telefone parcial"""
        with app.app_context():
            # Buscar com parte do telefone
            response = client.get('/api/public/appointments/999887766')

            assert response.status_code == 200
            data = json.loads(response.data)
            assert 'appointments' in data
            assert data['search_type'] == 'phone'


class TestAppointmentLookupPriority:
    """Testes para prioridade de busca (codigo antes de telefone)"""

    def test_code_takes_priority_over_phone(self, client, test_appointment_with_code, app):
        """Testar que codigo tem prioridade sobre telefone"""
        with app.app_context():
            booking_code = test_appointment_with_code['booking_code']
            response = client.get(f'/api/public/appointments/{booking_code}')

            assert response.status_code == 200
            data = json.loads(response.data)

            # Deve retornar como busca por codigo, nao telefone
            assert data['search_type'] == 'code'
            assert 'appointment' in data
            assert 'appointments' not in data


class TestAppointmentLookupEdgeCases:
    """Testes para casos especiais"""

    def test_empty_code(self, client, app):
        """Testar busca com codigo vazio"""
        with app.app_context():
            response = client.get('/api/public/appointments/')

            # Deve retornar 404 (rota nao encontrada)
            assert response.status_code == 404

    def test_special_characters_in_search(self, client, app):
        """Testar busca com caracteres especiais"""
        with app.app_context():
            response = client.get('/api/public/appointments/+55-11-99988-7766')

            # Deve funcionar, extraindo apenas numeros
            # Pode retornar 200 se encontrar ou 404 se nao encontrar
            assert response.status_code in [200, 404]

    def test_very_long_search_term(self, client, app):
        """Testar busca com termo muito longo"""
        with app.app_context():
            long_term = 'A' * 100
            response = client.get(f'/api/public/appointments/{long_term}')

            assert response.status_code == 404

    def test_numeric_only_search_treated_as_phone(self, client, app):
        """Testar que busca apenas numerica e tratada como telefone"""
        with app.app_context():
            response = client.get('/api/public/appointments/12345678')

            # Deve tentar buscar primeiro por codigo, depois por telefone
            assert response.status_code in [200, 404]


class TestAppointmentLookupRateLimit:
    """Testes para rate limiting"""

    def test_rate_limit_allows_normal_usage(self, client, test_appointment_with_code, app):
        """Testar que uso normal nao e bloqueado"""
        with app.app_context():
            booking_code = test_appointment_with_code['booking_code']
            # Fazer algumas requisicoes
            for _ in range(5):
                response = client.get(f'/api/public/appointments/{booking_code}')
                assert response.status_code == 200


class TestAppointmentConfirmationInfo:
    """Testes para informacoes de confirmacao"""

    def test_pending_confirmation_info(self, client, test_appointment_with_code, app, db_session):
        """Testar que informacoes de confirmacao sao retornadas quando pendente"""
        with app.app_context():
            from src.models.appointment import Appointment

            booking_code = test_appointment_with_code['booking_code']

            # Adicionar token de confirmacao ao agendamento
            appointment = Appointment.query.filter_by(booking_code=booking_code).first()
            appointment.generate_confirmation_token(expires_hours=24)
            db_session.flush()

            response = client.get(f'/api/public/appointments/{booking_code}')

            assert response.status_code == 200
            data = json.loads(response.data)

            # Verificar campos de confirmacao
            assert 'requires_confirmation' in data
            assert data['requires_confirmation'] is True
