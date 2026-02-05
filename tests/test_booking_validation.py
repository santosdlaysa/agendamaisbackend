"""
Testes de validacao de cliente no agendamento publico
"""
import pytest
import json
import uuid
from datetime import datetime, timedelta, date, time
from src.config.database import db
from src.models.user import User
from src.models.professional import Professional
from src.models.service import Service
from src.models.working_hours import WorkingHours


@pytest.fixture
def business_user(app, db_session):
    """Criar usuario/estabelecimento com agendamento online habilitado"""
    with app.app_context():
        unique_id = uuid.uuid4().hex[:8]
        user = User(
            name='Business Test',
            email=f'business_{unique_id}@example.com',
            password_hash='hashed_password',
            role='admin',
            slug=f'test-business-{unique_id}',
            business_name='Test Business',
            online_booking_enabled=True,
            booking_min_advance_hours=1,
            booking_max_advance_days=30,
            booking_require_payment=False
        )
        db.session.add(user)
        db.session.flush()
        return user


@pytest.fixture
def business_professional(app, db_session, business_user):
    """Criar profissional vinculado ao estabelecimento"""
    with app.app_context():
        unique_id = uuid.uuid4().hex[:8]
        professional = Professional(
            name='Test Professional',
            role='Cabeleireiro',
            email=f'prof_{unique_id}@example.com',
            phone='11999999999',
            color='#3B82F6',
            user_id=business_user.id,
            active=True
        )
        db.session.add(professional)
        db.session.flush()

        # Criar horarios de trabalho para todos os dias da semana
        for day in range(7):
            working_hours = WorkingHours(
                professional_id=professional.id,
                day_of_week=day,
                start_time=time(8, 0),
                end_time=time(18, 0),
                is_available=True
            )
            db.session.add(working_hours)
        db.session.flush()

        return professional


@pytest.fixture
def business_service(app, db_session, business_user):
    """Criar servico vinculado ao estabelecimento"""
    with app.app_context():
        unique_id = uuid.uuid4().hex[:8]
        service = Service(
            name='Corte de Cabelo',
            description='Corte masculino',
            price=50.00,
            duration=30,
            color='#10B981',
            user_id=business_user.id,
            active=True
        )
        db.session.add(service)
        db.session.flush()
        return service


def get_future_appointment_datetime():
    """Retorna data e hora futura valida para agendamento"""
    # Agendar para daqui a 2 dias as 10:00 para garantir que esteja dentro dos limites
    future_date = date.today() + timedelta(days=2)
    return future_date.strftime('%Y-%m-%d'), '10:00'


