from src.config.database import db
from datetime import datetime

class Subscription(db.Model):
    __tablename__ = 'subscriptions'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    plan = db.Column(db.String(50), nullable=False)  # basic, pro, enterprise
    stripe_customer_id = db.Column(db.String(100))
    stripe_subscription_id = db.Column(db.String(100), unique=True)
    status = db.Column(db.String(20), nullable=False, default='trialing')  # active, past_due, canceled, trialing
    start_date = db.Column(db.DateTime, default=datetime.utcnow)
    end_date = db.Column(db.DateTime)
    trial_end = db.Column(db.DateTime)
    cancel_at_period_end = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relacionamento com User
    user = db.relationship('User', backref=db.backref('subscription', uselist=False))

    def to_dict(self):
        """Converte o objeto para dicionário"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'plan': self.plan,
            'stripe_customer_id': self.stripe_customer_id,
            'stripe_subscription_id': self.stripe_subscription_id,
            'status': self.status,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'trial_end': self.trial_end.isoformat() if self.trial_end else None,
            'cancel_at_period_end': self.cancel_at_period_end,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    def is_active(self):
        """Verifica se a assinatura está ativa"""
        return self.status in ['active', 'trialing']

    def can_access_feature(self, required_plans=None):
        """Verifica se a assinatura pode acessar uma feature específica"""
        if not self.is_active():
            return False
        if not required_plans:
            return True
        return self.plan in required_plans
