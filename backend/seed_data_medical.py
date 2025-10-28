"""
Seed realistic medical terminology data: ICD-9-CM, ICD-10-CM, SNOMED CT
"""
import sys
sys.path.append('/app/backend')
from database import SessionLocal, CodeSystemModel, ValueSetModel, ConceptMapModel
from datetime import datetime
import uuid
import json

# ICD-9-CM Data (International Classification of Diseases, 9th Revision, Clinical Modification)
ICD9_DATA = {
    "id": "icd9cm",
    "resource_type": "CodeSystem",
    "url": "http://hl7.org/fhir/sid/icd-9-cm",
    "version": "2014",
    "name": "ICD9CM",
    "title": "International Classification of Diseases, 9th Revision, Clinical Modification",
    "status": "active",
    "experimental": False,
    "date": datetime(2014, 10, 1),
    "publisher": "National Center for Health Statistics (NCHS)",
    "description": "ICD-9-CM is the official system of assigning codes to diagnoses and procedures",
    "case_sensitive": False,
    "content": "fragment",
    "count": 30,
    "concept": [
        {"code": "001.0", "display": "Cholera due to vibrio cholerae", "definition": "Cholera caused by Vibrio cholerae serotype O1"},
        {"code": "003.0", "display": "Salmonella gastroenteritis", "definition": "Gastroenteritis due to salmonella"},
        {"code": "008.45", "display": "Intestinal infection due to Clostridium difficile", "definition": "C. diff colitis"},
        {"code": "250.00", "display": "Diabetes mellitus without mention of complication", "definition": "Type II diabetes uncomplicated"},
        {"code": "401.1", "display": "Benign essential hypertension", "definition": "Primary hypertension, benign"},
        {"code": "401.9", "display": "Unspecified essential hypertension", "definition": "Essential hypertension NOS"},
        {"code": "410.00", "display": "Acute myocardial infarction of anterolateral wall", "definition": "AMI anterolateral wall, episode unspecified"},
        {"code": "410.01", "display": "Acute myocardial infarction of anterolateral wall, initial episode", "definition": "AMI anterolateral wall, initial"},
        {"code": "410.90", "display": "Acute myocardial infarction of unspecified site", "definition": "AMI unspecified site"},
        {"code": "414.00", "display": "Coronary atherosclerosis of unspecified type of vessel", "definition": "CAD unspecified"},
        {"code": "414.01", "display": "Coronary atherosclerosis of native coronary artery", "definition": "CAD of native vessel"},
        {"code": "427.31", "display": "Atrial fibrillation", "definition": "AF - irregular heart rhythm"},
        {"code": "428.0", "display": "Congestive heart failure, unspecified", "definition": "CHF"},
        {"code": "480.9", "display": "Viral pneumonia, unspecified", "definition": "Pneumonia due to virus"},
        {"code": "481", "display": "Pneumococcal pneumonia", "definition": "Pneumonia due to Streptococcus pneumoniae"},
        {"code": "486", "display": "Pneumonia, organism unspecified", "definition": "Pneumonia NOS"},
        {"code": "493.00", "display": "Extrinsic asthma without status asthmaticus", "definition": "Allergic asthma"},
        {"code": "493.90", "display": "Asthma, unspecified type, without status asthmaticus", "definition": "Asthma NOS"},
        {"code": "530.81", "display": "Esophageal reflux", "definition": "GERD - Gastroesophageal reflux disease"},
        {"code": "531.00", "display": "Acute gastric ulcer with hemorrhage", "definition": "Bleeding stomach ulcer, acute"},
        {"code": "550.90", "display": "Inguinal hernia without obstruction or gangrene", "definition": "Inguinal hernia, unilateral or unspecified"},
        {"code": "571.5", "display": "Cirrhosis of liver without mention of alcohol", "definition": "Non-alcoholic cirrhosis"},
        {"code": "578.9", "display": "Hemorrhage of gastrointestinal tract, unspecified", "definition": "GI bleeding NOS"},
        {"code": "599.0", "display": "Urinary tract infection, site not specified", "definition": "UTI"},
        {"code": "715.00", "display": "Osteoarthrosis, generalized, site unspecified", "definition": "Generalized osteoarthritis"},
        {"code": "715.90", "display": "Osteoarthrosis, unspecified whether generalized or localized", "definition": "Osteoarthritis NOS"},
        {"code": "780.60", "display": "Fever, unspecified", "definition": "Fever NOS"},
        {"code": "784.0", "display": "Headache", "definition": "Cephalgia"},
        {"code": "786.50", "display": "Chest pain, unspecified", "definition": "Chest pain NOS"},
        {"code": "789.00", "display": "Abdominal pain, unspecified site", "definition": "Abdominal pain NOS"}
    ]
}

