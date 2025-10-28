from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import or_
from models.fhir_models import (
    Parameters, Parameter, Coding, ValueSetExpansion, ValueSetExpansionContains
)
from database import CodeSystemModel, ValueSetModel, ConceptMapModel
import json

class TerminologyServiceSQL:
    def __init__(self):
        pass

    def lookup(self, db: Session, system: str, code: str, version: Optional[str] = None, properties: Optional[List[str]] = None) -> Parameters:
        query = db.query(CodeSystemModel).filter(CodeSystemModel.url == system)
        if version:
            query = query.filter(CodeSystemModel.version == version)
        
        cs = query.first()
        if not cs:
            return Parameters(parameter=[Parameter(name="message", valueString=f"Code system {system} not found")])
        
        concept = self._find_concept(cs.concept or [], code)
        if not concept:
            return Parameters(parameter=[Parameter(name="message", valueString=f"Code {code} not found")])
        
        params = [
            Parameter(name="name", valueString=cs.name),
            Parameter(name="display", valueString=concept.get("display", "")),
        ]
        if cs.version:
            params.append(Parameter(name="version", valueString=cs.version))
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
        
        concept = self._find_concept(cs.concept or [], code)
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
        
        expanded = self._perform_expansion(db, vs.compose or {}, filter_text)
        
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
                    all_concepts = self._flatten_concepts(cs.concept)
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
