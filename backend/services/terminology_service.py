from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorDatabase
from models.fhir_models import (
    CodeSystem,
    ValueSet,
    ConceptMap,
    Parameters,
    Parameter,
    Coding,
    ValueSetExpansion,
    ValueSetExpansionContains,
    ConceptMapEquivalence,
)
import uuid
import re


class TerminologyService:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db

    # CodeSystem Operations
    async def lookup(self, system: str, code: str, version: Optional[str] = None, properties: Optional[List[str]] = None) -> Parameters:
        """$lookup operation - Get information about a code"""
        query = {"url": system}
        if version:
            query["version"] = version

        code_system = await self.db.code_systems.find_one(query, {"_id": 0})
        if not code_system:
            return Parameters(
                parameter=[
                    Parameter(name="message", valueString=f"Code system {system} not found")
                ]
            )

        # Find the concept
        concept = self._find_concept_in_system(code_system.get("concept", []), code)
        if not concept:
            return Parameters(
                parameter=[
                    Parameter(name="message", valueString=f"Code {code} not found in system {system}")
                ]
            )

        # Build response
        params = [
            Parameter(name="name", valueString=code_system.get("name")),
            Parameter(name="display", valueString=concept.get("display", "")),
        ]

        if code_system.get("version"):
            params.append(Parameter(name="version", valueString=code_system["version"]))

        if concept.get("definition"):
            params.append(Parameter(name="definition", valueString=concept["definition"]))

        # Add designations
        if concept.get("designation"):
            for desig in concept["designation"]:
                params.append(
                    Parameter(
                        name="designation",
                        part=[
                            Parameter(name="language", valueString=desig.get("language", "en")),
                            Parameter(name="value", valueString=desig["value"]),
                        ],
                    )
                )

        # Add properties if requested
        if properties and concept.get("property"):
            for prop in concept["property"]:
                if not properties or prop["code"] in properties:
                    prop_params = [Parameter(name="code", valueCode=prop["code"])]
                    
                    # Add the value based on type
                    for key in ["valueCode", "valueString", "valueInteger", "valueBoolean", "valueDateTime", "valueDecimal"]:
                        if key in prop:
                            prop_params.append(Parameter(name="value", **{key: prop[key]}))
                    
                    params.append(Parameter(name="property", part=prop_params))

        return Parameters(parameter=params)

    async def validate_code(self, system: str, code: str, version: Optional[str] = None, display: Optional[str] = None) -> Parameters:
        """$validate-code operation for CodeSystem - Check if a code is valid"""
        query = {"url": system}
        if version:
            query["version"] = version

        code_system = await self.db.code_systems.find_one(query, {"_id": 0})
        if not code_system:
            return Parameters(
                parameter=[
                    Parameter(name="result", valueBoolean=False),
                    Parameter(name="message", valueString=f"Code system {system} not found"),
                ]
            )

        concept = self._find_concept_in_system(code_system.get("concept", []), code)
        if not concept:
            return Parameters(
                parameter=[
                    Parameter(name="result", valueBoolean=False),
                    Parameter(name="message", valueString=f"Code {code} not found in system {system}"),
                ]
            )

        # Check display if provided
        params = [Parameter(name="result", valueBoolean=True)]
        
        if display and concept.get("display"):
            case_sensitive = code_system.get("caseSensitive", True)
            concept_display = concept["display"]
            
            if case_sensitive:
                display_matches = display == concept_display
            else:
                display_matches = display.lower() == concept_display.lower()
            
            if not display_matches:
                params.append(
                    Parameter(name="message", valueString=f"The display '{display}' is not correct. Expected: '{concept_display}'")
                )
        
        if concept.get("display"):
            params.append(Parameter(name="display", valueString=concept["display"]))

        return Parameters(parameter=params)

    async def subsumes(self, system: str, code_a: str, code_b: str, version: Optional[str] = None) -> Parameters:
        """$subsumes operation - Test subsumption relationship"""
        query = {"url": system}
        if version:
            query["version"] = version

        code_system = await self.db.code_systems.find_one(query, {"_id": 0})
        if not code_system:
            return Parameters(
                parameter=[
                    Parameter(name="message", valueString=f"Code system {system} not found")
                ]
            )

        # For simplicity, this checks hierarchical is-a relationships
        # In a full implementation, this would use the code system's subsumption rules
        
        if code_a == code_b:
            return Parameters(parameter=[Parameter(name="outcome", valueCode="equivalent")])

        concepts = code_system.get("concept", [])
        
        # Check if code_a subsumes code_b (code_b is descendant of code_a)
        if self._is_descendant(concepts, code_a, code_b):
            return Parameters(parameter=[Parameter(name="outcome", valueCode="subsumes")])
        
        # Check if code_b subsumes code_a (code_a is descendant of code_b)
        if self._is_descendant(concepts, code_b, code_a):
            return Parameters(parameter=[Parameter(name="outcome", valueCode="subsumed-by")])

        return Parameters(parameter=[Parameter(name="outcome", valueCode="not-subsumed")])

    # ValueSet Operations
    async def expand_valueset(self, url: Optional[str] = None, valueset_id: Optional[str] = None, 
                             filter_text: Optional[str] = None, offset: int = 0, count: Optional[int] = None) -> ValueSet:
        """$expand operation - Expand a value set"""
        if valueset_id:
            valueset = await self.db.value_sets.find_one({"id": valueset_id}, {"_id": 0})
        elif url:
            valueset = await self.db.value_sets.find_one({"url": url}, {"_id": 0})
        else:
            raise ValueError("Either url or valueset_id must be provided")

        if not valueset:
            raise ValueError(f"ValueSet not found")

        # Perform expansion
        expanded_concepts = await self._perform_expansion(valueset, filter_text)

        # Apply pagination
        total = len(expanded_concepts)
        if count:
            paginated_concepts = expanded_concepts[offset:offset + count]
        else:
            paginated_concepts = expanded_concepts[offset:]

        # Build expansion
        expansion = ValueSetExpansion(
            timestamp=datetime.now(timezone.utc),
            total=total,
            offset=offset if offset > 0 else None,
            contains=paginated_concepts,
        )

        # Create result ValueSet
        result = ValueSet(
            id=str(uuid.uuid4()),
            url=valueset["url"],
            name=valueset["name"],
            status=valueset["status"],
            expansion=expansion,
        )

        return result

    async def validate_code_valueset(self, url: str, code: str, system: str, 
                                    system_version: Optional[str] = None, display: Optional[str] = None) -> Parameters:
        """$validate-code operation for ValueSet - Check if a code is in a value set"""
        valueset = await self.db.value_sets.find_one({"url": url}, {"_id": 0})
        if not valueset:
            return Parameters(
                parameter=[
                    Parameter(name="result", valueBoolean=False),
                    Parameter(name="message", valueString=f"ValueSet {url} not found"),
                ]
            )

        # Check if code is in the expanded value set
        expanded_concepts = await self._perform_expansion(valueset)
        
        code_found = False
        concept_display = None
        
        for concept in expanded_concepts:
            if concept.code == code and (concept.system == system or system is None):
                code_found = True
                concept_display = concept.display
                break

        if not code_found:
            return Parameters(
                parameter=[
                    Parameter(name="result", valueBoolean=False),
                    Parameter(name="message", valueString=f"Code {code} from system {system} not found in value set"),
                ]
            )

        params = [Parameter(name="result", valueBoolean=True)]
        
        if display and concept_display:
            if display != concept_display:
                params.append(
                    Parameter(name="message", valueString=f"The display '{display}' is not correct. Expected: '{concept_display}'")
                )
        
        if concept_display:
            params.append(Parameter(name="display", valueString=concept_display))

        return Parameters(parameter=params)

    # ConceptMap Operations
    async def translate(self, url: Optional[str] = None, source_code: str = None, 
                       source_system: str = None, target_system: Optional[str] = None) -> Parameters:
        """$translate operation - Translate a code from one value set to another"""
        query = {}
        if url:
            query["url"] = url
        
        # Find applicable concept maps
        concept_maps = await self.db.concept_maps.find(query, {"_id": 0}).to_list(100)
        
        if not concept_maps:
            return Parameters(
                parameter=[
                    Parameter(name="result", valueBoolean=False),
                    Parameter(name="message", valueString="No concept map found"),
                ]
            )

        # Search for translation
        for concept_map in concept_maps:
            for group in concept_map.get("group", []):
                # Check if source system matches
                if source_system and group.get("source") and group["source"] != source_system:
                    continue
                
                # Check if target system matches (if specified)
                if target_system and group.get("target") and group["target"] != target_system:
                    continue

                # Find the source code
                for element in group.get("element", []):
                    if element.get("code") == source_code:
                        # Found a match, return targets
                        if element.get("target"):
                            params = [Parameter(name="result", valueBoolean=True)]
                            
                            for target in element["target"]:
                                if target.get("relationship") in ["equivalent", "equal", "relatedto"]:
                                    outcome_params = [
                                        Parameter(name="relationship", valueCode=target["relationship"])
                                    ]
                                    
                                    if target.get("code"):
                                        concept_coding = Coding(
                                            system=group.get("target"),
                                            code=target["code"],
                                            display=target.get("display")
                                        )
                                        outcome_params.append(Parameter(name="concept", valueCoding=concept_coding))
                                    
                                    params.append(Parameter(name="match", part=outcome_params))
                            
                            return Parameters(parameter=params)

        return Parameters(
            parameter=[
                Parameter(name="result", valueBoolean=False),
                Parameter(name="message", valueString=f"No translation found for code {source_code}"),
            ]
        )

    # Helper methods
    def _find_concept_in_system(self, concepts: List[Dict], code: str) -> Optional[Dict]:
        """Recursively find a concept by code in a concept list"""
        for concept in concepts:
            if concept.get("code") == code:
                return concept
            # Check nested concepts (hierarchical)
            if concept.get("concept"):
                nested = self._find_concept_in_system(concept["concept"], code)
                if nested:
                    return nested
        return None

    def _is_descendant(self, concepts: List[Dict], parent_code: str, child_code: str) -> bool:
        """Check if child_code is a descendant of parent_code"""
        parent = self._find_concept_in_system(concepts, parent_code)
        if not parent:
            return False
        
        # Check if child is in parent's descendants
        return self._find_concept_in_system(parent.get("concept", []), child_code) is not None

    async def _perform_expansion(self, valueset: Dict, filter_text: Optional[str] = None) -> List[ValueSetExpansionContains]:
        """Perform the actual expansion of a value set"""
        expanded = []
        
        if not valueset.get("compose"):
            return expanded

        compose = valueset["compose"]
        
        # Process includes
        for include in compose.get("include", []):
            system = include.get("system")
            
            # If specific concepts are listed
            if include.get("concept"):
                for concept in include["concept"]:
                    if filter_text:
                        # Simple text filter on code and display
                        if filter_text.lower() not in concept.get("code", "").lower() and \
                           filter_text.lower() not in concept.get("display", "").lower():
                            continue
                    
                    expanded.append(
                        ValueSetExpansionContains(
                            system=system,
                            code=concept["code"],
                            display=concept.get("display"),
                        )
                    )
            
            # If filters are specified
            elif include.get("filter"):
                # Get the code system
                if system:
                    code_system = await self.db.code_systems.find_one({"url": system}, {"_id": 0})
                    if code_system and code_system.get("concept"):
                        filtered_concepts = self._apply_filters(code_system["concept"], include["filter"])
                        
                        for concept in filtered_concepts:
                            if filter_text:
                                if filter_text.lower() not in concept.get("code", "").lower() and \
                                   filter_text.lower() not in concept.get("display", "").lower():
                                    continue
                            
                            expanded.append(
                                ValueSetExpansionContains(
                                    system=system,
                                    code=concept["code"],
                                    display=concept.get("display"),
                                )
                            )
            
            # If no filters or concepts, include all from system
            elif system:
                code_system = await self.db.code_systems.find_one({"url": system}, {"_id": 0})
                if code_system and code_system.get("concept"):
                    all_concepts = self._flatten_concepts(code_system["concept"])
                    
                    for concept in all_concepts:
                        if filter_text:
                            if filter_text.lower() not in concept.get("code", "").lower() and \
                               filter_text.lower() not in concept.get("display", "").lower():
                                continue
                        
                        expanded.append(
                            ValueSetExpansionContains(
                                system=system,
                                code=concept["code"],
                                display=concept.get("display"),
                            )
                        )

        # TODO: Process excludes
        # For now, we're not implementing exclude logic

        return expanded

    def _flatten_concepts(self, concepts: List[Dict]) -> List[Dict]:
        """Flatten hierarchical concept list"""
        result = []
        for concept in concepts:
            result.append(concept)
            if concept.get("concept"):
                result.extend(self._flatten_concepts(concept["concept"]))
        return result

    def _apply_filters(self, concepts: List[Dict], filters: List[Dict]) -> List[Dict]:
        """Apply filters to concept list"""
        result = []
        all_concepts = self._flatten_concepts(concepts)
        
        for concept in all_concepts:
            matches = True
            
            for filter_def in filters:
                property_name = filter_def["property"]
                operator = filter_def["op"]
                value = filter_def["value"]
                
                # Simple filter implementation
                if property_name == "code":
                    concept_value = concept.get("code", "")
                elif property_name == "display":
                    concept_value = concept.get("display", "")
                else:
                    # Check in properties
                    concept_value = None
                    for prop in concept.get("property", []):
                        if prop.get("code") == property_name:
                            # Get the value from the property
                            for key in ["valueCode", "valueString", "valueInteger", "valueBoolean"]:
                                if key in prop:
                                    concept_value = str(prop[key])
                                    break
                            break
                
                if concept_value is None:
                    matches = False
                    break
                
                # Apply operator
                if operator == "=":
                    if concept_value != value:
                        matches = False
                elif operator == "regex":
                    if not re.search(value, concept_value):
                        matches = False
                # Add more operators as needed
            
            if matches:
                result.append(concept)
        
        return result