# ICD-10-CM Data (International Classification of Diseases, 10th Revision, Clinical Modification)
ICD10_DATA = {
    "id": "icd10cm",
    "resource_type": "CodeSystem",
    "url": "http://hl7.org/fhir/sid/icd-10-cm",
    "version": "2024",
    "name": "ICD10CM",
    "title": "International Classification of Diseases, 10th Revision, Clinical Modification",
    "status": "active",
    "experimental": False,
    "date": datetime(2023, 10, 1),
    "publisher": "National Center for Health Statistics (NCHS)",
    "description": "ICD-10-CM is the diagnosis classification system developed by the Centers for Disease Control and Prevention",
    "case_sensitive": False,
    "content": "fragment",
    "count": 35,
    "concept": [
        {"code": "A00.0", "display": "Cholera due to Vibrio cholerae 01, biovar cholerae", "definition": "Classical cholera"},
        {"code": "A02.0", "display": "Salmonella enteritis", "definition": "Salmonella gastroenteritis"},
        {"code": "A04.7", "display": "Enterocolitis due to Clostridium difficile", "definition": "C. difficile colitis"},
        {"code": "E11.9", "display": "Type 2 diabetes mellitus without complications", "definition": "Type II DM uncomplicated"},
        {"code": "E11.65", "display": "Type 2 diabetes mellitus with hyperglycemia", "definition": "Type II DM with high blood sugar"},
        {"code": "I10", "display": "Essential (primary) hypertension", "definition": "Primary hypertension"},
        {"code": "I11.0", "display": "Hypertensive heart disease with heart failure", "definition": "Hypertensive heart disease with CHF"},
        {"code": "I21.01", "display": "ST elevation (STEMI) myocardial infarction involving left main coronary artery", "definition": "STEMI of LMCA"},
        {"code": "I21.09", "display": "ST elevation (STEMI) myocardial infarction involving other coronary artery", "definition": "STEMI other vessel"},
        {"code": "I21.4", "display": "Non-ST elevation (NSTEMI) myocardial infarction", "definition": "NSTEMI"},
        {"code": "I25.10", "display": "Atherosclerotic heart disease of native coronary artery without angina pectoris", "definition": "CAD without angina"},
        {"code": "I48.0", "display": "Paroxysmal atrial fibrillation", "definition": "Intermittent AF"},
        {"code": "I48.91", "display": "Unspecified atrial fibrillation", "definition": "Atrial fibrillation NOS"},
        {"code": "I50.9", "display": "Heart failure, unspecified", "definition": "Congestive heart failure NOS"},
        {"code": "J12.9", "display": "Viral pneumonia, unspecified", "definition": "Pneumonia due to virus NOS"},
        {"code": "J13", "display": "Pneumonia due to Streptococcus pneumoniae", "definition": "Pneumococcal pneumonia"},
        {"code": "J18.9", "display": "Pneumonia, unspecified organism", "definition": "Pneumonia NOS"},
        {"code": "J45.20", "display": "Mild intermittent asthma, uncomplicated", "definition": "Mild asthma"},
        {"code": "J45.909", "display": "Unspecified asthma, uncomplicated", "definition": "Asthma NOS"},
        {"code": "K21.9", "display": "Gastro-esophageal reflux disease without esophagitis", "definition": "GERD"},
        {"code": "K25.0", "display": "Acute gastric ulcer with hemorrhage", "definition": "Bleeding stomach ulcer"},
        {"code": "K40.90", "display": "Unilateral inguinal hernia, without obstruction or gangrene, not specified as recurrent", "definition": "Inguinal hernia"},
        {"code": "K70.30", "display": "Alcoholic cirrhosis of liver without ascites", "definition": "Alcoholic cirrhosis"},
        {"code": "K74.60", "display": "Unspecified cirrhosis of liver", "definition": "Cirrhosis NOS"},
        {"code": "K92.2", "display": "Gastrointestinal hemorrhage, unspecified", "definition": "GI bleeding"},
        {"code": "N39.0", "display": "Urinary tract infection, site not specified", "definition": "UTI"},
        {"code": "M15.0", "display": "Primary generalized (osteo)arthritis", "definition": "Generalized osteoarthritis"},
        {"code": "M19.90", "display": "Unspecified osteoarthritis, unspecified site", "definition": "Osteoarthritis NOS"},
        {"code": "R50.9", "display": "Fever, unspecified", "definition": "Fever NOS"},
        {"code": "R51", "display": "Headache", "definition": "Cephalalgia"},
        {"code": "R07.9", "display": "Chest pain, unspecified", "definition": "Chest pain NOS"},
        {"code": "R10.9", "display": "Unspecified abdominal pain", "definition": "Abdominal pain"},
        {"code": "Z23", "display": "Encounter for immunization", "definition": "Vaccination encounter"},
        {"code": "Z00.00", "display": "Encounter for general adult medical examination without abnormal findings", "definition": "Annual physical"},
        {"code": "Z79.4", "display": "Long term (current) use of insulin", "definition": "Insulin therapy"}
    ]
}

