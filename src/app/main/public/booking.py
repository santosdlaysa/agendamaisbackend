from flask import Blueprint, request, jsonify
from flasgger import swag_from
from datetime import datetime, timedelta
from src.config.database import db
from src.models.user import User
from src.models.professional import Professional
from src.models.service import Service
from src.models.client import Client
from src.models.appointment import Appointment, generate_booking_code

public_bp = Blueprint('public', __name__)


@public_bp.route('/business/<slug>', methods=['GET'])
@swag_from({
    'tags': ['Agendamento Online'],
    'summary': 'Dados do estabelecimento',
    'description': 'Retorna dados públicos do estabelecimento pelo slug',
    'parameters': [
        {'name': 'slug', 'in': 'path', 'type': 'string', 'required': True}
    ],
    'responses': {
        200: {'description': 'Dados do estabelecimento'},
        404: {'description': 'Estabelecimento não encontrado'}
    }
})
def get_business(slug):
    """Retorna dados públicos do estabelecimento"""
    user = User.query.filter_by(slug=slug, active=True).first()

    if not user:
        return jsonify({'error': 'Estabelecimento não encontrado'}), 404

    if not user.online_booking_enabled:
        return jsonify({'error': 'Agendamento online não disponível'}), 403

    return jsonify(user.to_public_dict()), 200


@public_bp.route('/business/<slug>/services', methods=['GET'])
@swag_from({
    'tags': ['Agendamento Online'],
    'summary': 'Listar serviços',
    'description': 'Retorna serviços disponíveis do estabelecimento',
    'parameters': [
        {'name': 'slug', 'in': 'path', 'type': 'string', 'required': True}
    ],
    'responses': {
        200: {'description': 'Lista de serviços'},
        404: {'description': 'Estabelecimento não encontrado'}
    }
})
def get_services(slug):
    """Retorna serviços disponíveis"""
    user = User.query.filter_by(slug=slug, active=True).first()

    if not user:
        return jsonify({'error': 'Estabelecimento não encontrado'}), 404

    services = Service.query.filter_by(active=True).all()

    return jsonify({
        'services': [
            {
                'id': s.id,
                'name': s.name,
                'description': s.description,
                'price': float(s.price) if s.price else 0,
                'duration': s.duration,
                'color': s.color
            }
            for s in services
        ]
    }), 200


@public_bp.route('/business/<slug>/professionals', methods=['GET'])
@swag_from({
    'tags': ['Agendamento Online'],
    'summary': 'Listar profissionais',
    'description': 'Retorna profissionais disponíveis do estabelecimento',
    'parameters': [
        {'name': 'slug', 'in': 'path', 'type': 'string', 'required': True},
        {'name': 'service_id', 'in': 'query', 'type': 'integer', 'required': False}
    ],
    'responses': {
        200: {'description': 'Lista de profissionais'},
        404: {'description': 'Estabelecimento não encontrado'}
    }
})
def get_professionals(slug):
    """Retorna profissionais disponíveis"""
    user = User.query.filter_by(slug=slug, active=True).first()

    if not user:
        return jsonify({'error': 'Estabelecimento não encontrado'}), 404

    service_id = request.args.get('service_id', type=int)

    if service_id:
        # Filtrar profissionais que atendem o serviço
        professionals = Professional.query.filter_by(active=True).filter(
            Professional.services.any(id=service_id)
        ).all()
    else:
        professionals = Professional.query.filter_by(active=True).all()

    return jsonify({
        'professionals': [
            {
                'id': p.id,
                'name': p.name,
                'role': p.role,
                'color': p.color,
                'services': [{'id': s.id, 'name': s.name} for s in p.services]
            }
            for p in professionals
        ]
    }), 200


@public_bp.route('/business/<slug>/professionals/<int:professional_id>/services', methods=['GET'])
@swag_from({
    'tags': ['Agendamento Online'],
    'summary': 'Serviços do profissional',
    'description': 'Retorna serviços que o profissional atende',
    'parameters': [
        {'name': 'slug', 'in': 'path', 'type': 'string', 'required': True},
        {'name': 'professional_id', 'in': 'path', 'type': 'integer', 'required': True}
    ],
    'responses': {
        200: {'description': 'Lista de serviços do profissional'},
        404: {'description': 'Profissional não encontrado'}
    }
})
def get_professional_services(slug, professional_id):
    """Retorna serviços do profissional"""
    user = User.query.filter_by(slug=slug, active=True).first()

    if not user:
        return jsonify({'error': 'Estabelecimento não encontrado'}), 404

    professional = Professional.query.filter_by(id=professional_id, active=True).first()

    if not professional:
        return jsonify({'error': 'Profissional não encontrado'}), 404

    return jsonify({
        'professional': {
            'id': professional.id,
            'name': professional.name
        },
        'services': [
            {
                'id': s.id,
                'name': s.name,
                'description': s.description,
                'price': float(s.price) if s.price else 0,
                'duration': s.duration
            }
            for s in professional.services if s.active
        ]
    }), 200


