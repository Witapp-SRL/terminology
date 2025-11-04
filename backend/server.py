from fastapi import FastAPI, APIRouter, HTTPException, Query, Depends, UploadFile, File
from fastapi.responses import JSONResponse, StreamingResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
import os
import logging
from pathlib import Path
from typing import List, Optional
import uuid
from datetime import datetime, timezone
from sqlalchemy.orm import Session
import csv
import io
import json

from models.fhir_models import (
    CodeSystem,
    CodeSystemCreate,
    ValueSet,
    ValueSetCreate,
    ConceptMap,
    ConceptMapCreate,
    Parameters,
    Parameter,
    PublicationStatus,
)
from database import get_db, CodeSystemModel, ValueSetModel, ConceptMapModel, UserModel, AuditLogModel
from services.terminology_service_sql import TerminologyServiceSQL
from auth import (
    User, UserCreate, UserLogin, Token,
    authenticate_user, create_user, create_access_token,
    get_current_user, get_current_user_optional, create_audit_log,
    ACCESS_TOKEN_EXPIRE_MINUTES
)

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Initialize terminology service
terminology_service = TerminologyServiceSQL()

# Create the main app
app = FastAPI(title="FHIR Terminology Service", version="1.0.0")
api_router = APIRouter(prefix="/api")

@api_router.get("/")
async def root():
    return {"message": "FHIR Terminology Service", "version": "1.0.0", "status": "active"}

# Authentication endpoints
@api_router.post("/auth/register", response_model=User, status_code=201)
async def register(user: UserCreate, db: Session = Depends(get_db)):
    """Register a new user"""
    return create_user(db, user)

@api_router.post("/auth/login", response_model=Token)
async def login(user_login: UserLogin, db: Session = Depends(get_db)):
    """Login and get access token"""
    user = authenticate_user(db, user_login.username, user_login.password)
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password"
        )
    
    # Update last login
    user.last_login = datetime.now(timezone.utc)
    db.commit()
    
    # Create access token
    from datetime import timedelta
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@api_router.get("/auth/me", response_model=User)
async def get_me(current_user: UserModel = Depends(get_current_user)):
    """Get current user info"""
    return current_user

