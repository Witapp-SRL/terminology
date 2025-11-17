from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import or_
from models.fhir_models import (
    Parameters, Parameter, Coding, ValueSetExpansion, ValueSetExpansionContains
)
from database import CodeSystemModel, ValueSetModel, ConceptMapModel
import json
import uuid

class TerminologyServiceSQL:
    def __init__(self):
        pass

    def lookup(self, db: Session, system: str, code: str, version: Optional[str] = None, properties: Optional[List[str]] = None) -> Parameters:
        query = db.query(CodeSystemModel).filter(CodeSystemModel.url == system)
        if version:
            query = query.filter(CodeSystemModel.version == version)
        
        cs_model = query.first()
        if not cs_model:
            return Parameters(parameter=[Parameter(name="message", valueString=f"Code system {system} not found")])
        
        # Parse concepts from JSON string
        concepts = json.loads(cs_model.concept) if cs_model.concept and isinstance(cs_model.concept, str) else (cs_model.concept or [])
        concept = self._find_concept(concepts, code)
        if not concept:
            return Parameters(parameter=[Parameter(name="message", valueString=f"Code {code} not found")])
        
        params = [
            Parameter(name="name", valueString=cs_model.name),
            Parameter(name="display", valueString=concept.get("display", "")),
        ]
        if cs_model.version:
            params.append(Parameter(name="version", valueString=cs_model.version))
        if concept.get("definition"):
            params.append(Parameter(name="definition", valueString=concept["definition"]))
        
        return Parameters(parameter=params)

    def validate_code(self, db: Session, system: str, code: str, version: Optional[str] = None, display: Optional[str] = None) -> Parameters:
        query = db.query(CodeSystemModel).filter(CodeSystemModel.url == system)
        if version:
            query = query.filter(CodeSystemModel.version == version)
        
        cs = query.first()
        if not cs:
            return Parameters(parameter=[
                Parameter(name="result", valueBoolean=False),
                Parameter(name="message", valueString=f"Code system not found")
            ])
        
        concepts = json.loads(cs.concept) if cs.concept and isinstance(cs.concept, str) else (cs.concept or [])
        concept = self._find_concept(concepts, code)
        if not concept:
            return Parameters(parameter=[
                Parameter(name="result", valueBoolean=False),
                Parameter(name="message", valueString=f"Code not found")
            ])
        
        params = [Parameter(name="result", valueBoolean=True)]
        if display and concept.get("display") and display != concept["display"]:
            params.append(Parameter(name="message", valueString=f"Display incorrect. Expected: {concept['display']}"))
        if concept.get("display"):
            params.append(Parameter(name="display", valueString=concept["display"]))
        
        return Parameters(parameter=params)
    
    def subsumes(self, db: Session, system: str, codeA: str, codeB: str, version: Optional[str] = None) -> Parameters:
        """
        Test the subsumption relationship between two codes
        Returns: equivalent | subsumes | subsumed-by | not-subsumed
        """
        query = db.query(CodeSystemModel).filter(CodeSystemModel.url == system)
        if version:
            query = query.filter(CodeSystemModel.version == version)
        
        cs = query.first()
        if not cs:
            return Parameters(parameter=[
                Parameter(name="outcome", valueString="not-subsumed"),
                Parameter(name="message", valueString=f"Code system not found")
            ])
        
        concepts = json.loads(cs.concept) if cs.concept and isinstance(cs.concept, str) else (cs.concept or [])
        
        # Check if codes exist
        conceptA = self._find_concept(concepts, codeA)
        conceptB = self._find_concept(concepts, codeB)
        
        if not conceptA or not conceptB:
            return Parameters(parameter=[
                Parameter(name="outcome", valueString="not-subsumed"),
                Parameter(name="message", valueString="One or both codes not found")
            ])
        
        # If codes are the same, they're equivalent
        if codeA == codeB:
            return Parameters(parameter=[Parameter(name="outcome", valueString="equivalent")])
        
        # Check if codeA subsumes codeB (codeB is a child of codeA)
        if self._is_descendant(concepts, codeA, codeB):
            return Parameters(parameter=[Parameter(name="outcome", valueString="subsumes")])
        
        # Check if codeB subsumes codeA (codeA is a child of codeB)
        if self._is_descendant(concepts, codeB, codeA):
            return Parameters(parameter=[Parameter(name="outcome", valueString="subsumed-by")])
        
        return Parameters(parameter=[Parameter(name="outcome", valueString="not-subsumed")])

    def validate_code_in_valueset(self, db: Session, url: str, code: str, system: Optional[str] = None, 
                                   display: Optional[str] = None, version: Optional[str] = None) -> Parameters:
        """
        Validate a code against a ValueSet
        """
        vs = db.query(ValueSetModel).filter(ValueSetModel.url == url).first()
        if not vs:
            return Parameters(parameter=[
                Parameter(name="result", valueBoolean=False),
                Parameter(name="message", valueString="ValueSet not found")
            ])
        
        # Expand the valueset
        expanded = self._perform_expansion(db, vs.compose or {}, None)
        
        # Check if code exists in expansion
        for item in expanded:
            if item["code"] == code:
                if system and item.get("system") != system:
                    continue
                if display and item.get("display") and display != item["display"]:
                    return Parameters(parameter=[
                        Parameter(name="result", valueBoolean=True),
                        Parameter(name="message", valueString=f"Display incorrect. Expected: {item['display']}")
                    ])
                return Parameters(parameter=[
                    Parameter(name="result", valueBoolean=True),
                    Parameter(name="display", valueString=item.get("display", ""))
                ])
        
        return Parameters(parameter=[
            Parameter(name="result", valueBoolean=False),
            Parameter(name="message", valueString="Code not found in ValueSet")
        ])

    def translate(self, db: Session, url: Optional[str] = None, conceptmap_id: Optional[str] = None,
                  code: Optional[str] = None, system: Optional[str] = None, 
                  source: Optional[str] = None, target: Optional[str] = None) -> Parameters:
        """
        Translate a code from one value set to another using a ConceptMap
        """
        # Find the ConceptMap
        if conceptmap_id:
            cm = db.query(ConceptMapModel).filter(ConceptMapModel.id == conceptmap_id).first()
        elif url:
            cm = db.query(ConceptMapModel).filter(ConceptMapModel.url == url).first()
        else:
            return Parameters(parameter=[
                Parameter(name="result", valueBoolean=False),
                Parameter(name="message", valueString="ConceptMap url or id required")
            ])
        
        if not cm:
            return Parameters(parameter=[
                Parameter(name="result", valueBoolean=False),
                Parameter(name="message", valueString="ConceptMap not found")
            ])
        
        # Parse group from JSON
        groups = json.loads(cm.group) if cm.group and isinstance(cm.group, str) else (cm.group or [])
        
        # Find matching translation
        for group in groups:
            if system and group.get("source") != system:
                continue
            if target and group.get("target") != target:
                continue
            
            for element in group.get("element", []):
                if element.get("code") == code:
                    targets = element.get("target", [])
                    if targets:
                        # Return first match
                        matched = targets[0]
                        return Parameters(parameter=[
                            Parameter(name="result", valueBoolean=True),
                            Parameter(name="match", valueString=json.dumps({
                                "equivalence": matched.get("equivalence", "equivalent"),
                                "concept": {
                                    "system": group.get("target"),
                                    "code": matched.get("code"),
                                    "display": matched.get("display")
                                }
                            }))
                        ])
        
        return Parameters(parameter=[
            Parameter(name="result", valueBoolean=False),
            Parameter(name="message", valueString="No translation found")
        ])

    def expand_valueset(self, db: Session, url: Optional[str] = None, valueset_id: Optional[str] = None,
                       filter_text: Optional[str] = None, offset: int = 0, count: Optional[int] = None) -> Dict:
        if valueset_id:
            vs = db.query(ValueSetModel).filter(ValueSetModel.id == valueset_id).first()
        elif url:
            vs = db.query(ValueSetModel).filter(ValueSetModel.url == url).first()
        else:
            raise ValueError("Either url or valueset_id required")
        
        if not vs:
            raise ValueError("ValueSet not found")
        
        compose_data = json.loads(vs.compose) if vs.compose and isinstance(vs.compose, str) else (vs.compose or {})
        expanded = self._perform_expansion(db, compose_data, filter_text)
        
        total = len(expanded)
        if count:
            paginated = expanded[offset:offset + count]
        else:
            paginated = expanded[offset:]
        
        return {
            "id": str(uuid.uuid4()),
            "url": vs.url,
            "name": vs.name,
            "status": vs.status,
            "expansion": {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "total": total,
                "offset": offset if offset > 0 else None,
                "contains": paginated
            }
        }

    def _find_concept(self, concepts: List[Dict], code: str) -> Optional[Dict]:
        for concept in concepts:
            if concept.get("code") == code:
                return concept
            if concept.get("concept"):
                nested = self._find_concept(concept["concept"], code)
                if nested:
                    return nested
        return None
    
    def _is_descendant(self, concepts: List[Dict], parent_code: str, child_code: str) -> bool:
        """
        Check if child_code is a descendant of parent_code in the concept hierarchy
        """
        parent = self._find_concept(concepts, parent_code)
        if not parent:
            return False
        
        # Check direct children
        if parent.get("concept"):
            for child in parent["concept"]:
                if child.get("code") == child_code:
                    return True
                # Recursively check descendants
                if self._is_descendant(parent["concept"], child["code"], child_code):
                    return True
        
        return False

    def _perform_expansion(self, db: Session, compose: Dict, filter_text: Optional[str] = None) -> List[Dict]:
        expanded = []
        for include in compose.get("include", []):
            system = include.get("system")
            if include.get("concept"):
                for concept in include["concept"]:
                    if filter_text and filter_text.lower() not in concept.get("code", "").lower() and \
                       filter_text.lower() not in concept.get("display", "").lower():
                        continue
                    expanded.append({
                        "system": system,
                        "code": concept["code"],
                        "display": concept.get("display")
                    })
            elif system:
                cs = db.query(CodeSystemModel).filter(CodeSystemModel.url == system).first()
                if cs and cs.concept:
                    concepts = json.loads(cs.concept) if isinstance(cs.concept, str) else cs.concept
                    all_concepts = self._flatten_concepts(concepts)
                    for concept in all_concepts:
                        if filter_text and filter_text.lower() not in concept.get("code", "").lower() and \
                           filter_text.lower() not in concept.get("display", "").lower():
                            continue
                        expanded.append({
                            "system": system,
                            "code": concept["code"],
                            "display": concept.get("display")
                        })
        return expanded

    def _flatten_concepts(self, concepts: List[Dict]) -> List[Dict]:
        result = []
        for concept in concepts:
            result.append(concept)
            if concept.get("concept"):
                result.extend(self._flatten_concepts(concept["concept"]))
        return result

    def compose(self, db: Session, include_systems: List[str], exclude_systems: Optional[List[str]] = None, 
                filter_text: Optional[str] = None) -> Dict[str, Any]:
        """
        $compose operation - Creates a ValueSet from a composition of CodeSystems
        https://build.fhir.org/valueset-operation-compose.html
        
        This operation composes a ValueSet by including concepts from specified CodeSystems
        and optionally excluding concepts from other systems.
        """
        composed_concepts = []
        
        # Include concepts from specified systems
        for system_url in include_systems:
            cs = db.query(CodeSystemModel).filter(CodeSystemModel.url == system_url).first()
            if cs and cs.concept:
                concepts = json.loads(cs.concept) if isinstance(cs.concept, str) else cs.concept
                all_concepts = self._flatten_concepts(concepts)
                
                for concept in all_concepts:
                    # Apply filter if specified
                    if filter_text and filter_text.lower() not in concept.get("code", "").lower() and \
                       filter_text.lower() not in concept.get("display", "").lower():
                        continue
                    
                    composed_concepts.append({
                        "system": system_url,
                        "code": concept["code"],
                        "display": concept.get("display"),
                        "definition": concept.get("definition")
                    })
        
        # Exclude concepts from specified systems if provided
        if exclude_systems:
            exclude_codes = set()
            for system_url in exclude_systems:
                cs = db.query(CodeSystemModel).filter(CodeSystemModel.url == system_url).first()
                if cs and cs.concept:
                    concepts = json.loads(cs.concept) if isinstance(cs.concept, str) else cs.concept
                    all_concepts = self._flatten_concepts(concepts)
                    for concept in all_concepts:
                        exclude_codes.add((system_url, concept["code"]))
            
            # Filter out excluded concepts
            composed_concepts = [
                c for c in composed_concepts 
                if (c["system"], c["code"]) not in exclude_codes
            ]
        
        # Create ValueSet structure
        valueset_id = str(uuid.uuid4())
        valueset = {
            "resourceType": "ValueSet",
            "id": valueset_id,
            "url": f"http://example.org/fhir/ValueSet/composed-{valueset_id}",
            "version": "1.0.0",
            "name": f"ComposedValueSet{valueset_id[:8]}",
            "title": "Composed ValueSet",
            "status": "draft",
            "date": datetime.now(timezone.utc).isoformat(),
            "compose": {
                "include": [{"system": sys} for sys in include_systems],
                "exclude": [{"system": sys} for sys in (exclude_systems or [])]
            },
            "expansion": {
                "identifier": str(uuid.uuid4()),
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "total": len(composed_concepts),
                "contains": composed_concepts
            }
        }
        
        return valueset

    def find_matches(self, db: Session, system: Optional[str] = None, property_name: Optional[str] = None,
                    property_value: Optional[str] = None, exact: bool = False) -> Parameters:
        """
        $find-matches operation - Search for codes matching supplied properties
        https://build.fhir.org/codesystem-operation-find-matches.html
        
        This operation searches for codes that match the provided search criteria.
        Can search by:
        - display text (default)
        - code
        - any other property
        """
        matches = []
        
        # Query CodeSystems
        query = db.query(CodeSystemModel)
        if system:
            query = query.filter(CodeSystemModel.url == system)
        
        code_systems = query.all()
        
        for cs in code_systems:
            if not cs.concept:
                continue
            
            concepts = json.loads(cs.concept) if isinstance(cs.concept, str) else cs.concept
            all_concepts = self._flatten_concepts(concepts)
            
            for concept in all_concepts:
                match_found = False
                
                # If no property specified, search in display and code
                if not property_name or property_name == "display":
                    display = concept.get("display", "")
                    if property_value:
                        if exact:
                            match_found = display == property_value
                        else:
                            match_found = property_value.lower() in display.lower()
                
                if not match_found and (not property_name or property_name == "code"):
                    code = concept.get("code", "")
                    if property_value:
                        if exact:
                            match_found = code == property_value
                        else:
                            match_found = property_value.lower() in code.lower()
                
                # Search in definition
                if not match_found and (not property_name or property_name == "definition"):
                    definition = concept.get("definition", "")
                    if property_value and definition:
                        if exact:
                            match_found = definition == property_value
                        else:
                            match_found = property_value.lower() in definition.lower()
                
                # Search in custom properties
                if not match_found and property_name and property_name not in ["display", "code", "definition"]:
                    properties = concept.get("property", [])
                    for prop in properties:
                        if prop.get("code") == property_name:
                            prop_value = prop.get("valueString", prop.get("valueCode", ""))
                            if property_value:
                                if exact:
                                    match_found = prop_value == property_value
                                else:
                                    match_found = property_value.lower() in str(prop_value).lower()
                
                if match_found:
                    matches.append({
                        "system": cs.url,
                        "code": concept.get("code"),
                        "display": concept.get("display"),
                        "definition": concept.get("definition")
                    })
        
        # Build Parameters response
        params = [
            Parameter(name="count", valueInteger=len(matches))
        ]
        
        for match in matches[:100]:  # Limit to 100 results
            params.append(
                Parameter(
                    name="match",
                    part=[
                        Parameter(name="code", valueCoding=Coding(
                            system=match["system"],
                            code=match["code"],
                            display=match.get("display")
                        )),
                        Parameter(name="display", valueString=match.get("display", "")),
                    ]
                )
            )
        
        return Parameters(parameter=params)

