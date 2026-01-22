import stripe
import os
from datetime import datetime, timedelta
from decimal import Decimal

stripe.api_key = os.getenv('STRIPE_SECRET_KEY')


class PaymentService:
    """Serviço para gerenciar pagamentos de serviços via Stripe"""

    @staticmethod
    def calculate_payment_amount(service_price, user, payment_type=None):
        """
        Calcula o valor a ser cobrado baseado nas configurações do estabelecimento.

        Args:
            service_price: Preço do serviço (Decimal ou float)
            user: Objeto User com as configurações de pagamento
            payment_type: Tipo de pagamento ('full' ou 'deposit'). Se None, usa config do user.

        Returns:
            tuple: (amount_in_cents, payment_type, deposit_percentage)
        """
        price = Decimal(str(service_price)) if service_price else Decimal('0')

        # Usa o tipo de pagamento do parâmetro ou das configurações do user
        pmt_type = payment_type or user.booking_payment_type or 'full'
        deposit_pct = user.booking_deposit_percentage or 50

        if pmt_type == 'deposit':
            amount = price * Decimal(str(deposit_pct)) / Decimal('100')
        else:
            amount = price
            deposit_pct = None

        # Converte para centavos (Stripe usa centavos)
        amount_cents = int(amount * 100)

        return amount_cents, pmt_type, deposit_pct

    @staticmethod
    def create_service_checkout_session(appointment, user, service, client, success_url, cancel_url):
        """
        Cria uma sessão de Stripe Checkout para pagamento de serviço.

        Args:
            appointment: Objeto Appointment
            user: Objeto User (estabelecimento)
            service: Objeto Service
            client: Objeto Client
            success_url: URL para redirecionar após sucesso
            cancel_url: URL para redirecionar após cancelamento

        Returns:
            dict: Contém checkout_url, session_id, amount, payment_type
        """
        try:
            amount_cents, payment_type, deposit_pct = PaymentService.calculate_payment_amount(
                service.price, user
            )

            if amount_cents <= 0:
                return {
                    'success': False,
                    'error': 'O valor do serviço deve ser maior que zero'
                }

            # Descrição do item
            if payment_type == 'deposit':
                item_name = f"{service.name} - Sinal ({deposit_pct}%)"
            else:
                item_name = service.name

            business_name = user.business_name or user.name

            # Metadados para rastrear o pagamento
            metadata = {
                'appointment_id': str(appointment.id),
                'user_id': str(user.id),
                'client_id': str(client.id),
                'service_id': str(service.id),
                'payment_type': payment_type,
                'booking_code': appointment.booking_code or ''
            }

            if deposit_pct:
                metadata['deposit_percentage'] = str(deposit_pct)

            # Configurar métodos de pagamento (cartão + PIX)
            payment_method_types = ['card']

            # PIX só está disponível para BRL
            # Adicionar PIX se disponível na conta Stripe
            try:
                payment_method_types.append('pix')
            except Exception:
                pass  # PIX pode não estar habilitado

            # Criar sessão de checkout
            session = stripe.checkout.Session.create(
                payment_method_types=payment_method_types,
                line_items=[{
                    'price_data': {
                        'currency': 'brl',
                        'product_data': {
                            'name': item_name,
                            'description': f'Agendamento em {business_name} - {appointment.appointment_date.strftime("%d/%m/%Y")} às {appointment.start_time.strftime("%H:%M")}',
                        },
                        'unit_amount': amount_cents,
                    },
                    'quantity': 1,
                }],
                mode='payment',
                success_url=success_url,
                cancel_url=cancel_url,
                customer_email=client.email if client.email else None,
                metadata=metadata,
                expires_at=int((datetime.utcnow() + timedelta(hours=24)).timestamp()),
                locale='pt-BR',
            )

            return {
                'success': True,
                'checkout_url': session.url,
                'session_id': session.id,
                'amount': amount_cents / 100,  # Retorna em reais
                'payment_type': payment_type,
                'deposit_percentage': deposit_pct,
                'expires_at': datetime.utcnow() + timedelta(hours=24)
            }

        except stripe.error.StripeError as e:
            print(f"Stripe error: {str(e)}")
            return {
                'success': False,
                'error': f'Erro ao criar sessão de pagamento: {str(e)}'
            }
        except Exception as e:
            print(f"Error creating checkout session: {str(e)}")
            return {
                'success': False,
                'error': f'Erro interno: {str(e)}'
            }

    @staticmethod
    def retrieve_checkout_session(session_id):
        """
        Recupera informações de uma sessão de checkout.

        Args:
            session_id: ID da sessão de checkout

        Returns:
            stripe.checkout.Session ou None
        """
        try:
            return stripe.checkout.Session.retrieve(session_id)
        except stripe.error.StripeError as e:
            print(f"Error retrieving session: {str(e)}")
            return None

    @staticmethod
    def handle_service_payment_completed(session):
        """
        Processa pagamento de serviço completado com sucesso.

        Args:
            session: Objeto da sessão de checkout do Stripe

        Returns:
            dict: Informações do pagamento processado
        """
        from src.models.appointment import Appointment
        from src.models.service_payment import ServicePayment
        from src.config.database import db

        try:
            metadata = session.get('metadata', {})
            appointment_id = metadata.get('appointment_id')

            if not appointment_id:
                return {'success': False, 'error': 'appointment_id não encontrado nos metadados'}

            appointment = Appointment.query.get(int(appointment_id))
            if not appointment:
                return {'success': False, 'error': 'Agendamento não encontrado'}

            # Atualizar o agendamento
            appointment.payment_status = 'paid'
            appointment.stripe_checkout_session_id = session.get('id')
            appointment.stripe_payment_intent_id = session.get('payment_intent')
            appointment.amount_paid = Decimal(str(session.get('amount_total', 0))) / Decimal('100')
            appointment.payment_completed_at = datetime.utcnow()

            # Se estava pendente de pagamento, mudar para scheduled ou confirmed
            if appointment.status == 'pending_payment':
                appointment.status = 'scheduled'

            # Criar/atualizar registro de ServicePayment
            service_payment = ServicePayment.find_by_checkout_session(session.get('id'))
            if service_payment:
                service_payment.mark_as_paid(
                    payment_intent_id=session.get('payment_intent'),
                    payment_method_type=session.get('payment_method_types', ['card'])[0] if session.get('payment_method_types') else 'card'
                )
            else:
                # Criar novo registro se não existir
                service_payment = ServicePayment(
                    appointment_id=appointment.id,
                    user_id=int(metadata.get('user_id', 0)),
                    client_id=int(metadata.get('client_id', 0)),
                    stripe_checkout_session_id=session.get('id'),
                    stripe_payment_intent_id=session.get('payment_intent'),
                    amount=Decimal(str(session.get('amount_total', 0))) / Decimal('100'),
                    currency='BRL',
                    payment_type=metadata.get('payment_type', 'full'),
                    deposit_percentage=int(metadata.get('deposit_percentage')) if metadata.get('deposit_percentage') else None,
                    status='paid',
                    paid_at=datetime.utcnow()
                )
                db.session.add(service_payment)

            db.session.commit()

            return {
                'success': True,
                'appointment_id': appointment.id,
                'booking_code': appointment.booking_code,
                'amount_paid': float(appointment.amount_paid),
                'payment_status': 'paid'
            }

        except Exception as e:
            print(f"Error handling payment completed: {str(e)}")
            db.session.rollback()
            return {'success': False, 'error': str(e)}

    @staticmethod
    def handle_service_payment_failed(payment_intent):
        """
        Processa falha de pagamento de serviço.

        Args:
            payment_intent: Objeto do payment intent do Stripe

        Returns:
            dict: Informações do processamento
        """
        from src.models.appointment import Appointment
        from src.models.service_payment import ServicePayment
        from src.config.database import db

        try:
            # Tentar encontrar pelo payment intent
            service_payment = ServicePayment.find_by_payment_intent(payment_intent.get('id'))

            if service_payment:
                failure_message = payment_intent.get('last_payment_error', {}).get('message', 'Pagamento falhou')
                service_payment.mark_as_failed(reason=failure_message)

                # Atualizar o agendamento
                if service_payment.appointment:
                    service_payment.appointment.payment_status = 'failed'

                db.session.commit()

                return {
                    'success': True,
                    'appointment_id': service_payment.appointment_id,
                    'payment_status': 'failed',
                    'reason': failure_message
                }

            return {'success': False, 'error': 'Pagamento não encontrado'}

        except Exception as e:
            print(f"Error handling payment failed: {str(e)}")
            db.session.rollback()
            return {'success': False, 'error': str(e)}

    @staticmethod
    def handle_checkout_expired(session):
        """
        Processa sessão de checkout expirada.

        Args:
            session: Objeto da sessão de checkout do Stripe

        Returns:
            dict: Informações do processamento
        """
        from src.models.appointment import Appointment
        from src.models.service_payment import ServicePayment
        from src.config.database import db

        try:
            metadata = session.get('metadata', {})
            appointment_id = metadata.get('appointment_id')

            service_payment = ServicePayment.find_by_checkout_session(session.get('id'))

            if service_payment:
                service_payment.status = 'expired'
                service_payment.updated_at = datetime.utcnow()

            if appointment_id:
                appointment = Appointment.query.get(int(appointment_id))
                if appointment and appointment.status == 'pending_payment':
                    # Manter como pending_payment para permitir nova tentativa
                    appointment.payment_status = 'expired'

            db.session.commit()

            return {
                'success': True,
                'status': 'expired'
            }

        except Exception as e:
            print(f"Error handling checkout expired: {str(e)}")
            db.session.rollback()
            return {'success': False, 'error': str(e)}

    @staticmethod
    def create_refund(payment_intent_id, amount_cents=None, reason=None):
        """
        Cria um reembolso para um pagamento.

        Args:
            payment_intent_id: ID do payment intent
            amount_cents: Valor em centavos (None para reembolso total)
            reason: Motivo do reembolso

        Returns:
            dict: Informações do reembolso
        """
        try:
            refund_params = {'payment_intent': payment_intent_id}

            if amount_cents:
                refund_params['amount'] = amount_cents

            if reason:
                refund_params['reason'] = 'requested_by_customer'

            refund = stripe.Refund.create(**refund_params)

            return {
                'success': True,
                'refund_id': refund.id,
                'amount': refund.amount / 100,
                'status': refund.status
            }

        except stripe.error.StripeError as e:
            print(f"Stripe refund error: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    @staticmethod
    def verify_webhook_signature(payload, sig_header, webhook_secret):
        """
        Verifica a assinatura do webhook do Stripe.

        Args:
            payload: Corpo da requisição
            sig_header: Header Stripe-Signature
            webhook_secret: Secret do webhook

        Returns:
            stripe.Event ou None
        """
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, webhook_secret
            )
            return event
        except ValueError as e:
            print(f"Invalid payload: {str(e)}")
            return None
        except stripe.error.SignatureVerificationError as e:
            print(f"Invalid signature: {str(e)}")
            return None
