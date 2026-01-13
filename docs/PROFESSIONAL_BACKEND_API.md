# API Backend - Portal do Profissional

Guia completo para implementacao dos endpoints do portal do profissional no Flask.

---

## 1. Banco de Dados

### Criar tabela `professional_users`

```sql
CREATE TABLE professional_users (
    id SERIAL PRIMARY KEY,
    professional_id INTEGER NOT NULL REFERENCES professionals(id) ON DELETE CASCADE,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255),
    invite_token VARCHAR(255),
    invite_expires_at TIMESTAMP,
    reset_token VARCHAR(255),
    reset_expires_at TIMESTAMP,
    is_active BOOLEAN DEFAULT false,
    last_login TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_professional_users_professional_id ON professional_users(professional_id);
CREATE INDEX idx_professional_users_email ON professional_users(email);
CREATE INDEX idx_professional_users_invite_token ON professional_users(invite_token);
CREATE INDEX idx_professional_users_reset_token ON professional_users(reset_token);
```

---

## 2. Modelo SQLAlchemy

```python
# models/professional_user.py

from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from extensions import db

class ProfessionalUser(db.Model):
    __tablename__ = 'professional_users'

    id = db.Column(db.Integer, primary_key=True)
    professional_id = db.Column(db.Integer, db.ForeignKey('professionals.id', ondelete='CASCADE'), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255))
    invite_token = db.Column(db.String(255))
    invite_expires_at = db.Column(db.DateTime)
    reset_token = db.Column(db.String(255))
    reset_expires_at = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=False)
    last_login = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relacionamento
    professional = db.relationship('Professional', backref='user_account')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            'id': self.id,
            'professional_id': self.professional_id,
            'email': self.email,
            'is_active': self.is_active,
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'professional': self.professional.to_dict() if self.professional else None
        }
```

---

## 3. Rotas de Autenticacao

### Arquivo: `routes/professional_auth.py`

