from src.config.database import db
from datetime import datetime

class Payment(db.Model):
    __tablename__ = 'payments'

    id = db.Column(db.Integer, primary_key=True)
    subscription_id = db.Column(db.Integer, db.ForeignKey('subscriptions.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    # Stripe IDs
    stripe_invoice_id = db.Column(db.String(100), unique=True)
    stripe_payment_intent_id = db.Column(db.String(100))

    # Valores
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    currency = db.Column(db.String(3), default='brl')

    # Status e datas
    status = db.Column(db.String(50), default='paid')
    paid_at = db.Column(db.DateTime)
    period_start = db.Column(db.DateTime)
    period_end = db.Column(db.DateTime)

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relacionamentos
    subscription = db.relationship('Subscription', backref=db.backref('payments', lazy=True))
    user = db.relationship('User', backref=db.backref('payments', lazy=True))

    def to_dict(self):
        """Converte o objeto para dicionário"""
        return {
            'id': self.id,
            'subscription_id': self.subscription_id,
            'user_id': self.user_id,
            'stripe_invoice_id': self.stripe_invoice_id,
            'stripe_payment_intent_id': self.stripe_payment_intent_id,
            'amount': float(self.amount) if self.amount else None,
            'currency': self.currency,
            'status': self.status,
            'paid_at': self.paid_at.isoformat() if self.paid_at else None,
            'period_start': self.period_start.isoformat() if self.period_start else None,
            'period_end': self.period_end.isoformat() if self.period_end else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
