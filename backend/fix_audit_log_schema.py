#!/usr/bin/env python3
"""
Script to fix audit_log table schema
"""
import os
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

# Load environment variables
env_path = Path(__file__).parent / '.env'
load_dotenv(env_path)

DATABASE_URL = os.environ.get('DATABASE_URL')

def fix_audit_log_schema():
    engine = create_engine(DATABASE_URL)
    
    with engine.connect() as conn:
        print("Fixing audit_log table schema...")
        
        try:
            # Drop the old table if it exists
            conn.execute(text("DROP TABLE IF EXISTS audit_log CASCADE"))
            conn.commit()
            print("✓ Dropped old audit_log table")
            
            # Create the new table with correct schema
            conn.execute(text("""
                CREATE TABLE audit_log (
                    id VARCHAR PRIMARY KEY,
                    resource_type VARCHAR NOT NULL,
                    resource_id VARCHAR NOT NULL,
                    action VARCHAR NOT NULL,
                    user_id VARCHAR NOT NULL,
                    username VARCHAR NOT NULL,
                    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
                    changes JSONB,
                    ip_address VARCHAR
                )
            """))
            conn.commit()
            print("✓ Created new audit_log table with correct schema")
            
            # Create indexes
            conn.execute(text("CREATE INDEX idx_audit_log_resource_type ON audit_log(resource_type)"))
            conn.execute(text("CREATE INDEX idx_audit_log_resource_id ON audit_log(resource_id)"))
            conn.execute(text("CREATE INDEX idx_audit_log_user_id ON audit_log(user_id)"))
            conn.execute(text("CREATE INDEX idx_audit_log_timestamp ON audit_log(timestamp)"))
            conn.commit()
            print("✓ Created indexes")
            
            print("\n✅ Schema fix completed successfully!")
            return True
            
        except Exception as e:
            print(f"❌ Error fixing schema: {e}")
            conn.rollback()
            return False

if __name__ == "__main__":
    fix_audit_log_schema()