```python
from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from datetime import datetime, timedelta
import secrets
from models.professional_user import ProfessionalUser
from models.professional import Professional
from extensions import db

professional_auth_bp = Blueprint('professional_auth', __name__, url_prefix='/api/professional-auth')


@professional_auth_bp.route('/invite', methods=['POST'])
@jwt_required()  # Requer que seja admin autenticado
def invite_professional():
    """Envia convite para profissional criar conta"""
    data = request.get_json()
    professional_id = data.get('professional_id')
    email = data.get('email')

    if not professional_id or not email:
        return jsonify({'message': 'professional_id e email sao obrigatorios'}), 400

    # Verificar se profissional existe
    professional = Professional.query.get(professional_id)
    if not professional:
        return jsonify({'message': 'Profissional nao encontrado'}), 404

    # Verificar se ja existe conta
    existing = ProfessionalUser.query.filter_by(email=email).first()
    if existing:
        return jsonify({'message': 'Ja existe uma conta com este email'}), 400

    # Criar usuario com token de convite
    invite_token = secrets.token_urlsafe(32)
    user = ProfessionalUser(
        professional_id=professional_id,
        email=email,
        invite_token=invite_token,
        invite_expires_at=datetime.utcnow() + timedelta(hours=48)
    )

    db.session.add(user)
    db.session.commit()

    # TODO: Enviar email com link de ativacao
    # link = f"{FRONTEND_URL}/#/profissional/ativar/{invite_token}"
    # send_invite_email(email, professional.name, link)

    return jsonify({
        'message': 'Convite enviado com sucesso',
        'invite_token': invite_token  # Remover em producao, apenas para debug
    }), 201


@professional_auth_bp.route('/activate', methods=['POST'])
def activate_account():
    """Profissional ativa sua conta definindo senha"""
    data = request.get_json()
    token = data.get('token')
    password = data.get('password')

    if not token or not password:
        return jsonify({'message': 'Token e senha sao obrigatorios'}), 400

    if len(password) < 6:
        return jsonify({'message': 'Senha deve ter pelo menos 6 caracteres'}), 400

    user = ProfessionalUser.query.filter_by(invite_token=token).first()

    if not user:
        return jsonify({'message': 'Token invalido'}), 400

    if user.invite_expires_at < datetime.utcnow():
        return jsonify({'message': 'Token expirado'}), 400

    if user.is_active:
        return jsonify({'message': 'Conta ja foi ativada'}), 400

    # Ativar conta
    user.set_password(password)
    user.is_active = True
    user.invite_token = None
    user.invite_expires_at = None

    db.session.commit()

    return jsonify({'message': 'Conta ativada com sucesso'}), 200


@professional_auth_bp.route('/login', methods=['POST'])
def login():
    """Login do profissional"""
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({'message': 'Email e senha sao obrigatorios'}), 400

    user = ProfessionalUser.query.filter_by(email=email).first()

    if not user or not user.check_password(password):
        return jsonify({'message': 'Email ou senha incorretos'}), 401

    if not user.is_active:
        return jsonify({'message': 'Conta ainda nao foi ativada'}), 401

    # Atualizar ultimo login
    user.last_login = datetime.utcnow()
    db.session.commit()

    # Criar token JWT com claim especial para profissional
    access_token = create_access_token(
        identity=user.id,
        additional_claims={'type': 'professional', 'professional_id': user.professional_id}
    )

    return jsonify({
        'access_token': access_token,
        'professional': {
            'id': user.professional.id,
            'name': user.professional.name,
            'role': user.professional.role,
            'color': user.professional.color,
            'email': user.email
        }
    }), 200


@professional_auth_bp.route('/forgot-password', methods=['POST'])
def forgot_password():
    """Solicita reset de senha"""
    data = request.get_json()
    email = data.get('email')

    if not email:
        return jsonify({'message': 'Email e obrigatorio'}), 400

    user = ProfessionalUser.query.filter_by(email=email).first()

    # Sempre retorna sucesso para nao revelar se email existe
    if user and user.is_active:
        reset_token = secrets.token_urlsafe(32)
        user.reset_token = reset_token
        user.reset_expires_at = datetime.utcnow() + timedelta(hours=1)
        db.session.commit()

        # TODO: Enviar email
        # link = f"{FRONTEND_URL}/#/profissional/resetar-senha/{reset_token}"
        # send_reset_email(email, link)

    return jsonify({'message': 'Se o email existir, um link sera enviado'}), 200


@professional_auth_bp.route('/reset-password', methods=['POST'])
def reset_password():
    """Reseta senha com token"""
    data = request.get_json()
    token = data.get('token')
    password = data.get('password')

    if not token or not password:
        return jsonify({'message': 'Token e senha sao obrigatorios'}), 400

    if len(password) < 6:
        return jsonify({'message': 'Senha deve ter pelo menos 6 caracteres'}), 400

    user = ProfessionalUser.query.filter_by(reset_token=token).first()

    if not user:
        return jsonify({'message': 'Token invalido'}), 400

    if user.reset_expires_at < datetime.utcnow():
        return jsonify({'message': 'Token expirado'}), 400

    user.set_password(password)
    user.reset_token = None
    user.reset_expires_at = None
    db.session.commit()

    return jsonify({'message': 'Senha alterada com sucesso'}), 200


@professional_auth_bp.route('/change-password', methods=['POST'])
@jwt_required()
def change_password():
    """Altera senha (usuario logado)"""
    # Verificar se e um profissional
    claims = get_jwt_identity()
    # ... implementar verificacao

    data = request.get_json()
    current_password = data.get('current_password')
    new_password = data.get('new_password')

    if not current_password or not new_password:
        return jsonify({'message': 'Senhas sao obrigatorias'}), 400

    if len(new_password) < 6:
        return jsonify({'message': 'Nova senha deve ter pelo menos 6 caracteres'}), 400

    user = ProfessionalUser.query.get(claims)

    if not user.check_password(current_password):
        return jsonify({'message': 'Senha atual incorreta'}), 400

    user.set_password(new_password)
    db.session.commit()

    return jsonify({'message': 'Senha alterada com sucesso'}), 200
```

---

## 4. Rotas da Dashboard

### Arquivo: `routes/professional_dashboard.py`

