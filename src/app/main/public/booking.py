from flask import Blueprint, request, jsonify
from flasgger import swag_from
from datetime import datetime, timedelta, time
from functools import wraps
from src.config.database import db
from src.models.user import User
from src.models.professional import Professional
from src.models.service import Service
from src.models.client import Client
from src.models.appointment import Appointment, generate_booking_code
from src.models.working_hours import WorkingHours, ProfessionalBlockedDate

public_bp = Blueprint('public', __name__)

# Rate limiting simples em memória (para produção, usar Redis)
rate_limit_storage = {}


def simple_rate_limit(max_requests=30, window_seconds=60):
    """Decorator para rate limiting simples"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            client_ip = request.remote_addr
            now = datetime.now()
            window_key = f"{client_ip}:{f.__name__}"

            if window_key not in rate_limit_storage:
                rate_limit_storage[window_key] = {'count': 0, 'reset_time': now + timedelta(seconds=window_seconds)}

            storage = rate_limit_storage[window_key]

            # Reset if window expired
            if now > storage['reset_time']:
                storage['count'] = 0
                storage['reset_time'] = now + timedelta(seconds=window_seconds)

            storage['count'] += 1

            if storage['count'] > max_requests:
                return jsonify({
                    'error': 'Muitas requisições. Tente novamente em alguns segundos.',
                    'retry_after': (storage['reset_time'] - now).seconds
                }), 429

            return f(*args, **kwargs)
        return decorated_function
    return decorator


def get_business_or_404(slug):
    """Helper para buscar estabelecimento ou retornar 404"""
    user = User.query.filter_by(slug=slug, active=True).first()
    if not user:
        return None, ({'error': 'Estabelecimento não encontrado'}, 404)
    if not user.online_booking_enabled:
        return None, ({'error': 'Agendamento online não disponível para este estabelecimento'}, 403)
    return user, None


@public_bp.route('/business/<slug>', methods=['GET'])
@simple_rate_limit(max_requests=60, window_seconds=60)
@swag_from({
    'tags': ['Agendamento Online'],
    'summary': 'Dados do estabelecimento',
    'description': 'Retorna dados públicos do estabelecimento pelo slug, incluindo configurações de agendamento',
    'parameters': [
        {'name': 'slug', 'in': 'path', 'type': 'string', 'required': True}
    ],
    'responses': {
        200: {'description': 'Dados do estabelecimento'},
        404: {'description': 'Estabelecimento não encontrado'},
        403: {'description': 'Agendamento online não disponível'}
    }
})
def get_business(slug):
    """Retorna dados públicos do estabelecimento"""
    user, error = get_business_or_404(slug)
    if error:
        return jsonify(error[0]), error[1]

    return jsonify(user.to_public_dict()), 200


@public_bp.route('/business/<slug>/services', methods=['GET'])
@simple_rate_limit(max_requests=60, window_seconds=60)
@swag_from({
    'tags': ['Agendamento Online'],
    'summary': 'Listar serviços',
    'description': 'Retorna serviços disponíveis do estabelecimento',
    'parameters': [
        {'name': 'slug', 'in': 'path', 'type': 'string', 'required': True},
        {'name': 'category', 'in': 'query', 'type': 'string', 'required': False}
    ],
    'responses': {
        200: {'description': 'Lista de serviços'},
        404: {'description': 'Estabelecimento não encontrado'}
    }
})
def get_services(slug):
    """Retorna serviços disponíveis"""
    user, error = get_business_or_404(slug)
    if error:
        return jsonify(error[0]), error[1]

    query = Service.query.filter_by(active=True, user_id=user.id)

    # Filtro por categoria se informado
    category = request.args.get('category')
    if category:
        query = query.filter(Service.category == category)

    services = query.order_by(Service.name).all()

    return jsonify({
        'business': {
            'name': user.business_name or user.name,
            'slug': user.slug
        },
        'services': [
            {
                'id': s.id,
                'name': s.name,
                'description': s.description,
                'price': float(s.price) if s.price else 0,
                'duration': s.duration,
                'color': s.color,
                'category': getattr(s, 'category', None)
            }
            for s in services
        ]
    }), 200


@public_bp.route('/business/<slug>/professionals', methods=['GET'])
@simple_rate_limit(max_requests=60, window_seconds=60)
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
    user, error = get_business_or_404(slug)
    if error:
        return jsonify(error[0]), error[1]

    service_id = request.args.get('service_id', type=int)

    if service_id:
        # Verificar se o serviço pertence a esta empresa
        service = Service.query.filter_by(id=service_id, user_id=user.id, active=True).first()
        if not service:
            return jsonify({'error': 'Serviço não encontrado'}), 404
        professionals = Professional.query.filter_by(active=True, user_id=user.id).filter(
            Professional.services.any(id=service_id)
        ).all()
    else:
        professionals = Professional.query.filter_by(active=True, user_id=user.id).all()

    result = []
    for p in professionals:
        # Buscar horários de trabalho do profissional
        working_hours = WorkingHours.query.filter_by(
            professional_id=p.id,
            is_available=True
        ).all()

        days_available = [wh.day_of_week for wh in working_hours]

        result.append({
            'id': p.id,
            'name': p.name,
            'role': p.role,
            'color': p.color,
            'services': [{'id': s.id, 'name': s.name} for s in p.services if s.active],
            'days_available': days_available
        })

    return jsonify({
        'business': {
            'name': user.business_name or user.name,
            'slug': user.slug
        },
        'professionals': result
    }), 200


@public_bp.route('/business/<slug>/professionals/<int:professional_id>/services', methods=['GET'])
@simple_rate_limit(max_requests=60, window_seconds=60)
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
    user, error = get_business_or_404(slug)
    if error:
        return jsonify(error[0]), error[1]

    professional = Professional.query.filter_by(id=professional_id, active=True, user_id=user.id).first()

    if not professional:
        return jsonify({'error': 'Profissional não encontrado'}), 404

    return jsonify({
        'professional': {
            'id': professional.id,
            'name': professional.name,
            'role': professional.role
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


@public_bp.route('/business/<slug>/professionals/<int:professional_id>/working-hours', methods=['GET'])
@simple_rate_limit(max_requests=60, window_seconds=60)
@swag_from({
    'tags': ['Agendamento Online'],
    'summary': 'Horários de trabalho do profissional',
    'description': 'Retorna os horários de trabalho do profissional',
    'parameters': [
        {'name': 'slug', 'in': 'path', 'type': 'string', 'required': True},
        {'name': 'professional_id', 'in': 'path', 'type': 'integer', 'required': True}
    ],
    'responses': {
        200: {'description': 'Horários de trabalho'},
        404: {'description': 'Profissional não encontrado'}
    }
})
def get_professional_working_hours(slug, professional_id):
    """Retorna horários de trabalho do profissional"""
    user, error = get_business_or_404(slug)
    if error:
        return jsonify(error[0]), error[1]

    professional = Professional.query.filter_by(id=professional_id, active=True, user_id=user.id).first()
    if not professional:
        return jsonify({'error': 'Profissional não encontrado'}), 404

    working_hours = WorkingHours.query.filter_by(professional_id=professional_id).all()

    return jsonify({
        'professional_id': professional_id,
        'working_hours': [wh.to_dict() for wh in working_hours]
    }), 200


@public_bp.route('/business/<slug>/availability', methods=['GET'])
@simple_rate_limit(max_requests=30, window_seconds=60)
@swag_from({
    'tags': ['Agendamento Online'],
    'summary': 'Horários disponíveis',
    'description': 'Retorna horários disponíveis para agendamento em uma data específica',
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
    """Retorna horários disponíveis para uma data"""
    user, error = get_business_or_404(slug)
    if error:
        return jsonify(error[0]), error[1]

    professional_id = request.args.get('professional_id', type=int)
    service_id = request.args.get('service_id', type=int)
    date_str = request.args.get('date')

    if not all([professional_id, service_id, date_str]):
        return jsonify({'error': 'professional_id, service_id e date são obrigatórios'}), 400

    try:
        date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'error': 'Data inválida. Use o formato YYYY-MM-DD'}), 400

    # Validar antecedência mínima
    now = datetime.now()
    min_advance = timedelta(hours=user.booking_min_advance_hours or 2)
    if datetime.combine(date, time(23, 59)) < now + min_advance:
        return jsonify({'error': f'Antecedência mínima de {user.booking_min_advance_hours} horas'}), 400

    # Validar antecedência máxima
    max_advance = timedelta(days=user.booking_max_advance_days or 30)
    if date > (now + max_advance).date():
        return jsonify({'error': f'Antecedência máxima de {user.booking_max_advance_days} dias'}), 400

    service = Service.query.filter_by(id=service_id, user_id=user.id, active=True).first()
    if not service:
        return jsonify({'error': 'Serviço não encontrado'}), 404

    professional = Professional.query.filter_by(id=professional_id, user_id=user.id, active=True).first()
    if not professional:
        return jsonify({'error': 'Profissional não encontrado'}), 404

    # Verificar se é data bloqueada
    if ProfessionalBlockedDate.is_date_blocked(professional_id, date):
        return jsonify({
            'date': date_str,
            'professional_id': professional_id,
            'service_id': service_id,
            'service_duration': service.duration,
            'slots': [],
            'message': 'Profissional não disponível nesta data'
        }), 200

    # Buscar horários de trabalho do profissional para o dia da semana
    day_of_week = date.weekday()  # 0=Segunda, 6=Domingo
    working_hours = WorkingHours.query.filter_by(
        professional_id=professional_id,
        day_of_week=day_of_week,
        is_available=True
    ).first()

    # Se não tem horário configurado, usar padrão do estabelecimento
    if working_hours:
        start_hour = working_hours.start_time.hour
        start_minute = working_hours.start_time.minute
        end_hour = working_hours.end_time.hour
        end_minute = working_hours.end_time.minute
        break_start = working_hours.break_start
        break_end = working_hours.break_end
    else:
        start_hour = user.booking_start_hour or 8
        start_minute = 0
        end_hour = user.booking_end_hour or 18
        end_minute = 0
        break_start = None
        break_end = None

    # Buscar agendamentos existentes do profissional na data
    existing_appointments = Appointment.query.filter(
        Appointment.professional_id == professional_id,
        Appointment.appointment_date == date,
        Appointment.status.in_(['scheduled', 'confirmed'])
    ).all()

    # Gerar slots de horário
    slots = []
    slot_interval = user.booking_slot_interval or 30

    current_time = datetime.combine(date, time(start_hour, start_minute))
    end_time_dt = datetime.combine(date, time(end_hour, end_minute))

    while current_time < end_time_dt:
        slot_start = current_time.time()
        slot_end_dt = current_time + timedelta(minutes=service.duration)
        slot_end = slot_end_dt.time()

        # Não gerar slot se termina após o horário de trabalho
        if slot_end_dt > end_time_dt:
            break

        is_available = True

        # Verificar se está no intervalo/almoço
        if break_start and break_end:
            if slot_start < break_end and slot_end > break_start:
                is_available = False

        # Verificar conflitos com agendamentos existentes
        if is_available:
            for apt in existing_appointments:
                if (slot_start < apt.end_time and slot_end > apt.start_time):
                    is_available = False
                    break

        # Não mostrar horários passados para hoje
        if is_available and date == now.date():
            min_time = (now + min_advance).time()
            if slot_start <= min_time:
                is_available = False

        if is_available:
            slots.append({
                'start_time': slot_start.strftime('%H:%M'),
                'end_time': slot_end.strftime('%H:%M')
            })

        current_time += timedelta(minutes=slot_interval)

    return jsonify({
        'date': date_str,
        'day_of_week': day_of_week,
        'professional_id': professional_id,
        'service_id': service_id,
        'service_duration': service.duration,
        'slots': slots,
        'total_slots': len(slots)
    }), 200


@public_bp.route('/business/<slug>/availability/multi-day', methods=['GET'])
@simple_rate_limit(max_requests=20, window_seconds=60)
@swag_from({
    'tags': ['Agendamento Online'],
    'summary': 'Disponibilidade de múltiplos dias',
    'description': 'Retorna resumo de disponibilidade para os próximos dias',
    'parameters': [
        {'name': 'slug', 'in': 'path', 'type': 'string', 'required': True},
        {'name': 'professional_id', 'in': 'query', 'type': 'integer', 'required': True},
        {'name': 'service_id', 'in': 'query', 'type': 'integer', 'required': True},
        {'name': 'days', 'in': 'query', 'type': 'integer', 'required': False, 'default': 14}
    ],
    'responses': {
        200: {'description': 'Disponibilidade por dia'},
        400: {'description': 'Parâmetros inválidos'}
    }
})
def get_multi_day_availability(slug):
    """Retorna disponibilidade resumida para múltiplos dias"""
    user, error = get_business_or_404(slug)
    if error:
        return jsonify(error[0]), error[1]

    professional_id = request.args.get('professional_id', type=int)
    service_id = request.args.get('service_id', type=int)
    days = request.args.get('days', type=int, default=14)

    if not all([professional_id, service_id]):
        return jsonify({'error': 'professional_id e service_id são obrigatórios'}), 400

    days = min(days, user.booking_max_advance_days or 30)

    service = Service.query.filter_by(id=service_id, user_id=user.id, active=True).first()
    if not service:
        return jsonify({'error': 'Serviço não encontrado'}), 404

    professional = Professional.query.filter_by(id=professional_id, user_id=user.id, active=True).first()
    if not professional:
        return jsonify({'error': 'Profissional não encontrado'}), 404

    # Buscar horários de trabalho
    working_hours_list = WorkingHours.query.filter_by(
        professional_id=professional_id,
        is_available=True
    ).all()
    working_days = {wh.day_of_week: wh for wh in working_hours_list}

    # Buscar datas bloqueadas
    start_date = datetime.now().date()
    end_date = start_date + timedelta(days=days)
    blocked_dates = ProfessionalBlockedDate.query.filter(
        ProfessionalBlockedDate.professional_id == professional_id,
        ProfessionalBlockedDate.blocked_date.between(start_date, end_date)
    ).all()
    blocked_set = {bd.blocked_date for bd in blocked_dates}

    # Buscar todos os agendamentos do período
    appointments = Appointment.query.filter(
        Appointment.professional_id == professional_id,
        Appointment.appointment_date.between(start_date, end_date),
        Appointment.status.in_(['scheduled', 'confirmed'])
    ).all()

    # Agrupar por data
    appointments_by_date = {}
    for apt in appointments:
        if apt.appointment_date not in appointments_by_date:
            appointments_by_date[apt.appointment_date] = []
        appointments_by_date[apt.appointment_date].append(apt)

    availability = []
    slot_interval = user.booking_slot_interval or 30
    min_advance = timedelta(hours=user.booking_min_advance_hours or 2)
    now = datetime.now()

    for i in range(days):
        check_date = start_date + timedelta(days=i)
        day_of_week = check_date.weekday()

        day_info = {
            'date': check_date.isoformat(),
            'day_of_week': day_of_week,
            'day_name': WorkingHours.DAY_NAMES.get(day_of_week, ''),
            'available': False,
            'slots_count': 0,
            'reason': None
        }

        # Verificar se é data bloqueada
        if check_date in blocked_set:
            day_info['reason'] = 'Data bloqueada'
            availability.append(day_info)
            continue

        # Verificar se profissional trabalha neste dia
        if day_of_week not in working_days:
            day_info['reason'] = 'Não trabalha neste dia'
            availability.append(day_info)
            continue

        wh = working_days[day_of_week]

        # Calcular slots disponíveis
        start_dt = datetime.combine(check_date, wh.start_time)
        end_dt = datetime.combine(check_date, wh.end_time)
        day_appointments = appointments_by_date.get(check_date, [])

        slots_count = 0
        current = start_dt

        while current + timedelta(minutes=service.duration) <= end_dt:
            slot_start = current.time()
            slot_end = (current + timedelta(minutes=service.duration)).time()

            is_available = True

            # Verificar intervalo
            if wh.break_start and wh.break_end:
                if slot_start < wh.break_end and slot_end > wh.break_start:
                    is_available = False

            # Verificar conflitos
            if is_available:
                for apt in day_appointments:
                    if slot_start < apt.end_time and slot_end > apt.start_time:
                        is_available = False
                        break

            # Verificar se não é passado
            if is_available and check_date == now.date():
                min_time = (now + min_advance).time()
                if slot_start <= min_time:
                    is_available = False

            if is_available:
                slots_count += 1

            current += timedelta(minutes=slot_interval)

        day_info['slots_count'] = slots_count
        day_info['available'] = slots_count > 0

        availability.append(day_info)

    return jsonify({
        'professional_id': professional_id,
        'service_id': service_id,
        'service_duration': service.duration,
        'days_checked': days,
        'availability': availability
    }), 200


@public_bp.route('/business/<slug>/appointments', methods=['POST'])
@simple_rate_limit(max_requests=10, window_seconds=60)
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
    user, error = get_business_or_404(slug)
    if error:
        return jsonify(error[0]), error[1]

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

    # Validar antecedência
    now = datetime.now()
    appointment_datetime = datetime.combine(appointment_date, start_time)
    min_advance = timedelta(hours=user.booking_min_advance_hours or 2)
    max_advance = timedelta(days=user.booking_max_advance_days or 30)

    if appointment_datetime < now + min_advance:
        return jsonify({'error': f'Antecedência mínima de {user.booking_min_advance_hours} horas'}), 400

    if appointment_date > (now + max_advance).date():
        return jsonify({'error': f'Antecedência máxima de {user.booking_max_advance_days} dias'}), 400

    # Buscar serviço e profissional (validando pertencimento à empresa)
    service = Service.query.filter_by(id=data['service_id'], user_id=user.id, active=True).first()
    if not service:
        return jsonify({'error': 'Serviço não encontrado'}), 404

    professional = Professional.query.filter_by(id=data['professional_id'], user_id=user.id, active=True).first()
    if not professional:
        return jsonify({'error': 'Profissional não encontrado'}), 404

    # Verificar se é data bloqueada
    if ProfessionalBlockedDate.is_date_blocked(data['professional_id'], appointment_date):
        return jsonify({'error': 'Profissional não disponível nesta data'}), 400

    # Calcular horário de término
    end_datetime = appointment_datetime + timedelta(minutes=service.duration)
    end_time = end_datetime.time()

    # Verificar conflito de horário
    if Appointment.check_conflict(data['professional_id'], appointment_date, start_time, end_time):
        return jsonify({'error': 'Horário não disponível'}), 400

    # Buscar ou criar cliente (associado ao estabelecimento)
    client = Client.query.filter_by(
        phone=client_data['phone'],
        user_id=user.id
    ).first()

    if not client:
        client = Client(
            name=client_data['name'],
            phone=client_data['phone'],
            email=client_data.get('email'),
            user_id=user.id
        )
        db.session.add(client)
        db.session.flush()
    else:
        # Atualizar dados do cliente se necessário
        if client_data.get('email') and not client.email:
            client.email = client_data.get('email')
        # Atualizar nome se mudou
        if client_data.get('name') and client.name != client_data['name']:
            client.name = client_data['name']

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

    # Gerar token de confirmação se necessário
    confirmation_token = None
    if user.booking_require_confirmation:
        confirmation_token = appointment.generate_confirmation_token()

    db.session.add(appointment)
    db.session.commit()

    response_data = {
        'message': 'Agendamento realizado com sucesso!',
        'booking_code': booking_code,
        'appointment': appointment.to_public_dict()
    }

    if confirmation_token:
        response_data['requires_confirmation'] = True
        response_data['confirmation_token'] = confirmation_token
        response_data['message'] = 'Agendamento criado. Confirme através do link enviado.'

    return jsonify(response_data), 201


@public_bp.route('/appointments/<code>', methods=['GET'])
@simple_rate_limit(max_requests=30, window_seconds=60)
@swag_from({
    'tags': ['Agendamento Online'],
    'summary': 'Consultar agendamento',
    'description': 'Consulta detalhes de um agendamento pelo código ou telefone do cliente',
    'parameters': [
        {'name': 'code', 'in': 'path', 'type': 'string', 'required': True, 'description': 'Código do agendamento ou telefone do cliente'},
        {'name': 'business_slug', 'in': 'query', 'type': 'string', 'required': False, 'description': 'Slug do estabelecimento para filtrar agendamentos por telefone'}
    ],
    'responses': {
        200: {'description': 'Dados do agendamento'},
        404: {'description': 'Agendamento não encontrado'}
    }
})
def get_appointment(code):
    """Consulta agendamento pelo código ou telefone"""
    try:
        # Obter slug do estabelecimento para filtro (opcional)
        business_slug = request.args.get('business_slug')
        business_user = None
        if business_slug:
            business_user = User.query.filter_by(slug=business_slug, active=True).first()

        # Primeiro tenta buscar pelo código
        appointment = Appointment.query.filter_by(booking_code=code.upper()).first()

        # Se fornecido business_slug, verificar se o agendamento pertence à empresa
        if appointment and business_user and appointment.user_id != business_user.id:
            appointment = None

        # Se não encontrar, tenta buscar pelo telefone do cliente
        if not appointment:
            # Limpa o telefone removendo caracteres não numéricos para comparação
            phone_clean = ''.join(filter(str.isdigit, code))

            if phone_clean:
                # Busca agendamentos pelo telefone do cliente (mais recentes primeiro)
                query = Appointment.query.join(Client).filter(
                    db.or_(
                        Client.phone == code,
                        Client.phone == phone_clean,
                        Client.phone.like(f'%{phone_clean}%')
                    )
                )

                # Se fornecido business_slug, filtrar apenas pela empresa
                if business_user:
                    query = query.filter(Appointment.user_id == business_user.id)

                appointments = query.order_by(Appointment.appointment_date.desc(), Appointment.start_time.desc()).all()

                if appointments:
                    # Retorna lista de agendamentos encontrados
                    appointments_data = []
                    for apt in appointments:
                        try:
                            appointments_data.append(apt.to_public_dict())
                        except Exception:
                            # Pula agendamentos com dados inconsistentes
                            continue

                    if appointments_data:
                        response = {
                            'appointments': appointments_data,
                            'count': len(appointments_data),
                            'search_type': 'phone'
                        }
                        return jsonify(response), 200

        if not appointment:
            return jsonify({'error': 'Agendamento não encontrado'}), 404

        response = {
            'appointment': appointment.to_public_dict(),
            'search_type': 'code'
        }

        # Adicionar informações de confirmação se pendente
        if appointment.is_confirmation_pending():
            response['requires_confirmation'] = True
            response['confirmation_expired'] = appointment.is_confirmation_expired()

        return jsonify(response), 200
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Erro ao consultar agendamento', 'details': str(e)}), 500


@public_bp.route('/appointments/confirm/<token>', methods=['POST'])
@simple_rate_limit(max_requests=10, window_seconds=60)
@swag_from({
    'tags': ['Agendamento Online'],
    'summary': 'Confirmar agendamento',
    'description': 'Confirma um agendamento usando o token de confirmação',
    'parameters': [
        {'name': 'token', 'in': 'path', 'type': 'string', 'required': True}
    ],
    'responses': {
        200: {'description': 'Agendamento confirmado'},
        400: {'description': 'Token inválido ou expirado'},
        404: {'description': 'Agendamento não encontrado'}
    }
})
def confirm_appointment(token):
    """Confirma agendamento pelo token"""
    appointment = Appointment.find_by_confirmation_token(token)

    if not appointment:
        return jsonify({'error': 'Agendamento não encontrado'}), 404

    result = appointment.confirm_appointment(token)

    if not result['success']:
        return jsonify({'error': result['error']}), 400

    db.session.commit()

    return jsonify({
        'message': result['message'],
        'appointment': appointment.to_public_dict()
    }), 200


@public_bp.route('/appointments/<code>/cancel', methods=['PUT'])
@simple_rate_limit(max_requests=10, window_seconds=60)
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

    # Buscar configurações do estabelecimento
    user = User.query.get(appointment.user_id) if appointment.user_id else None

    # Verificar se cancelamento online é permitido
    if user and not user.booking_allow_cancellation:
        return jsonify({'error': 'Cancelamento online não permitido. Entre em contato com o estabelecimento.'}), 400

    if appointment.status == 'cancelled':
        return jsonify({'error': 'Agendamento já está cancelado'}), 400

    if appointment.status == 'completed':
        return jsonify({'error': 'Não é possível cancelar um agendamento concluído'}), 400

    # Verificar antecedência mínima para cancelamento
    appointment_datetime = datetime.combine(appointment.appointment_date, appointment.start_time)
    now = datetime.now()
    min_hours = user.booking_cancellation_min_hours if user else 2
    time_until_appointment = appointment_datetime - now

    if time_until_appointment < timedelta(hours=min_hours):
        return jsonify({
            'error': f'Não é possível cancelar com menos de {min_hours} horas de antecedência',
            'details': {
                'appointment_datetime': appointment_datetime.isoformat(),
                'current_datetime': now.isoformat(),
                'hours_until_appointment': time_until_appointment.total_seconds() / 3600,
                'min_hours_required': min_hours
            }
        }), 400

    appointment.status = 'cancelled'
    db.session.commit()

    return jsonify({
        'message': 'Agendamento cancelado com sucesso',
        'appointment': appointment.to_public_dict()
    }), 200
