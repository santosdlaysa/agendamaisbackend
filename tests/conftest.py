"""
Configuração de testes para o sistema AgendaMais
"""
import pytest
import os
from datetime import datetime, timedelta
from app import create_app
from src.config.database import db
from src.models.user import User
from src.models.client import Client
from src.models.subscription import Subscription
from src.models.professional import Professional
from src.models.service import Service
from flask_jwt_extended import create_access_token


@pytest.fixture(scope='session')
def app():
    """Criar aplicação Flask para testes"""
    # Configurar variáveis de ambiente para testes
    os.environ['FLASK_ENV'] = 'testing'
    os.environ['DATABASE_URL'] = 'sqlite:///:memory:'
    os.environ['STRIPE_SECRET_KEY'] = 'sk_test_mock_key'
    os.environ['STRIPE_WEBHOOK_SECRET'] = 'whsec_test_mock_secret'

    app = create_app()
    app.config.update({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'JWT_SECRET_KEY': 'test-jwt-secret'
    })

    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
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
    """Sessão de banco de dados para testes"""
    with app.app_context():
        yield db.session
        db.session.rollback()


@pytest.fixture
def test_user(app, db_session):
    """Criar usuário de teste"""
    with app.app_context():
        user = User(
            name='Test User',
            email='test@example.com',
            password_hash='hashed_password',
            role='admin'
        )
        db.session.add(user)
        db.session.commit()
        return user


@pytest.fixture
def test_client_user(app, db_session):
    """Criar cliente de teste"""
    with app.app_context():
        client_user = Client(
            name='Test Client',
            email='client@example.com',
            phone='+5511999999999'
        )
        db.session.add(client_user)
        db.session.commit()
        return client_user


@pytest.fixture
def test_subscription(app, db_session, test_client_user):
    """Criar assinatura de teste"""
    with app.app_context():
        subscription = Subscription(
            client_id=test_client_user.id,
            plan='pro',
            stripe_customer_id='cus_test123',
            stripe_subscription_id='sub_test123',
            status='active',
            start_date=datetime.utcnow(),
            trial_end=datetime.utcnow() + timedelta(days=7)
        )
        db.session.add(subscription)
        db.session.commit()
        return subscription


@pytest.fixture
def test_subscription_basic(app, db_session, test_client_user):
    """Criar assinatura básica de teste"""
    with app.app_context():
        subscription = Subscription(
            client_id=test_client_user.id,
            plan='basic',
            stripe_customer_id='cus_test456',
            stripe_subscription_id='sub_test456',
            status='active'
        )
        db.session.add(subscription)
        db.session.commit()
        return subscription


@pytest.fixture
def test_subscription_trialing(app, db_session, test_client_user):
    """Criar assinatura em trial de teste"""
    with app.app_context():
        subscription = Subscription(
            client_id=test_client_user.id,
            plan='pro',
            stripe_customer_id='cus_test789',
            stripe_subscription_id='sub_test789',
            status='trialing',
            trial_end=datetime.utcnow() + timedelta(days=5)
        )
        db.session.add(subscription)
        db.session.commit()
        return subscription


@pytest.fixture
def test_subscription_canceled(app, db_session, test_client_user):
    """Criar assinatura cancelada de teste"""
    with app.app_context():
        subscription = Subscription(
            client_id=test_client_user.id,
            plan='basic',
            stripe_customer_id='cus_test999',
            stripe_subscription_id='sub_test999',
            status='canceled',
            end_date=datetime.utcnow()
        )
        db.session.add(subscription)
        db.session.commit()
        return subscription


@pytest.fixture
def auth_token(app, test_client_user):
    """Token JWT de autenticação para testes"""
    with app.app_context():
        token = create_access_token(identity=test_client_user.id)
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
    """Criar profissional de teste"""
    with app.app_context():
        professional = Professional(
            name='Test Professional',
            role='Cabeleireiro',
            email='professional@example.com',
            phone='+5511988888888',
            color='#3B82F6'
        )
        db.session.add(professional)
        db.session.commit()
        return professional


@pytest.fixture
def test_service(app, db_session):
    """Criar serviço de teste"""
    with app.app_context():
        service = Service(
            name='Test Service',
            description='Test service description',
            price=50.00,
            duration=60,
            color='#10B981'
        )
        db.session.add(service)
        db.session.commit()
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
