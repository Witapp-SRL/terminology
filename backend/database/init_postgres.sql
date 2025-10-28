-- FHIR Terminology Service - PostgreSQL Database Schema
-- =====================================================

-- Create database (run as postgres superuser)
-- CREATE DATABASE fhir_terminology;
-- \c fhir_terminology;

-- Create extension for UUID support
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Drop tables if they exist (for clean install)
DROP TABLE IF EXISTS concept_maps CASCADE;
DROP TABLE IF EXISTS value_sets CASCADE;
DROP TABLE IF EXISTS code_systems CASCADE;

-- =====================================================
-- CODE SYSTEMS TABLE
-- =====================================================
CREATE TABLE code_systems (
    id VARCHAR(255) PRIMARY KEY,
    resource_type VARCHAR(50) DEFAULT 'CodeSystem' NOT NULL,
    url VARCHAR(500) UNIQUE NOT NULL,
    version VARCHAR(100),
    name VARCHAR(255) NOT NULL,
    title VARCHAR(500),
    status VARCHAR(50) NOT NULL CHECK (status IN ('draft', 'active', 'retired', 'unknown')),
    experimental BOOLEAN DEFAULT TRUE,
    date TIMESTAMP,
    publisher VARCHAR(255),
    description TEXT,
    case_sensitive BOOLEAN DEFAULT TRUE,
    content VARCHAR(50) DEFAULT 'complete' CHECK (content IN ('not-present', 'example', 'fragment', 'complete', 'supplement')),
    count INTEGER,
    property JSONB,
    concept JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for code_systems
CREATE INDEX idx_code_systems_url ON code_systems(url);
CREATE INDEX idx_code_systems_name ON code_systems(name);
CREATE INDEX idx_code_systems_status ON code_systems(status);
CREATE INDEX idx_code_systems_concept ON code_systems USING GIN (concept);

-- =====================================================
-- VALUE SETS TABLE
-- =====================================================
CREATE TABLE value_sets (
    id VARCHAR(255) PRIMARY KEY,
    resource_type VARCHAR(50) DEFAULT 'ValueSet' NOT NULL,
    url VARCHAR(500) UNIQUE NOT NULL,
    version VARCHAR(100),
    name VARCHAR(255) NOT NULL,
    title VARCHAR(500),
    status VARCHAR(50) NOT NULL CHECK (status IN ('draft', 'active', 'retired', 'unknown')),
    experimental BOOLEAN DEFAULT TRUE,
    date TIMESTAMP,
    publisher VARCHAR(255),
    description TEXT,
    compose JSONB,
    expansion JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for value_sets
CREATE INDEX idx_value_sets_url ON value_sets(url);
CREATE INDEX idx_value_sets_name ON value_sets(name);
CREATE INDEX idx_value_sets_status ON value_sets(status);
CREATE INDEX idx_value_sets_compose ON value_sets USING GIN (compose);

-- =====================================================
-- CONCEPT MAPS TABLE
-- =====================================================
CREATE TABLE concept_maps (
    id VARCHAR(255) PRIMARY KEY,
    resource_type VARCHAR(50) DEFAULT 'ConceptMap' NOT NULL,
    url VARCHAR(500) UNIQUE NOT NULL,
    version VARCHAR(100),
    name VARCHAR(255) NOT NULL,
    title VARCHAR(500),
    status VARCHAR(50) NOT NULL CHECK (status IN ('draft', 'active', 'retired', 'unknown')),
    experimental BOOLEAN DEFAULT TRUE,
    date TIMESTAMP,
    publisher VARCHAR(255),
    description TEXT,
    source_canonical VARCHAR(500),
    target_canonical VARCHAR(500),
    "group" JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for concept_maps
CREATE INDEX idx_concept_maps_url ON concept_maps(url);
CREATE INDEX idx_concept_maps_name ON concept_maps(name);
CREATE INDEX idx_concept_maps_status ON concept_maps(status);
CREATE INDEX idx_concept_maps_source ON concept_maps(source_canonical);
CREATE INDEX idx_concept_maps_target ON concept_maps(target_canonical);
CREATE INDEX idx_concept_maps_group ON concept_maps USING GIN ("group");

-- =====================================================
-- TRIGGERS FOR UPDATED_AT
-- =====================================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_code_systems_updated_at
    BEFORE UPDATE ON code_systems
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_value_sets_updated_at
    BEFORE UPDATE ON value_sets
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_concept_maps_updated_at
    BEFORE UPDATE ON concept_maps
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- =====================================================
-- GRANT PERMISSIONS (adjust user as needed)
-- =====================================================
-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO fhir_user;
-- GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO fhir_user;

-- =====================================================
-- COMMENTS
-- =====================================================
COMMENT ON TABLE code_systems IS 'FHIR CodeSystem resources - managed collections of medical codes';
COMMENT ON TABLE value_sets IS 'FHIR ValueSet resources - collections of codes from one or more code systems';
COMMENT ON TABLE concept_maps IS 'FHIR ConceptMap resources - mappings between code systems';

COMMENT ON COLUMN code_systems.concept IS 'JSONB array of concepts with code, display, definition, and properties';
COMMENT ON COLUMN value_sets.compose IS 'JSONB definition of value set composition rules';
COMMENT ON COLUMN value_sets.expansion IS 'JSONB expanded list of codes in the value set';
COMMENT ON COLUMN concept_maps."group" IS 'JSONB array of concept mapping groups';
