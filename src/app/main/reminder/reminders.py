from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required
from flasgger import swag_from

reminders_bp = Blueprint('reminders', __name__)


@reminders_bp.route('/stats', methods=['GET'])
@jwt_required()
@swag_from({
    'tags': ['Lembretes'],
    'summary': 'Estatisticas de lembretes',
    'description': 'Retorna estatisticas dos lembretes (funcionalidade em desenvolvimento)',
    'security': [{'Bearer': []}],
    'responses': {
        200: {
            'description': 'Estatisticas dos lembretes',
            'schema': {
                'type': 'object',
                'properties': {
                    'total': {'type': 'integer'},
                    'pending': {'type': 'integer'},
                    'sent': {'type': 'integer'},
                    'failed': {'type': 'integer'},
                    'message': {'type': 'string'}
                }
            }
        }
    }
})
def get_stats():
    """Retorna estatisticas dos lembretes (placeholder)"""
    return jsonify({
        'total': 0,
        'pending': 0,
        'sent': 0,
        'failed': 0,
        'message': 'Funcionalidade de lembretes em desenvolvimento'
    }), 200


@reminders_bp.route('/', methods=['GET'])
@jwt_required()
@swag_from({
    'tags': ['Lembretes'],
    'summary': 'Listar lembretes',
    'description': 'Lista todos os lembretes (funcionalidade em desenvolvimento)',
    'security': [{'Bearer': []}],
    'parameters': [
        {'name': 'page', 'in': 'query', 'type': 'integer', 'default': 1},
        {'name': 'per_page', 'in': 'query', 'type': 'integer', 'default': 20}
    ],
    'responses': {
        200: {
            'description': 'Lista de lembretes',
            'schema': {
                'type': 'object',
                'properties': {
                    'reminders': {'type': 'array', 'items': {'type': 'object'}},
                    'pagination': {'$ref': '#/definitions/Pagination'},
                    'message': {'type': 'string'}
                }
            }
        }
    }
})
def list_reminders():
    """Lista lembretes (placeholder)"""
    return jsonify({
        'reminders': [],
        'pagination': {
            'page': 1,
            'pages': 0,
            'per_page': 20,
            'total': 0
        },
        'message': 'Funcionalidade de lembretes em desenvolvimento'
    }), 200


@reminders_bp.route('/scheduler/status', methods=['GET'])
@jwt_required()
@swag_from({
    'tags': ['Lembretes'],
    'summary': 'Status do agendador de lembretes',
    'description': 'Retorna o status do agendador (funcionalidade em desenvolvimento)',
    'security': [{'Bearer': []}],
    'responses': {
        200: {
            'description': 'Status do agendador',
            'schema': {
                'type': 'object',
                'properties': {
                    'running': {'type': 'boolean'},
                    'next_run': {'type': 'string'},
                    'message': {'type': 'string'}
                }
            }
        }
    }
})
def scheduler_status():
    """Status do agendador de lembretes (placeholder)"""
    return jsonify({
        'running': False,
        'next_run': None,
        'message': 'Funcionalidade de lembretes em desenvolvimento'
    }), 200
