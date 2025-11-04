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