```python
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt
from datetime import datetime, timedelta
from sqlalchemy import func, and_
from models.appointment import Appointment
from models.client import Client
from models.service import Service
from extensions import db

professional_bp = Blueprint('professional', __name__, url_prefix='/api/professional')


def get_current_professional_id():
    """Helper para obter ID do profissional do token JWT"""
    claims = get_jwt()
    if claims.get('type') != 'professional':
        return None
    return claims.get('professional_id')


@professional_bp.route('/dashboard', methods=['GET'])
@jwt_required()
def get_dashboard():
    """Retorna dados da dashboard do profissional"""
    professional_id = get_current_professional_id()
    if not professional_id:
        return jsonify({'message': 'Acesso nao autorizado'}), 403

    today = datetime.utcnow().date()
    week_start = today - timedelta(days=today.weekday())
    week_end = week_start + timedelta(days=6)
    month_start = today.replace(day=1)
    month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)

    # Stats de hoje
    today_appointments = Appointment.query.filter(
        and_(
            Appointment.professional_id == professional_id,
            Appointment.appointment_date == today
        )
    ).count()

    today_completed = Appointment.query.filter(
        and_(
            Appointment.professional_id == professional_id,
            Appointment.appointment_date == today,
            Appointment.status == 'completed'
        )
    ).count()

    # Stats da semana
    week_appointments = Appointment.query.filter(
        and_(
            Appointment.professional_id == professional_id,
            Appointment.appointment_date >= week_start,
            Appointment.appointment_date <= week_end
        )
    ).count()

    # Stats do mes
    month_query = Appointment.query.filter(
        and_(
            Appointment.professional_id == professional_id,
            Appointment.appointment_date >= month_start,
            Appointment.appointment_date <= month_end
        )
    )

    month_appointments = month_query.count()
    month_completed = month_query.filter(Appointment.status == 'completed').count()
    month_cancelled = month_query.filter(Appointment.status == 'cancelled').count()

    # Receita do mes
    month_revenue = db.session.query(func.sum(Appointment.price)).filter(
        and_(
            Appointment.professional_id == professional_id,
            Appointment.appointment_date >= month_start,
            Appointment.appointment_date <= month_end,
            Appointment.status == 'completed'
        )
    ).scalar() or 0

    # Taxa de conclusao
    total_finished = month_completed + month_cancelled
    completion_rate = round((month_completed / total_finished * 100), 1) if total_finished > 0 else 0

    # Agenda de hoje
    today_schedule = Appointment.query.filter(
        and_(
            Appointment.professional_id == professional_id,
            Appointment.appointment_date == today
        )
    ).order_by(Appointment.start_time).all()

    # Proximos agendamentos
    upcoming = Appointment.query.filter(
        and_(
            Appointment.professional_id == professional_id,
            Appointment.appointment_date >= today,
            Appointment.status == 'scheduled'
        )
    ).order_by(Appointment.appointment_date, Appointment.start_time).limit(10).all()

    return jsonify({
        'stats': {
            'today_appointments': today_appointments,
            'today_completed': today_completed,
            'today_pending': today_appointments - today_completed,
            'week_appointments': week_appointments,
            'month_appointments': month_appointments,
            'month_completed': month_completed,
            'month_cancelled': month_cancelled,
            'month_revenue': float(month_revenue),
            'completion_rate': completion_rate
        },
        'today_schedule': [{
            'id': apt.id,
            'client_name': apt.client.name if apt.client else 'Cliente',
            'client_phone': apt.client.phone if apt.client else '',
            'service_name': apt.service.name if apt.service else 'Servico',
            'start_time': apt.start_time.strftime('%H:%M') if apt.start_time else None,
            'end_time': apt.end_time.strftime('%H:%M') if apt.end_time else None,
            'status': apt.status,
            'price': float(apt.price) if apt.price else 0
        } for apt in today_schedule],
        'upcoming_appointments': [{
            'id': apt.id,
            'client_name': apt.client.name if apt.client else 'Cliente',
            'appointment_date': apt.appointment_date.strftime('%d/%m/%Y'),
            'start_time': apt.start_time.strftime('%H:%M') if apt.start_time else None,
            'service_name': apt.service.name if apt.service else 'Servico'
        } for apt in upcoming]
    }), 200


@professional_bp.route('/appointments', methods=['GET'])
@jwt_required()
def get_appointments():
    """Lista agendamentos do profissional"""
    professional_id = get_current_professional_id()
    if not professional_id:
        return jsonify({'message': 'Acesso nao autorizado'}), 403

    # Filtros
    date = request.args.get('date')
    status = request.args.get('status')
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)

    query = Appointment.query.filter(Appointment.professional_id == professional_id)

    if date:
        query = query.filter(Appointment.appointment_date == date)

    if status:
        query = query.filter(Appointment.status == status)

    query = query.order_by(Appointment.appointment_date.desc(), Appointment.start_time.desc())

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        'appointments': [{
            'id': apt.id,
            'client_name': apt.client.name if apt.client else 'Cliente',
            'client_phone': apt.client.phone if apt.client else '',
            'service_name': apt.service.name if apt.service else 'Servico',
            'appointment_date': apt.appointment_date.strftime('%Y-%m-%d'),
            'start_time': apt.start_time.strftime('%H:%M') if apt.start_time else None,
            'end_time': apt.end_time.strftime('%H:%M') if apt.end_time else None,
            'status': apt.status,
            'price': float(apt.price) if apt.price else 0,
            'notes': apt.notes
        } for apt in pagination.items],
        'total': pagination.total,
        'page': pagination.page,
        'pages': pagination.pages
    }), 200


@professional_bp.route('/appointments/<int:appointment_id>/complete', methods=['PUT'])
@jwt_required()
def complete_appointment(appointment_id):
    """Marca agendamento como concluido"""
    professional_id = get_current_professional_id()
    if not professional_id:
        return jsonify({'message': 'Acesso nao autorizado'}), 403

    appointment = Appointment.query.get(appointment_id)

    if not appointment:
        return jsonify({'message': 'Agendamento nao encontrado'}), 404

    if appointment.professional_id != professional_id:
        return jsonify({'message': 'Acesso nao autorizado'}), 403

    if appointment.status != 'scheduled':
        return jsonify({'message': 'Agendamento nao pode ser concluido'}), 400

    data = request.get_json() or {}

    appointment.status = 'completed'
    appointment.completed_at = datetime.utcnow()
    appointment.notes = data.get('notes', appointment.notes)

    if data.get('price'):
        appointment.price = data.get('price')

    if data.get('payment_method'):
        appointment.payment_method = data.get('payment_method')

    db.session.commit()

    return jsonify({'message': 'Agendamento concluido com sucesso'}), 200


@professional_bp.route('/schedule', methods=['GET'])
@jwt_required()
def get_schedule():
    """Retorna agenda do profissional para um periodo"""
    professional_id = get_current_professional_id()
    if not professional_id:
        return jsonify({'message': 'Acesso nao autorizado'}), 403

    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    if not start_date or not end_date:
        return jsonify({'message': 'start_date e end_date sao obrigatorios'}), 400

    appointments = Appointment.query.filter(
        and_(
            Appointment.professional_id == professional_id,
            Appointment.appointment_date >= start_date,
            Appointment.appointment_date <= end_date
        )
    ).order_by(Appointment.appointment_date, Appointment.start_time).all()

    return jsonify({
        'appointments': [{
            'id': apt.id,
            'client_name': apt.client.name if apt.client else 'Cliente',
            'service_name': apt.service.name if apt.service else 'Servico',
            'appointment_date': apt.appointment_date.strftime('%Y-%m-%d'),
            'start_time': apt.start_time.strftime('%H:%M') if apt.start_time else None,
            'end_time': apt.end_time.strftime('%H:%M') if apt.end_time else None,
            'status': apt.status
        } for apt in appointments]
    }), 200


@professional_bp.route('/clients', methods=['GET'])
@jwt_required()
def get_clients():
    """Lista clientes atendidos pelo profissional"""
    professional_id = get_current_professional_id()
    if not professional_id:
        return jsonify({'message': 'Acesso nao autorizado'}), 403

    search = request.args.get('search', '')

    # Buscar clientes que tem agendamentos com este profissional
    subquery = db.session.query(Appointment.client_id).filter(
        Appointment.professional_id == professional_id
    ).distinct()

    query = Client.query.filter(Client.id.in_(subquery))

    if search:
        query = query.filter(
            Client.name.ilike(f'%{search}%') |
            Client.phone.ilike(f'%{search}%')
        )

    clients = query.order_by(Client.name).all()

    result = []
    for client in clients:
        # Contar agendamentos
        total = Appointment.query.filter(
            and_(
                Appointment.client_id == client.id,
                Appointment.professional_id == professional_id
            )
        ).count()

        completed = Appointment.query.filter(
            and_(
                Appointment.client_id == client.id,
                Appointment.professional_id == professional_id,
                Appointment.status == 'completed'
            )
        ).count()

        result.append({
            'id': client.id,
            'name': client.name,
            'phone': client.phone,
            'email': client.email,
            'total_appointments': total,
            'completed_appointments': completed
        })

    return jsonify({'clients': result}), 200


@professional_bp.route('/clients/<int:client_id>', methods=['GET'])
@jwt_required()
def get_client(client_id):
    """Retorna detalhes de um cliente e historico de atendimentos"""
    professional_id = get_current_professional_id()
    if not professional_id:
        return jsonify({'message': 'Acesso nao autorizado'}), 403

    client = Client.query.get(client_id)
    if not client:
        return jsonify({'message': 'Cliente nao encontrado'}), 404

    # Verificar se profissional ja atendeu este cliente
    has_appointments = Appointment.query.filter(
        and_(
            Appointment.client_id == client_id,
            Appointment.professional_id == professional_id
        )
    ).first()

    if not has_appointments:
        return jsonify({'message': 'Acesso nao autorizado'}), 403

    # Buscar historico
    appointments = Appointment.query.filter(
        and_(
            Appointment.client_id == client_id,
            Appointment.professional_id == professional_id
        )
    ).order_by(Appointment.appointment_date.desc()).all()

    return jsonify({
        'client': {
            'id': client.id,
            'name': client.name,
            'phone': client.phone,
            'email': client.email
        },
        'appointments': [{
            'id': apt.id,
            'service_name': apt.service.name if apt.service else 'Servico',
            'appointment_date': apt.appointment_date.strftime('%Y-%m-%d'),
            'start_time': apt.start_time.strftime('%H:%M') if apt.start_time else None,
            'status': apt.status,
            'price': float(apt.price) if apt.price else 0,
            'notes': apt.notes
        } for apt in appointments]
    }), 200


@professional_bp.route('/working-hours', methods=['GET'])
@jwt_required()
def get_working_hours():
    """Retorna horarios de trabalho do profissional"""
    professional_id = get_current_professional_id()
    if not professional_id:
        return jsonify({'message': 'Acesso nao autorizado'}), 403

    from models.professional import Professional
    professional = Professional.query.get(professional_id)

    return jsonify({
        'working_hours': professional.working_hours or []
    }), 200


@professional_bp.route('/working-hours', methods=['PUT'])
@jwt_required()
def update_working_hours():
    """Atualiza horarios de trabalho"""
    professional_id = get_current_professional_id()
    if not professional_id:
        return jsonify({'message': 'Acesso nao autorizado'}), 403

    data = request.get_json()
    working_hours = data.get('working_hours', [])

    from models.professional import Professional
    professional = Professional.query.get(professional_id)
    professional.working_hours = working_hours

    db.session.commit()

    return jsonify({'message': 'Horarios atualizados com sucesso'}), 200


@professional_bp.route('/blocked-dates', methods=['GET'])
@jwt_required()
def get_blocked_dates():
    """Retorna datas bloqueadas do profissional"""
    professional_id = get_current_professional_id()
    if not professional_id:
        return jsonify({'message': 'Acesso nao autorizado'}), 403

    from models.professional import Professional
    professional = Professional.query.get(professional_id)

    return jsonify({
        'blocked_dates': professional.blocked_dates or []
    }), 200


@professional_bp.route('/blocked-dates', methods=['POST'])
@jwt_required()
def add_blocked_date():
    """Adiciona data bloqueada"""
    professional_id = get_current_professional_id()
    if not professional_id:
        return jsonify({'message': 'Acesso nao autorizado'}), 403

    data = request.get_json()
    date = data.get('date')
    reason = data.get('reason', '')

    if not date:
        return jsonify({'message': 'Data e obrigatoria'}), 400

    from models.professional import Professional
    import uuid

    professional = Professional.query.get(professional_id)
    blocked_dates = professional.blocked_dates or []

    blocked_dates.append({
        'id': str(uuid.uuid4()),
        'date': date,
        'reason': reason
    })

    professional.blocked_dates = blocked_dates
    db.session.commit()

    return jsonify({'message': 'Data bloqueada com sucesso'}), 201


@professional_bp.route('/blocked-dates/<string:block_id>', methods=['DELETE'])
@jwt_required()
def remove_blocked_date(block_id):
    """Remove data bloqueada"""
    professional_id = get_current_professional_id()
    if not professional_id:
        return jsonify({'message': 'Acesso nao autorizado'}), 403

    from models.professional import Professional

    professional = Professional.query.get(professional_id)
    blocked_dates = professional.blocked_dates or []

    professional.blocked_dates = [b for b in blocked_dates if b.get('id') != block_id]
    db.session.commit()

    return jsonify({'message': 'Bloqueio removido com sucesso'}), 200
```