# SNOMED CT Data (Systematized Nomenclature of Medicine Clinical Terms)
SNOMED_DATA = {
    "id": "snomed-ct",
    "resource_type": "CodeSystem",
    "url": "http://snomed.info/sct",
    "version": "http://snomed.info/sct/900000000000207008/version/20230901",
    "name": "SNOMEDCT",
    "title": "SNOMED CT (International Edition)",
    "status": "active",
    "experimental": False,
    "date": datetime(2023, 9, 1),
    "publisher": "SNOMED International",
    "description": "SNOMED CT is the most comprehensive and precise clinical health terminology product in the world",
    "case_sensitive": False,
    "content": "fragment",
    "count": 40,
    "property": [
        {"code": "parent", "type": "code", "description": "Parent concept"},
        {"code": "inactive", "type": "boolean", "description": "Whether the concept is active"}
    ],
    "concept": [
        {"code": "73211009", "display": "Diabetes mellitus", "definition": "Metabolic disease characterized by high blood glucose", 
         "property": [{"code": "parent", "valueCode": "362969004"}]},
        {"code": "44054006", "display": "Type 2 diabetes mellitus", "definition": "Non-insulin dependent diabetes mellitus",
         "property": [{"code": "parent", "valueCode": "73211009"}]},
        {"code": "46635009", "display": "Type 1 diabetes mellitus", "definition": "Insulin dependent diabetes mellitus",
         "property": [{"code": "parent", "valueCode": "73211009"}]},
        {"code": "38341003", "display": "Hypertensive disorder", "definition": "Persistently elevated blood pressure",
         "property": [{"code": "parent", "valueCode": "49601007"}]},
        {"code": "59621000", "display": "Essential hypertension", "definition": "Primary hypertension",
         "property": [{"code": "parent", "valueCode": "38341003"}]},
        {"code": "22298006", "display": "Myocardial infarction", "definition": "Heart attack",
         "property": [{"code": "parent", "valueCode": "414545008"}]},
        {"code": "401303003", "display": "Acute ST segment elevation myocardial infarction", "definition": "STEMI",
         "property": [{"code": "parent", "valueCode": "22298006"}]},
        {"code": "401314000", "display": "Acute non-ST segment elevation myocardial infarction", "definition": "NSTEMI",
         "property": [{"code": "parent", "valueCode": "22298006"}]},
        {"code": "53741008", "display": "Coronary arteriosclerosis", "definition": "Coronary artery disease",
         "property": [{"code": "parent", "valueCode": "414545008"}]},
        {"code": "49436004", "display": "Atrial fibrillation", "definition": "Irregular heart rhythm",
         "property": [{"code": "parent", "valueCode": "698247007"}]},
        {"code": "42343007", "display": "Congestive heart failure", "definition": "Heart failure with congestion",
         "property": [{"code": "parent", "valueCode": "84114007"}]},
        {"code": "233604007", "display": "Pneumonia", "definition": "Inflammation of the lungs",
         "property": [{"code": "parent", "valueCode": "50417007"}]},
        {"code": "6142004", "display": "Influenza", "definition": "Flu - viral respiratory infection",
         "property": [{"code": "parent", "valueCode": "95896000"}]},
        {"code": "195967001", "display": "Asthma", "definition": "Chronic respiratory condition with airway inflammation",
         "property": [{"code": "parent", "valueCode": "50417007"}]},
        {"code": "195979001", "display": "Extrinsic asthma", "definition": "Allergic asthma",
         "property": [{"code": "parent", "valueCode": "195967001"}]},
        {"code": "235595009", "display": "Gastroesophageal reflux disease", "definition": "GERD",
         "property": [{"code": "parent", "valueCode": "53619000"}]},
        {"code": "397825006", "display": "Gastric ulcer", "definition": "Stomach ulcer",
         "property": [{"code": "parent", "valueCode": "13200003"}]},
        {"code": "396275006", "display": "Osteoarthritis", "definition": "Degenerative joint disease",
         "property": [{"code": "parent", "valueCode": "64859006"}]},
        {"code": "68496003", "display": "Polyarticular osteoarthritis", "definition": "Osteoarthritis affecting multiple joints",
         "property": [{"code": "parent", "valueCode": "396275006"}]},
        {"code": "68566005", "display": "Urinary tract infectious disease", "definition": "UTI",
         "property": [{"code": "parent", "valueCode": "40733004"}]},
        {"code": "235856003", "display": "Disorder of liver", "definition": "Hepatic disorder",
         "property": [{"code": "parent", "valueCode": "118940003"}]},
        {"code": "19943007", "display": "Cirrhosis of liver", "definition": "Hepatic cirrhosis",
         "property": [{"code": "parent", "valueCode": "235856003"}]},
        {"code": "74474003", "display": "Gastrointestinal hemorrhage", "definition": "GI bleeding",
         "property": [{"code": "parent", "valueCode": "131148009"}]},
        {"code": "386661006", "display": "Fever", "definition": "Pyrexia - elevated body temperature",
         "property": [{"code": "parent", "valueCode": "404684003"}]},
        {"code": "25064002", "display": "Headache", "definition": "Cephalalgia - pain in the head",
         "property": [{"code": "parent", "valueCode": "22253000"}]},
        {"code": "29857009", "display": "Chest pain", "definition": "Pain in chest region",
         "property": [{"code": "parent", "valueCode": "22253000"}]},
        {"code": "21522001", "display": "Abdominal pain", "definition": "Stomachache",
         "property": [{"code": "parent", "valueCode": "22253000"}]},
        {"code": "84229001", "display": "Fatigue", "definition": "Tiredness, lack of energy",
         "property": [{"code": "parent", "valueCode": "404684003"}]},
        {"code": "267036007", "display": "Dyspnea", "definition": "Shortness of breath",
         "property": [{"code": "parent", "valueCode": "404684003"}]},
        {"code": "422587007", "display": "Nausea", "definition": "Feeling of sickness",
         "property": [{"code": "parent", "valueCode": "404684003"}]},
        {"code": "422400008", "display": "Vomiting", "definition": "Emesis",
         "property": [{"code": "parent", "valueCode": "404684003"}]},
        {"code": "62315008", "display": "Diarrhea", "definition": "Loose or liquid bowel movements",
         "property": [{"code": "parent", "valueCode": "404684003"}]},
        {"code": "9826008", "display": "Conjunctivitis", "definition": "Pink eye - inflammation of conjunctiva",
         "property": [{"code": "parent", "valueCode": "128473001"}]},
        {"code": "70153002", "display": "Hemorrhoids", "definition": "Swollen veins in rectum or anus",
         "property": [{"code": "parent", "valueCode": "64572001"}]},
        {"code": "239720000", "display": "Tear of meniscus of knee", "definition": "Meniscal tear",
         "property": [{"code": "parent", "valueCode": "125605004"}]},
        {"code": "73595000", "display": "Strain", "definition": "Musculoskeletal strain",
         "property": [{"code": "parent", "valueCode": "125605004"}]},
        {"code": "271807003", "display": "Eruption of skin", "definition": "Rash",
         "property": [{"code": "parent", "valueCode": "95320005"}]},
        {"code": "247441003", "display": "Erythema", "definition": "Redness of skin",
         "property": [{"code": "parent", "valueCode": "95320005"}]},
        {"code": "271757001", "display": "Papular eruption", "definition": "Papular rash",
         "property": [{"code": "parent", "valueCode": "271807003"}]},
        {"code": "90560007", "display": "Gout", "definition": "Metabolic arthritis due to uric acid crystals",
         "property": [{"code": "parent", "valueCode": "399269003"}]}
    ]
}

