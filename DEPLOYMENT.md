# FHIR Terminology Service - Guida al Deployment con Docker

Questa guida spiega come deployare il FHIR Terminology Service utilizzando Docker e docker-compose con database PostgreSQL esterno.

## 📋 Prerequisiti

- Docker Engine 20.10 o superiore
- Docker Compose 2.0 o superiore
- Database PostgreSQL 12+ accessibile dalla rete
- Almeno 2GB RAM disponibile
- Almeno 5GB spazio disco

## 🗂️ Struttura del Progetto

```
fhir-terminology-service/
├── backend/
│   ├── Dockerfile
│   ├── .dockerignore
│   ├── requirements.txt
│   └── ... (codice backend)
├── frontend/
│   ├── Dockerfile
│   ├── .dockerignore
│   ├── nginx.conf
│   └── ... (codice frontend)
├── docker-compose.yml
├── .env.docker.example
└── DEPLOYMENT.md (questo file)
```

## 🚀 Quick Start

### 1. Preparazione Database PostgreSQL

Assicurati che il tuo database PostgreSQL esterno sia pronto:

```sql
-- Crea il database
CREATE DATABASE fhir_terminology;

-- Crea un utente (opzionale)
CREATE USER fhir_user WITH PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE fhir_terminology TO fhir_user;
```

### 2. Configurazione Variabili d'Ambiente

Copia il file di esempio e modifica le variabili:

```bash
cp .env.docker.example .env
```

Modifica `.env` con i tuoi valori:

```env
# Database esterno
DATABASE_URL=postgresql://fhir_user:secure_password@192.168.1.100:5432/fhir_terminology

# Security
SECRET_KEY=your-very-secret-key-minimum-32-characters-long

# CORS (aggiungi i tuoi domini)
CORS_ORIGINS=http://localhost:3000,https://your-domain.com

# Backend URL (accessibile dal browser)
REACT_APP_BACKEND_URL=http://your-server:8001
```

### 3. Build e Avvio

```bash
# Build delle immagini
docker-compose build

# Avvio dei container
docker-compose up -d

# Verifica lo stato
docker-compose ps
```

### 4. Inizializzazione Database

Prima del primo utilizzo, esegui le migrazioni:

```bash
# Entra nel container backend
docker-compose exec backend bash

# Esegui lo script di inizializzazione (se presente)
python database/run_migration.py

# Crea utente admin
python create_admin.py

# Esci dal container
exit
```

### 5. Verifica Installazione

Accedi ai servizi:
- Frontend: `http://localhost:3000`
- Backend API: `http://localhost:8001/api`
- CapabilityStatement: `http://localhost:8001/api/metadata`

## 🔧 Configurazione Avanzata

### Connessione a Database su Host Diverso

Se il PostgreSQL è su un altro server:

```env
# .env
DATABASE_URL=postgresql://user:password@db.example.com:5432/fhir_terminology
```

### Connessione a PostgreSQL su Host Locale

Per connettersi al PostgreSQL sulla macchina host:

**Linux/Mac:**
```env
DATABASE_URL=postgresql://user:password@host.docker.internal:5432/fhir_terminology
```

