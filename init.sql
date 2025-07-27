-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Core entity structure based on PRD requirements
CREATE TABLE IF NOT EXISTS contacts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    email VARCHAR(255) UNIQUE,
    phone VARCHAR(20),
    address JSONB,
    contact_type VARCHAR(50) DEFAULT 'prospect',
    source VARCHAR(100),
    preferences JSONB,
    total_lifetime_giving DECIMAL(12,2) DEFAULT 0.00,
    last_donation_date DATE,
    donation_count INTEGER DEFAULT 0,
    rfm_score VARCHAR(3),
    donor_segment VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    event_date DATE,
    event_type VARCHAR(50),
    capacity INTEGER,
    ticket_price DECIMAL(10,2),
    description TEXT,
    status VARCHAR(20) DEFAULT 'planned',
    venue_name VARCHAR(255),
    venue_address JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS transactions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    contact_id UUID REFERENCES contacts(id) ON DELETE CASCADE,
    event_id UUID REFERENCES events(id) ON DELETE SET NULL,
    type VARCHAR(50) NOT NULL,
    amount DECIMAL(12,2) NOT NULL,
    quantity INTEGER DEFAULT 1,
    payment_method VARCHAR(50),
    processor_transaction_id VARCHAR(255),
    status VARCHAR(20) DEFAULT 'pending',
    campaign VARCHAR(100),
    notes TEXT,
    transaction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS communications (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    contact_id UUID REFERENCES contacts(id) ON DELETE CASCADE,
    author_id UUID,
    type VARCHAR(50),
    subject VARCHAR(255),
    content TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_private BOOLEAN DEFAULT false,
    scheduled_date TIMESTAMP,
    sent_date TIMESTAMP
);

CREATE TABLE IF NOT EXISTS event_attendance (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    contact_id UUID REFERENCES contacts(id) ON DELETE CASCADE,
    event_id UUID REFERENCES events(id) ON DELETE CASCADE,
    attendance_status VARCHAR(20) DEFAULT 'registered',
    checked_in_at TIMESTAMP,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(contact_id, event_id)
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_contacts_email ON contacts(email);
CREATE INDEX IF NOT EXISTS idx_contacts_type ON contacts(contact_type);
CREATE INDEX IF NOT EXISTS idx_contacts_segment ON contacts(donor_segment);
CREATE INDEX IF NOT EXISTS idx_transactions_contact_id ON transactions(contact_id);
CREATE INDEX IF NOT EXISTS idx_transactions_date ON transactions(transaction_date);
CREATE INDEX IF NOT EXISTS idx_transactions_type ON transactions(type);
CREATE INDEX IF NOT EXISTS idx_communications_contact_id ON communications(contact_id);
CREATE INDEX IF NOT EXISTS idx_events_date ON events(event_date);
CREATE INDEX IF NOT EXISTS idx_events_type ON events(event_type);
CREATE INDEX IF NOT EXISTS idx_attendance_contact_event ON event_attendance(contact_id, event_id);