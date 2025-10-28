from sqlalchemy import create_engine, Column, String, Boolean, Integer, Text, DateTime, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from datetime import datetime
import os

DATABASE_URL = os.environ.get('DATABASE_URL', 'sqlite:///./terminology.db')

# Create engine
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if 'sqlite' in DATABASE_URL else {}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Database Models
class CodeSystemModel(Base):
    __tablename__ = "code_systems"
    
    id = Column(String, primary_key=True, index=True)
    resource_type = Column(String, default="CodeSystem")
    url = Column(String, unique=True, index=True, nullable=False)
    version = Column(String)
    name = Column(String, nullable=False, index=True)
    title = Column(String)
    status = Column(String, nullable=False)
    experimental = Column(Boolean, default=True)
    date = Column(DateTime, default=datetime.utcnow)
    publisher = Column(String)
    description = Column(Text)
    case_sensitive = Column(Boolean, default=True)
    content = Column(String, default="complete")
    count = Column(Integer)
    property = Column(JSON)
    concept = Column(JSON)
    
class ValueSetModel(Base):
    __tablename__ = "value_sets"
    
    id = Column(String, primary_key=True, index=True)
    resource_type = Column(String, default="ValueSet")
    url = Column(String, unique=True, index=True, nullable=False)
    version = Column(String)
    name = Column(String, nullable=False, index=True)
    title = Column(String)
    status = Column(String, nullable=False)
    experimental = Column(Boolean, default=True)
    date = Column(DateTime, default=datetime.utcnow)
    publisher = Column(String)
    description = Column(Text)
    compose = Column(JSON)
    expansion = Column(JSON)

class ConceptMapModel(Base):
    __tablename__ = "concept_maps"
    
    id = Column(String, primary_key=True, index=True)
    resource_type = Column(String, default="ConceptMap")
    url = Column(String, unique=True, index=True, nullable=False)
    version = Column(String)
    name = Column(String, nullable=False, index=True)
    title = Column(String)
    status = Column(String, nullable=False)
    experimental = Column(Boolean, default=True)
    date = Column(DateTime, default=datetime.utcnow)
    publisher = Column(String)
    description = Column(Text)
    source_canonical = Column(String)
    target_canonical = Column(String)
    group = Column(JSON)

# Create tables
Base.metadata.create_all(bind=engine)

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
