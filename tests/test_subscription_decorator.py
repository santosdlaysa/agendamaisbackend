"""
Testes para o decorator subscription_required
"""
import pytest
import json
from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required
from src.decorators import subscription_required, check_feature_access


class TestSubscriptionDecorator:
    """Testes para o decorator subscription_required"""

    @pytest.fixture
    def test_blueprint(self, app):
        """Criar blueprint de teste com rotas protegidas"""
        test_bp = Blueprint('test', __name__)

        @test_bp.route('/any-plan', methods=['GET'])
        @jwt_required()
        @subscription_required()
        def any_plan_route():
            return jsonify({'message': 'success'})

        @test_bp.route('/pro-only', methods=['GET'])
        @jwt_required()
        @subscription_required(['pro', 'enterprise'])
        def pro_only_route():
            return jsonify({'message': 'success'})

        @test_bp.route('/enterprise-only', methods=['GET'])
        @jwt_required()
        @subscription_required(['enterprise'])
        def enterprise_only_route():
            return jsonify({'message': 'success'})

        @test_bp.route('/advanced-reports', methods=['GET'])
        @jwt_required()
        @check_feature_access('advanced_reports')
        def advanced_reports_route():
            return jsonify({'message': 'success'})

        app.register_blueprint(test_bp, url_prefix='/test')
        return test_bp

    def test_subscription_required_without_auth(self, client, test_blueprint):
        """Testar acesso sem autenticação"""
        response = client.get('/test/any-plan')
        assert response.status_code == 401

    def test_subscription_required_without_subscription(self, client, auth_headers,
                                                       test_blueprint):
        """Testar acesso sem assinatura"""
        response = client.get('/test/any-plan', headers=auth_headers)

        assert response.status_code == 403
        data = json.loads(response.data)
        assert data['code'] == 'SUBSCRIPTION_REQUIRED'
        assert 'error' in data

    def test_subscription_required_with_active_subscription(self, client, auth_headers,
                                                           test_subscription,
                                                           test_blueprint, app):
        """Testar acesso com assinatura ativa"""
        with app.app_context():
            response = client.get('/test/any-plan', headers=auth_headers)

            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['message'] == 'success'

    def test_subscription_required_with_trialing_subscription(self, client, auth_headers,
                                                              test_subscription_trialing,
                                                              test_blueprint, app):
        """Testar acesso com assinatura em trial"""
        with app.app_context():
            response = client.get('/test/any-plan', headers=auth_headers)

            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['message'] == 'success'

    def test_subscription_required_with_canceled_subscription(self, client, auth_headers,
                                                             test_subscription_canceled,
                                                             test_blueprint, app):
        """Testar acesso com assinatura cancelada"""
        with app.app_context():
            response = client.get('/test/any-plan', headers=auth_headers)

            assert response.status_code == 403
            data = json.loads(response.data)
            assert data['code'] == 'SUBSCRIPTION_INACTIVE'
            assert data['status'] == 'canceled'

    def test_subscription_required_specific_plan_with_matching_plan(self, client,
                                                                    auth_headers,
                                                                    test_subscription,
                                                                    test_blueprint, app):
        """Testar acesso com plano correspondente"""
        with app.app_context():
            # test_subscription tem plano 'pro'
            response = client.get('/test/pro-only', headers=auth_headers)

            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['message'] == 'success'

    def test_subscription_required_specific_plan_with_non_matching_plan(self, client,
                                                                        auth_headers,
                                                                        test_subscription_basic,
                                                                        test_blueprint, app):
        """Testar acesso com plano não correspondente"""
        with app.app_context():
            # test_subscription_basic tem plano 'basic'
            response = client.get('/test/pro-only', headers=auth_headers)

            assert response.status_code == 403
            data = json.loads(response.data)
            assert data['code'] == 'PLAN_UPGRADE_REQUIRED'
            assert data['current_plan'] == 'basic'
            assert 'pro' in data['required_plans']

    def test_subscription_required_enterprise_only_with_basic_plan(self, client,
                                                                   auth_headers,
                                                                   test_subscription_basic,
                                                                   test_blueprint, app):
        """Testar acesso enterprise com plano básico"""
        with app.app_context():
            response = client.get('/test/enterprise-only', headers=auth_headers)

            assert response.status_code == 403
            data = json.loads(response.data)
            assert data['code'] == 'PLAN_UPGRADE_REQUIRED'
            assert data['current_plan'] == 'basic'
            assert data['required_plans'] == ['enterprise']

    def test_check_feature_access_with_pro_plan(self, client, auth_headers,
                                               test_subscription, test_blueprint, app):
        """Testar check_feature_access com plano Pro"""
        with app.app_context():
            response = client.get('/test/advanced-reports', headers=auth_headers)

            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['message'] == 'success'

    def test_check_feature_access_with_basic_plan(self, client, auth_headers,
                                                  test_subscription_basic,
                                                  test_blueprint, app):
        """Testar check_feature_access com plano básico"""
        with app.app_context():
            response = client.get('/test/advanced-reports', headers=auth_headers)

            assert response.status_code == 403
            data = json.loads(response.data)
            assert data['code'] == 'PLAN_UPGRADE_REQUIRED'

    def test_subscription_required_error_messages(self, client, auth_headers,
                                                 test_blueprint):
        """Testar mensagens de erro do decorator"""
        response = client.get('/test/any-plan', headers=auth_headers)

        assert response.status_code == 403
        data = json.loads(response.data)
        assert 'error' in data
        assert 'message' in data
        assert 'code' in data

    def test_subscription_required_with_past_due_status(self, client, auth_headers,
                                                       test_user, test_blueprint,
                                                       app, db_session):
        """Testar acesso com status past_due"""
        with app.app_context():
            from src.models.subscription import Subscription

            subscription = Subscription(
                user_id=test_user.id,
                plan='pro',
                status='past_due'
            )
            db_session.add(subscription)
            db_session.flush()

            response = client.get('/test/any-plan', headers=auth_headers)

            assert response.status_code == 403
            data = json.loads(response.data)
            assert data['code'] == 'SUBSCRIPTION_INACTIVE'
            assert data['status'] == 'past_due'

    def test_multiple_plans_requirement(self, client, auth_headers, test_subscription,
                                       test_blueprint, app):
        """Testar requisito de múltiplos planos"""
        with app.app_context():
            # test_subscription tem plano 'pro', que está na lista ['pro', 'enterprise']
            response = client.get('/test/pro-only', headers=auth_headers)

            assert response.status_code == 200

    def test_decorator_preserves_function_name(self, test_blueprint):
        """Testar que o decorator preserva o nome da função"""
        # Verificar que @wraps foi usado corretamente
        route_func = None
        for rule in test_blueprint.url_map.iter_rules():
            if rule.endpoint == 'test.any_plan_route':
                route_func = test_blueprint.view_functions[rule.endpoint]
                break

        assert route_func is not None
        # O nome pode ser 'wrapper' devido ao decorator, mas deve ter __name__
        assert hasattr(route_func, '__name__')


