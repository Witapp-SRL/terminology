#!/bin/bash

#############################################
# FHIR Terminology Service - Auto Install
# Ubuntu 20.04/22.04 LTS
#############################################

set -e  # Exit on error

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
APP_DIR="/opt/fhir-terminology"
APP_USER="fhir"
BACKEND_PORT=8001
FRONTEND_PORT=3000

# Banner
echo -e "${GREEN}"
echo "╔════════════════════════════════════════════╗"
echo "║  FHIR Terminology Service Installer       ║"
echo "║  Ubuntu 20.04/22.04 LTS                   ║"
echo "╚════════════════════════════════════════════╝"
echo -e "${NC}"

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   echo -e "${RED}This script must be run as root (use sudo)${NC}"
   exit 1
fi

# Get real user (if using sudo)
REAL_USER=${SUDO_USER:-$USER}

echo -e "${BLUE}Installation will be performed in: ${APP_DIR}${NC}"
echo ""

# Prompt for configuration
read -p "Continue with installation? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    exit 1
fi

echo ""
echo -e "${GREEN}Starting installation...${NC}"
echo ""

#############################################
# 1. System Update
#############################################
echo -e "${YELLOW}[1/10] Updating system packages...${NC}"
apt-get update -qq
apt-get upgrade -y -qq

#############################################
# 2. Install Base Tools
#############################################
echo -e "${YELLOW}[2/10] Installing base tools...${NC}"
apt-get install -y -qq \
    build-essential \
    git \
    curl \
    wget \
    vim \
    software-properties-common \
    apt-transport-https \
    ca-certificates \
    gnupg \
    lsb-release \
    supervisor \
    nginx

#############################################
# 3. Install Python 3
#############################################
echo -e "${YELLOW}[3/10] Installing Python 3 and pip...${NC}"
apt-get install -y -qq python3 python3-pip python3-venv
python3 --version

#############################################
# 4. Install Node.js and Yarn
#############################################
echo -e "${YELLOW}[4/10] Installing Node.js 18.x and Yarn...${NC}"
curl -fsSL https://deb.nodesource.com/setup_18.x | bash - > /dev/null 2>&1
apt-get install -y -qq nodejs
npm install -g yarn > /dev/null 2>&1
node --version
yarn --version

#############################################
# 5. Install PostgreSQL (Optional)
#############################################
read -p "Install PostgreSQL? (recommended) (Y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]] || [[ -z $REPLY ]]; then
    echo -e "${YELLOW}[5/10] Installing PostgreSQL...${NC}"
    apt-get install -y -qq postgresql postgresql-contrib
    systemctl start postgresql
    systemctl enable postgresql
    echo -e "${GREEN}✓ PostgreSQL installed${NC}"
else
    echo -e "${YELLOW}[5/10] Skipping PostgreSQL (will use SQLite)${NC}"
fi

#############################################
# 6. Create Application User
#############################################
echo -e "${YELLOW}[6/10] Creating application user...${NC}"
if id "$APP_USER" &>/dev/null; then
    echo "User $APP_USER already exists"
else
    useradd -m -s /bin/bash $APP_USER
    echo -e "${GREEN}✓ User $APP_USER created${NC}"
fi

#############################################
# 7. Setup Application Directory
#############################################
echo -e "${YELLOW}[7/10] Setting up application directory...${NC}"

# Check if source files exist
if [ -d "/app/backend" ] && [ -d "/app/frontend" ]; then
    echo "Copying files from /app..."
    mkdir -p $APP_DIR
    cp -r /app/backend $APP_DIR/
    cp -r /app/frontend $APP_DIR/
    
    # Copy documentation
    [ -f "/app/README.md" ] && cp /app/README.md $APP_DIR/
    [ -f "/app/INSTALLATION_UBUNTU.md" ] && cp /app/INSTALLATION_UBUNTU.md $APP_DIR/
else
    echo -e "${RED}Source files not found in /app/${NC}"
    echo "Please ensure backend and frontend directories exist"
    exit 1
fi

# Set ownership
chown -R $APP_USER:$APP_USER $APP_DIR

#############################################
# 8. Setup Backend
#############################################
echo -e "${YELLOW}[8/10] Setting up backend...${NC}"

cd $APP_DIR/backend

# Create virtual environment
sudo -u $APP_USER python3 -m venv venv

# Install dependencies
sudo -u $APP_USER bash -c "source venv/bin/activate && pip install --upgrade pip > /dev/null 2>&1"
sudo -u $APP_USER bash -c "source venv/bin/activate && pip install -r requirements.txt > /dev/null 2>&1"

# Install psycopg2 if PostgreSQL is installed
if command -v psql &> /dev/null; then
    sudo -u $APP_USER bash -c "source venv/bin/activate && pip install psycopg2-binary > /dev/null 2>&1"
fi

# Check if .env exists, if not create it
if [ ! -f "$APP_DIR/backend/.env" ]; then
    cat > $APP_DIR/backend/.env << 'EOF'
DATABASE_URL=sqlite:///./terminology.db
DB_NAME=terminology_db
CORS_ORIGINS=*
EOF
    chown $APP_USER:$APP_USER $APP_DIR/backend/.env
fi

# Initialize database
echo "Initializing database with medical data..."
sudo -u $APP_USER bash -c "cd $APP_DIR/backend && source venv/bin/activate && python seed_data_medical.py"

