"""
OAuth2 and SMART on FHIR Implementation
Compliant with FHIR Security specifications: https://build.fhir.org/security.html
"""
from datetime import datetime, timedelta, timezone
from typing import Optional, List, Dict
from passlib.context import CryptContext
from jose import JWTError, jwt
import secrets
import uuid
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from database import OAuth2ClientModel, OAuth2TokenModel, UserModel

# Configuration
SECRET_KEY = "your-secret-key-change-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60
REFRESH_TOKEN_EXPIRE_DAYS = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# FHIR/SMART Scopes
# Format: <patient|user|system>/<resource>.<read|write|*>
FHIR_SCOPES = {
    # Patient scopes (patient-specific data)
    "patient/*.read": "Read all patient data",
    "patient/*.write": "Write all patient data",
    "patient/CodeSystem.read": "Read patient's CodeSystems",
    "patient/ValueSet.read": "Read patient's ValueSets",
    "patient/ConceptMap.read": "Read patient's ConceptMaps",
    
    # User scopes (user-specific data)
    "user/*.read": "Read all user data",
    "user/*.write": "Write all user data",
    "user/CodeSystem.read": "Read user's CodeSystems",
    "user/CodeSystem.write": "Write user's CodeSystems",
    "user/ValueSet.read": "Read user's ValueSets",
    "user/ValueSet.write": "Write user's ValueSets",
    "user/ConceptMap.read": "Read user's ConceptMaps",
    "user/ConceptMap.write": "Write user's ConceptMaps",
    
    # System scopes (server-wide access, no user context)
    "system/*.read": "Read all resources",
    "system/*.write": "Write all resources",
    "system/CodeSystem.read": "Read all CodeSystems",
    "system/CodeSystem.write": "Write all CodeSystems",
    "system/ValueSet.read": "Read all ValueSets",
    "system/ValueSet.write": "Write all ValueSets",
    "system/ConceptMap.read": "Read all ConceptMaps",
    "system/ConceptMap.write": "Write all ConceptMaps",
    
    # Special scopes
    "openid": "OpenID Connect authentication",
    "fhirUser": "FHIR user identity",
    "launch": "SMART launch context",
    "launch/patient": "Patient launch context",
    "offline_access": "Refresh token access",
    
    # Admin scopes
    "admin": "Full administrative access",
    "admin.users": "Manage users",
    "admin.clients": "Manage OAuth2 clients",
}

# Pydantic Models
class OAuth2ClientCreate(BaseModel):
    client_name: str
    description: Optional[str] = None
    redirect_uris: List[str]
    grant_types: List[str] = ["authorization_code", "refresh_token"]
    scopes: List[str]

class OAuth2ClientResponse(BaseModel):
    id: str
    client_id: str
    client_name: str
    description: Optional[str]
    redirect_uris: List[str]
    grant_types: List[str]
    scopes: List[str]
    is_active: bool
    created_at: datetime
    last_used: Optional[datetime]
    
    class Config:
        from_attributes = True

class OAuth2TokenResponse(BaseModel):
    access_token: str
    token_type: str = "Bearer"
    expires_in: int
    refresh_token: Optional[str] = None
    scope: str

class TokenInfo(BaseModel):
    active: bool
    scope: Optional[str] = None
    client_id: Optional[str] = None
    username: Optional[str] = None
    exp: Optional[int] = None

# Helper functions
def generate_client_id() -> str:
    """Generate a unique client ID"""
    return f"client_{secrets.token_urlsafe(16)}"

def generate_client_secret() -> str:
    """Generate a secure client secret"""
    return secrets.token_urlsafe(32)

def hash_secret(secret: str) -> str:
    """Hash a client secret"""
    return pwd_context.hash(secret)

def verify_client_secret(plain_secret: str, hashed_secret: str) -> bool:
    """Verify a client secret"""
    return pwd_context.verify(plain_secret, hashed_secret)

def create_oauth2_client(db: Session, client_data: OAuth2ClientCreate, created_by: str) -> tuple[OAuth2ClientModel, str]:
    """
    Create a new OAuth2 client
    Returns: (client_model, plain_client_secret)
    """
    client_id = generate_client_id()
    client_secret = generate_client_secret()
    
    # Validate scopes
    invalid_scopes = [s for s in client_data.scopes if s not in FHIR_SCOPES]
    if invalid_scopes:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid scopes: {', '.join(invalid_scopes)}"
        )
    
    client = OAuth2ClientModel(
        id=str(uuid.uuid4()),
        client_id=client_id,
        client_secret_hash=hash_secret(client_secret),
        client_name=client_data.client_name,
        description=client_data.description,
        redirect_uris=client_data.redirect_uris,
        grant_types=client_data.grant_types,
        response_types=["code"],
        scopes=client_data.scopes,
        is_active=True,
        created_at=datetime.now(timezone.utc),
        created_by=created_by
    )
    
    db.add(client)
    db.commit()
    db.refresh(client)
    
    return client, client_secret

def get_client_by_client_id(db: Session, client_id: str) -> Optional[OAuth2ClientModel]:
    """Get OAuth2 client by client_id"""
    return db.query(OAuth2ClientModel).filter(
        OAuth2ClientModel.client_id == client_id,
        OAuth2ClientModel.is_active == True
    ).first()