---

## 5. Registrar Blueprints

No arquivo principal `app.py`:

```python
from routes.professional_auth import professional_auth_bp
from routes.professional_dashboard import professional_bp

# Registrar blueprints
app.register_blueprint(professional_auth_bp)
app.register_blueprint(professional_bp)
```

---

## 6. Middleware JWT para Profissional

Adicionar verificacao de tipo no JWT:

```python
from flask_jwt_extended import verify_jwt_in_request, get_jwt

def professional_required():
    """Decorator para rotas que requerem profissional autenticado"""
    def wrapper(fn):
        @wraps(fn)
        def decorator(*args, **kwargs):
            verify_jwt_in_request()
            claims = get_jwt()
            if claims.get('type') != 'professional':
                return jsonify({'message': 'Acesso restrito a profissionais'}), 403
            return fn(*args, **kwargs)
        return decorator
    return wrapper
```

---

## 7. Funcionalidade de Convite no Admin

Adicionar no formulario de profissional (`ProfessionalForm.jsx`) um botao para enviar convite:

```python
# Endpoint para admin enviar convite
@professionals_bp.route('/<int:professional_id>/invite', methods=['POST'])
@jwt_required()
def invite_professional(professional_id):
    """Admin envia convite para profissional"""
    data = request.get_json()
    email = data.get('email')

    if not email:
        return jsonify({'message': 'Email e obrigatorio'}), 400

    professional = Professional.query.get(professional_id)
    if not professional:
        return jsonify({'message': 'Profissional nao encontrado'}), 404

    # Verificar se ja existe conta
    existing = ProfessionalUser.query.filter_by(professional_id=professional_id).first()
    if existing:
        return jsonify({'message': 'Profissional ja possui conta'}), 400

    # Criar usuario com convite
    invite_token = secrets.token_urlsafe(32)
    user = ProfessionalUser(
        professional_id=professional_id,
        email=email,
        invite_token=invite_token,
        invite_expires_at=datetime.utcnow() + timedelta(hours=48)
    )

    db.session.add(user)
    db.session.commit()

    # TODO: Enviar email

    return jsonify({
        'message': 'Convite enviado',
        'invite_link': f'/profissional/ativar/{invite_token}'
    }), 201
```

