#!/bin/bash
# =====================================================
# FHIR Terminology Service - PostgreSQL Setup for Ubuntu
# =====================================================

set -e  # Exit on error

echo "========================================"
echo "FHIR Terminology Service - PostgreSQL Setup"
echo "========================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   echo -e "${RED}This script must be run as root (use sudo)${NC}"
   exit 1
fi

echo -e "${GREEN}Step 1: Updating system packages...${NC}"
apt-get update

echo -e "${GREEN}Step 2: Installing PostgreSQL...${NC}"
apt-get install -y postgresql postgresql-contrib

echo -e "${GREEN}Step 3: Starting PostgreSQL service...${NC}"
systemctl start postgresql
systemctl enable postgresql

echo -e "${GREEN}Step 4: Creating database and user...${NC}"

# Prompt for database configuration
read -p "Enter database name [default: fhir_terminology]: " DB_NAME
DB_NAME=${DB_NAME:-fhir_terminology}

read -p "Enter database user [default: fhir_user]: " DB_USER
DB_USER=${DB_USER:-fhir_user}

read -sp "Enter database password: " DB_PASSWORD
echo ""

if [ -z "$DB_PASSWORD" ]; then
    echo -e "${RED}Password cannot be empty!${NC}"
    exit 1
fi

# Create database and user
sudo -u postgres psql <<EOF
-- Create user
CREATE USER $DB_USER WITH PASSWORD '$DB_PASSWORD';

-- Create database
CREATE DATABASE $DB_NAME OWNER $DB_USER;

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;

-- Connect to database and grant schema privileges
\c $DB_NAME
GRANT ALL ON SCHEMA public TO $DB_USER;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO $DB_USER;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO $DB_USER;

EOF

echo -e "${GREEN}Step 5: Running database schema initialization...${NC}"
sudo -u postgres psql -d $DB_NAME -f /app/backend/database/init_postgres.sql

echo -e "${GREEN}Step 6: Configuring PostgreSQL for remote connections (optional)...${NC}"
read -p "Allow remote connections? (y/N): " ALLOW_REMOTE

if [[ $ALLOW_REMOTE =~ ^[Yy]$ ]]; then
    PG_VERSION=$(psql --version | awk '{print $3}' | cut -d. -f1)
    PG_CONF="/etc/postgresql/$PG_VERSION/main/postgresql.conf"
    PG_HBA="/etc/postgresql/$PG_VERSION/main/pg_hba.conf"
    
    # Backup original files
    cp $PG_CONF "${PG_CONF}.backup"
    cp $PG_HBA "${PG_HBA}.backup"
    
    # Allow listening on all interfaces
    sed -i "s/#listen_addresses = 'localhost'/listen_addresses = '*'/g" $PG_CONF
    
    # Add rule to allow connections (adjust as needed)
    echo "host    all             all             0.0.0.0/0               md5" >> $PG_HBA
    
    # Restart PostgreSQL
    systemctl restart postgresql
    
    echo -e "${YELLOW}WARNING: PostgreSQL is now accessible from any IP address.${NC}"
    echo -e "${YELLOW}Make sure to configure firewall rules appropriately!${NC}"
fi

echo -e "${GREEN}Step 7: Creating .env configuration file...${NC}"

cat > /app/backend/.env.postgres <<EOF
# PostgreSQL Database Configuration
DATABASE_URL=postgresql://${DB_USER}:${DB_PASSWORD}@localhost:5432/${DB_NAME}
DB_NAME=${DB_NAME}
CORS_ORIGINS=*
EOF

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}PostgreSQL Setup Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Database Name: $DB_NAME"
echo "Database User: $DB_USER"
echo "Connection String: postgresql://${DB_USER}:****@localhost:5432/${DB_NAME}"
echo ""
echo "Configuration file created: /app/backend/.env.postgres"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo "1. Backup your current .env: cp /app/backend/.env /app/backend/.env.sqlite.backup"
echo "2. Use PostgreSQL config: cp /app/backend/.env.postgres /app/backend/.env"
echo "3. Install psycopg2: pip install psycopg2-binary"
echo "4. Run seed data: python /app/backend/seed_data_medical.py"
echo "5. Restart backend: sudo supervisorctl restart backend"
echo ""