def authenticate_client(db: Session, client_id: str, client_secret: str) -> Optional[OAuth2ClientModel]:
    """Authenticate an OAuth2 client"""
    client = get_client_by_client_id(db, client_id)
    if not client:
        return None
    if not verify_client_secret(client_secret, client.client_secret_hash):
        return None
    return client

def create_oauth2_token(
    db: Session,
    client: OAuth2ClientModel,
    scopes: List[str],
    user: Optional[UserModel] = None,
    include_refresh: bool = False
) -> OAuth2TokenModel:
    """Create OAuth2 access token (and optional refresh token)"""
    
    # Generate tokens
    access_token = secrets.token_urlsafe(32)
    refresh_token = secrets.token_urlsafe(32) if include_refresh else None
    
    # Calculate expiration
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    refresh_expires_at = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS) if include_refresh else None
    
    token = OAuth2TokenModel(
        id=str(uuid.uuid4()),
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="Bearer",
        expires_at=expires_at,
        refresh_expires_at=refresh_expires_at,
        scopes=scopes,
        client_id=client.client_id,
        user_id=user.id if user else None,
        created_at=datetime.now(timezone.utc),
        revoked=False
    )
    
    db.add(token)
    
    # Update client last_used
    client.last_used = datetime.now(timezone.utc)
    
    db.commit()
    db.refresh(token)
    
    return token

def validate_token(db: Session, token: str) -> Optional[Dict]:
    """
    Validate an OAuth2 access token
    Returns: Dict with token info or None if invalid
    """
    token_model = db.query(OAuth2TokenModel).filter(
        OAuth2TokenModel.access_token == token,
        OAuth2TokenModel.revoked == False
    ).first()
    
    if not token_model:
        return None
    
    # Check expiration
    if datetime.now(timezone.utc) > token_model.expires_at:
        return None
    
    # Get client
    client = get_client_by_client_id(db, token_model.client_id)
    if not client or not client.is_active:
        return None
    
    # Get user if token has user_id
    user = None
    if token_model.user_id:
        user = db.query(UserModel).filter(UserModel.id == token_model.user_id).first()
    
    return {
        "active": True,
        "scope": " ".join(token_model.scopes),
        "client_id": token_model.client_id,
        "username": user.username if user else None,
        "user_id": token_model.user_id,
        "exp": int(token_model.expires_at.timestamp()),
        "scopes": token_model.scopes
    }

def revoke_token(db: Session, token: str) -> bool:
    """Revoke an OAuth2 token"""
    token_model = db.query(OAuth2TokenModel).filter(
        OAuth2TokenModel.access_token == token
    ).first()
    
    if not token_model:
        return False
    
    token_model.revoked = True
    token_model.revoked_at = datetime.now(timezone.utc)
    db.commit()
    
    return True

def check_scope_permission(required_scope: str, granted_scopes: List[str]) -> bool:
    """
    Check if granted scopes include required scope
    Supports wildcards: user/*.read includes user/CodeSystem.read
    """
    for granted in granted_scopes:
        # Exact match
        if granted == required_scope:
            return True
        
        # Wildcard match
        if "*" in granted:
            # Extract context and permission
            # e.g., "user/*.read" matches "user/CodeSystem.read"
            parts_granted = granted.split("/")
            parts_required = required_scope.split("/")
            
            if len(parts_granted) == 2 and len(parts_required) == 2:
                context_granted, resource_action_granted = parts_granted
                context_required, resource_action_required = parts_required
                
                # Context must match
                if context_granted != context_required:
                    continue
                
                # Check resource and action
                if resource_action_granted == "*.*":
                    return True
                
                if resource_action_granted.endswith(".*"):
                    # e.g., "CodeSystem.*" matches "CodeSystem.read" and "CodeSystem.write"
                    resource_granted = resource_action_granted.split(".")[0]
                    resource_required = resource_action_required.split(".")[0]
                    if resource_granted == "*" or resource_granted == resource_required:
                        return True
                
                if resource_action_granted.startswith("*."):
                    # e.g., "*.read" matches "CodeSystem.read" and "ValueSet.read"
                    action_granted = resource_action_granted.split(".")[1]
                    action_required = resource_action_required.split(".")[1]
                    if action_granted == "*" or action_granted == action_required:
                        return True
    
    return False

def get_smart_configuration() -> Dict:
    """
    Return SMART on FHIR configuration
    https://build.fhir.org/ig/HL7/smart-app-launch/conformance.html
    """
    base_url = "https://terminology-manager.preview.emergentagent.com/api"
    
    return {
        "issuer": base_url,
        "authorization_endpoint": f"{base_url}/oauth2/authorize",
        "token_endpoint": f"{base_url}/oauth2/token",
        "token_endpoint_auth_methods_supported": [
            "client_secret_post",
            "client_secret_basic"
        ],
        "registration_endpoint": f"{base_url}/oauth2/register",
        "scopes_supported": list(FHIR_SCOPES.keys()),
        "response_types_supported": ["code", "token"],
        "grant_types_supported": [
            "authorization_code",
            "client_credentials",
            "refresh_token"
        ],
        "code_challenge_methods_supported": ["S256"],
        "capabilities": [
            "launch-ehr",
            "launch-standalone",
            "client-public",
            "client-confidential-symmetric",
            "context-ehr-patient",
            "context-standalone-patient",
            "permission-offline",
            "permission-patient",
            "permission-user"
        ],
        "introspection_endpoint": f"{base_url}/oauth2/introspect",
        "revocation_endpoint": f"{base_url}/oauth2/revoke"
    }
