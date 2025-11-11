# Quick Reference - Ubuntu 24 + Docker + PostgreSQL Esterno

## 🎯 Setup Veloce (3 minuti)

```bash
# 1. Trova IP gateway Docker (su Ubuntu)
docker network inspect bridge | grep Gateway
# Output: "Gateway": "172.17.0.1"

# 2. Configura .env
cp .env.docker.example .env
nano .env
# Imposta: DATABASE_URL=postgresql://user:pass@172.17.0.1:5432/dbname

# 3. Test database
./test-db-connection.sh

# 4. Deploy
./deploy.sh
# Opzione 1: Build e primo avvio
```

---

## 🔍 Comandi Debug Rapidi

### Test Connessione Database

```bash
# Da host
psql -h 172.17.0.1 -U postgres -d fhir_terminology

# Da Docker
docker run --rm postgres:15-alpine psql \
  "postgresql://user:pass@172.17.0.1:5432/dbname" \
  -c "SELECT version();"

# Dal backend container
docker-compose exec backend psql $DATABASE_URL -c "SELECT version();"
```

### Fix PostgreSQL per Connessioni Esterne

```bash
# 1. Modifica configurazione
sudo nano /etc/postgresql/15/main/postgresql.conf
# Aggiungi: listen_addresses = '*'

sudo nano /etc/postgresql/15/main/pg_hba.conf
# Aggiungi: host all all 172.17.0.0/16 md5

# 2. Riavvia
sudo systemctl restart postgresql

# 3. Verifica
sudo netstat -tlnp | grep 5432
# Deve mostrare: 0.0.0.0:5432

# 4. Firewall
sudo ufw allow from 172.17.0.0/16 to any port 5432
```

### Trova IP Docker su Linux

```bash
# Metodo 1
ip addr show docker0 | grep inet

# Metodo 2
docker network inspect bridge | grep Gateway

# Metodo 3
ip route | grep docker0
```

---

## 🐳 Docker Compose - Comandi Essenziali

```bash
# Build
docker-compose build --no-cache

# Avvio
docker-compose up -d

# Stop
docker-compose stop

# Logs
docker-compose logs -f backend

# Stato
docker-compose ps

# Restart singolo servizio
docker-compose restart backend

# Entra in container
docker-compose exec backend bash

# Rimozione completa
docker-compose down -v
```

---

## 🔧 Risoluzione Problemi Veloci

### Errore: "Connection refused"
```bash
# Verifica PostgreSQL
sudo systemctl status postgresql

# Verifica porta
sudo netstat -tlnp | grep 5432

# Test connessione
nc -zv 172.17.0.1 5432
```

### Errore: "Password authentication failed"
```bash
# Connetti come postgres
sudo -u postgres psql

# Crea/aggiorna utente
ALTER USER postgres WITH PASSWORD 'newpassword';
GRANT ALL PRIVILEGES ON DATABASE fhir_terminology TO postgres;
```

### Backend non si avvia
```bash
# Verifica variabili
docker-compose exec backend env | grep DATABASE

# Test database dal container
docker-compose exec backend bash
psql $DATABASE_URL -c "SELECT 1"
```

### Node version error (Ubuntu 24)
```bash
# Il Dockerfile ora usa Node 20 (compatibile Ubuntu 24)
# Se problemi, rebuild:
docker-compose build frontend --no-cache
```

---

## 📋 Checklist Pre-Deploy

```bash
# 1. PostgreSQL configurato
sudo grep listen_addresses /etc/postgresql/15/main/postgresql.conf
# Output atteso: listen_addresses = '*'

# 2. Firewall aperto
sudo ufw status | grep 5432

# 3. Test connessione
./test-db-connection.sh

# 4. .env configurato
cat .env | grep DATABASE_URL

# 5. Docker funziona
docker run hello-world

# 6. Deploy
./deploy.sh
```

---

## 🎓 3 Scenari Comuni

### Scenario 1: PostgreSQL su stessa macchina (Ubuntu)
```env
DATABASE_URL=postgresql://postgres:pass@172.17.0.1:5432/fhir_terminology
```

### Scenario 2: PostgreSQL su server remoto
```env
DATABASE_URL=postgresql://postgres:pass@192.168.1.100:5432/fhir_terminology
```

### Scenario 3: Usa network host (solo Linux)
```yaml
# docker-compose.yml
services:
  backend:
    network_mode: "host"
    environment:
      - DATABASE_URL=postgresql://postgres:pass@localhost:5432/fhir_terminology
```

---

## 📞 Script Utili

```bash
# Test Docker setup
./test-docker.sh

# Test database connection
./test-db-connection.sh

# Deploy interattivo
./deploy.sh

# Logs real-time
docker-compose logs -f --tail=50

# Health check
docker-compose ps
curl http://localhost:8001/api/
```

---

## 🔐 Sicurezza Produzione

```bash
# Genera secret key sicura
python3 -c "import secrets; print(secrets.token_urlsafe(32))"

# Usa in .env
SECRET_KEY=<generated-key>

# SSL per PostgreSQL
DATABASE_URL=postgresql://user:pass@host:5432/db?sslmode=require

# Limita CORS
CORS_ORIGINS=https://your-domain.com
```

---

## 📚 Documentazione Completa

- **Setup completo:** `UBUNTU24_POSTGRES_SETUP.md`
- **Troubleshooting:** `DOCKER_TROUBLESHOOTING.md`
- **Deployment:** `DEPLOYMENT.md`
- **API Docs:** `FHIR_API_DOCUMENTATION.md`
