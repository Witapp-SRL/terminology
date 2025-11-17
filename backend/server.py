from fastapi import FastAPI, APIRouter, HTTPException, Query, Depends, UploadFile, File, Form
from fastapi.responses import JSONResponse, StreamingResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
import os
import logging
from pathlib import Path
from typing import List, Optional
import uuid
from datetime import datetime, timezone, timedelta
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
from database import get_db, CodeSystemModel, ValueSetModel, ConceptMapModel, UserModel, AuditLogModel, OAuth2ClientModel, OAuth2TokenModel
from services.terminology_service_sql import TerminologyServiceSQL
from auth import (
    User, UserCreate, UserLogin, Token,
    authenticate_user, create_user, create_access_token,
    get_current_user, get_current_user_optional, create_audit_log,
    ACCESS_TOKEN_EXPIRE_MINUTES
)
from oauth2_service import (
    OAuth2ClientCreate, OAuth2ClientResponse, OAuth2TokenResponse, TokenInfo,
    create_oauth2_client, authenticate_client, create_oauth2_token,
    validate_token, revoke_token, check_scope_permission,
    get_smart_configuration, FHIR_SCOPES, generate_client_secret
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

# OAuth2 and SMART on FHIR endpoints

@api_router.get("/.well-known/smart-configuration")
async def smart_configuration():
    """
    SMART on FHIR configuration endpoint
    https://build.fhir.org/ig/HL7/smart-app-launch/conformance.html
    """
    return get_smart_configuration()

@api_router.post("/oauth2/clients", status_code=201)
async def create_client(
    client_data: OAuth2ClientCreate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """Create a new OAuth2 client (admin only)"""
    if not current_user.is_admin and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    client, plain_secret = create_oauth2_client(db, client_data, current_user.username)
    
    response = OAuth2ClientResponse.model_validate(client)
    # Include plain secret only on creation (no response_model to allow extra fields)
    return {
        **response.model_dump(),
        "client_secret": plain_secret,
        "warning": "Save the client_secret - it won't be shown again!"
    }

@api_router.get("/oauth2/clients")
async def list_clients(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """List OAuth2 clients (admin only)"""
    if not current_user.is_admin and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    query = db.query(OAuth2ClientModel)
    total = query.count()
    clients = query.offset(skip).limit(limit).all()
    
    return {
        "total": total,
        "clients": [OAuth2ClientResponse.model_validate(c).model_dump() for c in clients]
    }

@api_router.get("/oauth2/clients/{client_id}")
async def get_client(
    client_id: str,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """Get OAuth2 client details (admin only)"""
    if not current_user.is_admin and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    client = db.query(OAuth2ClientModel).filter(OAuth2ClientModel.client_id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    return OAuth2ClientResponse.model_validate(client)

@api_router.put("/oauth2/clients/{client_id}")
async def update_client(
    client_id: str,
    client_data: OAuth2ClientCreate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """Update OAuth2 client (admin only)"""
    if not current_user.is_admin and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    client = db.query(OAuth2ClientModel).filter(OAuth2ClientModel.client_id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    # Validate scopes
    invalid_scopes = [s for s in client_data.scopes if s not in FHIR_SCOPES]
    if invalid_scopes:
        raise HTTPException(status_code=400, detail=f"Invalid scopes: {', '.join(invalid_scopes)}")
    
    client.client_name = client_data.client_name
    client.description = client_data.description
    client.redirect_uris = client_data.redirect_uris
    client.grant_types = client_data.grant_types
    client.scopes = client_data.scopes
    
    db.commit()
    db.refresh(client)
    
    return OAuth2ClientResponse.model_validate(client)

@api_router.delete("/oauth2/clients/{client_id}", status_code=204)
async def delete_client(
    client_id: str,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """Deactivate OAuth2 client (admin only)"""
    if not current_user.is_admin and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    client = db.query(OAuth2ClientModel).filter(OAuth2ClientModel.client_id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    client.is_active = False
    db.commit()

@api_router.post("/oauth2/clients/{client_id}/reset-secret")
async def reset_client_secret(
    client_id: str,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """Reset client secret (admin only)"""
    if not current_user.is_admin and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    client = db.query(OAuth2ClientModel).filter(OAuth2ClientModel.client_id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    from oauth2_service import hash_secret
    new_secret = generate_client_secret()
    client.client_secret_hash = hash_secret(new_secret)
    db.commit()
    
    return {
        "client_id": client_id,
        "client_secret": new_secret,
        "warning": "Save the client_secret - it won't be shown again!"
    }

@api_router.post("/oauth2/token")
async def oauth2_token(
    grant_type: str = Form(...),
    client_id: str = Form(...),
    client_secret: str = Form(...),
    code: Optional[str] = Form(None),
    refresh_token: Optional[str] = Form(None),
    redirect_uri: Optional[str] = Form(None),
    scope: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """
    OAuth2 token endpoint
    Supports: authorization_code, client_credentials, refresh_token
    """
    # Authenticate client
    client = authenticate_client(db, client_id, client_secret)
    if not client:
        raise HTTPException(
            status_code=401,
            detail="Invalid client credentials",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    # Check grant type is allowed
    if grant_type not in client.grant_types:
        raise HTTPException(status_code=400, detail=f"Grant type {grant_type} not allowed for this client")
    
    if grant_type == "client_credentials":
        # Server-to-server authentication
        requested_scopes = scope.split() if scope else client.scopes
        
        # Verify scopes are allowed for this client
        for s in requested_scopes:
            if s not in client.scopes:
                raise HTTPException(status_code=400, detail=f"Scope {s} not allowed")
        
        # Create token without user context
        token = create_oauth2_token(db, client, requested_scopes, user=None, include_refresh=False)
        
        return OAuth2TokenResponse(
            access_token=token.access_token,
            token_type="Bearer",
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            scope=" ".join(requested_scopes)
        )
    
    elif grant_type == "refresh_token":
        if not refresh_token:
            raise HTTPException(status_code=400, detail="refresh_token required")
        
        # Find and validate refresh token
        token_model = db.query(OAuth2TokenModel).filter(
            OAuth2TokenModel.refresh_token == refresh_token,
            OAuth2TokenModel.client_id == client_id,
            OAuth2TokenModel.revoked == False
        ).first()
        
        # Handle timezone-aware comparison
        if token_model:
            refresh_expires_at = token_model.refresh_expires_at
            if refresh_expires_at and refresh_expires_at.tzinfo is None:
                refresh_expires_at = refresh_expires_at.replace(tzinfo=timezone.utc)
            
            if not token_model or (refresh_expires_at and datetime.now(timezone.utc) > refresh_expires_at):
                raise HTTPException(status_code=400, detail="Invalid or expired refresh token")
        else:
            raise HTTPException(status_code=400, detail="Invalid or expired refresh token")
        
        # Get user if exists
        user = db.query(UserModel).filter(UserModel.id == token_model.user_id).first() if token_model.user_id else None
        
        # Create new token
        new_token = create_oauth2_token(db, client, token_model.scopes, user, include_refresh=True)
        
        # Revoke old token
        token_model.revoked = True
        db.commit()
        
        return OAuth2TokenResponse(
            access_token=new_token.access_token,
            token_type="Bearer",
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            refresh_token=new_token.refresh_token,
            scope=" ".join(new_token.scopes)
        )
    
    else:
        raise HTTPException(status_code=400, detail="Unsupported grant type")

@api_router.post("/oauth2/introspect")
async def introspect_token(
    token: str = Form(...),
    client_id: str = Form(...),
    client_secret: str = Form(...),
    db: Session = Depends(get_db)
):
    """Token introspection endpoint"""
    # Authenticate client
    client = authenticate_client(db, client_id, client_secret)
    if not client:
        raise HTTPException(status_code=401, detail="Invalid client credentials")
    
    # Validate token
    token_info = validate_token(db, token)
    
    if not token_info:
        return TokenInfo(active=False)
    
    return TokenInfo(**token_info)

@api_router.post("/oauth2/revoke")
async def revoke_oauth2_token(
    token: str = Form(...),
    client_id: str = Form(...),
    client_secret: str = Form(...),
    db: Session = Depends(get_db)
):
    """Token revocation endpoint"""
    # Authenticate client
    client = authenticate_client(db, client_id, client_secret)
    if not client:
        raise HTTPException(status_code=401, detail="Invalid client credentials")
    
    revoke_token(db, token)
    return {"status": "revoked"}

@api_router.get("/oauth2/tokens")
async def list_active_tokens(
    client_id: Optional[str] = None,
    user_id: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """List active tokens (admin only)"""
    if not current_user.is_admin and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Get all non-revoked tokens first
    query = db.query(OAuth2TokenModel).filter(OAuth2TokenModel.revoked == False)
    
    if client_id:
        query = query.filter(OAuth2TokenModel.client_id == client_id)
    if user_id:
        query = query.filter(OAuth2TokenModel.user_id == user_id)
    
    # Filter by expiration in Python to handle timezone issues
    all_tokens = query.order_by(OAuth2TokenModel.created_at.desc()).all()
    now = datetime.now(timezone.utc)
    
    active_tokens = []
    for t in all_tokens:
        expires_at = t.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        if expires_at > now:
            active_tokens.append(t)
    
    # Apply pagination
    total = len(active_tokens)
    tokens = active_tokens[skip:skip+limit]
    
    return {
        "total": total,
        "tokens": [
            {
                "id": t.id,
                "client_id": t.client_id,
                "user_id": t.user_id,
                "scopes": t.scopes,
                "created_at": t.created_at.isoformat(),
                "expires_at": t.expires_at.isoformat(),
                "token_preview": t.access_token[:10] + "..."
            }
            for t in tokens
        ]
    }

@api_router.delete("/oauth2/tokens/{token_id}")
async def revoke_token_by_id(
    token_id: str,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """Revoke a token by ID (admin only)"""
    if not current_user.is_admin and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    token = db.query(OAuth2TokenModel).filter(OAuth2TokenModel.id == token_id).first()
    if not token:
        raise HTTPException(status_code=404, detail="Token not found")
    
    token.revoked = True
    token.revoked_at = datetime.now(timezone.utc)
    db.commit()
    
    return {"status": "revoked"}

@api_router.get("/oauth2/scopes")
async def list_available_scopes():
    """List all available FHIR scopes"""
    return {
        "scopes": [
            {"name": name, "description": desc}
            for name, desc in FHIR_SCOPES.items()
        ]
    }

# Admin - User Management
@api_router.get("/admin/users")
async def list_users(
    skip: int = 0,
    limit: int = 100,
    role: Optional[str] = None,
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """List users (admin only)"""
    if not current_user.is_admin and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    query = db.query(UserModel)
    
    if role:
        query = query.filter(UserModel.role == role)
    if is_active is not None:
        query = query.filter(UserModel.is_active == is_active)
    
    total = query.count()
    users = query.offset(skip).limit(limit).all()
    
    return {
        "total": total,
        "users": [
            {
                "id": u.id,
                "username": u.username,
                "email": u.email,
                "full_name": u.full_name,
                "role": u.role,
                "is_active": u.is_active,
                "is_admin": u.is_admin,
                "created_at": u.created_at.isoformat(),
                "last_login": u.last_login.isoformat() if u.last_login else None
            }
            for u in users
        ]
    }

@api_router.put("/admin/users/{user_id}/role")
async def update_user_role(
    user_id: str,
    role: str,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """Update user role (admin only)"""
    if not current_user.is_admin and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    allowed_roles = ["user", "admin", "clinician", "researcher"]
    if role not in allowed_roles:
        raise HTTPException(status_code=400, detail=f"Invalid role. Allowed: {allowed_roles}")
    
    user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.role = role
    user.is_admin = (role == "admin")
    db.commit()
    
    return {"status": "updated", "user_id": user_id, "new_role": role}

@api_router.delete("/admin/users/{user_id}")
async def deactivate_user(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """Deactivate user (admin only)"""
    if not current_user.is_admin and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if user.id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot deactivate yourself")
    
    user.is_active = False
    db.commit()
    
    return {"status": "deactivated"}

@api_router.get("/admin/dashboard")
async def admin_dashboard(
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """Get admin dashboard statistics"""
    if not current_user.is_admin and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    from sqlalchemy import func
    
    stats = {
        "users": {
            "total": db.query(UserModel).count(),
            "active": db.query(UserModel).filter(UserModel.is_active == True).count(),
            "by_role": {}
        },
        "oauth2_clients": {
            "total": db.query(OAuth2ClientModel).count(),
            "active": db.query(OAuth2ClientModel).filter(OAuth2ClientModel.is_active == True).count()
        },
        "tokens": {
            "total": db.query(OAuth2TokenModel).count(),
            "active": db.query(OAuth2TokenModel).filter(
                OAuth2TokenModel.revoked == False,
                OAuth2TokenModel.expires_at > datetime.now(timezone.utc)
            ).count(),
            "revoked": db.query(OAuth2TokenModel).filter(OAuth2TokenModel.revoked == True).count()
        },
        "resources": {
            "code_systems": db.query(CodeSystemModel).count(),
            "value_sets": db.query(ValueSetModel).count(),
            "concept_maps": db.query(ConceptMapModel).count(),
            "code_systems_active": db.query(CodeSystemModel).filter(CodeSystemModel.active == True).count()
        },
        "audit_logs": {
            "total": db.query(AuditLogModel).count(),
            "last_24h": db.query(AuditLogModel).filter(
                AuditLogModel.timestamp > datetime.now(timezone.utc) - timedelta(days=1)
            ).count()
        }
    }
    
    # Count by role
    role_counts = db.query(UserModel.role, func.count(UserModel.id)).group_by(UserModel.role).all()
    stats["users"]["by_role"] = {role: count for role, count in role_counts}
    
    return stats

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
        "url": "https://fhirterm.preview.emergentagent.com/api/metadata",
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
            "url": "https://fhirterm.preview.emergentagent.com/api"
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
                        "valueUri": "https://fhirterm.preview.emergentagent.com/api/auth/login"
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
