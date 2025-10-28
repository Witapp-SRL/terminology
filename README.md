# FHIR Terminology Service

Servizio completo di terminologia FHIR con supporto ICD-9, ICD-10, SNOMED CT e funzionalità Import/Export CSV.

## 📋 Panoramica

Sistema di gestione terminologie mediche FHIR-compliant con:
- **Database SQL** (SQLite/PostgreSQL)
- **Dataset medici realistici**: ICD-9-CM, ICD-10-CM, SNOMED CT
- **Operazioni FHIR**: $lookup, $validate-code, $expand, $subsumes, $translate
- **Import/Export CSV** massivo
- **UI amministrativa** completa

## 🚀 Quick Start

### Avvio Servizi

```bash
# Avvia tutti i servizi
sudo supervisorctl start all

# Verifica stato
sudo supervisorctl status
```

Accedi all'applicazione all'URL fornito da Emergent.

## 📊 Dataset Disponibili

### ICD-9-CM (2014)
- **URL**: `http://hl7.org/fhir/sid/icd-9-cm`
- **Codici**: 30 diagnosi comuni
- **Esempi**: 250.00 (Diabetes), 401.9 (Hypertension), 486 (Pneumonia)

### ICD-10-CM (2024)
- **URL**: `http://hl7.org/fhir/sid/icd-10-cm`
- **Codici**: 35 diagnosi moderne
- **Esempi**: E11.9 (Type 2 DM), I10 (Hypertension), J18.9 (Pneumonia)

### SNOMED CT (2023)
- **URL**: `http://snomed.info/sct`
- **Concetti**: 40 concetti clinici con gerarchia
- **Esempi**: 73211009 (Diabetes mellitus), 44054006 (Type 2 DM)

## 🗄️ Database

### Attuale: SQLite
```bash
# File database
/app/backend/terminology.db

# Visualizza dati
cd /app/backend
python -c "from database import SessionLocal, CodeSystemModel; db = SessionLocal(); print(f'CodeSystems: {db.query(CodeSystemModel).count()}'); db.close()"
```

### Migrazione a PostgreSQL

Ho creato tutti i file necessari per PostgreSQL su Ubuntu:

#### 📁 File Creati

**1. Schema Database SQL:**
- `/app/backend/database/init_postgres.sql` (5.6KB)
  - DDL completo per PostgreSQL
  - 3 tabelle ottimizzate: code_systems, value_sets, concept_maps
  - Indici GIN per JSONB
  - Trigger automatici per updated_at

**2. Script di Setup Automatico:**
- `/app/backend/database/setup_ubuntu.sh` ⭐ **ESEGUIBILE**
  - Installazione completa PostgreSQL
  - Creazione database e utente
  - Inizializzazione schema
  - Configurazione .env

**3. File di Configurazione:**
- `/app/backend/database/postgresql.conf.sample`
- `/app/backend/database/pg_hba.conf.sample`

**4. Script di Migrazione:**
- `/app/backend/database/migrate_to_postgres.py` ⭐ **ESEGUIBILE**
  - Migrazione automatica SQLite → PostgreSQL

**5. Documentazione:**
- `/app/backend/README_POSTGRESQL.md` (guida completa)
- `/app/backend/database/postgres_commands.sh` (quick reference)

#### 🚀 Setup PostgreSQL (2 Minuti)

**Opzione 1: Setup Automatico (Consigliato)**
```bash
sudo /app/backend/database/setup_ubuntu.sh
```

Lo script farà tutto:
- ✅ Installa PostgreSQL
- ✅ Crea database `fhir_terminology`
- ✅ Crea utente `fhir_user`
- ✅ Inizializza schema
- ✅ Crea `.env.postgres`

**Opzione 2: Setup Manuale**
```bash
# 1. Installa PostgreSQL
sudo apt update && sudo apt install postgresql postgresql-contrib

# 2. Crea database
sudo -u postgres psql
CREATE USER fhir_user WITH PASSWORD 'your_password';
CREATE DATABASE fhir_terminology OWNER fhir_user;
GRANT ALL PRIVILEGES ON DATABASE fhir_terminology TO fhir_user;
\q

# 3. Inizializza schema
sudo -u postgres psql -d fhir_terminology -f /app/backend/database/init_postgres.sql

# 4. Aggiorna .env
DATABASE_URL=postgresql://fhir_user:your_password@localhost:5432/fhir_terminology
```

#### 🔄 Migrazione Dati

```bash
# Migra da SQLite a PostgreSQL
python /app/backend/database/migrate_to_postgres.py
```

#### 📝 Dopo l'Installazione

```bash
# 1. Installa driver Python
pip install psycopg2-binary

# 2. Usa configurazione PostgreSQL
cp /app/backend/.env.postgres /app/backend/.env

# 3. Popola database (se nuova installazione)
python /app/backend/seed_data_medical.py

# 4. Riavvia backend
sudo supervisorctl restart backend
```

#### 🔧 Comandi PostgreSQL Utili

```bash
# Connetti al database
psql -U fhir_user -d fhir_terminology

# Service management
sudo systemctl status postgresql
sudo systemctl restart postgresql

# Backup
pg_dump -U fhir_user fhir_terminology > backup.sql

# Quick reference completo
bash /app/backend/database/postgres_commands.sh
```