echo -e "${GREEN}✓ Backend setup complete${NC}"

#############################################
# 9. Setup Frontend
#############################################
echo -e "${YELLOW}[9/10] Setting up frontend...${NC}"

cd $APP_DIR/frontend

# Check if .env exists
if [ ! -f "$APP_DIR/frontend/.env" ]; then
    cat > $APP_DIR/frontend/.env << 'EOF'
REACT_APP_BACKEND_URL=http://localhost:8001
EOF
    chown $APP_USER:$APP_USER $APP_DIR/frontend/.env
fi

# Install dependencies
echo "Installing frontend dependencies (this may take a few minutes)..."
sudo -u $APP_USER yarn install > /dev/null 2>&1

echo -e "${GREEN}✓ Frontend setup complete${NC}"

#############################################
# 10. Configure Services
#############################################
echo -e "${YELLOW}[10/10] Configuring services...${NC}"

# Supervisor configuration for backend
cat > /etc/supervisor/conf.d/fhir-backend.conf << EOF
[program:fhir-backend]
command=$APP_DIR/backend/venv/bin/uvicorn server:app --host 0.0.0.0 --port $BACKEND_PORT --workers 2
directory=$APP_DIR/backend
user=$APP_USER
autostart=true
autorestart=true
stderr_logfile=/var/log/supervisor/fhir-backend.err.log
stdout_logfile=/var/log/supervisor/fhir-backend.out.log
environment=PATH="$APP_DIR/backend/venv/bin"
stdout_logfile_maxbytes=50MB
stdout_logfile_backups=10
stderr_logfile_maxbytes=50MB
stderr_logfile_backups=10
EOF

# Supervisor configuration for frontend
cat > /etc/supervisor/conf.d/fhir-frontend.conf << EOF
[program:fhir-frontend]
command=/usr/bin/yarn start
directory=$APP_DIR/frontend
user=$APP_USER
autostart=true
autorestart=true
stderr_logfile=/var/log/supervisor/fhir-frontend.err.log
stdout_logfile=/var/log/supervisor/fhir-frontend.out.log
environment=PORT="$FRONTEND_PORT"
stdout_logfile_maxbytes=50MB
stdout_logfile_backups=10
stderr_logfile_maxbytes=50MB
stderr_logfile_backups=10
EOF

# Reload supervisor
supervisorctl reread
supervisorctl update

# Wait for services to start
sleep 3

# Nginx configuration
cat > /etc/nginx/sites-available/fhir-terminology << 'EOF'
server {
    listen 80;
    server_name _;

    access_log /var/log/nginx/fhir-access.log;
    error_log /var/log/nginx/fhir-error.log;

    # Frontend
    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }

    # Backend API
    location /api/ {
        proxy_pass http://localhost:8001/api/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EOF

# Enable site
ln -sf /etc/nginx/sites-available/fhir-terminology /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# Test and reload Nginx
nginx -t
systemctl reload nginx

# Configure firewall
if command -v ufw &> /dev/null; then
    ufw allow 'Nginx Full' > /dev/null 2>&1
    ufw allow OpenSSH > /dev/null 2>&1
fi

echo -e "${GREEN}✓ Services configured${NC}"

#############################################
# Final Status Check
#############################################
echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}Installation Complete!${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Get server IP
SERVER_IP=$(hostname -I | awk '{print $1}')

echo -e "${BLUE}📍 Installation Details:${NC}"
echo "   Application Directory: $APP_DIR"
echo "   Application User: $APP_USER"
echo "   Backend Port: $BACKEND_PORT"
echo "   Frontend Port: $FRONTEND_PORT"
echo ""

echo -e "${BLUE}🌐 Access URLs:${NC}"
echo "   Application: http://$SERVER_IP"
echo "   Backend API: http://$SERVER_IP/api/"
echo ""

echo -e "${BLUE}📊 Service Status:${NC}"
supervisorctl status

echo ""
echo -e "${BLUE}📝 Useful Commands:${NC}"
echo "   Check services: sudo supervisorctl status"
echo "   Restart backend: sudo supervisorctl restart fhir-backend"
echo "   Restart frontend: sudo supervisorctl restart fhir-frontend"
echo "   View logs: sudo tail -f /var/log/supervisor/fhir-*.log"
echo "   Nginx logs: sudo tail -f /var/log/nginx/fhir-*.log"
echo ""

echo -e "${BLUE}📚 Documentation:${NC}"
echo "   Full guide: $APP_DIR/INSTALLATION_UBUNTU.md"
echo "   PostgreSQL: $APP_DIR/backend/README_POSTGRESQL.md"
echo "   Project README: $APP_DIR/README.md"
echo ""

echo -e "${YELLOW}⚠️  Important Notes:${NC}"
echo "   1. Default database is SQLite (in $APP_DIR/backend/terminology.db)"
echo "   2. For PostgreSQL, run: sudo $APP_DIR/backend/database/setup_ubuntu.sh"
echo "   3. Update frontend .env with your domain for production"
echo "   4. Configure SSL with: sudo certbot --nginx -d yourdomain.com"
echo ""

echo -e "${GREEN}✅ You can now access the application at: http://$SERVER_IP${NC}"
echo ""
