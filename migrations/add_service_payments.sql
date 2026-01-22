-- Migration: Add service payments functionality
-- Description: Adds payment configuration to users, payment tracking to appointments,
--              and creates the service_payments table for tracking Stripe payments

-- =====================================================
-- 1. Add payment configuration columns to users table
-- =====================================================
ALTER TABLE users
ADD COLUMN IF NOT EXISTS booking_require_payment BOOLEAN DEFAULT FALSE;

ALTER TABLE users
ADD COLUMN IF NOT EXISTS booking_payment_type VARCHAR(20) DEFAULT 'full';

ALTER TABLE users
ADD COLUMN IF NOT EXISTS booking_deposit_percentage INTEGER DEFAULT 50;

-- =====================================================
-- 2. Add payment tracking columns to appointments table
-- =====================================================
ALTER TABLE appointments
ADD COLUMN IF NOT EXISTS payment_status VARCHAR(20) DEFAULT 'pending';

ALTER TABLE appointments
ADD COLUMN IF NOT EXISTS stripe_checkout_session_id VARCHAR(100);

ALTER TABLE appointments
ADD COLUMN IF NOT EXISTS stripe_payment_intent_id VARCHAR(100);

ALTER TABLE appointments
ADD COLUMN IF NOT EXISTS amount_paid DECIMAL(10, 2);

ALTER TABLE appointments
ADD COLUMN IF NOT EXISTS payment_completed_at TIMESTAMP;

-- =====================================================
-- 3. Create service_payments table
-- =====================================================
CREATE TABLE IF NOT EXISTS service_payments (
    id SERIAL PRIMARY KEY,
    appointment_id INTEGER NOT NULL REFERENCES appointments(id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    client_id INTEGER NOT NULL REFERENCES clients(id) ON DELETE CASCADE,

    -- Stripe data
    stripe_checkout_session_id VARCHAR(100) UNIQUE,
    stripe_payment_intent_id VARCHAR(100) UNIQUE,

    -- Payment details
    amount DECIMAL(10, 2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'BRL',
    payment_type VARCHAR(20) DEFAULT 'full',
    deposit_percentage INTEGER,

    -- Status
    status VARCHAR(20) DEFAULT 'pending',
    payment_method_type VARCHAR(50),
    failure_reason TEXT,

    -- Timestamps
    paid_at TIMESTAMP,
    refunded_at TIMESTAMP,
    expires_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- 4. Create indexes for better query performance
-- =====================================================
CREATE INDEX IF NOT EXISTS idx_service_payments_appointment_id ON service_payments(appointment_id);
CREATE INDEX IF NOT EXISTS idx_service_payments_user_id ON service_payments(user_id);
CREATE INDEX IF NOT EXISTS idx_service_payments_client_id ON service_payments(client_id);
CREATE INDEX IF NOT EXISTS idx_service_payments_status ON service_payments(status);
CREATE INDEX IF NOT EXISTS idx_service_payments_checkout_session ON service_payments(stripe_checkout_session_id);
CREATE INDEX IF NOT EXISTS idx_service_payments_payment_intent ON service_payments(stripe_payment_intent_id);

CREATE INDEX IF NOT EXISTS idx_appointments_payment_status ON appointments(payment_status);
CREATE INDEX IF NOT EXISTS idx_appointments_stripe_checkout ON appointments(stripe_checkout_session_id);

-- =====================================================
-- 5. Add comment descriptions
-- =====================================================
COMMENT ON TABLE service_payments IS 'Tracks Stripe payments for service bookings';
COMMENT ON COLUMN service_payments.payment_type IS 'full = full payment, deposit = partial payment';
COMMENT ON COLUMN service_payments.status IS 'pending, paid, failed, refunded, expired';

COMMENT ON COLUMN users.booking_require_payment IS 'Whether payment is required to book an appointment';
COMMENT ON COLUMN users.booking_payment_type IS 'full = charge full price, deposit = charge percentage';
COMMENT ON COLUMN users.booking_deposit_percentage IS 'Percentage to charge if payment_type is deposit';

COMMENT ON COLUMN appointments.payment_status IS 'Payment status: pending, paid, failed, refunded, expired';
COMMENT ON COLUMN appointments.amount_paid IS 'Amount paid by the client';
