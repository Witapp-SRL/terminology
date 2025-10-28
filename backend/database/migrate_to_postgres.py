#!/usr/bin/env python3
"""
Migration script to move data from SQLite to PostgreSQL
"""
import sys
import os
sys.path.append('/app/backend')

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database import CodeSystemModel, ValueSetModel, ConceptMapModel, Base
import json

print("="*50)
print("FHIR Terminology Service - SQLite to PostgreSQL Migration")
print("="*50)
print()

# Source: SQLite
SQLITE_URL = "sqlite:///./terminology.db"
print(f"Source: {SQLITE_URL}")

# Target: PostgreSQL (from environment or input)
POSTGRES_URL = os.environ.get('DATABASE_URL')

if not POSTGRES_URL:
    print("\nPostgreSQL connection string not found in environment.")
    print("Please provide connection details:")
    user = input("Username [fhir_user]: ") or "fhir_user"
    password = input("Password: ")
    host = input("Host [localhost]: ") or "localhost"
    port = input("Port [5432]: ") or "5432"
    database = input("Database [fhir_terminology]: ") or "fhir_terminology"
    
    POSTGRES_URL = f"postgresql://{user}:{password}@{host}:{port}/{database}"

print(f"Target: {POSTGRES_URL.replace(password, '****' if password else '')}")
print()

try:
    # Create engines
    print("Connecting to databases...")
    sqlite_engine = create_engine(SQLITE_URL)
    postgres_engine = create_engine(POSTGRES_URL)
    
    # Create sessions
    SQLiteSession = sessionmaker(bind=sqlite_engine)
    PostgresSession = sessionmaker(bind=postgres_engine)
    
    sqlite_session = SQLiteSession()
    postgres_session = PostgresSession()
    
    print("✓ Connected successfully\n")
    
    # Create tables in PostgreSQL (if not exist)
    print("Creating tables in PostgreSQL...")
    Base.metadata.create_all(postgres_engine)
    print("✓ Tables created\n")
    
    # Migrate CodeSystems
    print("Migrating CodeSystems...")
    code_systems = sqlite_session.query(CodeSystemModel).all()
    count = 0
    for cs in code_systems:
        # Check if already exists
        existing = postgres_session.query(CodeSystemModel).filter_by(id=cs.id).first()
        if not existing:
            # Create new record
            new_cs = CodeSystemModel(
                id=cs.id,
                resource_type=cs.resource_type,
                url=cs.url,
                version=cs.version,
                name=cs.name,
                title=cs.title,
                status=cs.status,
                experimental=cs.experimental,
                date=cs.date,
                publisher=cs.publisher,
                description=cs.description,
                case_sensitive=cs.case_sensitive,
                content=cs.content,
                count=cs.count,
                property=cs.property,
                concept=cs.concept
            )
            postgres_session.add(new_cs)
            count += 1
            print(f"  ✓ {cs.name}")
    postgres_session.commit()
    print(f"✓ Migrated {count} CodeSystems\n")
    
    # Migrate ValueSets
    print("Migrating ValueSets...")
    value_sets = sqlite_session.query(ValueSetModel).all()
    count = 0
    for vs in value_sets:
        existing = postgres_session.query(ValueSetModel).filter_by(id=vs.id).first()
        if not existing:
            new_vs = ValueSetModel(
                id=vs.id,
                resource_type=vs.resource_type,
                url=vs.url,
                version=vs.version,
                name=vs.name,
                title=vs.title,
                status=vs.status,
                experimental=vs.experimental,
                date=vs.date,
                publisher=vs.publisher,
                description=vs.description,
                compose=vs.compose,
                expansion=vs.expansion
            )
            postgres_session.add(new_vs)
            count += 1
            print(f"  ✓ {vs.name}")
    postgres_session.commit()
    print(f"✓ Migrated {count} ValueSets\n")
    
    # Migrate ConceptMaps
    print("Migrating ConceptMaps...")
    concept_maps = sqlite_session.query(ConceptMapModel).all()
    count = 0
    for cm in concept_maps:
        existing = postgres_session.query(ConceptMapModel).filter_by(id=cm.id).first()
        if not existing:
            new_cm = ConceptMapModel(
                id=cm.id,
                resource_type=cm.resource_type,
                url=cm.url,
                version=cm.version,
                name=cm.name,
                title=cm.title,
                status=cm.status,
                experimental=cm.experimental,
                date=cm.date,
                publisher=cm.publisher,
                description=cm.description,
                source_canonical=cm.source_canonical,
                target_canonical=cm.target_canonical,
                group=cm.group
            )
            postgres_session.add(new_cm)
            count += 1
            print(f"  ✓ {cm.name}")
    postgres_session.commit()
    print(f"✓ Migrated {count} ConceptMaps\n")
    
    # Summary
    print("="*50)
    print("Migration completed successfully!")
    print("="*50)
    print(f"Total CodeSystems: {postgres_session.query(CodeSystemModel).count()}")
    print(f"Total ValueSets: {postgres_session.query(ValueSetModel).count()}")
    print(f"Total ConceptMaps: {postgres_session.query(ConceptMapModel).count()}")
    
    # Close sessions
    sqlite_session.close()
    postgres_session.close()
    
except Exception as e:
    print(f"\n❌ Error during migration: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
