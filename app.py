from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from src.config.database import db, init_db
import src.models
from src.app.auth.auth import auth_bp
from src.app.main.client.clients import clients_bp
from src.app.main.professional.professionals import professionals_bp
from src.app.main.service.services import services_bp
from src.app.main.appointment.appointments import appointments_bp
from src.app.main.subscription.subscriptions import subscriptions_bp
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
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///agendamento.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'jwt-secret-string')
    
    # Configuração CORS
    allowed_origins = [
        'http://localhost:3000',
        'http://localhost:5173',
        'http://172.29.16.1:3001',
        'https://agendamais-x19j-32f6fx9yd-santosdlaysas-projects.vercel.app',
        'https://agendamais-x19j.vercel.app',
        'https://agendamais.site/'
        os.getenv('FRONTEND_URL')
    ]

    # Remove valores None/vazios
    allowed_origins = [origin for origin in allowed_origins if origin]

    CORS(app,
         origins=allowed_origins,
         methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
         allow_headers=['Content-Type', 'Authorization'],
         supports_credentials=True)

    JWTManager(app)
    db.init_app(app)
    
    # Registrar blueprints
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(clients_bp, url_prefix='/api/clients')
    app.register_blueprint(professionals_bp, url_prefix='/api/professionals')
    app.register_blueprint(services_bp, url_prefix='/api/services')
    app.register_blueprint(appointments_bp, url_prefix='/api/appointments')
    app.register_blueprint(subscriptions_bp, url_prefix='/api/subscriptions')

    # Register reminder blueprint if available
    if REMINDERS_AVAILABLE and reminders_bp:
        app.register_blueprint(reminders_bp, url_prefix='/api/reminders')
    
    # Criar tabelas
    with app.app_context():
        init_db()
    
    return app

if __name__ == '__main__':
    app = create_app()
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_ENV') == 'development'
    app.run(debug=debug, host='0.0.0.0', port=port)