@public_bp.route('/business/<slug>/availability', methods=['GET'])
@swag_from({
    'tags': ['Agendamento Online'],
    'summary': 'Horários disponíveis',
    'description': 'Retorna horários disponíveis para agendamento',
    'parameters': [
        {'name': 'slug', 'in': 'path', 'type': 'string', 'required': True},
        {'name': 'professional_id', 'in': 'query', 'type': 'integer', 'required': True},
        {'name': 'service_id', 'in': 'query', 'type': 'integer', 'required': True},
        {'name': 'date', 'in': 'query', 'type': 'string', 'required': True, 'description': 'Data no formato YYYY-MM-DD'}
    ],
    'responses': {
        200: {'description': 'Lista de horários disponíveis'},
        400: {'description': 'Parâmetros inválidos'}
    }
})
def get_availability(slug):
    """Retorna horários disponíveis"""
    user = User.query.filter_by(slug=slug, active=True).first()

    if not user:
        return jsonify({'error': 'Estabelecimento não encontrado'}), 404

    professional_id = request.args.get('professional_id', type=int)
    service_id = request.args.get('service_id', type=int)
    date_str = request.args.get('date')

    if not all([professional_id, service_id, date_str]):
        return jsonify({'error': 'professional_id, service_id e date são obrigatórios'}), 400

    try:
        date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'error': 'Data inválida. Use o formato YYYY-MM-DD'}), 400

    # Não permitir datas passadas
    if date < datetime.now().date():
        return jsonify({'error': 'Não é possível agendar em datas passadas'}), 400

    service = Service.query.get(service_id)
    if not service:
        return jsonify({'error': 'Serviço não encontrado'}), 404

    # Buscar agendamentos existentes do profissional na data
    existing_appointments = Appointment.query.filter(
        Appointment.professional_id == professional_id,
        Appointment.appointment_date == date,
        Appointment.status.in_(['scheduled', 'confirmed'])
    ).all()

    # Gerar slots de horário (08:00 - 18:00 com intervalos de 30 min)
    slots = []
    start_hour = 8
    end_hour = 18
    slot_interval = 30  # minutos

    current_time = datetime.combine(date, datetime.min.time().replace(hour=start_hour))
    end_time = datetime.combine(date, datetime.min.time().replace(hour=end_hour))

    while current_time < end_time:
        slot_start = current_time.time()
        slot_end = (current_time + timedelta(minutes=service.duration)).time()

        # Verificar se o slot está disponível
        is_available = True
        for apt in existing_appointments:
            if (slot_start < apt.end_time and slot_end > apt.start_time):
                is_available = False
                break

        # Não mostrar horários passados para hoje
        if date == datetime.now().date():
            if slot_start <= datetime.now().time():
                is_available = False

        if is_available:
            slots.append({
                'start_time': slot_start.strftime('%H:%M'),
                'end_time': slot_end.strftime('%H:%M')
            })

        current_time += timedelta(minutes=slot_interval)

    return jsonify({
        'date': date_str,
        'professional_id': professional_id,
        'service_id': service_id,
        'service_duration': service.duration,
        'slots': slots
    }), 200


