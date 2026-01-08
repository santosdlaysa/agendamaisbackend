from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flasgger import Swagger
from src.config.database import db, init_db
from src.services.email_service import mail
import src.models
from src.app.auth.auth import auth_bp
from src.app.main.client.clients import clients_bp
from src.app.main.professional.professionals import professionals_bp
from src.app.main.service.services import services_bp
from src.app.main.appointment.appointments import appointments_bp
from src.app.main.subscription.subscriptions import subscriptions_bp
from src.app.main.public.booking import public_bp
# Import reminder blueprint conditionally
try:
    from src.app.main.reminder.reminders import reminders_bp
    REMINDERS_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Reminder functionality not available: {e}")
    reminders_bp = None
    REMINDERS_AVAILABLE = False
import os
from dotenv import load_dotenv

load_dotenv()

def create_app():
    app = Flask(__name__)
    
    # Configurações
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key')

    # Handle database URL - convert postgres:// to postgresql+psycopg:// for psycopg3
    database_url = os.getenv('DATABASE_URL', 'sqlite:///agendamento.db')
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql+psycopg://', 1)
    elif database_url.startswith('postgresql://'):
        database_url = database_url.replace('postgresql://', 'postgresql+psycopg://', 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'jwt-secret-string')

    # Configuração Flask-Mail (Gmail SMTP)
    app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
    app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT', 587))
    app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS', 'True').lower() == 'true'
    app.config['MAIL_USE_SSL'] = os.getenv('MAIL_USE_SSL', 'False').lower() == 'true'
    app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
    app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
    app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_DEFAULT_SENDER', os.getenv('MAIL_USERNAME'))

    # URL base do frontend para links de verificação
    app.config['FRONTEND_URL'] = os.getenv('FRONTEND_URL', 'http://localhost:3000')

    # Configuração CORS
    allowed_origins = [
        'http://localhost:3000',
        'http://localhost:5173',
        'http://172.29.16.1:3001',
        'http://192.168.100.136:3000',
        'http://192.168.100.136:5173',
        'https://agendamais-x19j-32f6fx9yd-santosdlaysas-projects.vercel.app',
        'https://agendamais-x19j.vercel.app',
        'https://agendamais.site',
        os.getenv('FRONTEND_URL')
    ]

    # Remove valores None/vazios
    allowed_origins = [origin for origin in allowed_origins if origin]

    # Em desenvolvimento, permite todas as origens
    if os.getenv('FLASK_ENV') == 'development':
        CORS(app,
             origins='*',
             methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS', 'PATCH'],
             allow_headers=['Content-Type', 'Authorization'],
             supports_credentials=True)
    else:
        CORS(app,
             origins=allowed_origins,
             methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS', 'PATCH'],
             allow_headers=['Content-Type', 'Authorization'],
             supports_credentials=True)

    JWTManager(app)
    db.init_app(app)
    mail.init_app(app)

    # Configuração do Swagger
    swagger_config = {
        "headers": [],
        "specs": [
            {
                "endpoint": 'apispec',
                "route": '/apispec.json',
                "rule_filter": lambda rule: True,
                "model_filter": lambda tag: True,
            }
        ],
        "static_url_path": "/flasgger_static",
        "swagger_ui": True,
        "specs_route": "/docs"
    }

    swagger_template = {
        "swagger": "2.0",
        "info": {
            "title": "Agenda+ API",
            "description": "API para sistema de agendamentos de serviços",
            "version": "1.0.0",
            "contact": {
                "name": "Suporte Agenda+",
                "email": "suporte@agendamais.com"
            }
        },
        "host": "localhost:5000",
        "basePath": "/api",
        "schemes": ["http", "https"],
        "securityDefinitions": {
            "Bearer": {
                "type": "apiKey",
                "name": "Authorization",
                "in": "header",
                "description": "JWT Authorization header usando o esquema Bearer. Exemplo: 'Bearer {token}'"
            }
        },
        "tags": [
            {"name": "Autenticação", "description": "Endpoints de autenticação de usuários"},
            {"name": "Clientes", "description": "Gerenciamento de clientes"},
            {"name": "Profissionais", "description": "Gerenciamento de profissionais"},
            {"name": "Serviços", "description": "Gerenciamento de serviços"},
            {"name": "Agendamentos", "description": "Gerenciamento de agendamentos"},
            {"name": "Assinaturas", "description": "Gerenciamento de assinaturas SaaS"}
        ],
        "definitions": {
            "User": {
                "type": "object",
                "properties": {
                    "id": {"type": "integer"},
                    "email": {"type": "string"},
                    "name": {"type": "string"},
                    "role": {"type": "string"}
                }
            },
            "Client": {
                "type": "object",
                "properties": {
                    "id": {"type": "integer"},
                    "name": {"type": "string"},
                    "phone": {"type": "string"},
                    "email": {"type": "string"},
                    "notes": {"type": "string"}
                }
            },
            "Professional": {
                "type": "object",
                "properties": {
                    "id": {"type": "integer"},
                    "name": {"type": "string"},
                    "role": {"type": "string"},
                    "phone": {"type": "string"},
                    "email": {"type": "string"},
                    "color": {"type": "string"},
                    "active": {"type": "boolean"}
                }
            },
            "Service": {
                "type": "object",
                "properties": {
                    "id": {"type": "integer"},
                    "name": {"type": "string"},
                    "description": {"type": "string"},
                    "price": {"type": "number"},
                    "duration": {"type": "integer"},
                    "color": {"type": "string"},
                    "active": {"type": "boolean"}
                }
            },
            "Appointment": {
                "type": "object",
                "properties": {
                    "id": {"type": "integer"},
                    "client_id": {"type": "integer"},
                    "professional_id": {"type": "integer"},
                    "service_id": {"type": "integer"},
                    "appointment_date": {"type": "string", "format": "date"},
                    "start_time": {"type": "string", "format": "time"},
                    "end_time": {"type": "string", "format": "time"},
                    "status": {"type": "string", "enum": ["scheduled", "confirmed", "completed", "cancelled", "no_show"]},
                    "notes": {"type": "string"},
                    "price": {"type": "number"},
                    "payment_method": {"type": "string"}
                }
            },
            "Subscription": {
                "type": "object",
                "properties": {
                    "id": {"type": "integer"},
                    "client_id": {"type": "integer"},
                    "plan": {"type": "string", "enum": ["basic", "pro", "enterprise"]},
                    "status": {"type": "string"},
                    "trial_end": {"type": "string", "format": "date-time"},
                    "cancel_at_period_end": {"type": "boolean"}
                }
            },
            "Pagination": {
                "type": "object",
                "properties": {
                    "page": {"type": "integer"},
                    "pages": {"type": "integer"},
                    "per_page": {"type": "integer"},
                    "total": {"type": "integer"}
                }
            },
            "Error": {
                "type": "object",
                "properties": {
                    "message": {"type": "string"}
                }
            }
        }
    }

    Swagger(app, config=swagger_config, template=swagger_template)

    # Registrar blueprints
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(clients_bp, url_prefix='/api/clients')
    app.register_blueprint(professionals_bp, url_prefix='/api/professionals')
    app.register_blueprint(services_bp, url_prefix='/api/services')
    app.register_blueprint(appointments_bp, url_prefix='/api/appointments')
    app.register_blueprint(subscriptions_bp, url_prefix='/api/subscriptions')
    app.register_blueprint(public_bp, url_prefix='/api/public')

    # Register reminder blueprint if available
    if REMINDERS_AVAILABLE and reminders_bp:
        app.register_blueprint(reminders_bp, url_prefix='/api/reminders')

    # Health check endpoint
    @app.route('/health')
    def health_check():
        return {'status': 'healthy', 'service': 'agendamais-api'}, 200

    # Criar tabelas
    with app.app_context():
        init_db()

    return app

if __name__ == '__main__':
    app = create_app()
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_ENV') == 'development'
    print(f"Starting server on port {port}, debug={debug}")
    app.run(debug=debug, host='0.0.0.0', port=port)