---

## 8. Checklist de Implementacao

### Banco de Dados
- [ ] Criar tabela `professional_users`
- [ ] Adicionar indices

### Autenticacao
- [ ] `POST /api/professional-auth/invite` - Enviar convite
- [ ] `POST /api/professional-auth/activate` - Ativar conta
- [ ] `POST /api/professional-auth/login` - Login
- [ ] `POST /api/professional-auth/forgot-password` - Solicitar reset
- [ ] `POST /api/professional-auth/reset-password` - Resetar senha
- [ ] `POST /api/professional-auth/change-password` - Alterar senha

### Dashboard
- [ ] `GET /api/professional/dashboard` - Dados da dashboard
- [ ] `GET /api/professional/appointments` - Listar agendamentos
- [ ] `PUT /api/professional/appointments/:id/complete` - Concluir
- [ ] `GET /api/professional/schedule` - Agenda
- [ ] `GET /api/professional/clients` - Clientes
- [ ] `GET /api/professional/clients/:id` - Detalhe cliente

### Configuracoes
- [ ] `GET /api/professional/working-hours` - Obter horarios
- [ ] `PUT /api/professional/working-hours` - Atualizar horarios
- [ ] `GET /api/professional/blocked-dates` - Obter bloqueios
- [ ] `POST /api/professional/blocked-dates` - Adicionar bloqueio
- [ ] `DELETE /api/professional/blocked-dates/:id` - Remover bloqueio

### Admin
- [ ] `POST /api/professionals/:id/invite` - Enviar convite
- [ ] Adicionar campo de email no formulario de profissional
- [ ] Mostrar status da conta do profissional

---

*Documento criado em Janeiro 2026*
