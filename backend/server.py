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
    db: Session = Depends(get_db)
):
    query = db.query(CodeSystemModel)
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
async def create_code_system(data: CodeSystemCreate, db: Session = Depends(get_db)):
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
        property=json.dumps(data.property) if data.property else None,
        concept=json.dumps(data.concept) if data.concept else None,
        count=len(data.concept) if data.concept else 0,
        date=datetime.utcnow()
    )
    db.add(cs)
    db.commit()
    return model_to_dict(cs)

@api_router.put("/CodeSystem/{id}")
async def update_code_system(id: str, data: CodeSystemCreate, db: Session = Depends(get_db)):
    cs = db.query(CodeSystemModel).filter(CodeSystemModel.id == id).first()
    if not cs:
        raise HTTPException(status_code=404, detail="CodeSystem not found")
    
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
    cs.property = json.dumps(data.property) if data.property else None
    cs.concept = json.dumps(data.concept) if data.concept else None
    cs.count = len(data.concept) if data.concept else 0
    cs.date = datetime.utcnow()
    
    db.commit()
    db.refresh(cs)
    return model_to_dict(cs)

@api_router.delete("/CodeSystem/{id}", status_code=204)
async def delete_code_system(id: str, db: Session = Depends(get_db)):
    cs = db.query(CodeSystemModel).filter(CodeSystemModel.id == id).first()
    if not cs:
        raise HTTPException(status_code=404, detail="Not found")
    db.delete(cs)
    db.commit()

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

@api_router.get("/ValueSet/$expand")
async def valueset_expand(
    url: str = Query(...),
    filter: Optional[str] = Query(None),
    offset: int = Query(0),
    count: Optional[int] = Query(None),
    db: Session = Depends(get_db)
):
    return terminology_service.expand_valueset(db, url=url, filter_text=filter, offset=offset, count=count)

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
