# Guida Installazione FHIR Terminology Service su Ubuntu

Guida completa per installare e configurare il FHIR Terminology Service su Ubuntu Server/Desktop.

## 📋 Indice

- [Requisiti](#requisiti)
- [Installazione Base](#installazione-base)
- [Installazione Backend](#installazione-backend)
- [Installazione Frontend](#installazione-frontend)
- [Installazione PostgreSQL](#installazione-postgresql)
- [Configurazione Supervisor](#configurazione-supervisor)
- [Configurazione Nginx](#configurazione-nginx)
- [Avvio Applicazione](#avvio-applicazione)
- [Verifica Installazione](#verifica-installazione)
- [Troubleshooting](#troubleshooting)

---

## Requisiti

### Sistema Operativo
- **Ubuntu 20.04 LTS** o superiore (consigliato 22.04 LTS)
- Minimo 2GB RAM (consigliato 4GB)
- 10GB spazio disco
- Accesso root/sudo

### Software Necessario
- Python 3.8+
- Node.js 16+
- PostgreSQL 12+ (opzionale, può usare SQLite)
- Nginx (per produzione)
- Supervisor (per gestione processi)

---

## Installazione Base

### 1. Aggiornamento Sistema

```bash
sudo apt update
sudo apt upgrade -y
```

### 2. Installazione Strumenti Base

```bash
sudo apt install -y \
    build-essential \
    git \
    curl \
    wget \
    vim \
    software-properties-common \
    apt-transport-https \
    ca-certificates \
    gnupg \
    lsb-release
```

### 3. Creazione Utente Applicazione (Opzionale)

```bash
# Crea utente dedicato
sudo useradd -m -s /bin/bash fhir
sudo usermod -aG sudo fhir

# Passa all'utente
sudo su - fhir
```

---

## Installazione Backend

### 1. Installazione Python 3

```bash
# Verifica versione Python
python3 --version

# Installa Python e pip se necessario
sudo apt install -y python3 python3-pip python3-venv

# Verifica installazione
python3 --version
pip3 --version
```

### 2. Setup Directory Progetto

```bash
# Crea directory applicazione
sudo mkdir -p /opt/fhir-terminology
sudo chown -R $USER:$USER /opt/fhir-terminology
cd /opt/fhir-terminology

# Crea struttura
mkdir -p backend frontend
```

### 3. Copia File Backend

Se hai i file dal progetto Emergent:

```bash
# Copia file backend
cp -r /path/to/backend/* /opt/fhir-terminology/backend/

# Oppure clona da repository
# git clone <repository-url> /opt/fhir-terminology
```

### 4. Installazione Dipendenze Python

```bash
cd /opt/fhir-terminology/backend

# Crea virtual environment (consigliato)
python3 -m venv venv
source venv/bin/activate

# Installa dipendenze
pip install --upgrade pip
pip install -r requirements.txt

# Se non hai requirements.txt, installa manualmente:
pip install fastapi uvicorn sqlalchemy psycopg2-binary python-dotenv pydantic
```

### 5. Configurazione Backend

```bash
# Crea file .env
cat > /opt/fhir-terminology/backend/.env << 'EOF'
# Database Configuration
DATABASE_URL=sqlite:///./terminology.db
# Per PostgreSQL usa:
# DATABASE_URL=postgresql://fhir_user:password@localhost:5432/fhir_terminology

DB_NAME=terminology_db
CORS_ORIGINS=*
EOF
```

### 6. Inizializzazione Database

```bash
cd /opt/fhir-terminology/backend

# Crea database e popola con dati
python seed_data_medical.py

# Verifica
python -c "from database import SessionLocal, CodeSystemModel; db = SessionLocal(); print(f'CodeSystems: {db.query(CodeSystemModel).count()}'); db.close()"
```

---

## Installazione Frontend

### 1. Installazione Node.js e Yarn

```bash
# Installa Node.js 18.x (LTS)
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs

# Verifica installazione
node --version
npm --version

# Installa Yarn
sudo npm install -g yarn
yarn --version
```

### 2. Setup Frontend

```bash
cd /opt/fhir-terminology/frontend

# Copia file frontend (se non già fatto)
# cp -r /path/to/frontend/* .

# Installa dipendenze
yarn install
```

### 3. Configurazione Frontend

```bash
# Crea file .env per frontend
cat > /opt/fhir-terminology/frontend/.env << 'EOF'
# Backend URL (cambia con il tuo dominio in produzione)
REACT_APP_BACKEND_URL=http://localhost:8001
EOF
```

### 4. Build Frontend (Produzione)

```bash
cd /opt/fhir-terminology/frontend

# Build ottimizzato per produzione
yarn build

# I file saranno in: build/
```

---

## Installazione PostgreSQL

### 1. Installazione PostgreSQL

```bash
# Installa PostgreSQL
sudo apt install -y postgresql postgresql-contrib

# Avvia servizio
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Verifica
sudo systemctl status postgresql
```

### 2. Setup Automatico Database

```bash
# Usa lo script di setup automatico
cd /opt/fhir-terminology/backend
sudo chmod +x database/setup_ubuntu.sh
sudo ./database/setup_ubuntu.sh
```

**Lo script chiederà:**
- Nome database (default: `fhir_terminology`)
- Nome utente (default: `fhir_user`)
- Password
- Permettere connessioni remote (y/N)

### 3. Setup Manuale Database (Alternativa)

```bash
# Connetti come postgres
sudo -u postgres psql

# Esegui comandi SQL
CREATE USER fhir_user WITH PASSWORD 'your_secure_password';
CREATE DATABASE fhir_terminology OWNER fhir_user;
GRANT ALL PRIVILEGES ON DATABASE fhir_terminology TO fhir_user;
\q

# Inizializza schema
sudo -u postgres psql -d fhir_terminology -f /opt/fhir-terminology/backend/database/init_postgres.sql
```

### 4. Aggiorna Configurazione Backend

```bash
# Aggiorna .env con PostgreSQL
nano /opt/fhir-terminology/backend/.env

# Modifica DATABASE_URL
DATABASE_URL=postgresql://fhir_user:your_password@localhost:5432/fhir_terminology
```

### 5. Installa Driver PostgreSQL Python

```bash
cd /opt/fhir-terminology/backend
source venv/bin/activate
pip install psycopg2-binary
```

### 6. Popola Database

```bash
cd /opt/fhir-terminology/backend
python seed_data_medical.py
```

---

## Configurazione Supervisor

Supervisor gestisce i processi backend e frontend come servizi.

### 1. Installazione Supervisor

```bash
sudo apt install -y supervisor

# Avvia servizio
sudo systemctl start supervisor
sudo systemctl enable supervisor
```

### 2. Configurazione Backend Service

```bash
sudo nano /etc/supervisor/conf.d/fhir-backend.conf
```

Contenuto:

```ini
[program:fhir-backend]
command=/opt/fhir-terminology/backend/venv/bin/uvicorn server:app --host 0.0.0.0 --port 8001 --workers 2
directory=/opt/fhir-terminology/backend
user=fhir
autostart=true
autorestart=true
stderr_logfile=/var/log/supervisor/fhir-backend.err.log
stdout_logfile=/var/log/supervisor/fhir-backend.out.log
environment=PATH="/opt/fhir-terminology/backend/venv/bin"

[program:fhir-frontend]
command=/usr/bin/yarn start
directory=/opt/fhir-terminology/frontend
user=fhir
autostart=true
autorestart=true
stderr_logfile=/var/log/supervisor/fhir-frontend.err.log
stdout_logfile=/var/log/supervisor/fhir-frontend.out.log
```

### 3. Reload e Avvio Servizi

```bash
# Ricarica configurazione
sudo supervisorctl reread
sudo supervisorctl update

# Avvia servizi
sudo supervisorctl start fhir-backend
sudo supervisorctl start fhir-frontend

# Verifica stato
sudo supervisorctl status
```

---

## Configurazione Nginx

Nginx serve come reverse proxy e server per file statici.

### 1. Installazione Nginx

```bash
sudo apt install -y nginx

# Avvia servizio
sudo systemctl start nginx
sudo systemctl enable nginx
```

### 2. Configurazione Site

```bash
sudo nano /etc/nginx/sites-available/fhir-terminology
```

Contenuto:

```nginx
server {
    listen 80;
    server_name your-domain.com;  # Cambia con il tuo dominio o IP

    # Logs
    access_log /var/log/nginx/fhir-access.log;
    error_log /var/log/nginx/fhir-error.log;

    # Frontend (React Build)
    location / {
        root /opt/fhir-terminology/frontend/build;
        try_files $uri $uri/ /index.html;
    }

    # Backend API
    location /api/ {
        proxy_pass http://localhost:8001/api/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # WebSocket support (se necessario)
    location /ws {
        proxy_pass http://localhost:8001;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

### 3. Attivazione Site

```bash
# Crea symlink
sudo ln -s /etc/nginx/sites-available/fhir-terminology /etc/nginx/sites-enabled/

# Test configurazione
sudo nginx -t

# Reload Nginx
sudo systemctl reload nginx
```

### 4. Firewall (UFW)

```bash
# Abilita firewall
sudo ufw allow 'Nginx Full'
sudo ufw allow OpenSSH
sudo ufw enable

# Verifica
sudo ufw status
```

---

## Configurazione SSL (Opzionale ma Consigliato)

### Usando Let's Encrypt (Certbot)

```bash
# Installa Certbot
sudo apt install -y certbot python3-certbot-nginx

# Ottieni certificato SSL
sudo certbot --nginx -d your-domain.com

# Auto-rinnovo (già configurato)
sudo systemctl status certbot.timer
```

---

## Avvio Applicazione

### 1. Avvio Completo

```bash
# Avvia tutti i servizi
sudo supervisorctl start all

# Verifica stato
sudo supervisorctl status

# Dovrebbe mostrare:
# fhir-backend    RUNNING
# fhir-frontend   RUNNING
```

### 2. Restart Servizi

```bash
# Restart backend
sudo supervisorctl restart fhir-backend

# Restart frontend
sudo supervisorctl restart fhir-frontend

# Restart Nginx
sudo systemctl restart nginx
```

### 3. Logs

```bash
# Backend logs
sudo tail -f /var/log/supervisor/fhir-backend.out.log
sudo tail -f /var/log/supervisor/fhir-backend.err.log

# Frontend logs
sudo tail -f /var/log/supervisor/fhir-frontend.out.log

# Nginx logs
sudo tail -f /var/log/nginx/fhir-access.log
sudo tail -f /var/log/nginx/fhir-error.log
```

---

## Verifica Installazione

### 1. Test Backend API

```bash
# Health check
curl http://localhost:8001/api/

# Lista CodeSystems
curl http://localhost:8001/api/CodeSystem

# Test con jq per output formattato
curl -s http://localhost:8001/api/CodeSystem | jq '.[0]'
```

### 2. Test Frontend

```bash
# Apri browser
http://your-server-ip
# oppure
http://your-domain.com
```

### 3. Test Database

```bash
# PostgreSQL
psql -U fhir_user -d fhir_terminology -c "SELECT COUNT(*) FROM code_systems;"

# SQLite
cd /opt/fhir-terminology/backend
python -c "from database import SessionLocal, CodeSystemModel; db = SessionLocal(); print(f'Total: {db.query(CodeSystemModel).count()}'); db.close()"
```

### 4. Test Operazioni FHIR

```bash
# $lookup
curl "http://localhost:8001/api/CodeSystem/\$lookup?system=http://snomed.info/sct&code=73211009"

# $expand
curl "http://localhost:8001/api/ValueSet/\$expand?url=http://example.org/fhir/ValueSet/diabetes-codes"
```

---

## Troubleshooting

### Backend non si avvia

```bash
# Controlla logs
sudo tail -50 /var/log/supervisor/fhir-backend.err.log

# Verifica dipendenze Python
cd /opt/fhir-terminology/backend
source venv/bin/activate
pip list

# Test manuale
python -c "import fastapi; import uvicorn; print('OK')"

# Test avvio manuale
cd /opt/fhir-terminology/backend
source venv/bin/activate
uvicorn server:app --host 0.0.0.0 --port 8001
```

### Frontend non si avvia

```bash
# Controlla logs
sudo tail -50 /var/log/supervisor/fhir-frontend.err.log

# Verifica Node.js
node --version
yarn --version

# Reinstalla dipendenze
cd /opt/fhir-terminology/frontend
rm -rf node_modules
yarn install

# Test avvio manuale
yarn start
```

### Database connection error

```bash
# PostgreSQL - verifica servizio
sudo systemctl status postgresql

# Test connessione
psql -U fhir_user -d fhir_terminology

# Verifica .env
cat /opt/fhir-terminology/backend/.env

# Test connessione Python
cd /opt/fhir-terminology/backend
python -c "from database import SessionLocal; db = SessionLocal(); print('Connected OK'); db.close()"
```

### Nginx 502 Bad Gateway

```bash
# Verifica backend sia attivo
sudo supervisorctl status fhir-backend

# Verifica porta backend
sudo netstat -tlnp | grep 8001

# Test connessione diretta
curl http://localhost:8001/api/

# Controlla logs Nginx
sudo tail -50 /var/log/nginx/fhir-error.log
```

### Permessi File

```bash
# Fix ownership
sudo chown -R fhir:fhir /opt/fhir-terminology

# Fix permissions
sudo chmod -R 755 /opt/fhir-terminology
sudo chmod 644 /opt/fhir-terminology/backend/.env
```

### Porte già in uso

```bash
# Controlla chi usa porta 8001
sudo lsof -i :8001
sudo netstat -tlnp | grep 8001

# Kill processo se necessario
sudo kill <PID>

# Controlla porta 3000 (frontend)
sudo lsof -i :3000
```

---

## Manutenzione

### Backup Database

```bash
# PostgreSQL
pg_dump -U fhir_user fhir_terminology > backup_$(date +%Y%m%d).sql

# SQLite
cp /opt/fhir-terminology/backend/terminology.db \
   /backup/terminology_$(date +%Y%m%d).db
```

### Update Applicazione

```bash
# Stop servizi
sudo supervisorctl stop all

# Update codice
cd /opt/fhir-terminology
git pull  # se usi git

# Update dipendenze backend
cd backend
source venv/bin/activate
pip install -r requirements.txt

# Update dipendenze frontend
cd ../frontend
yarn install

# Rebuild frontend
yarn build

# Restart servizi
sudo supervisorctl start all
```

### Log Rotation

Supervisor gestisce automaticamente la rotazione dei log, ma puoi configurare:

```bash
sudo nano /etc/supervisor/conf.d/fhir-backend.conf
```

Aggiungi:
```ini
stdout_logfile_maxbytes=50MB
stdout_logfile_backups=10
stderr_logfile_maxbytes=50MB
stderr_logfile_backups=10
```

---

## Performance Tuning

### PostgreSQL

```bash
# Modifica configurazione
sudo nano /etc/postgresql/14/main/postgresql.conf

# Impostazioni consigliate per server con 4GB RAM
shared_buffers = 1GB
effective_cache_size = 3GB
work_mem = 16MB
maintenance_work_mem = 256MB
```

### Nginx

```bash
sudo nano /etc/nginx/nginx.conf
```

Aggiungi:
```nginx
worker_processes auto;
worker_connections 1024;

# Gzip compression
gzip on;
gzip_vary on;
gzip_types text/plain text/css application/json application/javascript;
```

### Uvicorn Workers

```bash
# Modifica supervisor config
sudo nano /etc/supervisor/conf.d/fhir-backend.conf

# Aumenta workers (1 per CPU core)
command=/opt/fhir-terminology/backend/venv/bin/uvicorn server:app --host 0.0.0.0 --port 8001 --workers 4
```

---

## Monitoring

### Setup Monitoring Base

```bash
# Installa htop per monitoring sistema
sudo apt install -y htop

# Monitor processi
htop

# Monitor servizi
watch -n 2 'sudo supervisorctl status'
```

### Log Aggregation

```bash
# Tutti i log in un comando
tail -f /var/log/supervisor/fhir-*.log /var/log/nginx/fhir-*.log
```

---

## Sicurezza

### Best Practices

1. **Non usare utente root** per eseguire l'applicazione
2. **Usa HTTPS** in produzione (Let's Encrypt)
3. **Firewall** configurato correttamente
4. **Password forti** per database
5. **Backup regolari** automatizzati
6. **Update sistema** regolari

### Hardening Base

```bash
# Disabilita root login SSH
sudo nano /etc/ssh/sshd_config
# PermitRootLogin no

# Configura fail2ban
sudo apt install -y fail2ban
sudo systemctl enable fail2ban

# Aggiorna sistema regolarmente
sudo apt update && sudo apt upgrade -y
```

---

## Checklist Post-Installazione

- [ ] Sistema aggiornato
- [ ] Python 3.8+ installato
- [ ] Node.js 16+ installato
- [ ] PostgreSQL configurato (o SQLite funzionante)
- [ ] Backend dependencies installate
- [ ] Frontend dependencies installate
- [ ] Database popolato con dati
- [ ] Supervisor configurato
- [ ] Backend avviato (porta 8001)
- [ ] Frontend avviato (porta 3000)
- [ ] Nginx configurato
- [ ] Firewall configurato
- [ ] SSL configurato (se in produzione)
- [ ] Backup automatici configurati
- [ ] Log rotation configurata
- [ ] Monitoring attivo

---

## Risorse Utili

- **Documentazione PostgreSQL**: `/opt/fhir-terminology/backend/README_POSTGRESQL.md`
- **Quick Commands**: `bash /opt/fhir-terminology/backend/database/postgres_commands.sh`
- **FHIR Specification**: https://build.fhir.org/terminology-service.html
- **FastAPI Docs**: https://fastapi.tiangolo.com/
- **React Docs**: https://react.dev/

---

## Supporto

Per problemi o domande:

1. Controlla i log: `/var/log/supervisor/` e `/var/log/nginx/`
2. Verifica stato servizi: `sudo supervisorctl status`
3. Test API: `curl http://localhost:8001/api/`
4. Consulta sezione Troubleshooting

---

**Installazione completata! L'applicazione dovrebbe essere accessibile su http://your-server-ip** 🎉