**Windows:**
Usa `host.docker.internal` (già incluso nell'esempio)

**Linux (alternativa):**
Trova l'IP del bridge Docker:
```bash
ip addr show docker0
# Usa l'IP mostrato (es. 172.17.0.1)
DATABASE_URL=postgresql://user:password@172.17.0.1:5432/fhir_terminology
```

### Configurazione PostgreSQL per Accesso Docker

Modifica `postgresql.conf`:
```
listen_addresses = '*'  # o 'localhost,172.17.0.1'
```

Modifica `pg_hba.conf`:
```
# Docker network
host    all             all             172.17.0.0/16           md5
# o per host.docker.internal
host    all             all             0.0.0.0/0               md5
```

Riavvia PostgreSQL:
```bash
sudo systemctl restart postgresql
```

### Personalizzazione Porte

Modifica `docker-compose.yml`:

```yaml
services:
  backend:
    ports:
      - "8080:8001"  # Esponi su porta 8080
  
  frontend:
    ports:
      - "80:3000"    # Esponi su porta 80
```

Aggiorna anche `REACT_APP_BACKEND_URL` nel `.env`:
```env
REACT_APP_BACKEND_URL=http://your-server:8080
```

### Produzione con HTTPS/SSL

Per produzione con SSL, usa un reverse proxy (nginx/traefik):

**Esempio con nginx reverse proxy:**

```nginx
server {
    listen 443 ssl http2;
    server_name your-domain.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    # Frontend
    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # Backend API
    location /api {
        proxy_pass http://localhost:8001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

Aggiorna `.env`:
```env
REACT_APP_BACKEND_URL=https://your-domain.com
CORS_ORIGINS=https://your-domain.com
```

## 📊 Gestione Container

### Comandi Utili

```bash
# Avvio
docker-compose up -d

# Stop
docker-compose stop

# Restart
docker-compose restart

# Logs
docker-compose logs -f
docker-compose logs -f backend
docker-compose logs -f frontend

# Stato
docker-compose ps

# Rimozione completa
docker-compose down
docker-compose down -v  # Rimuove anche i volumi

# Rebuild dopo modifiche
docker-compose build --no-cache
docker-compose up -d --force-recreate
```

### Health Check

Verifica lo stato di salute dei servizi:

```bash
docker-compose ps

# Output atteso:
# NAME                          STATUS              PORTS
# fhir-terminology-backend      Up (healthy)        0.0.0.0:8001->8001/tcp
# fhir-terminology-frontend     Up (healthy)        0.0.0.0:3000->3000/tcp
```

### Backup e Restore

**Backup Database:**
```bash
# Usando pg_dump dal container
docker-compose exec backend pg_dump -h host.docker.internal -U postgres -d fhir_terminology > backup.sql

# O direttamente dal server PostgreSQL
pg_dump -U postgres fhir_terminology > backup.sql
```

**Restore Database:**
```bash
psql -U postgres fhir_terminology < backup.sql
```

## 🐛 Troubleshooting

### Backend non si connette al database

1. Verifica che PostgreSQL accetti connessioni remote:
   ```bash
   # Testa la connessione
   docker-compose exec backend psql $DATABASE_URL -c "SELECT version();"
   ```

2. Controlla i log:
   ```bash
   docker-compose logs backend
   ```

3. Verifica configurazione firewall:
   ```bash
   # Porta PostgreSQL deve essere aperta
   sudo ufw allow 5432/tcp
   ```

### Frontend non carica

1. Verifica variabile REACT_APP_BACKEND_URL:
   ```bash
   # Ricostruisci con nuova variabile
   docker-compose build frontend --no-cache
   docker-compose up -d frontend
   ```

2. Controlla logs nginx:
   ```bash
   docker-compose logs frontend
   ```

### Errori di permessi

```bash
# Fix permessi su volumi
docker-compose down
sudo chown -R 1000:1000 backend-logs/
docker-compose up -d
```

### Container esce immediatamente

```bash
# Controlla logs per errori
docker-compose logs --tail=100

# Controlla health check
docker inspect fhir-terminology-backend | grep -A 10 Health
```

## 🔒 Sicurezza

### Best Practices per Produzione

1. **Cambia SECRET_KEY**:
   Genera una chiave sicura:
   ```bash
   python -c "import secrets; print(secrets.token_urlsafe(32))"
   ```

2. **Limita CORS_ORIGINS**:
   ```env
   CORS_ORIGINS=https://your-domain.com
   ```

3. **Usa HTTPS**:
   Implementa SSL/TLS con reverse proxy

4. **Firewall**:
   Esponi solo le porte necessarie

5. **Aggiorna regolarmente**:
   ```bash
   docker-compose pull
   docker-compose up -d
   ```

6. **Backup automatici**:
   Configura backup schedulati del database

7. **Monitoring**:
   Implementa monitoraggio con strumenti come Prometheus/Grafana

## 📈 Scaling e Performance

### Aumenta risorse container

Modifica `docker-compose.yml`:

```yaml
services:
  backend:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
        reservations:
          cpus: '1'
          memory: 1G
```

### Load Balancing

Per alta disponibilità, usa docker swarm o kubernetes:

```bash
# Docker Swarm
docker swarm init
docker stack deploy -c docker-compose.yml fhir-stack
```

## 📝 Aggiornamenti

```bash
# Pull nuove immagini
git pull origin main

# Rebuild
docker-compose build

# Restart con nuova versione
docker-compose up -d

# Verifica
docker-compose ps
```

## 🆘 Supporto

Per problemi o domande:
- Controlla i logs: `docker-compose logs -f`
- Verifica configurazione: `docker-compose config`
- Consulta la documentazione FHIR: [FHIR_API_DOCUMENTATION.md](./FHIR_API_DOCUMENTATION.md)

## 📄 Licenza

Questo progetto è distribuito sotto licenza [specificare licenza]