@public_bp.route('/business/<slug>/appointments', methods=['POST'])
@swag_from({
    'tags': ['Agendamento Online'],
    'summary': 'Criar agendamento',
    'description': 'Cria um novo agendamento online',
    'parameters': [
        {'name': 'slug', 'in': 'path', 'type': 'string', 'required': True},
        {
            'name': 'body',
            'in': 'body',
            'required': True,
            'schema': {
                'type': 'object',
                'required': ['professional_id', 'service_id', 'date', 'start_time', 'client'],
                'properties': {
                    'professional_id': {'type': 'integer'},
                    'service_id': {'type': 'integer'},
                    'date': {'type': 'string', 'example': '2024-01-15'},
                    'start_time': {'type': 'string', 'example': '09:00'},
                    'client': {
                        'type': 'object',
                        'properties': {
                            'name': {'type': 'string'},
                            'phone': {'type': 'string'},
                            'email': {'type': 'string'}
                        }
                    },
                    'notes': {'type': 'string'}
                }
            }
        }
    ],
    'responses': {
        201: {'description': 'Agendamento criado com sucesso'},
        400: {'description': 'Dados inválidos ou horário indisponível'}
    }
})
def create_appointment(slug):
    """Cria novo agendamento online"""
    user = User.query.filter_by(slug=slug, active=True).first()

    if not user:
        return jsonify({'error': 'Estabelecimento não encontrado'}), 404

    if not user.online_booking_enabled:
        return jsonify({'error': 'Agendamento online não disponível'}), 403

    data = request.json

    # Validar dados obrigatórios
    required = ['professional_id', 'service_id', 'date', 'start_time', 'client']
    for field in required:
        if field not in data:
            return jsonify({'error': f'Campo {field} é obrigatório'}), 400

    client_data = data.get('client', {})
    if not client_data.get('name') or not client_data.get('phone'):
        return jsonify({'error': 'Nome e telefone do cliente são obrigatórios'}), 400

    try:
        appointment_date = datetime.strptime(data['date'], '%Y-%m-%d').date()
        start_time = datetime.strptime(data['start_time'], '%H:%M').time()
    except ValueError:
        return jsonify({'error': 'Formato de data ou hora inválido'}), 400

    # Buscar serviço para calcular horário de término
    service = Service.query.get(data['service_id'])
    if not service:
        return jsonify({'error': 'Serviço não encontrado'}), 404

    professional = Professional.query.get(data['professional_id'])
    if not professional:
        return jsonify({'error': 'Profissional não encontrado'}), 404

    # Calcular horário de término
    start_datetime = datetime.combine(appointment_date, start_time)
    end_datetime = start_datetime + timedelta(minutes=service.duration)
    end_time = end_datetime.time()

    # Verificar conflito de horário
    if Appointment.check_conflict(data['professional_id'], appointment_date, start_time, end_time):
        return jsonify({'error': 'Horário não disponível'}), 400

    # Buscar ou criar cliente
    client = Client.query.filter_by(phone=client_data['phone']).first()
    if not client:
        client = Client(
            name=client_data['name'],
            phone=client_data['phone'],
            email=client_data.get('email')
        )
        db.session.add(client)
        db.session.flush()

    # Gerar código único de agendamento
    booking_code = generate_booking_code()
    while Appointment.query.filter_by(booking_code=booking_code).first():
        booking_code = generate_booking_code()

    # Criar agendamento
    appointment = Appointment(
        client_id=client.id,
        professional_id=data['professional_id'],
        service_id=data['service_id'],
        appointment_date=appointment_date,
        start_time=start_time,
        end_time=end_time,
        status='scheduled',
        notes=data.get('notes'),
        price=service.price,
        booking_code=booking_code,
        source='online',
        user_id=user.id
    )

    db.session.add(appointment)
    db.session.commit()

    return jsonify({
        'message': 'Agendamento realizado com sucesso!',
        'booking_code': booking_code,
        'appointment': appointment.to_public_dict()
    }), 201


@public_bp.route('/appointments/<code>', methods=['GET'])
@swag_from({
    'tags': ['Agendamento Online'],
    'summary': 'Consultar agendamento',
    'description': 'Consulta detalhes de um agendamento pelo código',
    'parameters': [
        {'name': 'code', 'in': 'path', 'type': 'string', 'required': True}
    ],
    'responses': {
        200: {'description': 'Dados do agendamento'},
        404: {'description': 'Agendamento não encontrado'}
    }
})
def get_appointment(code):
    """Consulta agendamento pelo código"""
    appointment = Appointment.query.filter_by(booking_code=code.upper()).first()

    if not appointment:
        return jsonify({'error': 'Agendamento não encontrado'}), 404

    return jsonify({
        'appointment': appointment.to_public_dict()
    }), 200


@public_bp.route('/appointments/<code>/cancel', methods=['PUT'])
@swag_from({
    'tags': ['Agendamento Online'],
    'summary': 'Cancelar agendamento',
    'description': 'Cancela um agendamento pelo código',
    'parameters': [
        {'name': 'code', 'in': 'path', 'type': 'string', 'required': True}
    ],
    'responses': {
        200: {'description': 'Agendamento cancelado'},
        400: {'description': 'Não é possível cancelar'},
        404: {'description': 'Agendamento não encontrado'}
    }
})
def cancel_appointment(code):
    """Cancela agendamento pelo código"""
    appointment = Appointment.query.filter_by(booking_code=code.upper()).first()

    if not appointment:
        return jsonify({'error': 'Agendamento não encontrado'}), 404

    if appointment.status == 'cancelled':
        return jsonify({'error': 'Agendamento já está cancelado'}), 400

    if appointment.status == 'completed':
        return jsonify({'error': 'Não é possível cancelar um agendamento concluído'}), 400

    # Verificar se não está muito próximo (ex: menos de 2 horas)
    appointment_datetime = datetime.combine(appointment.appointment_date, appointment.start_time)
    if appointment_datetime - datetime.now() < timedelta(hours=2):
        return jsonify({'error': 'Não é possível cancelar com menos de 2 horas de antecedência'}), 400

    appointment.status = 'cancelled'
    db.session.commit()

    return jsonify({
        'message': 'Agendamento cancelado com sucesso',
        'appointment': appointment.to_public_dict()
    }), 200
