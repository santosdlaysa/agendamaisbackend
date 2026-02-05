"""
Configuração de testes para o sistema AgendaMais
Testes usam transações com rollback automático - nenhum dado é persistido no banco
"""
import pytest
import os
from datetime import datetime, timedelta, date, time
from unittest.mock import MagicMock, patch
from app import create_app
from src.config.database import db
from src.models.user import User
from src.models.client import Client
from src.models.subscription import Subscription
from src.models.professional import Professional
from src.models.service import Service
from src.models.appointment import Appointment, generate_booking_code
from flask_jwt_extended import create_access_token


@pytest.fixture(scope='function')
def app():
    """Criar aplicação Flask para testes com banco isolado por teste"""
    os.environ['FLASK_ENV'] = 'testing'
    os.environ['DATABASE_URL'] = 'sqlite:///:memory:'
    os.environ['STRIPE_SECRET_KEY'] = 'sk_test_mock_key'
    os.environ['STRIPE_WEBHOOK_SECRET'] = 'whsec_test_mock_secret'

    app = create_app()
    app.config.update({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'SQLALCHEMY_TRACK_MODIFICATIONS': False,
        'JWT_SECRET_KEY': 'test-jwt-secret'
    })

    with app.app_context():
        db.create_all()
        yield app
        db.session.rollback()
        db.drop_all()


@pytest.fixture(scope='function')
def client(app):
    """Cliente de teste Flask"""
    return app.test_client()


@pytest.fixture(scope='function')
def runner(app):
    """CLI runner para testes"""
    return app.test_cli_runner()


@pytest.fixture(scope='function')
def db_session(app):
    """Sessão de banco de dados para testes - rollback automático ao final"""
    with app.app_context():
        yield db.session
        db.session.rollback()


@pytest.fixture
def test_user(app, db_session):
    """Criar usuário de teste - usa flush ao invés de commit"""
    user = User(
        name='Test User',
        email='test@example.com',
        password_hash='hashed_password',
        role='admin'
    )
    db_session.add(user)
    db_session.flush()
    return user


@pytest.fixture
def test_client_user(app, db_session):
    """Criar cliente de teste - usa flush ao invés de commit"""
    client_user = Client(
        name='Test Client',
        email='client@example.com',
        phone='+5511999999999'
    )
    db_session.add(client_user)
    db_session.flush()
    return client_user


@pytest.fixture
def test_subscription(app, db_session, test_user):
    """Criar assinatura de teste - usa flush ao invés de commit"""
    subscription = Subscription(
        user_id=test_user.id,
        plan='pro',
        stripe_customer_id='cus_test123',
        stripe_subscription_id='sub_test123',
        status='active',
        start_date=datetime.utcnow(),
        trial_end=datetime.utcnow() + timedelta(days=7)
    )
    db_session.add(subscription)
    db_session.flush()
    return subscription


@pytest.fixture
def test_subscription_basic(app, db_session, test_user):
    """Criar assinatura básica de teste - usa flush ao invés de commit"""
    subscription = Subscription(
        user_id=test_user.id,
        plan='basic',
        stripe_customer_id='cus_test456',
        stripe_subscription_id='sub_test456',
        status='active'
    )
    db_session.add(subscription)
    db_session.flush()
    return subscription


@pytest.fixture
def test_subscription_trialing(app, db_session, test_user):
    """Criar assinatura em trial de teste - usa flush ao invés de commit"""
    subscription = Subscription(
        user_id=test_user.id,
        plan='pro',
        stripe_customer_id='cus_test789',
        stripe_subscription_id='sub_test789',
        status='trialing',
        trial_end=datetime.utcnow() + timedelta(days=5)
    )
    db_session.add(subscription)
    db_session.flush()
    return subscription


@pytest.fixture
def test_subscription_canceled(app, db_session, test_user):
    """Criar assinatura cancelada de teste - usa flush ao invés de commit"""
    subscription = Subscription(
        user_id=test_user.id,
        plan='basic',
        stripe_customer_id='cus_test999',
        stripe_subscription_id='sub_test999',
        status='canceled',
        end_date=datetime.utcnow()
    )
    db_session.add(subscription)
    db_session.flush()
    return subscription


@pytest.fixture
def auth_token(app, db_session, test_user):
    """Token JWT de autenticação para testes"""
    token = create_access_token(identity=test_user.id)
    return token


@pytest.fixture
def auth_headers(auth_token):
    """Headers com token de autenticação"""
    return {
        'Authorization': f'Bearer {auth_token}',
        'Content-Type': 'application/json'
    }


@pytest.fixture
def test_professional(app, db_session):
    """Criar profissional de teste - usa flush ao invés de commit"""
    professional = Professional(
        name='Test Professional',
        role='Cabeleireiro',
        email='professional@example.com',
        phone='+5511988888888',
        color='#3B82F6'
    )
    db_session.add(professional)
    db_session.flush()
    return professional


@pytest.fixture
def test_service(app, db_session):
    """Criar serviço de teste - usa flush ao invés de commit"""
    service = Service(
        name='Test Service',
        description='Test service description',
        price=50.00,
        duration=60,
        color='#10B981'
    )
    db_session.add(service)
    db_session.flush()
    return service


@pytest.fixture
def mock_stripe_customer():
    """Mock de customer do Stripe"""
    return {
        'id': 'cus_mock123',
        'email': 'client@example.com',
        'name': 'Test Client',
        'metadata': {'client_id': '1'}
    }


@pytest.fixture
def mock_stripe_subscription():
    """Mock de subscription do Stripe"""
    return {
        'id': 'sub_mock123',
        'customer': 'cus_mock123',
        'status': 'active',
        'items': {
            'data': [
                {'price': {'id': 'price_mock123'}}
            ]
        },
        'trial_end': None,
        'cancel_at_period_end': False,
        'latest_invoice': {
            'payment_intent': {
                'client_secret': 'pi_mock_secret_123'
            }
        }
    }