# Audit Log endpoints
@api_router.get("/audit-logs")
async def get_audit_logs(
    resource_type: Optional[str] = None,
    resource_id: Optional[str] = None,
    action: Optional[str] = None,
    user_id: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """Get audit logs with optional filters"""
    query = db.query(AuditLogModel)
    
    if resource_type:
        query = query.filter(AuditLogModel.resource_type == resource_type)
    if resource_id:
        query = query.filter(AuditLogModel.resource_id == resource_id)
    if action:
        query = query.filter(AuditLogModel.action == action)
    if user_id:
        query = query.filter(AuditLogModel.user_id == user_id)
    
    query = query.order_by(AuditLogModel.timestamp.desc())
    total = query.count()
    logs = query.offset(skip).limit(limit).all()
    
    return {
        "total": total,
        "logs": [
            {
                "id": log.id,
                "resource_type": log.resource_type,
                "resource_id": log.resource_id,
                "action": log.action,
                "user_id": log.user_id,
                "username": log.username,
                "timestamp": log.timestamp.isoformat(),
                "changes": log.changes,
                "ip_address": log.ip_address
            }
            for log in logs
        ]
    }

@api_router.get("/audit-logs/export-csv")
async def export_audit_logs_csv(
    resource_type: Optional[str] = None,
    resource_id: Optional[str] = None,
    action: Optional[str] = None,
    user_id: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """Export audit logs as CSV"""
    query = db.query(AuditLogModel)
    
    if resource_type:
        query = query.filter(AuditLogModel.resource_type == resource_type)
    if resource_id:
        query = query.filter(AuditLogModel.resource_id == resource_id)
    if action:
        query = query.filter(AuditLogModel.action == action)
    if user_id:
        query = query.filter(AuditLogModel.user_id == user_id)
    
    logs = query.order_by(AuditLogModel.timestamp.desc()).all()
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Timestamp', 'Resource Type', 'Resource ID', 'Action', 'User', 'Changes', 'IP Address'])
    
    for log in logs:
        writer.writerow([
            log.timestamp.isoformat(),
            log.resource_type,
            log.resource_id,
            log.action,
            log.username,
            json.dumps(log.changes) if log.changes else '',
            log.ip_address or ''
        ])
    
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=audit_logs.csv"}
    )

# Helper function to convert model to dict with JSON parsing
def model_to_dict(model):
    result = {}
    for c in model.__table__.columns:
        value = getattr(model, c.name)
        # Parse JSON strings and ensure arrays for collection fields
        if c.name in ['concept', 'property', 'compose', 'expansion', 'group']:
            if value is None:
                result[c.name] = [] if c.name in ['concept', 'property'] else None
            elif isinstance(value, str):
                try:
                    result[c.name] = json.loads(value)
                except:
                    result[c.name] = [] if c.name in ['concept', 'property'] else None
            else:
                result[c.name] = value if value else ([] if c.name in ['concept', 'property'] else None)
        else:
            result[c.name] = value
    
    # Convert to camelCase for FHIR compliance
    if 'resource_type' in result:
        result['resourceType'] = result.pop('resource_type')
    if 'case_sensitive' in result:
        result['caseSensitive'] = result.pop('case_sensitive')
    if 'source_canonical' in result:
        result['sourceCanonical'] = result.pop('source_canonical')
    if 'target_canonical' in result:
        result['targetCanonical'] = result.pop('target_canonical')
    
    return result

# CSV Import/Export endpoints
@api_router.post("/CodeSystem/import-csv")
async def import_codesystem_csv(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """Import CodeSystem from CSV"""
    try:
        content = await file.read()
        csv_file = io.StringIO(content.decode('utf-8'))
        reader = csv.DictReader(csv_file)
        
        concepts = []
        for row in reader:
            concepts.append({
                "code": row.get("code", ""),
                "display": row.get("display", ""),
                "definition": row.get("definition", "")
            })
        
        cs_id = str(uuid.uuid4())
        cs = CodeSystemModel(
            id=cs_id,
            url=f"http://example.org/fhir/CodeSystem/{cs_id}",
            name=file.filename.replace('.csv', '').replace(' ', ''),
            title=f"Imported from {file.filename}",
            status="draft",
            date=datetime.utcnow(),
            concept=json.dumps(concepts),
            count=len(concepts)
        )
        db.add(cs)
        db.commit()
        
        return {"message": f"Imported {len(concepts)} concepts", "id": cs_id}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@api_router.get("/CodeSystem/{id}/export-csv")
async def export_codesystem_csv(id: str, db: Session = Depends(get_db)):
    """Export CodeSystem to CSV"""
    cs = db.query(CodeSystemModel).filter(CodeSystemModel.id == id).first()
    if not cs:
        raise HTTPException(status_code=404, detail="CodeSystem not found")
    
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=["code", "display", "definition"])
    writer.writeheader()
    
    concepts = json.loads(cs.concept) if cs.concept and isinstance(cs.concept, str) else (cs.concept or [])
    for concept in concepts:
        writer.writerow({
            "code": concept.get("code", ""),
            "display": concept.get("display", ""),
            "definition": concept.get("definition", "")
        })
    
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={cs.name}.csv"}
    )

# CodeSystem CRUD
@api_router.get("/CodeSystem")
async def list_code_systems(
    url: Optional[str] = Query(None),
    name: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    include_inactive: bool = Query(False),
    db: Session = Depends(get_db)
):
    query = db.query(CodeSystemModel)
    
    # By default, only show active records
    if not include_inactive:
        query = query.filter(CodeSystemModel.active == True)
    
    if url:
        query = query.filter(CodeSystemModel.url == url)
    if name:
        query = query.filter(CodeSystemModel.name.ilike(f"%{name}%"))
    if status:
        query = query.filter(CodeSystemModel.status == status)
    
    results = query.all()
    return [model_to_dict(r) for r in results]

@api_router.get("/CodeSystem/{id}")
async def get_code_system(id: str, db: Session = Depends(get_db)):
    cs = db.query(CodeSystemModel).filter(CodeSystemModel.id == id).first()
    if not cs:
        raise HTTPException(status_code=404, detail="CodeSystem not found")
    return model_to_dict(cs)

