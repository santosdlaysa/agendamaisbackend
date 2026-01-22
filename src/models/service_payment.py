from src.config.database import db
from datetime import datetime


class ServicePayment(db.Model):
    """Modelo para rastrear pagamentos de serviços via Stripe"""
    __tablename__ = 'service_payments'

    id = db.Column(db.Integer, primary_key=True)
    appointment_id = db.Column(db.Integer, db.ForeignKey('appointments.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)  # Estabelecimento
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'), nullable=False)

    # Dados do Stripe
    stripe_checkout_session_id = db.Column(db.String(100), unique=True, nullable=True)
    stripe_payment_intent_id = db.Column(db.String(100), unique=True, nullable=True)

    # Valores
    amount = db.Column(db.Numeric(10, 2), nullable=False)  # Valor cobrado
    currency = db.Column(db.String(3), default='BRL')

    # Tipo de pagamento
    payment_type = db.Column(db.String(20), default='full')  # 'full' ou 'deposit'
    deposit_percentage = db.Column(db.Integer, nullable=True)  # Se deposit, qual porcentagem

    # Status do pagamento
    status = db.Column(db.String(20), default='pending')  # 'pending', 'paid', 'failed', 'refunded', 'expired'

    # Timestamps
    paid_at = db.Column(db.DateTime, nullable=True)
    refunded_at = db.Column(db.DateTime, nullable=True)
    expires_at = db.Column(db.DateTime, nullable=True)  # Quando a sessão de checkout expira
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Metadados
    payment_method_type = db.Column(db.String(50), nullable=True)  # 'card', 'pix', etc
    failure_reason = db.Column(db.Text, nullable=True)

    # Relacionamentos
    appointment = db.relationship('Appointment', backref=db.backref('service_payments', lazy=True))
    user = db.relationship('User', backref=db.backref('service_payments', lazy=True))
    client = db.relationship('Client', backref=db.backref('service_payments', lazy=True))

    def to_dict(self):
        """Converte o objeto para dicionário"""
        return {
            'id': self.id,
            'appointment_id': self.appointment_id,
            'user_id': self.user_id,
            'client_id': self.client_id,
            'stripe_checkout_session_id': self.stripe_checkout_session_id,
            'stripe_payment_intent_id': self.stripe_payment_intent_id,
            'amount': float(self.amount) if self.amount else None,
            'currency': self.currency,
            'payment_type': self.payment_type,
            'deposit_percentage': self.deposit_percentage,
            'status': self.status,
            'payment_method_type': self.payment_method_type,
            'paid_at': self.paid_at.isoformat() if self.paid_at else None,
            'refunded_at': self.refunded_at.isoformat() if self.refunded_at else None,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    def mark_as_paid(self, payment_intent_id=None, payment_method_type=None):
        """Marca o pagamento como pago"""
        self.status = 'paid'
        self.paid_at = datetime.utcnow()
        if payment_intent_id:
            self.stripe_payment_intent_id = payment_intent_id
        if payment_method_type:
            self.payment_method_type = payment_method_type
        self.updated_at = datetime.utcnow()

    def mark_as_failed(self, reason=None):
        """Marca o pagamento como falhou"""
        self.status = 'failed'
        if reason:
            self.failure_reason = reason
        self.updated_at = datetime.utcnow()

    def mark_as_refunded(self):
        """Marca o pagamento como reembolsado"""
        self.status = 'refunded'
        self.refunded_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    @staticmethod
    def find_by_checkout_session(session_id):
        """Busca pagamento pelo ID da sessão de checkout"""
        return ServicePayment.query.filter_by(stripe_checkout_session_id=session_id).first()

    @staticmethod
    def find_by_payment_intent(payment_intent_id):
        """Busca pagamento pelo ID do payment intent"""
        return ServicePayment.query.filter_by(stripe_payment_intent_id=payment_intent_id).first()
