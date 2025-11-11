# OAuth2 e SMART on FHIR - Documentazione Completa

## 🔐 Sistema di Autenticazione Implementato

Questo sistema implementa le specifiche **FHIR Security** e **SMART on FHIR** secondo:
- https://build.fhir.org/security.html
- https://build.fhir.org/ig/HL7/smart-app-launch/conformance.html

---

## 📋 Panoramica

### Metodi di Autenticazione Supportati

1. **JWT (JSON Web Tokens)** - Per utenti web
2. **OAuth2 Client Credentials** - Per applicazioni server-to-server
3. **OAuth2 Authorization Code Flow** - Per applicazioni interattive
4. **OAuth2 Refresh Tokens** - Per sessioni long-lived

### Componenti del Sistema

- **User Management** - Gestione utenti con ruoli
- **OAuth2 Client Management** - Registrazione e gestione applicazioni client
- **Token Management** - Gestione e revoca token attivi
- **SMART Configuration** - Endpoint di discovery
- **Scopes FHIR Granulari** - Controllo accessi fine-grained
- **Audit Trail** - Log completo di tutti gli accessi

---

## 🎯 Scopes FHIR Supportati

### Patient Scopes (Dati specifici paziente)
- `patient/*.read` - Leggi tutti i dati paziente
- `patient/*.write` - Scrivi tutti i dati paziente
- `patient/CodeSystem.read` - Leggi CodeSystems paziente
- `patient/ValueSet.read` - Leggi ValueSets paziente
- `patient/ConceptMap.read` - Leggi ConceptMaps paziente

### User Scopes (Dati specifici utente)
- `user/*.read` - Leggi tutti i dati utente
- `user/*.write` - Scrivi tutti i dati utente
- `user/CodeSystem.read` - Leggi CodeSystems utente
- `user/CodeSystem.write` - Scrivi CodeSystems utente
- `user/ValueSet.read` - Leggi ValueSets utente
- `user/ValueSet.write` - Scrivi ValueSets utente
- `user/ConceptMap.read` - Leggi ConceptMaps utente
- `user/ConceptMap.write` - Scrivi ConceptMaps utente

### System Scopes (Accesso server-wide)
- `system/*.read` - Leggi tutte le risorse
- `system/*.write` - Scrivi tutte le risorse
- `system/CodeSystem.read` - Leggi tutti i CodeSystems
- `system/CodeSystem.write` - Scrivi tutti i CodeSystems
- `system/ValueSet.read` - Leggi tutti i ValueSets
- `system/ValueSet.write` - Scrivi tutti i ValueSets
- `system/ConceptMap.read` - Leggi tutti i ConceptMaps
- `system/ConceptMap.write` - Scrivi tutti i ConceptMaps

### Special Scopes
- `openid` - OpenID Connect authentication
- `fhirUser` - FHIR user identity
- `launch` - SMART launch context
- `launch/patient` - Patient launch context
- `offline_access` - Refresh token access

### Admin Scopes
- `admin` - Full administrative access
- `admin.users` - Manage users
- `admin.clients` - Manage OAuth2 clients

---

## 🚀 Endpoint OAuth2

### SMART Configuration (Discovery)
**GET** `/.well-known/smart-configuration`

Restituisce la configurazione SMART on FHIR del server.

**Response:**
```json
{
  "issuer": "https://terminology-manager.preview.emergentagent.com/api",
  "authorization_endpoint": ".../oauth2/authorize",
  "token_endpoint": ".../oauth2/token",
  "scopes_supported": [...],
  "grant_types_supported": ["authorization_code", "client_credentials", "refresh_token"],
  "capabilities": ["launch-ehr", "client-confidential-symmetric", ...]
}
```

### Token Endpoint
**POST** `/oauth2/token`

**Grant Type: client_credentials (Server-to-Server)**
```bash
curl -X POST https://your-server/api/oauth2/token \
  -d "grant_type=client_credentials" \
  -d "client_id=client_abc123" \
  -d "client_secret=secret_xyz789" \
  -d "scope=system/CodeSystem.read system/ValueSet.read"
```

**Response:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "Bearer",
  "expires_in": 3600,
  "scope": "system/CodeSystem.read system/ValueSet.read"
}
```

**Grant Type: refresh_token**
```bash
curl -X POST https://your-server/api/oauth2/token \
  -d "grant_type=refresh_token" \
  -d "client_id=client_abc123" \
  -d "client_secret=secret_xyz789" \
  -d "refresh_token=refresh_token_here"
