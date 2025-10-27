from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Any, Dict
from datetime import datetime
from enum import Enum

# Enums
class PublicationStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    RETIRED = "retired"
    UNKNOWN = "unknown"

class CodeSystemContentMode(str, Enum):
    NOT_PRESENT = "not-present"
    EXAMPLE = "example"
    FRAGMENT = "fragment"
    COMPLETE = "complete"
    SUPPLEMENT = "supplement"

class ConceptPropertyType(str, Enum):
    CODE = "code"
    CODING = "Coding"
    STRING = "string"
    INTEGER = "integer"
    BOOLEAN = "boolean"
    DATETIME = "dateTime"
    DECIMAL = "decimal"

class FilterOperator(str, Enum):
    EQUALS = "="
    IS_A = "is-a"
    DESCENDENT_OF = "descendent-of"
    IS_NOT_A = "is-not-a"
    REGEX = "regex"
    IN_SET = "in"
    NOT_IN = "not-in"
    GENERALIZES = "generalizes"
    EXISTS = "exists"

class ConceptMapEquivalence(str, Enum):
    RELATEDTO = "relatedto"
    EQUIVALENT = "equivalent"
    EQUAL = "equal"
    WIDER = "wider"
    SUBSUMES = "subsumes"
    NARROWER = "narrower"
    SPECIALIZES = "specializes"
    INEXACT = "inexact"
    UNMATCHED = "unmatched"
    DISJOINT = "disjoint"

# Base FHIR types
class Coding(BaseModel):
    system: Optional[str] = None
    version: Optional[str] = None
    code: Optional[str] = None
    display: Optional[str] = None
    userSelected: Optional[bool] = None

class CodeableConcept(BaseModel):
    coding: Optional[List[Coding]] = None
    text: Optional[str] = None

# CodeSystem Models
class CodeSystemProperty(BaseModel):
    code: str
    uri: Optional[str] = None
    description: Optional[str] = None
    type: ConceptPropertyType

class ConceptProperty(BaseModel):
    code: str
    valueCode: Optional[str] = None
    valueCoding: Optional[Coding] = None
    valueString: Optional[str] = None
    valueInteger: Optional[int] = None
    valueBoolean: Optional[bool] = None
    valueDateTime: Optional[str] = None
    valueDecimal: Optional[float] = None

class ConceptDesignation(BaseModel):
    language: Optional[str] = None
    use: Optional[Coding] = None
    value: str

class Concept(BaseModel):
    code: str
    display: Optional[str] = None
    definition: Optional[str] = None
    designation: Optional[List[ConceptDesignation]] = None
    property: Optional[List[ConceptProperty]] = None
    concept: Optional[List['Concept']] = None  # For hierarchical concepts

class CodeSystemFilter(BaseModel):
    code: str
    description: Optional[str] = None
    operator: List[FilterOperator]
    value: str

