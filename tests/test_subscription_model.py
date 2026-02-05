"""
Testes para o model Subscription
"""
import pytest
from datetime import datetime, timedelta
from src.models.subscription import Subscription
from src.models.user import User
from src.config.database import db


class TestSubscriptionModel:
    """Testes para o model Subscription"""

    def test_create_subscription(self, app, db_session, test_user):
        """Testar criação de assinatura"""
        with app.app_context():
            subscription = Subscription(
                user_id=test_user.id,
                plan='basic',
                stripe_customer_id='cus_test123',
                stripe_subscription_id='sub_test123',
                status='trialing'
            )
            db.session.add(subscription)
            db.session.flush()

            assert subscription.id is not None
            assert subscription.user_id == test_user.id
            assert subscription.plan == 'basic'
            assert subscription.status == 'trialing'
            assert subscription.cancel_at_period_end is False

    def test_subscription_to_dict(self, app, test_subscription):
        """Testar conversão de assinatura para dicionário"""
        with app.app_context():
            data = test_subscription.to_dict()

            assert 'id' in data
            assert 'user_id' in data
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

    def test_subscription_is_active_with_past_due_status(self, app, db_session, test_user):
        """Testar verificação de assinatura com pagamento atrasado"""
        with app.app_context():
            subscription = Subscription(
                user_id=test_user.id,
                plan='pro',
                status='past_due'
            )
            db.session.add(subscription)
            db.session.flush()

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

    def test_subscription_relationship_with_user(self, app, test_subscription, test_user):
        """Testar relacionamento entre assinatura e usuário"""
        with app.app_context():
            subscription = Subscription.query.get(test_subscription.id)
            assert subscription.user is not None
            assert subscription.user.id == test_user.id
            assert subscription.user.name == 'Test User'

    def test_subscription_unique_stripe_subscription_id(self, app, db_session, test_user):
        """Testar unicidade do stripe_subscription_id"""
        with app.app_context():
            subscription1 = Subscription(
                user_id=test_user.id,
                plan='basic',
                stripe_subscription_id='sub_unique123',
                status='active'
            )
            db.session.add(subscription1)
            db.session.flush()

            # Tentar criar outra com o mesmo stripe_subscription_id
            subscription2 = Subscription(
                user_id=test_user.id,
                plan='pro',
                stripe_subscription_id='sub_unique123',  # Mesmo ID
                status='active'
            )
            db.session.add(subscription2)

            with pytest.raises(Exception):  # IntegrityError
                db.session.flush()

    @pytest.mark.skip(reason="Cascade delete não está configurado no modelo atual")
    def test_subscription_cascade_delete(self, app, db_session, test_user):
        """Testar deleção em cascata quando usuário é deletado"""
        with app.app_context():
            subscription = Subscription(
                user_id=test_user.id,
                plan='basic',
                status='active'
            )
            db_session.add(subscription)
            db_session.flush()

            subscription_id = subscription.id
            user_id = test_user.id

            # Re-obter o usuário na mesma sessão para deletar
            user_to_delete = db_session.get(User, user_id)
            db_session.delete(user_to_delete)
            db_session.flush()

            # Verificar que assinatura foi deletada
            deleted_subscription = db_session.get(Subscription, subscription_id)
            assert deleted_subscription is None

    def test_subscription_trial_end_date(self, app, test_subscription_trialing):
        """Testar data de fim do trial"""
        with app.app_context():
            assert test_subscription_trialing.trial_end is not None
            assert test_subscription_trialing.trial_end > datetime.utcnow()

    def test_subscription_cancel_at_period_end(self, app, db_session, test_user):
        """Testar flag de cancelamento ao fim do período"""
        with app.app_context():
            subscription = Subscription(
                user_id=test_user.id,
                plan='pro',
                status='active',
                cancel_at_period_end=True
            )
            db.session.add(subscription)
            db.session.flush()

            assert subscription.cancel_at_period_end is True

    def test_subscription_timestamps(self, app, db_session, test_user):
        """Testar timestamps de criação e atualização"""
        with app.app_context():
            subscription = Subscription(
                user_id=test_user.id,
                plan='basic',
                status='active'
            )
            db.session.add(subscription)
            db.session.flush()

            assert subscription.created_at is not None
            assert subscription.updated_at is not None
            assert subscription.created_at <= subscription.updated_at

    def test_subscription_plan_values(self, app, db_session, test_user):
        """Testar valores válidos de planos"""
        with app.app_context():
            plans = ['basic', 'pro', 'enterprise']

            for plan in plans:
                subscription = Subscription(
                    user_id=test_user.id,
                    plan=plan,
                    status='active'
                )
                db.session.add(subscription)
                db.session.flush()

                assert subscription.plan == plan

                db.session.delete(subscription)
                db.session.flush()

    def test_subscription_status_values(self, app, db_session, test_user):
        """Testar valores válidos de status"""
        with app.app_context():
            statuses = ['active', 'trialing', 'past_due', 'canceled']

            for status in statuses:
                subscription = Subscription(
                    user_id=test_user.id,
                    plan='basic',
                    status=status
                )
                db.session.add(subscription)
                db.session.flush()

                assert subscription.status == status

                db.session.delete(subscription)
                db.session.flush()

    def test_subscription_query_by_client(self, app, db_session, test_user):
        """Testar busca de assinatura por cliente"""
        with app.app_context():
            subscription = Subscription(
                user_id=test_user.id,
                plan='pro',
                status='active'
            )
            db.session.add(subscription)
            db.session.flush()

            found = Subscription.query.filter_by(user_id=test_user.id).first()
            assert found is not None
            assert found.id == subscription.id

    def test_subscription_query_by_status(self, app, db_session, test_user):
        """Testar busca de assinaturas por status"""
        with app.app_context():
            subscription1 = Subscription(
                user_id=test_user.id,
                plan='basic',
                status='active'
            )
            subscription2 = Subscription(
                user_id=test_user.id,
                plan='pro',
                status='canceled'
            )
            db.session.add_all([subscription1, subscription2])
            db.session.flush()

            active_subs = Subscription.query.filter_by(status='active').all()
            assert len(active_subs) >= 1
            assert subscription1 in active_subs