```

### Token Introspection
**POST** `/oauth2/introspect`

Verifica se un token è valido.

```bash
curl -X POST https://your-server/api/oauth2/introspect \
  -d "token=access_token_here" \
  -d "client_id=client_abc123" \
  -d "client_secret=secret_xyz789"
```

**Response:**
```json
{
  "active": true,
  "scope": "system/CodeSystem.read",
  "client_id": "client_abc123",
  "exp": 1234567890
}
```

### Token Revocation
**POST** `/oauth2/revoke`

Revoca un token.

```bash
curl -X POST https://your-server/api/oauth2/revoke \
  -d "token=access_token_here" \
  -d "client_id=client_abc123" \
  -d "client_secret=secret_xyz789"
```

### List Available Scopes
**GET** `/oauth2/scopes`

Lista tutti gli scopes FHIR disponibili.

---

## 👥 Client Management API

### Create OAuth2 Client
**POST** `/oauth2/clients` (Admin only)

**Headers:** `Authorization: Bearer {admin_token}`

**Request Body:**
```json
{
  "client_name": "My FHIR App",
  "description": "Application description",
  "redirect_uris": ["https://myapp.com/callback"],
  "grant_types": ["client_credentials", "refresh_token"],
  "scopes": ["system/CodeSystem.read", "system/ValueSet.read"]
}
```

**Response:**
```json
{
  "id": "uuid",
  "client_id": "client_generated123",
  "client_secret": "secret_generated456",
  "client_name": "My FHIR App",
  "warning": "Save the client_secret - it won't be shown again!"
}
```

### List OAuth2 Clients
**GET** `/oauth2/clients` (Admin only)

### Get Client Details
**GET** `/oauth2/clients/{client_id}` (Admin only)

### Update Client
**PUT** `/oauth2/clients/{client_id}` (Admin only)

### Deactivate Client
**DELETE** `/oauth2/clients/{client_id}` (Admin only)

### Reset Client Secret
**POST** `/oauth2/clients/{client_id}/reset-secret` (Admin only)

---

## 👤 User Management API

### List Users
**GET** `/admin/users` (Admin only)

**Query Parameters:**
- `role` - Filter by role (admin, clinician, researcher, user)
- `is_active` - Filter by status (true, false)
- `skip`, `limit` - Pagination

### Update User Role
**PUT** `/admin/users/{user_id}/role?role={new_role}` (Admin only)

**Allowed roles:** admin, clinician, researcher, user

### Deactivate User
**DELETE** `/admin/users/{user_id}` (Admin only)

---

## 📊 Token Management API

### List Active Tokens
**GET** `/oauth2/tokens` (Admin only)

**Query Parameters:**
- `client_id` - Filter by client
- `user_id` - Filter by user
- `skip`, `limit` - Pagination

### Revoke Token by ID
**DELETE** `/oauth2/tokens/{token_id}` (Admin only)

---

## 📈 Admin Dashboard API

### Get Dashboard Statistics
**GET** `/admin/dashboard` (Admin only)

**Response:**
```json
{
  "users": {
    "total": 10,
    "active": 8,
    "by_role": {"admin": 2, "user": 8}
  },
  "oauth2_clients": {
    "total": 5,
    "active": 4
  },
  "tokens": {
    "total": 15,
    "active": 12,
    "revoked": 3
  },
  "resources": {
    "code_systems": 100,
    "value_sets": 50,
    "concept_maps": 25
  },
  "audit_logs": {
    "total": 1000,
    "last_24h": 50
  }
}
```

---

## 🔑 Uso dei Token nelle Richieste API

### Con Access Token OAuth2

```bash
# Ottieni token
TOKEN=$(curl -X POST https://your-server/api/oauth2/token \
  -d "grant_type=client_credentials" \
  -d "client_id=your_client_id" \
  -d "client_secret=your_secret" \
  -d "scope=system/CodeSystem.read" | jq -r '.access_token')

# Usa il token
curl https://your-server/api/CodeSystem \
  -H "Authorization: Bearer $TOKEN"
