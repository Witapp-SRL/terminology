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
from database import get_db, CodeSystemModel, ValueSetModel, ConceptMapModel
from services.terminology_service_sql import TerminologyServiceSQL

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Create the main app without a prefix
app = FastAPI(title="FHIR Terminology Service", version="1.0.0")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")


# ==================== HEALTH CHECK ====================
@api_router.get("/")
async def root():
    return {"message": "FHIR Terminology Service", "version": "1.0.0", "status": "active"}


# ==================== METADATA ENDPOINTS ====================
@api_router.get("/metadata")
async def get_capability_statement(mode: Optional[str] = Query(None)):
    """Get CapabilityStatement or TerminologyCapabilities"""
    if mode == "terminology":
        # Return TerminologyCapabilities
        code_systems = await db.code_systems.find({}, {"_id": 0, "url": 1, "version": 1, "content": 1}).to_list(100)
        
        return {
            "resourceType": "TerminologyCapabilities",
            "id": "terminology-server",
            "url": "http://terminology-service/TerminologyCapabilities",
            "name": "FHIRTerminologyServiceCapabilities",
            "title": "FHIR Terminology Service Capabilities",
            "status": "active",
            "date": datetime.now(timezone.utc).isoformat(),
            "kind": "instance",
            "software": {
                "name": "FHIR Terminology Service",
                "version": "1.0.0"
            },
            "implementation": {
                "description": "FHIR Terminology Service Implementation",
                "url": "http://terminology-service"
            },
            "fhirVersion": "4.0.1",
            "codeSystem": [
                {
                    "uri": cs["url"],
                    "version": {"code": cs.get("version", "1.0.0")},
                    "content": cs.get("content", "complete")
                }
                for cs in code_systems
            ]
        }
    else:
        # Return CapabilityStatement
        return {
            "resourceType": "CapabilityStatement",
            "id": "terminology-server",
            "url": "http://terminology-service/CapabilityStatement",
            "name": "FHIRTerminologyService",
            "title": "FHIR Terminology Service",
            "status": "active",
            "date": datetime.now(timezone.utc).isoformat(),
            "kind": "instance",
            "fhirVersion": "4.0.1",
            "format": ["json", "xml"],
            "rest": [{
                "mode": "server",
                "resource": [
                    {
                        "type": "CodeSystem",
                        "interaction": [
                            {"code": "read"},
                            {"code": "search-type"},
                            {"code": "create"},
                            {"code": "update"},
                            {"code": "delete"}
                        ],
                        "searchParam": [
                            {"name": "url", "type": "uri"},
                            {"name": "version", "type": "string"},
                            {"name": "name", "type": "string"},
                            {"name": "title", "type": "string"},
                            {"name": "status", "type": "token"}
                        ],
                        "operation": [
                            {"name": "lookup", "definition": "http://hl7.org/fhir/OperationDefinition/CodeSystem-lookup"},
                            {"name": "validate-code", "definition": "http://hl7.org/fhir/OperationDefinition/CodeSystem-validate-code"},
                            {"name": "subsumes", "definition": "http://hl7.org/fhir/OperationDefinition/CodeSystem-subsumes"}
                        ]
                    },
                    {
                        "type": "ValueSet",
                        "interaction": [
                            {"code": "read"},
                            {"code": "search-type"},
                            {"code": "create"},
                            {"code": "update"},
                            {"code": "delete"}
                        ],
                        "searchParam": [
                            {"name": "url", "type": "uri"},
                            {"name": "version", "type": "string"},
                            {"name": "name", "type": "string"},
                            {"name": "title", "type": "string"},
                            {"name": "status", "type": "token"}
                        ],
                        "operation": [
                            {"name": "expand", "definition": "http://hl7.org/fhir/OperationDefinition/ValueSet-expand"},
                            {"name": "validate-code", "definition": "http://hl7.org/fhir/OperationDefinition/ValueSet-validate-code"}
                        ]
                    },
                    {
                        "type": "ConceptMap",
                        "interaction": [
                            {"code": "read"},
                            {"code": "search-type"},
                            {"code": "create"},
                            {"code": "update"},
                            {"code": "delete"}
                        ],
                        "searchParam": [
                            {"name": "url", "type": "uri"},
                            {"name": "version", "type": "string"},
                            {"name": "name", "type": "string"},
                            {"name": "title", "type": "string"},
                            {"name": "status", "type": "token"}
                        ],
                        "operation": [
                            {"name": "translate", "definition": "http://hl7.org/fhir/OperationDefinition/ConceptMap-translate"}
                        ]
                    }
                ]
            }]
        }


