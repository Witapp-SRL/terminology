"""
Seed script to populate the database with example FHIR terminology data
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv
from pathlib import Path

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Sample data
SAMPLE_CODE_SYSTEMS = [
    {
        "id": "example-diagnosis-codes",
        "resourceType": "CodeSystem",
        "url": "http://example.org/fhir/CodeSystem/diagnosis-codes",
        "version": "1.0.0",
        "name": "DiagnosisCodes",
        "title": "Example Diagnosis Codes",
        "status": "active",
        "experimental": False,
        "date": "2025-01-01T00:00:00Z",
        "publisher": "Example Health Organization",
        "description": "A simple code system for common diagnoses",
        "caseSensitive": True,
        "content": "complete",
        "count": 5,
        "concept": [
            {
                "code": "DX001",
                "display": "Hypertension",
                "definition": "Persistent high blood pressure",
                "property": [
                    {"code": "status", "valueCode": "active"},
                    {"code": "parent", "valueCode": "cardiovascular"}
                ]
            },
            {
                "code": "DX002",
                "display": "Type 2 Diabetes",
                "definition": "Metabolic disorder characterized by high blood sugar",
                "property": [
                    {"code": "status", "valueCode": "active"},
                    {"code": "parent", "valueCode": "endocrine"}
                ]
            },
            {
                "code": "DX003",
                "display": "Asthma",
                "definition": "Chronic respiratory condition",
                "property": [
                    {"code": "status", "valueCode": "active"},
                    {"code": "parent", "valueCode": "respiratory"}
                ]
            },
            {
                "code": "DX004",
                "display": "Depression",
                "definition": "Major depressive disorder",
                "property": [
                    {"code": "status", "valueCode": "active"},
                    {"code": "parent", "valueCode": "mental-health"}
                ]
            },
            {
                "code": "DX005",
                "display": "Migraine",
                "definition": "Severe recurring headache",
                "property": [
                    {"code": "status", "valueCode": "active"},
                    {"code": "parent", "valueCode": "neurological"}
                ]
            }
        ]
    },
    {
        "id": "example-medication-codes",
        "resourceType": "CodeSystem",
        "url": "http://example.org/fhir/CodeSystem/medication-codes",
        "version": "1.0.0",
        "name": "MedicationCodes",
        "title": "Example Medication Codes",
        "status": "active",
        "experimental": False,
        "date": "2025-01-01T00:00:00Z",
        "publisher": "Example Pharmacy System",
        "description": "Common medication codes",
        "caseSensitive": True,
        "content": "complete",
        "count": 5,
        "concept": [
            {
                "code": "MED001",
                "display": "Aspirin 100mg",
                "definition": "Low-dose aspirin tablet",
                "designation": [
                    {"language": "en", "value": "Aspirin 100mg"},
                    {"language": "it", "value": "Aspirina 100mg"}
                ]
            },
            {
                "code": "MED002",
                "display": "Metformin 500mg",
                "definition": "Metformin hydrochloride tablet",
                "designation": [
                    {"language": "en", "value": "Metformin 500mg"},
                    {"language": "it", "value": "Metformina 500mg"}
                ]
            },
            {
                "code": "MED003",
                "display": "Lisinopril 10mg",
                "definition": "ACE inhibitor for hypertension",
                "designation": [
                    {"language": "en", "value": "Lisinopril 10mg"},
                    {"language": "it", "value": "Lisinopril 10mg"}
                ]
            },
            {
                "code": "MED004",
                "display": "Albuterol Inhaler",
                "definition": "Bronchodilator for asthma",
                "designation": [
                    {"language": "en", "value": "Albuterol Inhaler"},
                    {"language": "it", "value": "Inalatore di Albuterolo"}
                ]
            },
            {
                "code": "MED005",
                "display": "Sertraline 50mg",
                "definition": "SSRI antidepressant",
                "designation": [
                    {"language": "en", "value": "Sertraline 50mg"},
                    {"language": "it", "value": "Sertralina 50mg"}
                ]
            }
        ]
    }
]

SAMPLE_VALUE_SETS = [
    {
        "id": "cardiovascular-conditions",
        "resourceType": "ValueSet",
        "url": "http://example.org/fhir/ValueSet/cardiovascular-conditions",
        "version": "1.0.0",
        "name": "CardiovascularConditions",
        "title": "Cardiovascular Conditions",
        "status": "active",
        "experimental": False,
        "date": "2025-01-01T00:00:00Z",
        "publisher": "Example Health Organization",
        "description": "Value set for cardiovascular-related diagnoses",
        "compose": {
            "include": [
                {
                    "system": "http://example.org/fhir/CodeSystem/diagnosis-codes",
                    "concept": [
                        {
                            "code": "DX001",
                            "display": "Hypertension"
                        }
                    ]
                }
            ]
        }
    },
    {
        "id": "chronic-conditions",
        "resourceType": "ValueSet",
        "url": "http://example.org/fhir/ValueSet/chronic-conditions",
        "version": "1.0.0",
        "name": "ChronicConditions",
        "title": "Chronic Conditions",
        "status": "active",
        "experimental": False,
        "date": "2025-01-01T00:00:00Z",
        "publisher": "Example Health Organization",
        "description": "Value set for chronic medical conditions",
        "compose": {
            "include": [
                {
                    "system": "http://example.org/fhir/CodeSystem/diagnosis-codes",
                    "concept": [
                        {
                            "code": "DX001",
                            "display": "Hypertension"
                        },
                        {
                            "code": "DX002",
                            "display": "Type 2 Diabetes"
                        },
                        {
                            "code": "DX003",
                            "display": "Asthma"
                        }
                    ]
                }
            ]
        }
    },
    {
        "id": "all-medications",
        "resourceType": "ValueSet",
        "url": "http://example.org/fhir/ValueSet/all-medications",
        "version": "1.0.0",
        "name": "AllMedications",
        "title": "All Medications",
        "status": "active",
        "experimental": False,
        "date": "2025-01-01T00:00:00Z",
        "publisher": "Example Pharmacy System",
        "description": "Complete list of all medications",
        "compose": {
            "include": [
                {
                    "system": "http://example.org/fhir/CodeSystem/medication-codes"
                }
            ]
        }
    }
]

SAMPLE_CONCEPT_MAPS = [
    {
        "id": "diagnosis-to-medication",
        "resourceType": "ConceptMap",
        "url": "http://example.org/fhir/ConceptMap/diagnosis-to-medication",
        "version": "1.0.0",
        "name": "DiagnosisToMedication",
        "title": "Diagnosis to Medication Mapping",
        "status": "active",
        "experimental": False,
        "date": "2025-01-01T00:00:00Z",
        "publisher": "Example Health Organization",
        "description": "Maps common diagnoses to typical medications",
        "sourceCanonical": "http://example.org/fhir/ValueSet/chronic-conditions",
        "targetCanonical": "http://example.org/fhir/ValueSet/all-medications",
        "group": [
            {
                "source": "http://example.org/fhir/CodeSystem/diagnosis-codes",
                "target": "http://example.org/fhir/CodeSystem/medication-codes",
                "element": [
                    {
                        "code": "DX001",
                        "display": "Hypertension",
                        "target": [
                            {
                                "code": "MED003",
                                "display": "Lisinopril 10mg",
                                "relationship": "equivalent",
                                "comment": "First-line treatment for hypertension"
                            }
                        ]
                    },
                    {
                        "code": "DX002",
                        "display": "Type 2 Diabetes",
                        "target": [
                            {
                                "code": "MED002",
                                "display": "Metformin 500mg",
                                "relationship": "equivalent",
                                "comment": "First-line treatment for Type 2 Diabetes"
                            }
                        ]
                    },
                    {
                        "code": "DX003",
                        "display": "Asthma",
                        "target": [
                            {
                                "code": "MED004",
                                "display": "Albuterol Inhaler",
                                "relationship": "equivalent",
                                "comment": "Rescue inhaler for asthma"
                            }
                        ]
                    },
                    {
                        "code": "DX004",
                        "display": "Depression",
                        "target": [
                            {
                                "code": "MED005",
                                "display": "Sertraline 50mg",
                                "relationship": "equivalent",
                                "comment": "SSRI for depression treatment"
                            }
                        ]
                    }
                ]
            }
        ]
    }
]


async def seed_database():
    """Seed the database with example data"""
    mongo_url = os.environ['MONGO_URL']
    db_name = os.environ['DB_NAME']
    
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    
    try:
        print("🌱 Starting database seeding...")
        
        # Clear existing data
        print("Clearing existing data...")
        await db.code_systems.delete_many({})
        await db.value_sets.delete_many({})
        await db.concept_maps.delete_many({})
        
        # Insert Code Systems
        print(f"Inserting {len(SAMPLE_CODE_SYSTEMS)} Code Systems...")
        await db.code_systems.insert_many(SAMPLE_CODE_SYSTEMS)
        
        # Insert Value Sets
        print(f"Inserting {len(SAMPLE_VALUE_SETS)} Value Sets...")
        await db.value_sets.insert_many(SAMPLE_VALUE_SETS)
        
        # Insert Concept Maps
        print(f"Inserting {len(SAMPLE_CONCEPT_MAPS)} Concept Maps...")
        await db.concept_maps.insert_many(SAMPLE_CONCEPT_MAPS)
        
        print("✅ Database seeding completed successfully!")
        
        # Print summary
        print("\n📊 Summary:")
        print(f"   - Code Systems: {await db.code_systems.count_documents({})}")
        print(f"   - Value Sets: {await db.value_sets.count_documents({})}")
        print(f"   - Concept Maps: {await db.concept_maps.count_documents({})}")
        
    except Exception as e:
        print(f"❌ Error seeding database: {e}")
    finally:
        client.close()


if __name__ == "__main__":
    asyncio.run(seed_database())