```

### Con JWT User Token

```bash
# Login
TOKEN=$(curl -X POST https://your-server/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}' | jq -r '.access_token')

# Usa il token
curl https://your-server/api/CodeSystem \
  -H "Authorization: Bearer $TOKEN"
```

---

## 🎨 Interfaccia Admin Web

### Accesso Admin
1. Login con utente admin: http://localhost:3000
2. Naviga a sezione "Amministrazione" nella sidebar

### Pagine Admin

**1. Admin Dashboard** (`/admin`)
- Statistiche globali sistema
- Grafici utenti per ruolo
- Statistiche risorse FHIR
- Audit log summary
- Quick actions

**2. Gestione Utenti** (`/admin/users`)
- Lista tutti gli utenti
- Filtri per ruolo e stato
- Cambio ruolo inline (dropdown)
- Disattivazione utenti
- Visualizzazione ultimo accesso

**3. OAuth2 Clients** (`/admin/oauth2-clients`)
- Creazione nuovi client
- Visualizzazione client_id e redirect URIs
- Selezione scopes granulari
- Reset client secret
- Disattivazione client
- Copia credenziali negli appunti

**4. Token Attivi** (`/admin/tokens`)
- Lista token OAuth2 attivi
- Filtro per client
- Visualizzazione scopes e scadenza
- Revoca token individuale
- Tempo rimanente countdown

---

## 🔒 Ruoli Utente

| Ruolo | Permessi | Uso |
|-------|----------|-----|
| **admin** | Full access, gestione utenti e client | Amministratori sistema |
| **clinician** | Read/Write risorse cliniche | Personale clinico |
| **researcher** | Read-only accesso | Ricercatori, analisti |
| **user** | Base access | Utenti standard |

---

## 🛡️ Security Best Practices

### Client Secrets
- ⚠️ **Mai condividere** client secrets in repository
- ⚠️ Salva il secret **solo al momento della creazione**
- ✅ Usa variabili d'ambiente per client secrets
- ✅ Ruota periodicamente i secrets

### Scopes
- ✅ Richiedi **solo gli scopes necessari**
- ✅ Usa scopes granulari invece di wildcards quando possibile
- ✅ Rivedi periodicamente i permessi client

### Tokens
- ✅ Token hanno scadenza automatica (60 minuti default)
- ✅ Usa refresh tokens per sessioni long-lived
- ✅ Revoca immediatamente token compromessi
- ✅ Monitora token attivi nella dashboard admin

---

## 📝 Esempi d'Uso

### Scenario 1: Applicazione di Analisi (Read-Only)

```bash
# 1. Crea client nell'admin UI con scopes:
#    - system/CodeSystem.read
#    - system/ValueSet.read
#    - system/ConceptMap.read

# 2. Ottieni token
curl -X POST https://your-server/api/oauth2/token \
  -d "grant_type=client_credentials" \
  -d "client_id=analytics_app" \
  -d "client_secret=your_secret" \
  -d "scope=system/CodeSystem.read system/ValueSet.read"

# 3. Usa il token
curl https://your-server/api/CodeSystem \
  -H "Authorization: Bearer {token}"
```

### Scenario 2: Applicazione Clinica (Read/Write)

```bash
# 1. Crea client con scopes:
#    - user/*.read
#    - user/*.write
#    - launch
#    - fhirUser

# 2. Implementa Authorization Code Flow
# (Richiede user consent e browser redirect)
```

### Scenario 3: Script di Importazione Dati

```bash
# 1. Crea client con scopes:
#    - system/CodeSystem.write
#    - system/ValueSet.write

# 2. Script Python
import requests

# Get token
token_response = requests.post(
    'https://your-server/api/oauth2/token',
    data={
        'grant_type': 'client_credentials',
        'client_id': 'import_script',
        'client_secret': 'your_secret',
        'scope': 'system/CodeSystem.write'
    }
)
token = token_response.json()['access_token']

# Import data
headers = {'Authorization': f'Bearer {token}'}
requests.post(
    'https://your-server/api/CodeSystem',
    json=codesystem_data,
    headers=headers
)
```

---

## 🔍 Verifica e Testing

### Test SMART Configuration
```bash
curl https://your-server/api/.well-known/smart-configuration | jq
```

### Test Client Credentials Flow
```bash
# 1. Create client via admin UI
# 2. Get token
curl -X POST https://your-server/api/oauth2/token \
  -d "grant_type=client_credentials" \
  -d "client_id=YOUR_CLIENT_ID" \
  -d "client_secret=YOUR_SECRET" \
  -d "scope=system/CodeSystem.read"

# 3. Use token
curl https://your-server/api/CodeSystem \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Test Token Introspection
```bash
curl -X POST https://your-server/api/oauth2/introspect \
  -d "token=YOUR_TOKEN" \
  -d "client_id=YOUR_CLIENT_ID" \
  -d "client_secret=YOUR_SECRET"
```

### Test Token Revocation
```bash
curl -X POST https://your-server/api/oauth2/revoke \
  -d "token=YOUR_TOKEN" \
  -d "client_id=YOUR_CLIENT_ID" \
  -d "client_secret=YOUR_SECRET"
```

---

## 👨‍💼 Workflow Admin

### Creazione Nuovo Client OAuth2

1. **Login come admin** → http://localhost:3000
2. **Naviga** → Amministrazione → OAuth2 Clients
3. **Clic** → "Nuovo Client"
4. **Compila form:**
   - Nome client
   - Descrizione
   - Redirect URIs
   - Grant types (client_credentials, refresh_token, etc.)
   - Scopes (seleziona dalla lista)
5. **Crea** → Salva client_id e client_secret mostrati
6. **Importante:** Il secret non sarà più mostrato!

### Gestione Utenti

1. **Naviga** → Amministrazione → Gestione Utenti
2. **Filtra** per ruolo o stato
3. **Cambia ruolo** → Dropdown inline
4. **Disattiva utente** → Clic icona disattivazione

### Monitoraggio Token

1. **Naviga** → Amministrazione → Token Attivi
2. **Filtra** per client
3. **Visualizza** scopes, scadenza, utente
4. **Revoca** token se necessario

---

## 📚 Database Schema

### Tabelle Aggiunte

**oauth2_clients:**
- id, client_id, client_secret_hash
- client_name, description
- redirect_uris (JSON)
- grant_types, scopes (JSON)
- is_active, created_at, last_used

**oauth2_tokens:**
- id, access_token, refresh_token
- token_type, expires_at, refresh_expires_at
- scopes (JSON)
- client_id, user_id
- revoked, revoked_at

**users (updated):**
- Added: role (admin, clinician, researcher, user)

**audit_log (updated):**
- Added: client_id, scopes (JSON)

---

## 🔐 Sicurezza

### Protezioni Implementate

✅ Client secrets hashed con bcrypt
✅ Token validation con expiration check
✅ Scope verification per ogni richiesta
✅ Admin-only endpoints protetti
✅ Rate limiting (da configurare in produzione)
✅ CORS configurabile
✅ Audit trail completo

### Raccomandazioni Produzione

1. **Usa HTTPS obbligatorio** per tutti gli endpoint
2. **Configura SECRET_KEY** sicura in .env
3. **Abilita rate limiting** su endpoint token
4. **Monitora audit logs** per attività sospette
5. **Ruota client secrets** periodicamente
6. **Usa scopes minimi** necessari
7. **Implementa IP whitelisting** per client critici

---

## 📖 Conformità FHIR

Questo sistema è conforme a:
- ✅ FHIR R4 Security Specification
- ✅ SMART on FHIR v2.0
- ✅ OAuth2 RFC 6749
- ✅ OpenID Connect Core 1.0
- ✅ HL7 Terminology Security Guidelines

### Capabilities Dichiarate

Nel SMART configuration (`/.well-known/smart-configuration`):
- `launch-ehr` - EHR launch framework
- `launch-standalone` - Standalone launch
- `client-public` - Public clients
- `client-confidential-symmetric` - Confidential clients
- `context-ehr-patient` - EHR patient context
- `permission-offline` - Offline access
- `permission-patient` - Patient scopes
- `permission-user` - User scopes

---

## 🆘 Troubleshooting

### Client non si autentica
```bash
# Verifica credenziali
curl -X POST /oauth2/token ... -v

# Controlla client in database
docker compose exec backend python -c "
from database import SessionLocal, OAuth2ClientModel
db = SessionLocal()
client = db.query(OAuth2ClientModel).filter_by(client_id='YOUR_CLIENT').first()
print(f'Active: {client.is_active}')
print(f'Scopes: {client.scopes}')
"
```

### Token non valido
```bash
# Introspect token
curl -X POST /oauth2/introspect ...

# Controlla scadenza
# Token default: 60 minuti
```

### 403 Forbidden con token valido
- Verifica scopes del token
- Verifica scopes richiesti dall'endpoint
- Controlla audit log per dettagli

---

## 📞 Supporto

Per domande o problemi:
1. Controlla audit logs: `/audit-log`
2. Verifica token attivi: `/admin/tokens`
3. Consulta SMART configuration: `/.well-known/smart-configuration`
4. Logs backend: `docker compose logs backend`