class CodeSystem(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    id: str
    resourceType: str = "CodeSystem"
    url: str
    identifier: Optional[List[Dict[str, Any]]] = None
    version: Optional[str] = None
    name: str
    title: Optional[str] = None
    status: PublicationStatus
    experimental: Optional[bool] = None
    date: Optional[datetime] = None
    publisher: Optional[str] = None
    contact: Optional[List[Dict[str, Any]]] = None
    description: Optional[str] = None
    useContext: Optional[List[Dict[str, Any]]] = None
    jurisdiction: Optional[List[CodeableConcept]] = None
    purpose: Optional[str] = None
    copyright: Optional[str] = None
    caseSensitive: Optional[bool] = True
    valueSet: Optional[str] = None  # Canonical URL of implicit value set
    hierarchyMeaning: Optional[str] = None
    compositional: Optional[bool] = False
    versionNeeded: Optional[bool] = None
    content: CodeSystemContentMode = CodeSystemContentMode.COMPLETE
    supplements: Optional[str] = None
    count: Optional[int] = None
    filter: Optional[List[CodeSystemFilter]] = None
    property: Optional[List[CodeSystemProperty]] = None
    concept: Optional[List[Concept]] = None

class CodeSystemCreate(BaseModel):
    url: str
    version: Optional[str] = None
    name: str
    title: Optional[str] = None
    status: PublicationStatus = PublicationStatus.DRAFT
    experimental: Optional[bool] = True
    publisher: Optional[str] = None
    description: Optional[str] = None
    caseSensitive: Optional[bool] = True
    content: CodeSystemContentMode = CodeSystemContentMode.COMPLETE
    property: Optional[List[CodeSystemProperty]] = None
    concept: Optional[List[Concept]] = None

# ValueSet Models
class ValueSetComposeIncludeFilter(BaseModel):
    property: str
    op: FilterOperator
    value: str

class ValueSetComposeIncludeConcept(BaseModel):
    code: str
    display: Optional[str] = None
    designation: Optional[List[ConceptDesignation]] = None

class ValueSetComposeInclude(BaseModel):
    system: Optional[str] = None
    version: Optional[str] = None
    concept: Optional[List[ValueSetComposeIncludeConcept]] = None
    filter: Optional[List[ValueSetComposeIncludeFilter]] = None
    valueSet: Optional[List[str]] = None  # References to other value sets

class ValueSetCompose(BaseModel):
    lockedDate: Optional[str] = None
    inactive: Optional[bool] = False
    include: List[ValueSetComposeInclude]
    exclude: Optional[List[ValueSetComposeInclude]] = None

class ValueSetExpansionContains(BaseModel):
    system: Optional[str] = None
    abstract: Optional[bool] = None
    inactive: Optional[bool] = None
    version: Optional[str] = None
    code: Optional[str] = None
    display: Optional[str] = None
    designation: Optional[List[ConceptDesignation]] = None
    contains: Optional[List['ValueSetExpansionContains']] = None

class ValueSetExpansionParameter(BaseModel):
    name: str
    valueString: Optional[str] = None
    valueBoolean: Optional[bool] = None
    valueInteger: Optional[int] = None
    valueDecimal: Optional[float] = None
    valueUri: Optional[str] = None
    valueCode: Optional[str] = None

class ValueSetExpansion(BaseModel):
    identifier: Optional[str] = None
    timestamp: datetime
    total: Optional[int] = None
    offset: Optional[int] = None
    parameter: Optional[List[ValueSetExpansionParameter]] = None
    contains: Optional[List[ValueSetExpansionContains]] = None

class ValueSet(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    id: str
    resourceType: str = "ValueSet"
    url: str
    identifier: Optional[List[Dict[str, Any]]] = None
    version: Optional[str] = None
    name: str
    title: Optional[str] = None
    status: PublicationStatus
    experimental: Optional[bool] = None
    date: Optional[datetime] = None
    publisher: Optional[str] = None
    contact: Optional[List[Dict[str, Any]]] = None
    description: Optional[str] = None
    useContext: Optional[List[Dict[str, Any]]] = None
    jurisdiction: Optional[List[CodeableConcept]] = None
    immutable: Optional[bool] = None
    purpose: Optional[str] = None
    copyright: Optional[str] = None
    compose: Optional[ValueSetCompose] = None
    expansion: Optional[ValueSetExpansion] = None

class ValueSetCreate(BaseModel):
    url: str
    version: Optional[str] = None
    name: str
    title: Optional[str] = None
    status: PublicationStatus = PublicationStatus.DRAFT
    experimental: Optional[bool] = True
    publisher: Optional[str] = None
    description: Optional[str] = None
    compose: ValueSetCompose

# ConceptMap Models
class ConceptMapGroupElementTarget(BaseModel):
    code: Optional[str] = None
    display: Optional[str] = None
    relationship: ConceptMapEquivalence
    comment: Optional[str] = None

class ConceptMapGroupElement(BaseModel):
    code: Optional[str] = None
    display: Optional[str] = None
    target: Optional[List[ConceptMapGroupElementTarget]] = None

class ConceptMapGroup(BaseModel):
    source: Optional[str] = None
    sourceVersion: Optional[str] = None
    target: Optional[str] = None
    targetVersion: Optional[str] = None
    element: List[ConceptMapGroupElement]

class ConceptMap(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    id: str
    resourceType: str = "ConceptMap"
    url: str
    identifier: Optional[List[Dict[str, Any]]] = None
    version: Optional[str] = None
    name: str
    title: Optional[str] = None
    status: PublicationStatus
    experimental: Optional[bool] = None
    date: Optional[datetime] = None
    publisher: Optional[str] = None
    contact: Optional[List[Dict[str, Any]]] = None
    description: Optional[str] = None
    useContext: Optional[List[Dict[str, Any]]] = None
    jurisdiction: Optional[List[CodeableConcept]] = None
    purpose: Optional[str] = None
    copyright: Optional[str] = None
    sourceUri: Optional[str] = None
    sourceCanonical: Optional[str] = None
    targetUri: Optional[str] = None
    targetCanonical: Optional[str] = None
    group: Optional[List[ConceptMapGroup]] = None

class ConceptMapCreate(BaseModel):
    url: str
    version: Optional[str] = None
    name: str
    title: Optional[str] = None
    status: PublicationStatus = PublicationStatus.DRAFT
    experimental: Optional[bool] = True
    publisher: Optional[str] = None
    description: Optional[str] = None
    sourceCanonical: Optional[str] = None
    targetCanonical: Optional[str] = None
    group: Optional[List[ConceptMapGroup]] = None

# Operations Parameters
class Parameter(BaseModel):
    name: str
    valueString: Optional[str] = None
    valueBoolean: Optional[bool] = None
    valueInteger: Optional[int] = None
    valueDecimal: Optional[float] = None
    valueUri: Optional[str] = None
    valueCode: Optional[str] = None
    valueCoding: Optional[Coding] = None
    valueCodeableConcept: Optional[CodeableConcept] = None
    resource: Optional[Dict[str, Any]] = None
    part: Optional[List['Parameter']] = None

class Parameters(BaseModel):
    resourceType: str = "Parameters"
    parameter: List[Parameter] = Field(default_factory=list)
