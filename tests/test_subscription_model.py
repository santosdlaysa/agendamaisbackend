"""
Testes para o model Subscription
"""
import pytest
from datetime import datetime, timedelta
from src.models.subscription import Subscription
from src.config.database import db


class TestSubscriptionModel:
    """Testes para o model Subscription"""

    def test_create_subscription(self, app, db_session, test_client_user):
        """Testar criação de assinatura"""
        with app.app_context():
            subscription = Subscription(
                client_id=test_client_user.id,
                plan='basic',
                stripe_customer_id='cus_test123',
                stripe_subscription_id='sub_test123',
                status='trialing'
            )
            db.session.add(subscription)
            db.session.commit()

            assert subscription.id is not None
            assert subscription.client_id == test_client_user.id
            assert subscription.plan == 'basic'
            assert subscription.status == 'trialing'
            assert subscription.cancel_at_period_end is False

    def test_subscription_to_dict(self, app, test_subscription):
        """Testar conversão de assinatura para dicionário"""
        with app.app_context():
            data = test_subscription.to_dict()

            assert 'id' in data
            assert 'client_id' in data
            assert 'plan' in data
            assert 'status' in data
            assert 'stripe_customer_id' in data
            assert 'stripe_subscription_id' in data
            assert data['plan'] == 'pro'
            assert data['status'] == 'active'

    def test_subscription_is_active_with_active_status(self, app, test_subscription):
        """Testar verificação de assinatura ativa"""
        with app.app_context():
            assert test_subscription.is_active() is True

    def test_subscription_is_active_with_trialing_status(self, app, test_subscription_trialing):
        """Testar verificação de assinatura em trial"""
        with app.app_context():
            assert test_subscription_trialing.is_active() is True

    def test_subscription_is_active_with_canceled_status(self, app, test_subscription_canceled):
        """Testar verificação de assinatura cancelada"""
        with app.app_context():
            assert test_subscription_canceled.is_active() is False

    def test_subscription_is_active_with_past_due_status(self, app, db_session, test_client_user):
        """Testar verificação de assinatura com pagamento atrasado"""
        with app.app_context():
            subscription = Subscription(
                client_id=test_client_user.id,
                plan='pro',
                status='past_due'
            )
            db.session.add(subscription)
            db.session.commit()

            assert subscription.is_active() is False

    def test_can_access_feature_without_required_plans(self, app, test_subscription):
        """Testar acesso a feature sem planos específicos"""
        with app.app_context():
            assert test_subscription.can_access_feature() is True

    def test_can_access_feature_with_matching_plan(self, app, test_subscription):
        """Testar acesso a feature com plano correspondente"""
        with app.app_context():
            assert test_subscription.can_access_feature(['pro', 'enterprise']) is True

    def test_can_access_feature_with_non_matching_plan(self, app, test_subscription_basic):
        """Testar acesso negado a feature com plano não correspondente"""
        with app.app_context():
            assert test_subscription_basic.can_access_feature(['pro', 'enterprise']) is False

    def test_can_access_feature_with_inactive_subscription(self, app, test_subscription_canceled):
        """Testar acesso negado com assinatura inativa"""
        with app.app_context():
            assert test_subscription_canceled.can_access_feature() is False

    def test_subscription_relationship_with_client(self, app, test_subscription, test_client_user):
        """Testar relacionamento entre assinatura e cliente"""
        with app.app_context():
            subscription = Subscription.query.get(test_subscription.id)
            assert subscription.client is not None
            assert subscription.client.id == test_client_user.id
            assert subscription.client.name == 'Test Client'

    def test_subscription_unique_stripe_subscription_id(self, app, db_session, test_client_user):
        """Testar unicidade do stripe_subscription_id"""
        with app.app_context():
            subscription1 = Subscription(
                client_id=test_client_user.id,
                plan='basic',
                stripe_subscription_id='sub_unique123',
                status='active'
            )
            db.session.add(subscription1)
            db.session.commit()

            # Tentar criar outra com o mesmo stripe_subscription_id
            subscription2 = Subscription(
                client_id=test_client_user.id,
                plan='pro',
                stripe_subscription_id='sub_unique123',  # Mesmo ID
                status='active'
            )
            db.session.add(subscription2)

            with pytest.raises(Exception):  # IntegrityError
                db.session.commit()

    def test_subscription_cascade_delete(self, app, db_session, test_client_user):
        """Testar deleção em cascata quando cliente é deletado"""
        with app.app_context():
            subscription = Subscription(
                client_id=test_client_user.id,
                plan='basic',
                status='active'
            )
            db.session.add(subscription)
            db.session.commit()

            subscription_id = subscription.id

            # Deletar cliente
            db.session.delete(test_client_user)
            db.session.commit()

            # Verificar que assinatura foi deletada
            deleted_subscription = Subscription.query.get(subscription_id)
            assert deleted_subscription is None

    def test_subscription_trial_end_date(self, app, test_subscription_trialing):
        """Testar data de fim do trial"""
        with app.app_context():
            assert test_subscription_trialing.trial_end is not None
            assert test_subscription_trialing.trial_end > datetime.utcnow()

    def test_subscription_cancel_at_period_end(self, app, db_session, test_client_user):
        """Testar flag de cancelamento ao fim do período"""
        with app.app_context():
            subscription = Subscription(
                client_id=test_client_user.id,
                plan='pro',
                status='active',
                cancel_at_period_end=True
            )
            db.session.add(subscription)
            db.session.commit()

            assert subscription.cancel_at_period_end is True

    def test_subscription_timestamps(self, app, db_session, test_client_user):
        """Testar timestamps de criação e atualização"""
        with app.app_context():
            subscription = Subscription(
                client_id=test_client_user.id,
                plan='basic',
                status='active'
            )
            db.session.add(subscription)
            db.session.commit()

            assert subscription.created_at is not None
            assert subscription.updated_at is not None
            assert subscription.created_at <= subscription.updated_at

    def test_subscription_plan_values(self, app, db_session, test_client_user):
        """Testar valores válidos de planos"""
        with app.app_context():
            plans = ['basic', 'pro', 'enterprise']

            for plan in plans:
                subscription = Subscription(
                    client_id=test_client_user.id,
                    plan=plan,
                    status='active'
                )
                db.session.add(subscription)
                db.session.commit()

                assert subscription.plan == plan

                db.session.delete(subscription)
                db.session.commit()

    def test_subscription_status_values(self, app, db_session, test_client_user):
        """Testar valores válidos de status"""
        with app.app_context():
            statuses = ['active', 'trialing', 'past_due', 'canceled']

            for status in statuses:
                subscription = Subscription(
                    client_id=test_client_user.id,
                    plan='basic',
                    status=status
                )
                db.session.add(subscription)
                db.session.commit()

                assert subscription.status == status

                db.session.delete(subscription)
                db.session.commit()

    def test_subscription_query_by_client(self, app, db_session, test_client_user):
        """Testar busca de assinatura por cliente"""
        with app.app_context():
            subscription = Subscription(
                client_id=test_client_user.id,
                plan='pro',
                status='active'
            )
            db.session.add(subscription)
            db.session.commit()

            found = Subscription.query.filter_by(client_id=test_client_user.id).first()
            assert found is not None
            assert found.id == subscription.id

    def test_subscription_query_by_status(self, app, db_session, test_client_user):
        """Testar busca de assinaturas por status"""
        with app.app_context():
            subscription1 = Subscription(
                client_id=test_client_user.id,
                plan='basic',
                status='active'
            )
            subscription2 = Subscription(
                client_id=test_client_user.id,
                plan='pro',
                status='canceled'
            )
            db.session.add_all([subscription1, subscription2])
            db.session.commit()

            active_subs = Subscription.query.filter_by(status='active').all()
            assert len(active_subs) >= 1
            assert subscription1 in active_subs