def seed_medical_data():
    db = SessionLocal()
    try:
        print("🏥 Seeding medical terminology data...")
        
        # Clear existing data
        print("Clearing existing data...")
        db.query(CodeSystemModel).delete()
        db.query(ValueSetModel).delete()
        db.query(ConceptMapModel).delete()
        
        # Insert ICD-9-CM
        print("Inserting ICD-9-CM...")
        icd9 = CodeSystemModel(**{k: json.dumps(v) if isinstance(v, (dict, list)) else v for k, v in ICD9_DATA.items()})
        db.add(icd9)
        
        # Insert ICD-10-CM
        print("Inserting ICD-10-CM...")
        icd10 = CodeSystemModel(**{k: json.dumps(v) if isinstance(v, (dict, list)) else v for k, v in ICD10_DATA.items()})
        db.add(icd10)
        
        # Insert SNOMED CT
        print("Inserting SNOMED CT...")
        snomed = CodeSystemModel(**{k: json.dumps(v) if isinstance(v, (dict, list)) else v for k, v in SNOMED_DATA.items()})
        db.add(snomed)
        
        # Create example ValueSets
        print("Creating ValueSets...")
        diabetes_vs = ValueSetModel(
            id="diabetes-codes",
            url="http://example.org/fhir/ValueSet/diabetes-codes",
            name="DiabetesCodes",
            title="Diabetes Diagnosis Codes",
            status="active",
            description="All diabetes-related diagnosis codes from ICD-9, ICD-10, and SNOMED CT",
            compose=json.dumps({
                "include": [
                    {"system": "http://hl7.org/fhir/sid/icd-9-cm", "concept": [{"code": "250.00", "display": "Diabetes mellitus without mention of complication"}]},
                    {"system": "http://hl7.org/fhir/sid/icd-10-cm", "concept": [{"code": "E11.9", "display": "Type 2 diabetes mellitus without complications"}]},
                    {"system": "http://snomed.info/sct", "concept": [{"code": "73211009", "display": "Diabetes mellitus"}, {"code": "44054006", "display": "Type 2 diabetes mellitus"}]}
                ]
            })
        )
        db.add(diabetes_vs)
        
        # Create ConceptMap ICD-9 to ICD-10
        print("Creating ConceptMap...")
        icd_map = ConceptMapModel(
            id="icd9-to-icd10",
            url="http://example.org/fhir/ConceptMap/icd9-to-icd10",
            name="ICD9ToICD10",
            title="ICD-9-CM to ICD-10-CM Mapping",
            status="active",
            description="Mapping between ICD-9-CM and ICD-10-CM codes",
            source_canonical="http://hl7.org/fhir/sid/icd-9-cm",
            target_canonical="http://hl7.org/fhir/sid/icd-10-cm",
            group=json.dumps([{
                "source": "http://hl7.org/fhir/sid/icd-9-cm",
                "target": "http://hl7.org/fhir/sid/icd-10-cm",
                "element": [
                    {"code": "250.00", "target": [{"code": "E11.9", "relationship": "equivalent"}]},
                    {"code": "401.9", "target": [{"code": "I10", "relationship": "equivalent"}]},
                    {"code": "410.90", "target": [{"code": "I21.4", "relationship": "equivalent"}]},
                    {"code": "493.90", "target": [{"code": "J45.909", "relationship": "equivalent"}]},
                    {"code": "599.0", "target": [{"code": "N39.0", "relationship": "equivalent"}]}
                ]
            }])
        )
        db.add(icd_map)
        
        db.commit()
        
        print("✅ Medical terminology data seeded successfully!")
        print(f"   - ICD-9-CM: {len(ICD9_DATA['concept'])} concepts")
        print(f"   - ICD-10-CM: {len(ICD10_DATA['concept'])} concepts")
        print(f"   - SNOMED CT: {len(SNOMED_DATA['concept'])} concepts")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_medical_data()