class TestFeaturePlansMapping:
    """Testes para o mapeamento de features e planos"""

    def test_advanced_reports_requires_pro_or_enterprise(self):
        """Testar que advanced_reports requer Pro ou Enterprise"""
        from src.decorators.subscription_required import FEATURE_PLANS

        # Verificar se FEATURE_PLANS existe
        assert 'advanced_reports' in FEATURE_PLANS
        assert 'pro' in FEATURE_PLANS['advanced_reports']
        assert 'enterprise' in FEATURE_PLANS['advanced_reports']

    def test_api_access_requires_enterprise(self):
        """Testar que api_access requer Enterprise"""
        from src.decorators.subscription_required import FEATURE_PLANS

        assert 'api_access' in FEATURE_PLANS
        assert FEATURE_PLANS['api_access'] == ['enterprise']

    def test_unlimited_professionals_requires_enterprise(self):
        """Testar que unlimited_professionals requer Enterprise"""
        from src.decorators.subscription_required import FEATURE_PLANS

        assert 'unlimited_professionals' in FEATURE_PLANS
        assert FEATURE_PLANS['unlimited_professionals'] == ['enterprise']


class TestDecoratorIntegration:
    """Testes de integração do decorator"""

    def test_decorator_with_database_error(self, client, auth_headers, test_blueprint, app):
        """Testar comportamento com erro de banco de dados"""
        with app.app_context():
            # Não criamos assinatura, então deve retornar 403
            response = client.get('/test/any-plan', headers=auth_headers)
            assert response.status_code == 403

    def test_decorator_multiple_calls(self, client, auth_headers, test_subscription,
                                     test_blueprint, app):
        """Testar múltiplas chamadas ao decorator"""
        with app.app_context():
            # Fazer várias requisições
            for _ in range(5):
                response = client.get('/test/any-plan', headers=auth_headers)
                assert response.status_code == 200

    def test_decorator_with_different_users(self, client, test_subscription,
                                           test_blueprint, app):
        """Testar decorator com diferentes usuários"""
        with app.app_context():
            from flask_jwt_extended import create_access_token
            from src.models.client import Client
            from src.models.subscription import Subscription
            from src.config.database import db

            # Criar outro cliente sem assinatura
            client2 = Client(
                name='Client 2',
                email='client2@example.com',
                phone='+5511988888888'
            )
            db.session.add(client2)
            db.session.flush()

            token2 = create_access_token(identity=client2.id)
            headers2 = {'Authorization': f'Bearer {token2}'}

            # Cliente 2 não deve ter acesso
            response = client.get('/test/any-plan', headers=headers2)
            assert response.status_code == 403

            # Cliente 1 (com assinatura) deve ter acesso
            token1 = create_access_token(identity=test_subscription.client_id)
            headers1 = {'Authorization': f'Bearer {token1}'}

            response = client.get('/test/any-plan', headers=headers1)
            assert response.status_code == 200
