# Docker Build - Risoluzione Problemi Comuni

## 🐛 Errori Comuni e Soluzioni

### 1. Errore: "COPY package.json yarn.lock ./ failed"

**Problema:** File yarn.lock o package-lock.json non trovato

**Soluzione:**
```bash
# Verifica quale file esiste
ls -la frontend/ | grep lock

# Se hai yarn.lock
cd frontend && yarn install

# Se hai package-lock.json
cd frontend && npm install

# Poi prova il build
docker-compose build frontend
```

**Fix automatico:** Il nuovo Dockerfile supporta entrambi i package manager

---

### 2. Errore: "requirements.txt not found"

**Problema:** File requirements.txt mancante o non nel context

**Soluzione:**
```bash
# Verifica il file
ls -la backend/requirements.txt

# Se manca, generalo
cd backend
pip freeze > requirements.txt

# Build
docker-compose build backend
```

---

### 3. Errore: "failed to solve with frontend Dockerfile"

**Problema:** Build context o Dockerfile errato

**Soluzione:**
```bash
# Test build isolato
cd frontend
docker build -t test-frontend .

# Se fallisce, controlla il Dockerfile
cat Dockerfile

# Verifica file necessari
ls -la | grep -E "package|Dockerfile"
```

---

### 4. Errore: "Cannot connect to database"

**Problema:** DATABASE_URL non configurato o database non raggiungibile

**Soluzione:**
```bash
# 1. Verifica .env
cat .env | grep DATABASE_URL

# 2. Test connessione database
docker-compose exec backend psql $DATABASE_URL -c "SELECT version();"

# 3. Se usi host.docker.internal (Linux)
# Usa l'IP del bridge Docker
ip addr show docker0
# Esempio: 172.17.0.1

# Aggiorna .env
DATABASE_URL=postgresql://user:pass@172.17.0.1:5432/dbname
```

---

### 5. Errore: "port is already allocated"

**Problema:** Porta già in uso

**Soluzione:**
```bash
# Trova processo sulla porta
sudo lsof -i :8001
sudo lsof -i :3000

# Uccidi processo
kill -9 <PID>

# O cambia porta in docker-compose.yml
ports:
  - "8080:8001"  # Usa 8080 invece di 8001
```

---

### 6. Errore: "permission denied" durante build

**Problema:** Permessi insufficienti

**Soluzione:**
```bash
# Aggiungi utente a gruppo docker
sudo usermod -aG docker $USER

# Rilogga o
newgrp docker

# Verifica
docker run hello-world
```

---

### 7. Frontend build fallisce con errore memoria

**Problema:** Memoria insufficiente durante build Node

**Soluzione:**
```bash
# Aumenta memoria Docker (Docker Desktop)
# Settings -> Resources -> Memory: 4GB+

# O usa build con limite memoria
docker-compose build --memory 2g frontend
```

---

### 8. Backend health check fallisce

**Problema:** Backend non risponde su /api/

**Soluzione:**
```bash
# Controlla logs
docker-compose logs backend

# Test manuale endpoint
docker-compose exec backend curl http://localhost:8001/api/

# Disabilita health check temporaneamente
# Commenta nel docker-compose.yml:
# healthcheck:
#   test: [...]
```

---

### 9. Errore: "network not found"

**Problema:** Network Docker non creato

**Soluzione:**
```bash
# Ricrea network
docker-compose down
docker-compose up -d

# O manualmente
docker network create fhir-terminology-network
```

---

### 10. Cache problema durante rebuild

**Problema:** Build usa cache vecchia

**Soluzione:**
```bash
# Build completo senza cache
docker-compose build --no-cache

# Rimuovi immagini vecchie
docker image prune -a

# Rebuild completo
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

---

## 🔍 Comandi Debug Utili

```bash
# Verifica configurazione
docker-compose config

# Logs dettagliati durante build
docker-compose build --progress=plain

# Entra in container per debug
docker-compose run --rm backend bash
docker-compose run --rm frontend sh

# Verifica immagini create
docker images | grep fhir

# Verifica container running
docker-compose ps

# Logs con timestamp
docker-compose logs --timestamps

# Segui logs in real-time
docker-compose logs -f --tail=100

# Resource usage
docker stats

# Ispeziona container
docker inspect fhir-terminology-backend

# Verifica network
docker network ls
docker network inspect fhir-terminology-network
```

---

## 🛠️ Workflow Completo di Test

```bash
# 1. Pulizia completa
docker-compose down -v
docker system prune -a --volumes

# 2. Verifica file
./test-docker.sh

# 3. Build pulito
docker-compose build --no-cache

# 4. Avvio
docker-compose up -d

# 5. Verifica
docker-compose ps
docker-compose logs -f

# 6. Test endpoint
curl http://localhost:8001/api/
curl http://localhost:3000
```

---

## 📞 Supporto

Se il problema persiste:

1. Controlla logs completi: `docker-compose logs --tail=200`
2. Verifica versioni: `docker version && docker-compose version`
3. Controlla spazio disco: `df -h`
4. Verifica memoria: `free -h`
5. Consulta [DEPLOYMENT.md](./DEPLOYMENT.md)
