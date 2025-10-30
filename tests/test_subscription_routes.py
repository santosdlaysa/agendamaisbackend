"""
Testes para as rotas de subscription
"""
import pytest
import json
from unittest.mock import patch, MagicMock
from src.models.subscription import Subscription


class TestSubscriptionRoutes:
    """Testes para as rotas de assinaturas"""

    def test_get_plans(self, client):
        """Testar listagem de planos"""
        response = client.get('/api/subscriptions/plans')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'plans' in data
        assert len(data['plans']) == 3

        # Verificar estrutura dos planos
        for plan in data['plans']:
            assert 'id' in plan
            assert 'name' in plan
            assert 'price' in plan
            assert 'features' in plan

    def test_get_subscription_status_without_auth(self, client):
        """Testar status sem autenticação"""
        response = client.get('/api/subscriptions/status')
        assert response.status_code == 401

    def test_get_subscription_status_without_subscription(self, client, auth_headers):
        """Testar status quando não tem assinatura"""
        response = client.get('/api/subscriptions/status', headers=auth_headers)

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['has_subscription'] is False

    def test_get_subscription_status_with_subscription(self, client, auth_headers, test_subscription, app):
        """Testar status com assinatura ativa"""
        with app.app_context():
            with patch('stripe.Subscription.retrieve') as mock_retrieve:
                mock_retrieve.return_value = MagicMock(
                    status='active',
                    cancel_at_period_end=False
                )

                response = client.get('/api/subscriptions/status', headers=auth_headers)

                assert response.status_code == 200
                data = json.loads(response.data)
                assert data['has_subscription'] is True
                assert 'subscription' in data
                assert data['subscription']['plan'] == 'pro'
                assert data['subscription']['status'] == 'active'

    @patch('stripe.Customer.create')
    @patch('stripe.Subscription.create')
    def test_create_subscription_success(self, mock_sub_create, mock_cust_create,
                                        client, auth_headers, app, db_session):
        """Testar criação de assinatura com sucesso"""
        with app.app_context():
            # Mock Stripe responses
            mock_cust_create.return_value = MagicMock(id='cus_test123')
            mock_sub_create.return_value = MagicMock(
                id='sub_test123',
                status='trialing',
                latest_invoice=MagicMock(
                    payment_intent=MagicMock(
                        client_secret='pi_secret_123'
                    )
                )
            )

            response = client.post(
                '/api/subscriptions/subscribe',
                headers=auth_headers,
                json={'plan': 'pro'}
            )

            assert response.status_code == 201
            data = json.loads(response.data)
            assert 'subscription_id' in data
            assert 'stripe_subscription_id' in data
            assert data['status'] == 'trialing'
            assert 'trial_end' in data

    def test_create_subscription_without_auth(self, client):
        """Testar criação sem autenticação"""
        response = client.post(
            '/api/subscriptions/subscribe',
            json={'plan': 'pro'}
        )
        assert response.status_code == 401

    def test_create_subscription_invalid_plan(self, client, auth_headers):
        """Testar criação com plano inválido"""
        response = client.post(
            '/api/subscriptions/subscribe',
            headers=auth_headers,
            json={'plan': 'invalid_plan'}
        )

        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data

    def test_create_subscription_with_existing_active(self, client, auth_headers,
                                                     test_subscription, app):
        """Testar criação quando já tem assinatura ativa"""
        with app.app_context():
            response = client.post(
                '/api/subscriptions/subscribe',
                headers=auth_headers,
                json={'plan': 'enterprise'}
            )

            assert response.status_code == 400
            data = json.loads(response.data)
            assert 'error' in data
            assert 'já existe' in data['error'].lower()

    @patch('stripe.Subscription.modify')
    def test_cancel_subscription_success(self, mock_modify, client, auth_headers,
                                        test_subscription, app):
        """Testar cancelamento de assinatura com sucesso"""
        with app.app_context():
            mock_modify.return_value = MagicMock(cancel_at_period_end=True)

            response = client.post(
                '/api/subscriptions/cancel',
                headers=auth_headers
            )

            assert response.status_code == 200
            data = json.loads(response.data)
            assert 'message' in data
            assert data['subscription']['cancel_at_period_end'] is True

    def test_cancel_subscription_without_auth(self, client):
        """Testar cancelamento sem autenticação"""
        response = client.post('/api/subscriptions/cancel')
        assert response.status_code == 401

    def test_cancel_subscription_without_subscription(self, client, auth_headers):
        """Testar cancelamento sem ter assinatura"""
        response = client.post('/api/subscriptions/cancel', headers=auth_headers)

        assert response.status_code == 404
        data = json.loads(response.data)
        assert 'error' in data

    def test_cancel_subscription_already_canceled(self, client, auth_headers,
                                                  test_subscription_canceled, app):
        """Testar cancelamento de assinatura já cancelada"""
        with app.app_context():
            response = client.post(
                '/api/subscriptions/cancel',
                headers=auth_headers
            )

            assert response.status_code == 400
            data = json.loads(response.data)
            assert 'error' in data

    @patch('stripe.Subscription.modify')
    def test_reactivate_subscription_success(self, mock_modify, client, auth_headers,
                                            test_subscription, app, db_session):
        """Testar reativação de assinatura"""
        with app.app_context():
            # Marcar como cancelada
            subscription = Subscription.query.filter_by(
                client_id=test_subscription.client_id
            ).first()
            subscription.cancel_at_period_end = True
            db_session.commit()

            mock_modify.return_value = MagicMock(cancel_at_period_end=False)

            response = client.post(
                '/api/subscriptions/reactivate',
                headers=auth_headers
            )

            assert response.status_code == 200
            data = json.loads(response.data)
            assert 'message' in data
            assert data['subscription']['cancel_at_period_end'] is False

    def test_reactivate_subscription_without_cancelation(self, client, auth_headers,
                                                        test_subscription, app):
        """Testar reativação quando não está marcada para cancelamento"""
        with app.app_context():
            response = client.post(
                '/api/subscriptions/reactivate',
                headers=auth_headers
            )

            assert response.status_code == 400
            data = json.loads(response.data)
            assert 'error' in data

    @patch('stripe.Webhook.construct_event')
    def test_webhook_invoice_paid(self, mock_construct, client, test_subscription,
                                  app, db_session):
        """Testar webhook de pagamento bem-sucedido"""
        with app.app_context():
            mock_construct.return_value = {
                'type': 'invoice.paid',
                'data': {
                    'object': {
                        'subscription': test_subscription.stripe_subscription_id
                    }
                }
            }

            response = client.post(
                '/api/subscriptions/webhook',
                data=json.dumps({'test': 'data'}),
                headers={'Stripe-Signature': 'test_signature'}
            )

            assert response.status_code == 200

            # Verificar que o status foi atualizado
            subscription = Subscription.query.get(test_subscription.id)
            assert subscription.status == 'active'

    @patch('stripe.Webhook.construct_event')
    def test_webhook_payment_failed(self, mock_construct, client, test_subscription,
                                   app, db_session):
        """Testar webhook de falha no pagamento"""
        with app.app_context():
            mock_construct.return_value = {
                'type': 'invoice.payment_failed',
                'data': {
                    'object': {
                        'subscription': test_subscription.stripe_subscription_id
                    }
                }
            }

            response = client.post(
                '/api/subscriptions/webhook',
                data=json.dumps({'test': 'data'}),
                headers={'Stripe-Signature': 'test_signature'}
            )

            assert response.status_code == 200

            # Verificar que o status foi atualizado
            subscription = Subscription.query.get(test_subscription.id)
            assert subscription.status == 'past_due'

    @patch('stripe.Webhook.construct_event')
    def test_webhook_subscription_deleted(self, mock_construct, client,
                                         test_subscription, app, db_session):
        """Testar webhook de assinatura cancelada"""
        with app.app_context():
            mock_construct.return_value = {
                'type': 'customer.subscription.deleted',
                'data': {
                    'object': {
                        'id': test_subscription.stripe_subscription_id
                    }
                }
            }

            response = client.post(
                '/api/subscriptions/webhook',
                data=json.dumps({'test': 'data'}),
                headers={'Stripe-Signature': 'test_signature'}
            )

            assert response.status_code == 200

            # Verificar que o status foi atualizado
            subscription = Subscription.query.get(test_subscription.id)
            assert subscription.status == 'canceled'
            assert subscription.end_date is not None

    @patch('stripe.Webhook.construct_event')
    def test_webhook_subscription_updated(self, mock_construct, client,
                                         test_subscription, app, db_session):
        """Testar webhook de atualização de assinatura"""
        with app.app_context():
            mock_construct.return_value = {
                'type': 'customer.subscription.updated',
                'data': {
                    'object': {
                        'id': test_subscription.stripe_subscription_id,
                        'status': 'past_due',
                        'cancel_at_period_end': True
                    }
                }
            }

            response = client.post(
                '/api/subscriptions/webhook',
                data=json.dumps({'test': 'data'}),
                headers={'Stripe-Signature': 'test_signature'}
            )

            assert response.status_code == 200

            # Verificar que foi atualizado
            subscription = Subscription.query.get(test_subscription.id)
            assert subscription.status == 'past_due'
            assert subscription.cancel_at_period_end is True

    def test_webhook_invalid_signature(self, client):
        """Testar webhook com assinatura inválida"""
        with patch('stripe.Webhook.construct_event') as mock_construct:
            mock_construct.side_effect = Exception('Invalid signature')

            response = client.post(
                '/api/subscriptions/webhook',
                data=json.dumps({'test': 'data'}),
                headers={'Stripe-Signature': 'invalid'}
            )

            assert response.status_code == 400

    def test_webhook_invalid_payload(self, client):
        """Testar webhook com payload inválido"""
        with patch('stripe.Webhook.construct_event') as mock_construct:
            mock_construct.side_effect = ValueError('Invalid payload')

            response = client.post(
                '/api/subscriptions/webhook',
                data='invalid',
                headers={'Stripe-Signature': 'test'}
            )

            assert response.status_code == 400
