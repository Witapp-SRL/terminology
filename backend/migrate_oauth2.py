#!/usr/bin/env python3
"""
Migration script to add OAuth2 tables and update existing tables
"""
import os
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

# Load environment
env_path = Path(__file__).parent / '.env'
load_dotenv(env_path)

DATABASE_URL = os.environ.get('DATABASE_URL', 'sqlite:///./terminology.db')

def run_migration():
    engine = create_engine(DATABASE_URL)
    
    with engine.connect() as conn:
        print("🔧 Running OAuth2/SMART on FHIR migrations...")
        
        try:
            # Update users table - add role column
            print("1. Updating users table...")
            conn.execute(text("""
                ALTER TABLE users 
                ADD COLUMN IF NOT EXISTS role VARCHAR DEFAULT 'user'
            """))
            conn.commit()
            print("   ✓ Added role column to users")
            
            # Create oauth2_clients table
            print("2. Creating oauth2_clients table...")
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS oauth2_clients (
                    id VARCHAR PRIMARY KEY,
                    client_id VARCHAR UNIQUE NOT NULL,
                    client_secret_hash VARCHAR NOT NULL,
                    client_name VARCHAR NOT NULL,
                    description TEXT,
                    redirect_uris JSONB,
                    grant_types JSONB,
                    response_types JSONB,
                    scopes JSONB,
                    token_endpoint_auth_method VARCHAR DEFAULT 'client_secret_post',
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    created_by VARCHAR,
                    last_used TIMESTAMP WITH TIME ZONE
                )
            """))
            conn.commit()
            print("   ✓ Created oauth2_clients table")
            
            # Create indexes for oauth2_clients
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_oauth2_clients_client_id ON oauth2_clients(client_id)"))
            conn.commit()
            
            # Create oauth2_tokens table
            print("3. Creating oauth2_tokens table...")
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS oauth2_tokens (
                    id VARCHAR PRIMARY KEY,
                    access_token VARCHAR UNIQUE NOT NULL,
                    refresh_token VARCHAR UNIQUE,
                    token_type VARCHAR DEFAULT 'Bearer',
                    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
                    refresh_expires_at TIMESTAMP WITH TIME ZONE,
                    scopes JSONB,
                    client_id VARCHAR NOT NULL,
                    user_id VARCHAR,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    revoked BOOLEAN DEFAULT FALSE,
                    revoked_at TIMESTAMP WITH TIME ZONE
                )
            """))
            conn.commit()
            print("   ✓ Created oauth2_tokens table")
            
            # Create indexes for oauth2_tokens
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_oauth2_tokens_access_token ON oauth2_tokens(access_token)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_oauth2_tokens_client_id ON oauth2_tokens(client_id)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_oauth2_tokens_user_id ON oauth2_tokens(user_id)"))
            conn.commit()
            
            # Update audit_log table - add client_id and scopes
            print("4. Updating audit_log table...")
            conn.execute(text("""
                ALTER TABLE audit_log 
                ADD COLUMN IF NOT EXISTS client_id VARCHAR
            """))
            conn.execute(text("""
                ALTER TABLE audit_log 
                ADD COLUMN IF NOT EXISTS scopes JSONB
            """))
            conn.commit()
            print("   ✓ Updated audit_log table")
            
            # Create indexes
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_audit_log_client_id ON audit_log(client_id)"))
            conn.commit()
            
            print("\n✅ All migrations completed successfully!")
            print("\n📝 Tables created/updated:")
            print("   - users (added role column)")
            print("   - oauth2_clients (new)")
            print("   - oauth2_tokens (new)")
            print("   - audit_log (added client_id, scopes)")
            
            return True
            
        except Exception as e:
            print(f"\n❌ Migration error: {e}")
            conn.rollback()
            return False

if __name__ == "__main__":
    success = run_migration()
    exit(0 if success else 1)
