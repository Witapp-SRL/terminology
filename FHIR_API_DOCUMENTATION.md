# FHIR Terminology Service - API Documentation

## Base URL
`https://terminology-manager.preview.emergentagent.com/api`

## Metadata

### Get CapabilityStatement
Retrieve the FHIR CapabilityStatement describing this server's capabilities.

**Endpoint:** `GET /metadata`

**Response:** FHIR CapabilityStatement (JSON)

---

## Authentication

### Register User
**Endpoint:** `POST /auth/register`

**Request Body:**
```json
{
  "username": "string",
  "email": "string",
  "password": "string",
  "full_name": "string" (optional)
}
```

### Login
**Endpoint:** `POST /auth/login`

**Request Body:**
```json
{
  "username": "string",
  "password": "string"
}
```

**Response:**
```json
{
  "access_token": "string",
  "token_type": "bearer"
}
```

### Get Current User
**Endpoint:** `GET /auth/me`

**Headers:** `Authorization: Bearer {token}`

---

## CodeSystem Operations

### CRUD Operations

#### List CodeSystems
**Endpoint:** `GET /CodeSystem`

**Query Parameters:**
- `url` (string, optional): Filter by URL
- `name` (string, optional): Filter by name
- `status` (string, optional): Filter by status (draft, active, retired)
- `include_inactive` (boolean, default: false): Include deactivated CodeSystems

#### Get CodeSystem by ID
**Endpoint:** `GET /CodeSystem/{id}`

#### Create CodeSystem
**Endpoint:** `POST /CodeSystem`

**Headers:** `Authorization: Bearer {token}` (required)

**Request Body:** FHIR CodeSystem resource (JSON)

#### Update CodeSystem
**Endpoint:** `PUT /CodeSystem/{id}`

**Headers:** `Authorization: Bearer {token}` (required)

**Request Body:** FHIR CodeSystem resource (JSON)

#### Deactivate CodeSystem (Soft Delete)
**Endpoint:** `POST /CodeSystem/{id}/deactivate`

**Headers:** `Authorization: Bearer {token}` (required)

#### Activate CodeSystem
**Endpoint:** `POST /CodeSystem/{id}/activate`

**Headers:** `Authorization: Bearer {token}` (required)

### Import/Export

#### Import from CSV
**Endpoint:** `POST /CodeSystem/import-csv`

**Headers:** `Authorization: Bearer {token}` (required)

**Request:** Multipart/form-data with CSV file

#### Export to CSV
**Endpoint:** `GET /CodeSystem/{id}/export-csv`

**Response:** CSV file

### FHIR Terminology Operations

#### $lookup - Look up a code
Given a code/system, get additional details about the concept.

**Endpoint:** `GET /CodeSystem/$lookup`

**Query Parameters:**
- `system` (uri, required): The code system URI
- `code` (code, required): The code to lookup
- `version` (string, optional): The version of the code system

**Response:** FHIR Parameters resource

**Example:**
```
GET /CodeSystem/$lookup?system=http://snomed.info/sct&code=38341003
```

#### $validate-code - Validate a code
Validate that a coded value is in the code system.

**Endpoint:** `GET /CodeSystem/$validate-code`

**Query Parameters:**
- `system` (uri, required): The code system URI
- `code` (code, required): The code to validate
- `version` (string, optional): The version of the code system
- `display` (string, optional): The display text to validate

**Response:** FHIR Parameters resource with result (boolean)

**Example:**
```
GET /CodeSystem/$validate-code?system=http://snomed.info/sct&code=38341003
```

#### $subsumes - Test subsumption
Test the subsumption relationship between two codes.

**Endpoint:** `GET /CodeSystem/$subsumes`

**Query Parameters:**
- `system` (uri, required): The code system URI
- `codeA` (code, required): First code
- `codeB` (code, required): Second code
- `version` (string, optional): The version of the code system

**Response:** FHIR Parameters resource with outcome:
- `equivalent`: Codes are the same
- `subsumes`: codeA subsumes codeB (codeB is a child)
- `subsumed-by`: codeB subsumes codeA (codeA is a child)
- `not-subsumed`: No subsumption relationship

**Example:**
```
GET /CodeSystem/$subsumes?system=http://snomed.info/sct&codeA=38341003&codeB=39065001
```

---

## ValueSet Operations

### CRUD Operations

#### List ValueSets
**Endpoint:** `GET /ValueSet`

#### Get ValueSet by ID
**Endpoint:** `GET /ValueSet/{id}`

#### Create ValueSet
**Endpoint:** `POST /ValueSet`

**Request Body:** FHIR ValueSet resource (JSON)

#### Update ValueSet
**Endpoint:** `PUT /ValueSet/{id}`