#### 📊 Struttura Database PostgreSQL

```sql
code_systems (
  id VARCHAR(255) PRIMARY KEY,
  url VARCHAR(500) UNIQUE NOT NULL,
  name VARCHAR(255) NOT NULL,
  concept JSONB,              -- Array JSON di concetti
  property JSONB,             -- Proprietà del CodeSystem
  ... + metadata FHIR
  + indici GIN su JSONB
  + trigger updated_at
)

value_sets (...)
concept_maps (...)
```

## 📥 Import/Export CSV

### Import CSV

1. Vai su `/csv` nell'interfaccia
2. Carica CSV con formato: `code,display,definition`
3. Sistema crea automaticamente nuovo CodeSystem

**Template CSV:**
```csv
code,display,definition
DX001,Hypertension,High blood pressure
DX002,Diabetes,Metabolic disorder
```

### Export CSV

- Apri dettaglio CodeSystem
- Clicca "Esporta CSV"
- Scarica file

**Via API:**
```bash
# Import
curl -F "file=@mycodes.csv" http://localhost:8001/api/CodeSystem/import-csv

# Export
curl "http://localhost:8001/api/CodeSystem/icd9cm/export-csv" > icd9.csv
```

## 🔗 API Endpoints

### FHIR Operations

```bash
# Lookup codice
GET /api/CodeSystem/$lookup?system=http://snomed.info/sct&code=73211009

# Valida codice
GET /api/CodeSystem/$validate-code?system=http://hl7.org/fhir/sid/icd-10-cm&code=E11.9

# Espandi ValueSet
GET /api/ValueSet/$expand?url=http://example.org/fhir/ValueSet/diabetes-codes
```

### CRUD

```bash
# Lista CodeSystems
GET /api/CodeSystem

# Cerca per nome
GET /api/CodeSystem?name=SNOMED

# Dettagli specifico
GET /api/CodeSystem/icd9cm

# ValueSets
GET /api/ValueSet

# ConceptMaps
GET /api/ConceptMap
```

## 🎨 Interfaccia UI

- **Dashboard**: Overview con statistiche
- **Code Systems**: Gestione ICD-9, ICD-10, SNOMED
- **Value Sets**: Composizione value sets
- **Concept Maps**: Mappature tra terminologie
- **Import/Export CSV**: Caricamento massivo
- **Operations Tester**: Test operazioni FHIR

## 🏗️ Struttura Progetto

```
/app/
├── backend/
│   ├── database/
│   │   ├── init_postgres.sql          # Schema PostgreSQL
│   │   ├── setup_ubuntu.sh            # Setup automatico
│   │   ├── migrate_to_postgres.py     # Script migrazione
│   │   ├── postgresql.conf.sample     # Config PostgreSQL
│   │   ├── pg_hba.conf.sample         # Auth config
│   │   └── postgres_commands.sh       # Quick reference
│   ├── models/
│   │   └── fhir_models.py             # Modelli FHIR Pydantic
│   ├── services/
│   │   └── terminology_service_sql.py # Logica operazioni
│   ├── database.py                    # Setup SQLAlchemy
│   ├── server.py                      # API FastAPI
│   ├── seed_data_medical.py           # Dataset medici
│   ├── requirements.txt
│   └── .env
├── frontend/
│   ├── src/
│   │   ├── pages/                     # Tutte le pagine UI
│   │   ├── components/                # Componenti React
│   │   ├── api/client.js              # Client API
│   │   └── App.js
│   └── package.json
└── README.md (questo file)
```

## 🔐 Sicurezza

- Password forti per database
- Limita accesso in `pg_hba.conf`
- SSL per connessioni remote
- Backup regolari
- Monitora log

## 📚 Documentazione Completa

- **PostgreSQL**: `/app/backend/README_POSTGRESQL.md`
- **Quick Reference**: `bash /app/backend/database/postgres_commands.sh`
- **FHIR Specs**: https://build.fhir.org/terminology-service.html

## ✨ Caratteristiche

✅ Database SQL relazionale (SQLite/PostgreSQL)
✅ 105 codici medici realistici
✅ Standard HL7 URLs
✅ Gerarchie SNOMED con proprietà parent
✅ Mappings ICD-9 ↔ ICD-10
✅ Import/Export CSV massivo
✅ UI amministrativa completa
✅ Operazioni FHIR complete
✅ Ricerca e filtri avanzati

## 🆘 Troubleshooting

### Backend non parte
```bash
tail -50 /var/log/supervisor/backend.err.log
```

### Database connection error
```bash
# Verifica config
cat /app/backend/.env

# Testa connessione
python -c "from database import SessionLocal; db = SessionLocal(); print('✓ OK'); db.close()"
```

### PostgreSQL issues
```bash
# Stato servizio
sudo systemctl status postgresql

# Log PostgreSQL
sudo tail -50 /var/log/postgresql/postgresql-*-main.log
```

## 📞 Support

Per problemi o domande:
- Controlla i log: `/var/log/supervisor/`
- Documentazione PostgreSQL: `/app/backend/README_POSTGRESQL.md`
- Quick commands: `bash /app/backend/database/postgres_commands.sh`

---

**Sviluppato con FastAPI + React + SQLAlchemy + PostgreSQL**