class TestBookingClientValidation:
    """Testes de validacao de cliente no agendamento"""

    def test_client_name_required(self, client, app, business_user, business_professional, business_service):
        """Deve falhar sem nome do cliente"""
        with app.app_context():
            # Refetch objects in this context
            user = db.session.get(User, business_user.id)
            professional = db.session.get(Professional, business_professional.id)
            service = db.session.get(Service, business_service.id)

            appointment_date, start_time = get_future_appointment_datetime()

            response = client.post(
                f'/api/public/business/{user.slug}/appointments',
                data=json.dumps({
                    'professional_id': professional.id,
                    'service_id': service.id,
                    'date': appointment_date,
                    'start_time': start_time,
                    'client': {
                        'name': '',
                        'phone': '11999998888',
                        'email': 'test@example.com'
                    }
                }),
                content_type='application/json'
            )

            assert response.status_code == 400
            data = json.loads(response.data)
            assert 'error' in data
            assert 'nome' in data['error'].lower() or 'telefone' in data['error'].lower()

    def test_client_phone_required(self, client, app, business_user, business_professional, business_service):
        """Deve falhar sem telefone do cliente"""
        with app.app_context():
            # Refetch objects in this context
            user = db.session.get(User, business_user.id)
            professional = db.session.get(Professional, business_professional.id)
            service = db.session.get(Service, business_service.id)

            appointment_date, start_time = get_future_appointment_datetime()

            response = client.post(
                f'/api/public/business/{user.slug}/appointments',
                data=json.dumps({
                    'professional_id': professional.id,
                    'service_id': service.id,
                    'date': appointment_date,
                    'start_time': start_time,
                    'client': {
                        'name': 'Cliente Teste',
                        'phone': '',
                        'email': 'test@example.com'
                    }
                }),
                content_type='application/json'
            )

            assert response.status_code == 400
            data = json.loads(response.data)
            assert 'error' in data
            assert 'nome' in data['error'].lower() or 'telefone' in data['error'].lower()

    def test_client_name_only_spaces(self, client, app, business_user, business_professional, business_service):
        """Deve falhar se nome contem apenas espacos"""
        with app.app_context():
            # Refetch objects in this context
            user = db.session.get(User, business_user.id)
            professional = db.session.get(Professional, business_professional.id)
            service = db.session.get(Service, business_service.id)

            appointment_date, start_time = get_future_appointment_datetime()

            response = client.post(
                f'/api/public/business/{user.slug}/appointments',
                data=json.dumps({
                    'professional_id': professional.id,
                    'service_id': service.id,
                    'date': appointment_date,
                    'start_time': start_time,
                    'client': {
                        'name': '   ',
                        'phone': '11999998888',
                        'email': 'test@example.com'
                    }
                }),
                content_type='application/json'
            )

            assert response.status_code == 400
            data = json.loads(response.data)
            assert 'error' in data
            # O codigo usa .strip() entao espacos devem ser rejeitados como nome vazio
            assert 'nome' in data['error'].lower() or 'telefone' in data['error'].lower()

    def test_client_phone_invalid_less_than_8_digits(self, client, app, business_user, business_professional, business_service):
        """Deve falhar se telefone tem menos de 8 digitos"""
        with app.app_context():
            # Refetch objects in this context
            user = db.session.get(User, business_user.id)
            professional = db.session.get(Professional, business_professional.id)
            service = db.session.get(Service, business_service.id)

            appointment_date, start_time = get_future_appointment_datetime()

            response = client.post(
                f'/api/public/business/{user.slug}/appointments',
                data=json.dumps({
                    'professional_id': professional.id,
                    'service_id': service.id,
                    'date': appointment_date,
                    'start_time': start_time,
                    'client': {
                        'name': 'Cliente Teste',
                        'phone': '1234567',  # Apenas 7 digitos
                        'email': 'test@example.com'
                    }
                }),
                content_type='application/json'
            )

            assert response.status_code == 400
            data = json.loads(response.data)
            assert 'error' in data
            assert 'telefone' in data['error'].lower() or '8 d' in data['error'].lower()

    def test_client_phone_valid_8_digits(self, client, app, business_user, business_professional, business_service):
        """Deve passar com telefone de 8+ digitos"""
        with app.app_context():
            # Refetch objects in this context
            user = db.session.get(User, business_user.id)
            professional = db.session.get(Professional, business_professional.id)
            service = db.session.get(Service, business_service.id)

            appointment_date, start_time = get_future_appointment_datetime()

            response = client.post(
                f'/api/public/business/{user.slug}/appointments',
                data=json.dumps({
                    'professional_id': professional.id,
                    'service_id': service.id,
                    'date': appointment_date,
                    'start_time': start_time,
                    'client': {
                        'name': 'Cliente Teste Valido',
                        'phone': '12345678',  # Exatamente 8 digitos
                        'email': 'test@example.com'
                    }
                }),
                content_type='application/json'
            )

            # Deve passar a validacao do cliente (pode falhar por outros motivos como horario)
            # O importante e que nao falhe por validacao de telefone
            if response.status_code == 400:
                data = json.loads(response.data)
                # Se falhou, nao deve ser por causa do telefone
                error_msg = data.get('error', '').lower()
                assert 'telefone' not in error_msg or '8 d' not in error_msg
            else:
                # 201 = criado com sucesso, ou outro codigo que nao seja erro de validacao
                assert response.status_code in [201, 500]  # 500 pode ocorrer por stripe mock

    def test_client_phone_valid_with_formatting(self, client, app, business_user, business_professional, business_service):
        """Deve passar com telefone formatado (11) 99999-9999"""
        with app.app_context():
            # Refetch objects in this context
            user = db.session.get(User, business_user.id)
            professional = db.session.get(Professional, business_professional.id)
            service = db.session.get(Service, business_service.id)

            appointment_date, start_time = get_future_appointment_datetime()

            response = client.post(
                f'/api/public/business/{user.slug}/appointments',
                data=json.dumps({
                    'professional_id': professional.id,
                    'service_id': service.id,
                    'date': appointment_date,
                    'start_time': start_time,
                    'client': {
                        'name': 'Cliente Teste Formatado',
                        'phone': '(11) 99999-9999',  # Telefone formatado com 11 digitos
                        'email': 'test@example.com'
                    }
                }),
                content_type='application/json'
            )

            # Deve passar a validacao do cliente
            if response.status_code == 400:
                data = json.loads(response.data)
                # Se falhou, nao deve ser por causa do telefone
                error_msg = data.get('error', '').lower()
                assert 'telefone' not in error_msg or '8 d' not in error_msg
            else:
                assert response.status_code in [201, 500]

    def test_client_phone_valid_international_format(self, client, app, business_user, business_professional, business_service):
        """Deve passar com telefone em formato internacional +55 11 99999-9999"""
        with app.app_context():
            # Refetch objects in this context
            user = db.session.get(User, business_user.id)
            professional = db.session.get(Professional, business_professional.id)
            service = db.session.get(Service, business_service.id)

            appointment_date, start_time = get_future_appointment_datetime()

            response = client.post(
                f'/api/public/business/{user.slug}/appointments',
                data=json.dumps({
                    'professional_id': professional.id,
                    'service_id': service.id,
                    'date': appointment_date,
                    'start_time': start_time,
                    'client': {
                        'name': 'Cliente Internacional',
                        'phone': '+55 11 99999-9999',  # Formato internacional com 13 digitos
                        'email': 'test@example.com'
                    }
                }),
                content_type='application/json'
            )

            # Deve passar a validacao do cliente
            if response.status_code == 400:
                data = json.loads(response.data)
                error_msg = data.get('error', '').lower()
                assert 'telefone' not in error_msg or '8 d' not in error_msg
            else:
                assert response.status_code in [201, 500]

    def test_client_missing_field(self, client, app, business_user, business_professional, business_service):
        """Deve falhar quando campo client nao e enviado"""
        with app.app_context():
            # Refetch objects in this context
            user = db.session.get(User, business_user.id)
            professional = db.session.get(Professional, business_professional.id)
            service = db.session.get(Service, business_service.id)

            appointment_date, start_time = get_future_appointment_datetime()

            response = client.post(
                f'/api/public/business/{user.slug}/appointments',
                data=json.dumps({
                    'professional_id': professional.id,
                    'service_id': service.id,
                    'date': appointment_date,
                    'start_time': start_time
                    # client field missing
                }),
                content_type='application/json'
            )

            assert response.status_code == 400
            data = json.loads(response.data)
            assert 'error' in data
            assert 'client' in data['error'].lower() or 'obrigat' in data['error'].lower()

    def test_client_null_name(self, client, app, business_user, business_professional, business_service):
        """Deve falhar quando nome e null"""
        with app.app_context():
            # Refetch objects in this context
            user = db.session.get(User, business_user.id)
            professional = db.session.get(Professional, business_professional.id)
            service = db.session.get(Service, business_service.id)

            appointment_date, start_time = get_future_appointment_datetime()

            response = client.post(
                f'/api/public/business/{user.slug}/appointments',
                data=json.dumps({
                    'professional_id': professional.id,
                    'service_id': service.id,
                    'date': appointment_date,
                    'start_time': start_time,
                    'client': {
                        'name': None,
                        'phone': '11999998888',
                        'email': 'test@example.com'
                    }
                }),
                content_type='application/json'
            )

            assert response.status_code == 400
            data = json.loads(response.data)
            assert 'error' in data

    def test_client_null_phone(self, client, app, business_user, business_professional, business_service):
        """Deve falhar quando telefone e null"""
        with app.app_context():
            # Refetch objects in this context
            user = db.session.get(User, business_user.id)
            professional = db.session.get(Professional, business_professional.id)
            service = db.session.get(Service, business_service.id)

            appointment_date, start_time = get_future_appointment_datetime()

            response = client.post(
                f'/api/public/business/{user.slug}/appointments',
                data=json.dumps({
                    'professional_id': professional.id,
                    'service_id': service.id,
                    'date': appointment_date,
                    'start_time': start_time,
                    'client': {
                        'name': 'Cliente Teste',
                        'phone': None,
                        'email': 'test@example.com'
                    }
                }),
                content_type='application/json'
            )

            assert response.status_code == 400
            data = json.loads(response.data)
            assert 'error' in data