@pytest.fixture
def mock_stripe_webhook_event():
    """Mock de evento webhook do Stripe"""
    def _create_event(event_type, data_object):
        return {
            'type': event_type,
            'data': {
                'object': data_object
            }
        }
    return _create_event


@pytest.fixture
def test_appointment_with_code(app, db_session):
    """Criar agendamento de teste com codigo e todas as dependencias - usa flush"""
    import uuid
    unique_id = uuid.uuid4().hex[:8]
    booking_code = f'ABC{unique_id[:5].upper()}'

    # Criar usuario
    user = User(
        name='Business Owner',
        email=f'business_{unique_id}@example.com',
        password_hash='hashed_password',
        role='admin'
    )
    db_session.add(user)
    db_session.flush()

    # Criar cliente
    client = Client(
        name='Cliente Teste',
        email=f'cliente_{unique_id}@example.com',
        phone='11999887766',
        user_id=user.id
    )
    db_session.add(client)
    db_session.flush()

    # Criar profissional
    professional = Professional(
        name='Profissional Teste',
        role='Cabeleireiro',
        email=f'prof_{unique_id}@example.com',
        phone='11977776666',
        color='#3B82F6',
        user_id=user.id
    )
    db_session.add(professional)
    db_session.flush()

    # Criar servico
    service = Service(
        name='Corte de Cabelo',
        description='Corte masculino',
        price=50.00,
        duration=30,
        color='#10B981',
        user_id=user.id
    )
    db_session.add(service)
    db_session.flush()

    # Criar agendamento
    appointment = Appointment(
        client_id=client.id,
        professional_id=professional.id,
        service_id=service.id,
        appointment_date=date.today() + timedelta(days=1),
        start_time=time(10, 0),
        end_time=time(10, 30),
        status='scheduled',
        booking_code=booking_code,
        source='online',
        user_id=user.id
    )
    db_session.add(appointment)
    db_session.flush()

    return {
        'appointment': appointment,
        'client': client,
        'professional': professional,
        'service': service,
        'user': user,
        'booking_code': booking_code
    }


@pytest.fixture
def test_multiple_appointments_same_client(app, db_session):
    """Criar multiplos agendamentos para o mesmo cliente - usa flush"""
    import uuid
    unique_id = uuid.uuid4().hex[:8]

    # Criar usuario
    user = User(
        name='Business Owner Multi',
        email=f'business_multi_{unique_id}@example.com',
        password_hash='hashed_password',
        role='admin'
    )
    db_session.add(user)
    db_session.flush()

    # Criar cliente
    client = Client(
        name='Cliente Multi',
        email=f'cliente_multi_{unique_id}@example.com',
        phone='11999887766',
        user_id=user.id
    )
    db_session.add(client)
    db_session.flush()

    # Criar profissional
    professional = Professional(
        name='Profissional Multi',
        role='Cabeleireiro',
        email=f'prof_multi_{unique_id}@example.com',
        phone='11977776666',
        color='#3B82F6',
        user_id=user.id
    )
    db_session.add(professional)
    db_session.flush()

    # Criar servico
    service = Service(
        name='Corte de Cabelo',
        description='Corte masculino',
        price=50.00,
        duration=30,
        color='#10B981',
        user_id=user.id
    )
    db_session.add(service)
    db_session.flush()

    # Criar multiplos agendamentos
    appointments = []
    for i in range(3):
        appointment = Appointment(
            client_id=client.id,
            professional_id=professional.id,
            service_id=service.id,
            appointment_date=date.today() + timedelta(days=i+3),
            start_time=time(9 + i, 0),
            end_time=time(9 + i, 30),
            status='scheduled',
            booking_code=f'MLT{unique_id[:4]}{i}',
            source='online',
            user_id=user.id
        )
        db_session.add(appointment)
        appointments.append(appointment)

    db_session.flush()
    return appointments


@pytest.fixture
def test_appointment_formatted_phone(app, db_session):
    """Criar agendamento de teste com cliente que tem telefone formatado - usa flush"""
    import uuid
    unique_id = uuid.uuid4().hex[:8]

    # Criar usuario
    user = User(
        name='Business Owner Fmt',
        email=f'business_fmt_{unique_id}@example.com',
        password_hash='hashed_password',
        role='admin'
    )
    db_session.add(user)
    db_session.flush()

    # Criar cliente com telefone formatado
    client = Client(
        name='Cliente Formatado',
        email=f'cliente_fmt_{unique_id}@example.com',
        phone='(11) 98888-7777',
        user_id=user.id
    )
    db_session.add(client)
    db_session.flush()

    # Criar profissional
    professional = Professional(
        name='Profissional Fmt',
        role='Cabeleireiro',
        email=f'prof_fmt_{unique_id}@example.com',
        phone='11977776666',
        color='#3B82F6',
        user_id=user.id
    )
    db_session.add(professional)
    db_session.flush()

    # Criar servico
    service = Service(
        name='Corte de Cabelo',
        description='Corte masculino',
        price=50.00,
        duration=30,
        color='#10B981',
        user_id=user.id
    )
    db_session.add(service)
    db_session.flush()

    # Criar agendamento
    appointment = Appointment(
        client_id=client.id,
        professional_id=professional.id,
        service_id=service.id,
        appointment_date=date.today() + timedelta(days=5),
        start_time=time(16, 0),
        end_time=time(16, 30),
        status='scheduled',
        booking_code=f'FMT{unique_id[:5]}',
        source='online',
        user_id=user.id
    )
    db_session.add(appointment)
    db_session.flush()

    return {
        'appointment': appointment,
        'client': client
    }
