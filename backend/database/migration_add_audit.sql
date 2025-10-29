-- Migration: Add Audit Trail and Soft Delete
-- Add columns for soft delete and audit trail to all tables

-- Add columns to code_systems
ALTER TABLE code_systems 
ADD COLUMN IF NOT EXISTS active BOOLEAN DEFAULT TRUE,
ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMP,
ADD COLUMN IF NOT EXISTS created_by VARCHAR(255),
ADD COLUMN IF NOT EXISTS updated_by VARCHAR(255),
ADD COLUMN IF NOT EXISTS deleted_by VARCHAR(255);

-- Add columns to value_sets
ALTER TABLE value_sets 
ADD COLUMN IF NOT EXISTS active BOOLEAN DEFAULT TRUE,
ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMP,
ADD COLUMN IF NOT EXISTS created_by VARCHAR(255),
ADD COLUMN IF NOT EXISTS updated_by VARCHAR(255),
ADD COLUMN IF NOT EXISTS deleted_by VARCHAR(255);

-- Add columns to concept_maps
ALTER TABLE concept_maps 
ADD COLUMN IF NOT EXISTS active BOOLEAN DEFAULT TRUE,
ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMP,
ADD COLUMN IF NOT EXISTS created_by VARCHAR(255),
ADD COLUMN IF NOT EXISTS updated_by VARCHAR(255),
ADD COLUMN IF NOT EXISTS deleted_by VARCHAR(255);

-- Create users table for authentication
CREATE TABLE IF NOT EXISTS users (
    id VARCHAR(255) PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE,
    is_admin BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP
);

-- Create audit log table
CREATE TABLE IF NOT EXISTS audit_log (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) REFERENCES users(id),
    username VARCHAR(100),
    action VARCHAR(50) NOT NULL,
    resource_type VARCHAR(50) NOT NULL,
    resource_id VARCHAR(255),
    resource_name VARCHAR(255),
    changes JSONB,
    ip_address VARCHAR(50),
    user_agent TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_code_systems_active ON code_systems(active);
CREATE INDEX IF NOT EXISTS idx_value_sets_active ON value_sets(active);
CREATE INDEX IF NOT EXISTS idx_concept_maps_active ON concept_maps(active);
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_audit_log_user ON audit_log(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_log_resource ON audit_log(resource_type, resource_id);
CREATE INDEX IF NOT EXISTS idx_audit_log_timestamp ON audit_log(timestamp);

-- Comments
COMMENT ON COLUMN code_systems.active IS 'Soft delete flag - FALSE means record is disabled';
COMMENT ON COLUMN code_systems.deleted_at IS 'Timestamp when record was soft deleted';
COMMENT ON COLUMN code_systems.created_by IS 'Username who created the record';
COMMENT ON COLUMN code_systems.updated_by IS 'Username who last updated the record';
COMMENT ON COLUMN code_systems.deleted_by IS 'Username who soft deleted the record';

COMMENT ON TABLE users IS 'User accounts for authentication and authorization';
COMMENT ON TABLE audit_log IS 'Audit trail for all create, update, delete operations';
