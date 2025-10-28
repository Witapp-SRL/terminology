#!/bin/bash
# =====================================================
# Quick Reference - PostgreSQL Commands
# =====================================================

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${GREEN}PostgreSQL Quick Reference Commands${NC}"
echo "====================================="
echo ""

# Service Management
echo -e "${BLUE}SERVICE MANAGEMENT:${NC}"
echo "sudo systemctl start postgresql      # Start PostgreSQL"
echo "sudo systemctl stop postgresql       # Stop PostgreSQL"
echo "sudo systemctl restart postgresql    # Restart PostgreSQL"
echo "sudo systemctl status postgresql     # Check status"
echo ""

# Database Connection
echo -e "${BLUE}CONNECT TO DATABASE:${NC}"
echo "psql -U fhir_user -d fhir_terminology"
echo "sudo -u postgres psql                # Connect as postgres superuser"
echo ""

# Common SQL Commands
echo -e "${BLUE}INSIDE PSQL:${NC}"
echo "\\l                                   # List all databases"
echo "\\c fhir_terminology                  # Connect to database"
echo "\\dt                                  # List all tables"
echo "\\d code_systems                      # Describe table structure"
echo "\\dt+                                 # List tables with sizes"
echo "\\du                                  # List users/roles"
echo "\\q                                   # Quit psql"
echo ""

# Data Queries
echo -e "${BLUE}USEFUL QUERIES:${NC}"
echo ""
echo "-- Count records in each table"
echo "SELECT 'code_systems' as table_name, COUNT(*) as count FROM code_systems"
echo "UNION ALL"
echo "SELECT 'value_sets', COUNT(*) FROM value_sets"
echo "UNION ALL"
echo "SELECT 'concept_maps', COUNT(*) FROM concept_maps;"
echo ""
echo "-- Search CodeSystems by name"
echo "SELECT id, name, title, status, count FROM code_systems WHERE name ILIKE '%ICD%';"
echo ""
echo "-- Get all ICD-9 codes"
echo "SELECT concept->>'code' as code, concept->>'display' as display"
echo "FROM code_systems, jsonb_array_elements(concept) as concept"
echo "WHERE name = 'ICD9CM' LIMIT 10;"
echo ""

# Backup/Restore
echo -e "${BLUE}BACKUP & RESTORE:${NC}"
echo "# Backup"
echo "pg_dump -U fhir_user fhir_terminology > backup_\$(date +%Y%m%d).sql"
echo ""
echo "# Restore"
echo "psql -U fhir_user fhir_terminology < backup_20241028.sql"
echo ""
echo "# Compressed backup"
echo "pg_dump -U fhir_user -F c fhir_terminology > backup.dump"
echo ""

# Maintenance
echo -e "${BLUE}MAINTENANCE:${NC}"
echo "# Analyze tables (update statistics)"
echo "psql -U fhir_user -d fhir_terminology -c 'ANALYZE;'"
echo ""
echo "# Vacuum (clean up)"
echo "psql -U fhir_user -d fhir_terminology -c 'VACUUM ANALYZE;'"
echo ""

# Monitoring
echo -e "${BLUE}MONITORING:${NC}"
echo "# Database size"
echo "psql -U fhir_user -d fhir_terminology -c \"SELECT pg_size_pretty(pg_database_size('fhir_terminology'));\""
echo ""
echo "# Active connections"
echo "psql -U fhir_user -d fhir_terminology -c \"SELECT * FROM pg_stat_activity WHERE datname = 'fhir_terminology';\""
echo ""

# Application Integration
echo -e "${BLUE}APPLICATION INTEGRATION:${NC}"
echo "# Update .env file"
echo "DATABASE_URL=postgresql://fhir_user:password@localhost:5432/fhir_terminology"
echo ""
echo "# Test connection"
echo "python -c 'from database import SessionLocal; db = SessionLocal(); print(\"✓ Connected\"); db.close()'"
echo ""

echo "====================================="
echo -e "${GREEN}For detailed documentation, see:${NC}"
echo "/app/backend/README_POSTGRESQL.md"
echo ""