@api_router.post("/CodeSystem", status_code=201)
async def create_code_system(
    data: CodeSystemCreate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    cs = CodeSystemModel(
        id=str(uuid.uuid4()),
        url=data.url,
        version=data.version,
        name=data.name,
        title=data.title,
        status=data.status,
        publisher=data.publisher,
        description=data.description,
        case_sensitive=data.caseSensitive,
        content=data.content,
        property=json.dumps([p.model_dump() for p in data.property]) if data.property else None,
        concept=json.dumps([c.model_dump() for c in data.concept]) if data.concept else None,
        count=len(data.concept) if data.concept else 0,
        date=datetime.now(timezone.utc),
        created_by=current_user.username,
        created_at=datetime.now(timezone.utc),
        active=True
    )
    db.add(cs)
    db.commit()
    
    # Create audit log
    create_audit_log(
        db=db,
        resource_type="CodeSystem",
        resource_id=cs.id,
        action="create",
        user=current_user,
        changes={"name": cs.name, "url": cs.url}
    )
    
    return model_to_dict(cs)

@api_router.put("/CodeSystem/{id}")
async def update_code_system(
    id: str,
    data: CodeSystemCreate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    cs = db.query(CodeSystemModel).filter(CodeSystemModel.id == id).first()
    if not cs:
        raise HTTPException(status_code=404, detail="CodeSystem not found")
    
    # Track changes
    changes = {}
    if cs.name != data.name:
        changes['name'] = {'old': cs.name, 'new': data.name}
    if cs.url != data.url:
        changes['url'] = {'old': cs.url, 'new': data.url}
    
    # Update fields
    cs.url = data.url
    cs.version = data.version
    cs.name = data.name
    cs.title = data.title
    cs.status = data.status
    cs.publisher = data.publisher
    cs.description = data.description
    cs.case_sensitive = data.caseSensitive
    cs.content = data.content
    cs.property = json.dumps([p.model_dump() for p in data.property]) if data.property else None
    cs.concept = json.dumps([c.model_dump() for c in data.concept]) if data.concept else None
    cs.count = len(data.concept) if data.concept else 0
    cs.updated_at = datetime.now(timezone.utc)
    cs.updated_by = current_user.username
    
    db.commit()
    db.refresh(cs)
    
    # Create audit log
    create_audit_log(
        db=db,
        resource_type="CodeSystem",
        resource_id=cs.id,
        action="update",
        user=current_user,
        changes=changes
    )
    
    return model_to_dict(cs)

@api_router.post("/CodeSystem/{id}/deactivate")
async def deactivate_code_system(
    id: str,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """Soft delete - deactivate a CodeSystem"""
    cs = db.query(CodeSystemModel).filter(CodeSystemModel.id == id).first()
    if not cs:
        raise HTTPException(status_code=404, detail="Not found")
    
    cs.active = False
    cs.deleted_at = datetime.now(timezone.utc)
    cs.deleted_by = current_user.username
    db.commit()
    
    # Create audit log
    create_audit_log(
        db=db,
        resource_type="CodeSystem",
        resource_id=cs.id,
        action="deactivate",
        user=current_user,
        changes={"status": "deactivated"}
    )
    
    return {"message": "CodeSystem deactivated", "id": id}

@api_router.post("/CodeSystem/{id}/activate")
async def activate_code_system(
    id: str,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """Reactivate a deactivated CodeSystem"""
    cs = db.query(CodeSystemModel).filter(CodeSystemModel.id == id).first()
    if not cs:
        raise HTTPException(status_code=404, detail="Not found")
    
    cs.active = True
    cs.deleted_at = None
    cs.deleted_by = None
    db.commit()
    
    # Create audit log
    create_audit_log(
        db=db,
        resource_type="CodeSystem",
        resource_id=cs.id,
        action="activate",
        user=current_user,
        changes={"status": "activated"}
    )
    
    return {"message": "CodeSystem activated", "id": id}

# ValueSet endpoints
@api_router.get("/ValueSet")
async def list_value_sets(db: Session = Depends(get_db)):
    results = db.query(ValueSetModel).all()
    return [model_to_dict(r) for r in results]

@api_router.get("/ValueSet/{id}")
async def get_value_set(id: str, db: Session = Depends(get_db)):
    vs = db.query(ValueSetModel).filter(ValueSetModel.id == id).first()
    if not vs:
        raise HTTPException(status_code=404, detail="Not found")
    return model_to_dict(vs)

@api_router.post("/ValueSet", status_code=201)
async def create_value_set(data: ValueSetCreate, db: Session = Depends(get_db)):
    vs = ValueSetModel(
        id=str(uuid.uuid4()),
        url=data.url,
        version=data.version,
        name=data.name,
        title=data.title,
        status=data.status,
        publisher=data.publisher,
        description=data.description,
        compose=json.dumps(data.compose.model_dump()) if data.compose else None,
        date=datetime.utcnow()
    )
    db.add(vs)
    db.commit()
    return model_to_dict(vs)

@api_router.put("/ValueSet/{id}")
async def update_value_set(id: str, data: ValueSetCreate, db: Session = Depends(get_db)):
    vs = db.query(ValueSetModel).filter(ValueSetModel.id == id).first()
    if not vs:
        raise HTTPException(status_code=404, detail="ValueSet not found")
    
    vs.url = data.url
    vs.version = data.version
    vs.name = data.name
    vs.title = data.title
    vs.status = data.status
    vs.publisher = data.publisher
    vs.description = data.description
    vs.compose = json.dumps(data.compose.model_dump()) if data.compose else None
    vs.date = datetime.utcnow()
    
    db.commit()
    db.refresh(vs)
    return model_to_dict(vs)

@api_router.delete("/ValueSet/{id}", status_code=204)
async def delete_value_set(id: str, db: Session = Depends(get_db)):
    vs = db.query(ValueSetModel).filter(ValueSetModel.id == id).first()
    if not vs:
        raise HTTPException(status_code=404, detail="Not found")
    db.delete(vs)
    db.commit()

# ConceptMap endpoints
@api_router.get("/ConceptMap")
async def list_concept_maps(db: Session = Depends(get_db)):
    results = db.query(ConceptMapModel).all()
    return [model_to_dict(r) for r in results]

@api_router.get("/ConceptMap/{id}")
async def get_concept_map(id: str, db: Session = Depends(get_db)):
    cm = db.query(ConceptMapModel).filter(ConceptMapModel.id == id).first()
    if not cm:
        raise HTTPException(status_code=404, detail="Not found")
    return model_to_dict(cm)

@api_router.post("/ConceptMap", status_code=201)
async def create_concept_map(data: ConceptMapCreate, db: Session = Depends(get_db)):
    cm = ConceptMapModel(
        id=str(uuid.uuid4()),
        url=data.url,
        version=data.version,
        name=data.name,
        title=data.title,
        status=data.status,
        publisher=data.publisher,
        description=data.description,
        source_canonical=data.sourceCanonical,
        target_canonical=data.targetCanonical,
        group=json.dumps(data.group) if data.group else None,
        date=datetime.utcnow()
    )
    db.add(cm)
    db.commit()
    return model_to_dict(cm)

@api_router.put("/ConceptMap/{id}")
async def update_concept_map(id: str, data: ConceptMapCreate, db: Session = Depends(get_db)):
    cm = db.query(ConceptMapModel).filter(ConceptMapModel.id == id).first()
    if not cm:
        raise HTTPException(status_code=404, detail="ConceptMap not found")
    
    cm.url = data.url
    cm.version = data.version
    cm.name = data.name
    cm.title = data.title
    cm.status = data.status
    cm.publisher = data.publisher
    cm.description = data.description
    cm.source_canonical = data.sourceCanonical
    cm.target_canonical = data.targetCanonical
    cm.group = json.dumps(data.group) if data.group else None
    cm.date = datetime.utcnow()
    
    db.commit()
    db.refresh(cm)
    return model_to_dict(cm)

@api_router.delete("/ConceptMap/{id}", status_code=204)
async def delete_concept_map(id: str, db: Session = Depends(get_db)):
    cm = db.query(ConceptMapModel).filter(ConceptMapModel.id == id).first()
    if not cm:
        raise HTTPException(status_code=404, detail="Not found")
    db.delete(cm)
    db.commit()

# FHIR Operations
@api_router.get("/CodeSystem/$lookup")
async def codesystem_lookup(
    system: str = Query(...),
    code: str = Query(...),
    version: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    result = terminology_service.lookup(db, system, code, version)
    return result.model_dump()

@api_router.get("/CodeSystem/$validate-code")
async def codesystem_validate(
    system: str = Query(...),
    code: str = Query(...),
    version: Optional[str] = Query(None),
    display: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    result = terminology_service.validate_code(db, system, code, version, display)
    return result.model_dump()

@api_router.get("/CodeSystem/$subsumes")
async def codesystem_subsumes(
    system: str = Query(...),
    codeA: str = Query(...),
    codeB: str = Query(...),
    version: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """
    Test the subsumption relationship between code A and code B
    """
    result = terminology_service.subsumes(db, system, codeA, codeB, version)
    return result.model_dump()

@api_router.get("/ValueSet/$expand")
async def valueset_expand(
    url: str = Query(...),
    filter: Optional[str] = Query(None),
    offset: int = Query(0),
    count: Optional[int] = Query(None),
    db: Session = Depends(get_db)
):
    return terminology_service.expand_valueset(db, url=url, filter_text=filter, offset=offset, count=count)

@api_router.get("/ValueSet/$validate-code")
async def valueset_validate_code(
    url: str = Query(...),
    code: str = Query(...),
    system: Optional[str] = Query(None),
    display: Optional[str] = Query(None),
    version: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """
    Validate a code against a ValueSet
    """
    result = terminology_service.validate_code_in_valueset(db, url, code, system, display, version)
    return result.model_dump()

@api_router.get("/ConceptMap/$translate")
async def conceptmap_translate(
    url: Optional[str] = Query(None),
    conceptMapId: Optional[str] = Query(None),
    code: Optional[str] = Query(None),
    system: Optional[str] = Query(None),
    source: Optional[str] = Query(None),
    target: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """
    Translate a code from source to target using a ConceptMap
    """
    result = terminology_service.translate(
        db, url=url, conceptmap_id=conceptMapId, 
        code=code, system=system, source=source, target=target
    )
    return result.model_dump()

@api_router.get("/metadata")
async def get_capability_statement():
    """
    Return the CapabilityStatement for this FHIR Terminology Server
    """
    capability = {
        "resourceType": "CapabilityStatement",
        "id": "fhir-terminology-server",
        "url": "https://terminology-manager.preview.emergentagent.com/api/metadata",
        "version": "1.0.0",
        "name": "FHIRTerminologyServer",
        "title": "FHIR Terminology Service",
        "status": "active",
        "experimental": False,
        "date": datetime.now(timezone.utc).isoformat(),
        "publisher": "FHIR Terminology Service",
        "description": "A comprehensive FHIR R4 Terminology Service supporting CodeSystem, ValueSet, and ConceptMap resources with full terminology operations",
        "kind": "instance",
        "software": {
            "name": "FHIR Terminology Service",
            "version": "1.0.0"
        },
        "implementation": {
            "description": "FHIR R4 Terminology Server with PostgreSQL backend",
            "url": "https://terminology-manager.preview.emergentagent.com/api"
        },
        "fhirVersion": "4.0.1",
        "format": ["json", "application/fhir+json"],
        "rest": [{
            "mode": "server",
            "documentation": "RESTful FHIR Terminology Service",
            "security": {
                "extension": [{
                    "url": "http://fhir-registry.smarthealthit.org/StructureDefinition/oauth-uris",
                    "extension": [{
                        "url": "token",
                        "valueUri": "https://terminology-manager.preview.emergentagent.com/api/auth/login"
                    }]
                }],
                "cors": True,
                "service": [{
                    "coding": [{
                        "system": "http://terminology.hl7.org/CodeSystem/restful-security-service",
                        "code": "OAuth",
                        "display": "OAuth"
                    }],
                    "text": "JWT Bearer Token Authentication"
                }],
                "description": "JWT-based authentication required for write operations"
            },
            "resource": [
                {
                    "type": "CodeSystem",
                    "profile": "http://hl7.org/fhir/StructureDefinition/CodeSystem",
                    "interaction": [
                        {"code": "read"},
                        {"code": "search-type"},
                        {"code": "create"},
                        {"code": "update"}
                    ],
                    "versioning": "versioned",
                    "readHistory": False,
                    "updateCreate": False,
                    "conditionalCreate": False,
                    "conditionalUpdate": False,
                    "conditionalDelete": "not-supported",
                    "searchParam": [
                        {"name": "url", "type": "uri", "documentation": "The uri that identifies the code system"},
                        {"name": "name", "type": "string", "documentation": "Computationally friendly name of the code system"},
                        {"name": "status", "type": "token", "documentation": "The current status of the code system"},
                        {"name": "version", "type": "token", "documentation": "The business version of the code system"}
                    ],
                    "operation": [
                        {
                            "name": "lookup",
                            "definition": "http://hl7.org/fhir/OperationDefinition/CodeSystem-lookup",
                            "documentation": "Given a code/system, get additional details about the concept"
                        },
                        {
                            "name": "validate-code",
                            "definition": "http://hl7.org/fhir/OperationDefinition/CodeSystem-validate-code",
                            "documentation": "Validate that a coded value is in the code system"
                        },
                        {
                            "name": "subsumes",
                            "definition": "http://hl7.org/fhir/OperationDefinition/CodeSystem-subsumes",
                            "documentation": "Test subsumption relationship between two codes"
                        }
                    ]
                },
                {
                    "type": "ValueSet",
                    "profile": "http://hl7.org/fhir/StructureDefinition/ValueSet",
                    "interaction": [
                        {"code": "read"},
                        {"code": "search-type"},
                        {"code": "create"},
                        {"code": "update"},
                        {"code": "delete"}
                    ],
                    "versioning": "versioned",
                    "readHistory": False,
                    "updateCreate": False,
                    "conditionalCreate": False,
                    "conditionalUpdate": False,
                    "conditionalDelete": "not-supported",
                    "searchParam": [
                        {"name": "url", "type": "uri", "documentation": "The uri that identifies the value set"},
                        {"name": "name", "type": "string", "documentation": "Computationally friendly name of the value set"},
                        {"name": "status", "type": "token", "documentation": "The current status of the value set"}
                    ],
                    "operation": [
                        {
                            "name": "expand",
                            "definition": "http://hl7.org/fhir/OperationDefinition/ValueSet-expand",
                            "documentation": "Expand a value set to return the list of codes"
                        },
                        {
                            "name": "validate-code",
                            "definition": "http://hl7.org/fhir/OperationDefinition/ValueSet-validate-code",
                            "documentation": "Validate that a coded value is in the value set"
                        }
                    ]
                },
                {
                    "type": "ConceptMap",
                    "profile": "http://hl7.org/fhir/StructureDefinition/ConceptMap",
                    "interaction": [
                        {"code": "read"},
                        {"code": "search-type"},
                        {"code": "create"},
                        {"code": "update"},
                        {"code": "delete"}
                    ],
                    "versioning": "versioned",
                    "readHistory": False,
                    "updateCreate": False,
                    "conditionalCreate": False,
                    "conditionalUpdate": False,
                    "conditionalDelete": "not-supported",
                    "searchParam": [
                        {"name": "url", "type": "uri", "documentation": "The uri that identifies the concept map"},
                        {"name": "name", "type": "string", "documentation": "Computationally friendly name of the concept map"},
                        {"name": "source", "type": "uri", "documentation": "The source value set"},
                        {"name": "target", "type": "uri", "documentation": "The target value set"}
                    ],
                    "operation": [
                        {
                            "name": "translate",
                            "definition": "http://hl7.org/fhir/OperationDefinition/ConceptMap-translate",
                            "documentation": "Translate a code from source to target value set"
                        }
                    ]
                }
            ]
        }]
    }
    
    return JSONResponse(content=capability)

app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