# ==================== CODE SYSTEM CRUD ====================
@api_router.get("/CodeSystem", response_model=List[CodeSystem])
async def list_code_systems(
    url: Optional[str] = Query(None),
    name: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    title: Optional[str] = Query(None),
    version: Optional[str] = Query(None),
):
    """Search for code systems"""
    query = {}
    if url:
        query["url"] = url
    if name:
        query["name"] = {"$regex": name, "$options": "i"}
    if status:
        query["status"] = status
    if title:
        query["title"] = {"$regex": title, "$options": "i"}
    if version:
        query["version"] = version
    
    code_systems = await db.code_systems.find(query, {"_id": 0}).to_list(100)
    return code_systems


@api_router.get("/CodeSystem/{id}", response_model=CodeSystem)
async def get_code_system(id: str):
    """Get a specific code system by ID"""
    code_system = await db.code_systems.find_one({"id": id}, {"_id": 0})
    if not code_system:
        raise HTTPException(status_code=404, detail="CodeSystem not found")
    return code_system


@api_router.post("/CodeSystem", response_model=CodeSystem, status_code=201)
async def create_code_system(code_system_create: CodeSystemCreate):
    """Create a new code system"""
    # Check if URL already exists
    existing = await db.code_systems.find_one({"url": code_system_create.url})
    if existing:
        raise HTTPException(status_code=409, detail="CodeSystem with this URL already exists")
    
    code_system = CodeSystem(
        id=str(uuid.uuid4()),
        date=datetime.now(timezone.utc),
        **code_system_create.model_dump()
    )
    
    doc = code_system.model_dump()
    if doc.get("date"):
        doc["date"] = doc["date"].isoformat()
    
    await db.code_systems.insert_one(doc)
    return code_system


@api_router.put("/CodeSystem/{id}", response_model=CodeSystem)
async def update_code_system(id: str, code_system_create: CodeSystemCreate):
    """Update an existing code system"""
    existing = await db.code_systems.find_one({"id": id})
    if not existing:
        raise HTTPException(status_code=404, detail="CodeSystem not found")
    
    code_system = CodeSystem(
        id=id,
        date=datetime.now(timezone.utc),
        **code_system_create.model_dump()
    )
    
    doc = code_system.model_dump()
    if doc.get("date"):
        doc["date"] = doc["date"].isoformat()
    
    await db.code_systems.replace_one({"id": id}, doc)
    return code_system


