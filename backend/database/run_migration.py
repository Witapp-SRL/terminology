#!/usr/bin/env python3
"""
Migration script to add audit trail and soft delete support
"""
import sys
sys.path.append('/app/backend')

from sqlalchemy import create_engine, text, inspect
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment
env_path = Path('/app/backend/.env')
load_dotenv(env_path)

print("🔄 Starting migration...")
print(f"Database: {os.environ.get('DATABASE_URL', '').split('@')[1] if '@' in os.environ.get('DATABASE_URL', '') else 'Not set'}")
print()

engine = create_engine(os.environ['DATABASE_URL'])

with engine.connect() as conn:
    inspector = inspect(engine)
    
    # Add columns to existing tables
    for table in ['code_systems', 'value_sets', 'concept_maps']:
        print(f"Updating {table}...")
        columns = [c['name'] for c in inspector.get_columns(table)]
        
        if 'active' not in columns:
            conn.execute(text(f"ALTER TABLE {table} ADD COLUMN active BOOLEAN DEFAULT TRUE"))
            conn.commit()
            print(f"  ✓ Added 'active' column")
        
        if 'deleted_at' not in columns:
            conn.execute(text(f"ALTER TABLE {table} ADD COLUMN deleted_at TIMESTAMP"))
            conn.commit()
            print(f"  ✓ Added 'deleted_at' column")
        
        if 'created_by' not in columns:
            conn.execute(text(f"ALTER TABLE {table} ADD COLUMN created_by VARCHAR(255)"))
            conn.commit()
            print(f"  ✓ Added 'created_by' column")
        
        if 'updated_by' not in columns:
            conn.execute(text(f"ALTER TABLE {table} ADD COLUMN updated_by VARCHAR(255)"))
            conn.commit()
            print(f"  ✓ Added 'updated_by' column")
        
        if 'deleted_by' not in columns:
            conn.execute(text(f"ALTER TABLE {table} ADD COLUMN deleted_by VARCHAR(255)"))
            conn.commit()
            print(f"  ✓ Added 'deleted_by' column")
        
        # Set existing records to active
        conn.execute(text(f"UPDATE {table} SET active = TRUE WHERE active IS NULL"))
        conn.commit()
    
    print()
    
    # Create users table
    print("Creating users table...")
    conn.execute(text("""
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
        )
    """))
    conn.commit()
    print("✓ Users table created")
    
    # Create audit log table
    print("Creating audit_log table...")
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS audit_log (
            id SERIAL PRIMARY KEY,
            user_id VARCHAR(255),
            username VARCHAR(100),
            action VARCHAR(50) NOT NULL,
            resource_type VARCHAR(50) NOT NULL,
            resource_id VARCHAR(255),
            resource_name VARCHAR(255),
            changes JSONB,
            ip_address VARCHAR(50),
            user_agent TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """))
    conn.commit()
    print("✓ Audit log table created")
    
    # Create indexes
    print("Creating indexes...")
    try:
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_audit_log_user ON audit_log(user_id)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_audit_log_resource ON audit_log(resource_type, resource_id)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_audit_log_timestamp ON audit_log(timestamp)"))
        conn.commit()
        print("✓ Indexes created")
    except Exception as e:
        print(f"  Note: {e}")
    
    print()
    print("✅ Migration completata con successo!")
    
    # Summary
    tables = inspector.get_table_names()
    print(f"\nTabelle nel database: {len(tables)}")
    for table in sorted(tables):
        cols = inspector.get_columns(table)
        print(f"  - {table} ({len(cols)} columns)")

if __name__ == "__main__":
    pass