**Request Body:** FHIR ValueSet resource (JSON)

#### Delete ValueSet
**Endpoint:** `DELETE /ValueSet/{id}`

### FHIR Terminology Operations

#### $expand - Expand a ValueSet
Expand a value set to return the list of codes it contains.

**Endpoint:** `GET /ValueSet/$expand`

**Query Parameters:**
- `url` (uri, required): The ValueSet canonical URL
- `filter` (string, optional): Text filter for code/display
- `offset` (integer, default: 0): Pagination offset
- `count` (integer, optional): Maximum number of results

**Response:** FHIR ValueSet resource with expansion

**Example:**
```
GET /ValueSet/$expand?url=http://example.org/fhir/ValueSet/my-valueset
```

#### $validate-code - Validate against ValueSet
Validate that a coded value is in the value set.

**Endpoint:** `GET /ValueSet/$validate-code`

**Query Parameters:**
- `url` (uri, required): The ValueSet canonical URL
- `code` (code, required): The code to validate
- `system` (uri, optional): The code system
- `display` (string, optional): The display text to validate
- `version` (string, optional): The version

**Response:** FHIR Parameters resource with result (boolean)

**Example:**
```
GET /ValueSet/$validate-code?url=http://example.org/fhir/ValueSet/my-valueset&code=12345&system=http://snomed.info/sct
```

---

## ConceptMap Operations

### CRUD Operations

#### List ConceptMaps
**Endpoint:** `GET /ConceptMap`

#### Get ConceptMap by ID
**Endpoint:** `GET /ConceptMap/{id}`

#### Create ConceptMap
**Endpoint:** `POST /ConceptMap`

**Request Body:** FHIR ConceptMap resource (JSON)

#### Update ConceptMap
**Endpoint:** `PUT /ConceptMap/{id}`

**Request Body:** FHIR ConceptMap resource (JSON)

#### Delete ConceptMap
**Endpoint:** `DELETE /ConceptMap/{id}`

### FHIR Terminology Operations

#### $translate - Translate a code
Translate a code from source to target using a ConceptMap.

**Endpoint:** `GET /ConceptMap/$translate`

**Query Parameters:**
- `url` (uri, optional): The ConceptMap canonical URL
- `conceptMapId` (id, optional): The ConceptMap ID
- `code` (code, optional): The code to translate
- `system` (uri, optional): The source code system
- `source` (uri, optional): Source ValueSet
- `target` (uri, optional): Target ValueSet

**Response:** FHIR Parameters resource with match details

**Example:**
```
GET /ConceptMap/$translate?url=http://example.org/fhir/ConceptMap/icd9-to-icd10&code=250.00&system=http://hl7.org/fhir/sid/icd-9-cm
```

---

## Audit Trail

### Get Audit Logs
**Endpoint:** `GET /audit-logs`

**Headers:** `Authorization: Bearer {token}` (required)

**Query Parameters:**
- `resource_type` (string, optional): Filter by resource type
- `resource_id` (string, optional): Filter by resource ID
- `action` (string, optional): Filter by action (create, update, deactivate, activate)
- `user_id` (string, optional): Filter by user ID
- `skip` (integer, default: 0): Pagination offset
- `limit` (integer, default: 100): Maximum results

### Export Audit Logs (CSV)
**Endpoint:** `GET /audit-logs/export-csv`

**Headers:** `Authorization: Bearer {token}` (required)

**Query Parameters:** Same as GET /audit-logs

**Response:** CSV file

---

## FHIR Compliance

This server implements:
- **FHIR Version:** R4 (4.0.1)
- **Resources:** CodeSystem, ValueSet, ConceptMap
- **Operations:**
  - CodeSystem: $lookup, $validate-code, $subsumes
  - ValueSet: $expand, $validate-code
  - ConceptMap: $translate
- **Authentication:** JWT Bearer Token
- **Data Format:** JSON (application/fhir+json)

## Sample Datasets

The server includes sample medical terminology data:
- **ICD-9-CM:** International Classification of Diseases, 9th Revision
- **ICD-10-CM:** International Classification of Diseases, 10th Revision
- **SNOMED CT:** Systematized Nomenclature of Medicine Clinical Terms

---

## Error Handling

All endpoints return standard HTTP status codes:
- `200 OK`: Successful request
- `201 Created`: Resource created
- `204 No Content`: Successful deletion
- `400 Bad Request`: Invalid request
- `401 Unauthorized`: Missing or invalid authentication
- `403 Forbidden`: Insufficient permissions
- `404 Not Found`: Resource not found
- `405 Method Not Allowed`: HTTP method not supported
- `500 Internal Server Error`: Server error

Error responses include a JSON body with details:
```json
{
  "detail": "Error message"
}
```