@api_router.delete("/CodeSystem/{id}", status_code=204)
async def delete_code_system(id: str):
    """Delete a code system"""
    result = await db.code_systems.delete_one({"id": id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="CodeSystem not found")
    return None


# ==================== VALUE SET CRUD ====================
@api_router.get("/ValueSet", response_model=List[ValueSet])
async def list_value_sets(
    url: Optional[str] = Query(None),
    name: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    title: Optional[str] = Query(None),
    version: Optional[str] = Query(None),
):
    """Search for value sets"""
    query = {}
    if url:
        query["url"] = url
    if name:
        query["name"] = {"$regex": name, "$options": "i"}
    if status:
        query["status"] = status
    if title:
        query["title"] = {"$regex": title, "$options": "i"}
    if version:
        query["version"] = version
    
    value_sets = await db.value_sets.find(query, {"_id": 0}).to_list(100)
    return value_sets


@api_router.get("/ValueSet/{id}", response_model=ValueSet)
async def get_value_set(id: str):
    """Get a specific value set by ID"""
    value_set = await db.value_sets.find_one({"id": id}, {"_id": 0})
    if not value_set:
        raise HTTPException(status_code=404, detail="ValueSet not found")
    return value_set


@api_router.post("/ValueSet", response_model=ValueSet, status_code=201)
async def create_value_set(value_set_create: ValueSetCreate):
    """Create a new value set"""
    existing = await db.value_sets.find_one({"url": value_set_create.url})
    if existing:
        raise HTTPException(status_code=409, detail="ValueSet with this URL already exists")
    
    value_set = ValueSet(
        id=str(uuid.uuid4()),
        date=datetime.now(timezone.utc),
        **value_set_create.model_dump()
    )
    
    doc = value_set.model_dump()
    if doc.get("date"):
        doc["date"] = doc["date"].isoformat()
    
    await db.value_sets.insert_one(doc)
    return value_set


@api_router.put("/ValueSet/{id}", response_model=ValueSet)
async def update_value_set(id: str, value_set_create: ValueSetCreate):
    """Update an existing value set"""
    existing = await db.value_sets.find_one({"id": id})
    if not existing:
        raise HTTPException(status_code=404, detail="ValueSet not found")
    
    value_set = ValueSet(
        id=id,
        date=datetime.now(timezone.utc),
        **value_set_create.model_dump()
    )
    
    doc = value_set.model_dump()
    if doc.get("date"):
        doc["date"] = doc["date"].isoformat()
    
    await db.value_sets.replace_one({"id": id}, doc)
    return value_set


@api_router.delete("/ValueSet/{id}", status_code=204)
async def delete_value_set(id: str):
    """Delete a value set"""
    result = await db.value_sets.delete_one({"id": id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="ValueSet not found")
    return None


# ==================== CONCEPT MAP CRUD ====================
@api_router.get("/ConceptMap", response_model=List[ConceptMap])
async def list_concept_maps(
    url: Optional[str] = Query(None),
    name: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    title: Optional[str] = Query(None),
    version: Optional[str] = Query(None),
):
    """Search for concept maps"""
    query = {}
    if url:
        query["url"] = url
    if name:
        query["name"] = {"$regex": name, "$options": "i"}
    if status:
        query["status"] = status
    if title:
        query["title"] = {"$regex": title, "$options": "i"}
    if version:
        query["version"] = version
    
    concept_maps = await db.concept_maps.find(query, {"_id": 0}).to_list(100)
    return concept_maps


@api_router.get("/ConceptMap/{id}", response_model=ConceptMap)
async def get_concept_map(id: str):
    """Get a specific concept map by ID"""
    concept_map = await db.concept_maps.find_one({"id": id}, {"_id": 0})
    if not concept_map:
        raise HTTPException(status_code=404, detail="ConceptMap not found")
    return concept_map


@api_router.post("/ConceptMap", response_model=ConceptMap, status_code=201)
async def create_concept_map(concept_map_create: ConceptMapCreate):
    """Create a new concept map"""
    existing = await db.concept_maps.find_one({"url": concept_map_create.url})
    if existing:
        raise HTTPException(status_code=409, detail="ConceptMap with this URL already exists")
    
    concept_map = ConceptMap(
        id=str(uuid.uuid4()),
        date=datetime.now(timezone.utc),
        **concept_map_create.model_dump()
    )
    
    doc = concept_map.model_dump()
    if doc.get("date"):
        doc["date"] = doc["date"].isoformat()
    
    await db.concept_maps.insert_one(doc)
    return concept_map


@api_router.put("/ConceptMap/{id}", response_model=ConceptMap)
async def update_concept_map(id: str, concept_map_create: ConceptMapCreate):
    """Update an existing concept map"""
    existing = await db.concept_maps.find_one({"id": id})
    if not existing:
        raise HTTPException(status_code=404, detail="ConceptMap not found")
    
    concept_map = ConceptMap(
        id=id,
        date=datetime.now(timezone.utc),
        **concept_map_create.model_dump()
    )
    
    doc = concept_map.model_dump()
    if doc.get("date"):
        doc["date"] = doc["date"].isoformat()
    
    await db.concept_maps.replace_one({"id": id}, doc)
    return concept_map


@api_router.delete("/ConceptMap/{id}", status_code=204)
async def delete_concept_map(id: str):
    """Delete a concept map"""
    result = await db.concept_maps.delete_one({"id": id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="ConceptMap not found")
    return None


# ==================== FHIR OPERATIONS ====================

# CodeSystem Operations
@api_router.get("/CodeSystem/$lookup", response_model=Parameters)
async def codesystem_lookup_get(
    system: str = Query(..., description="The code system URL"),
    code: str = Query(..., description="The code to lookup"),
    version: Optional[str] = Query(None, description="The version of the code system"),
    property: Optional[List[str]] = Query(None, description="Properties to return"),
):
    """$lookup operation - Get information about a code (GET)"""
    try:
        return await terminology_service.lookup(system, code, version, property)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@api_router.post("/CodeSystem/$lookup", response_model=Parameters)
async def codesystem_lookup_post(params: Parameters):
    """$lookup operation - Get information about a code (POST)"""
    try:
        # Extract parameters
        system = None
        code = None
        version = None
        properties = []
        
        for param in params.parameter:
            if param.name == "system":
                system = param.valueUri or param.valueString
            elif param.name == "code":
                code = param.valueCode or param.valueString
            elif param.name == "version":
                version = param.valueString
            elif param.name == "property":
                properties.append(param.valueCode or param.valueString)
        
        if not system or not code:
            raise HTTPException(status_code=400, detail="system and code are required")
        
        return await terminology_service.lookup(system, code, version, properties if properties else None)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@api_router.get("/CodeSystem/$validate-code", response_model=Parameters)
async def codesystem_validate_get(
    system: str = Query(..., description="The code system URL"),
    code: str = Query(..., description="The code to validate"),
    version: Optional[str] = Query(None, description="The version of the code system"),
    display: Optional[str] = Query(None, description="The display string"),
):
    """$validate-code operation for CodeSystem (GET)"""
    try:
        return await terminology_service.validate_code(system, code, version, display)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@api_router.post("/CodeSystem/$validate-code", response_model=Parameters)
async def codesystem_validate_post(params: Parameters):
    """$validate-code operation for CodeSystem (POST)"""
    try:
        system = None
        code = None
        version = None
        display = None
        
        for param in params.parameter:
            if param.name == "system":
                system = param.valueUri or param.valueString
            elif param.name == "code":
                code = param.valueCode or param.valueString
            elif param.name == "version":
                version = param.valueString
            elif param.name == "display":
                display = param.valueString
        
        if not system or not code:
            raise HTTPException(status_code=400, detail="system and code are required")
        
        return await terminology_service.validate_code(system, code, version, display)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@api_router.get("/CodeSystem/$subsumes", response_model=Parameters)
async def codesystem_subsumes_get(
    system: str = Query(..., description="The code system URL"),
    codeA: str = Query(..., description="First code"),
    codeB: str = Query(..., description="Second code"),
    version: Optional[str] = Query(None, description="The version of the code system"),
):
    """$subsumes operation (GET)"""
    try:
        return await terminology_service.subsumes(system, codeA, codeB, version)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@api_router.post("/CodeSystem/$subsumes", response_model=Parameters)
async def codesystem_subsumes_post(params: Parameters):
    """$subsumes operation (POST)"""
    try:
        system = None
        code_a = None
        code_b = None
        version = None
        
        for param in params.parameter:
            if param.name == "system":
                system = param.valueUri or param.valueString
            elif param.name == "codeA":
                code_a = param.valueCode or param.valueString
            elif param.name == "codeB":
                code_b = param.valueCode or param.valueString
            elif param.name == "version":
                version = param.valueString
        
        if not system or not code_a or not code_b:
            raise HTTPException(status_code=400, detail="system, codeA, and codeB are required")
        
        return await terminology_service.subsumes(system, code_a, code_b, version)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ValueSet Operations
@api_router.get("/ValueSet/$expand", response_model=ValueSet)
async def valueset_expand_get(
    url: str = Query(..., description="The value set URL"),
    filter: Optional[str] = Query(None, description="Text filter"),
    offset: int = Query(0, description="Pagination offset"),
    count: Optional[int] = Query(None, description="Number of results"),
):
    """$expand operation (GET)"""
    try:
        return await terminology_service.expand_valueset(url=url, filter_text=filter, offset=offset, count=count)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@api_router.get("/ValueSet/{id}/$expand", response_model=ValueSet)
async def valueset_expand_by_id_get(
    id: str,
    filter: Optional[str] = Query(None, description="Text filter"),
    offset: int = Query(0, description="Pagination offset"),
    count: Optional[int] = Query(None, description="Number of results"),
):
    """$expand operation by ID (GET)"""
    try:
        return await terminology_service.expand_valueset(valueset_id=id, filter_text=filter, offset=offset, count=count)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@api_router.get("/ValueSet/$validate-code", response_model=Parameters)
async def valueset_validate_get(
    url: str = Query(..., description="The value set URL"),
    code: str = Query(..., description="The code to validate"),
    system: str = Query(..., description="The code system URL"),
    systemVersion: Optional[str] = Query(None, description="The system version"),
    display: Optional[str] = Query(None, description="The display string"),
):
    """$validate-code operation for ValueSet (GET)"""
    try:
        return await terminology_service.validate_code_valueset(url, code, system, systemVersion, display)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@api_router.get("/ValueSet/{id}/$validate-code", response_model=Parameters)
async def valueset_validate_by_id_get(
    id: str,
    code: str = Query(..., description="The code to validate"),
    system: str = Query(..., description="The code system URL"),
    systemVersion: Optional[str] = Query(None, description="The system version"),
    display: Optional[str] = Query(None, description="The display string"),
):
    """$validate-code operation for ValueSet by ID (GET)"""
    try:
        # Get URL from ID
        valueset = await db.value_sets.find_one({"id": id}, {"_id": 0, "url": 1})
        if not valueset:
            raise HTTPException(status_code=404, detail="ValueSet not found")
        
        return await terminology_service.validate_code_valueset(valueset["url"], code, system, systemVersion, display)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ConceptMap Operations
@api_router.get("/ConceptMap/$translate", response_model=Parameters)
async def conceptmap_translate_get(
    url: Optional[str] = Query(None, description="The concept map URL"),
    sourceCode: str = Query(..., alias="code", description="The source code"),
    system: str = Query(..., description="The source system"),
    targetSystem: Optional[str] = Query(None, description="The target system"),
):
    """$translate operation (GET)"""
    try:
        return await terminology_service.translate(url, sourceCode, system, targetSystem)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@api_router.get("/ConceptMap/{id}/$translate", response_model=Parameters)
async def conceptmap_translate_by_id_get(
    id: str,
    sourceCode: str = Query(..., alias="code", description="The source code"),
    system: str = Query(..., description="The source system"),
    targetSystem: Optional[str] = Query(None, description="The target system"),
):
    """$translate operation by ID (GET)"""
    try:
        # Get URL from ID
        concept_map = await db.concept_maps.find_one({"id": id}, {"_id": 0, "url": 1})
        if not concept_map:
            raise HTTPException(status_code=404, detail="ConceptMap not found")
        
        return await terminology_service.translate(concept_map["url"], sourceCode, system, targetSystem)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
# Initialize terminology service
terminology_service = TerminologyServiceSQL()

# Create the main app
app = FastAPI(title="FHIR Terminology Service", version="1.0.0")
api_router = APIRouter(prefix="/api")

@api_router.get("/")
async def root():
    return {"message": "FHIR Terminology Service", "version": "1.0.0", "status": "active"}

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
        
        # Create CodeSystem
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
    
    # Create CSV
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=["code", "display", "definition"])
    writer.writeheader()
    
    concepts = json.loads(cs.concept) if cs.concept else []
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

# CodeSystem CRUD (simplified for SQL)
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
    return JSONResponse(content=[_model_to_dict(r) for r in results])

@api_router.get("/CodeSystem/{id}")
async def get_code_system(id: str, db: Session = Depends(get_db)):
    cs = db.query(CodeSystemModel).filter(CodeSystemModel.id == id).first()
    if not cs:
        raise HTTPException(status_code=404, detail="CodeSystem not found")
    return _model_to_dict(cs)

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
    return _model_to_dict(cs)

@api_router.delete("/CodeSystem/{id}", status_code=204)
async def delete_code_system(id: str, db: Session = Depends(get_db)):
    cs = db.query(CodeSystemModel).filter(CodeSystemModel.id == id).first()
    if not cs:
        raise HTTPException(status_code=404, detail="Not found")
    db.delete(cs)
    db.commit()

# ValueSet endpoints (simplified)
@api_router.get("/ValueSet")
async def list_value_sets(db: Session = Depends(get_db)):
    results = db.query(ValueSetModel).all()
    return [_model_to_dict(r) for r in results]

@api_router.get("/ValueSet/{id}")
async def get_value_set(id: str, db: Session = Depends(get_db)):
    vs = db.query(ValueSetModel).filter(ValueSetModel.id == id).first()
    if not vs:
        raise HTTPException(status_code=404, detail="Not found")
    return _model_to_dict(vs)

# ConceptMap endpoints
@api_router.get("/ConceptMap")
async def list_concept_maps(db: Session = Depends(get_db)):
    results = db.query(ConceptMapModel).all()
    return [_model_to_dict(r) for r in results]

@api_router.get("/ConceptMap/{id}")
async def get_concept_map(id: str, db: Session = Depends(get_db)):
    cm = db.query(ConceptMapModel).filter(ConceptMapModel.id == id).first()
    if not cm:
        raise HTTPException(status_code=404, detail="Not found")
    return _model_to_dict(cm)

# FHIR Operations
@api_router.get("/CodeSystem/$lookup", response_model=Parameters)
async def codesystem_lookup(
    system: str = Query(...),
    code: str = Query(...),
    version: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    return terminology_service.lookup(db, system, code, version)

@api_router.get("/CodeSystem/$validate-code", response_model=Parameters)
async def codesystem_validate(
    system: str = Query(...),
    code: str = Query(...),
    version: Optional[str] = Query(None),
    display: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    return terminology_service.validate_code(db, system, code, version, display)

@api_router.get("/ValueSet/$expand")
async def valueset_expand(
    url: str = Query(...),
    filter: Optional[str] = Query(None),
    offset: int = Query(0),
    count: Optional[int] = Query(None),
    db: Session = Depends(get_db)
):
    return terminology_service.expand_valueset(db, url=url, filter_text=filter, offset=offset, count=count)

# Helper function
def _model_to_dict(model):
    result = {c.name: getattr(model, c.name) for c in model.__table__.columns}
    # Parse JSON fields
    for field in ['concept', 'property', 'compose', 'expansion', 'group']:
        if field in result and result[field] and isinstance(result[field], str):
            try:
                result[field] = json.loads(result[field])
            except:
                pass
    # Rename fields to camelCase for FHIR
    if 'resource_type' in result:
        result['resourceType'] = result.pop('resource_type')
    if 'case_sensitive' in result:
        result['caseSensitive'] = result.pop('case_sensitive')
    if 'source_canonical' in result:
        result['sourceCanonical'] = result.pop('source_canonical')
    if 'target_canonical' in result:
        result['targetCanonical'] = result.pop('target_canonical')
    return result

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
