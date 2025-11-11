# Guida Setup per Ubuntu 24 con Database Esterno

## 🐧 Configurazione PostgreSQL per Connessioni Esterne

### 1. Configurazione PostgreSQL Server (sulla macchina con il database)

#### Trova i file di configurazione
```bash
# Trova la directory dati PostgreSQL
sudo -u postgres psql -c "SHOW config_file;"
sudo -u postgres psql -c "SHOW hba_file;"

# Di solito in:
# /etc/postgresql/15/main/postgresql.conf
# /etc/postgresql/15/main/pg_hba.conf
```

#### Modifica postgresql.conf
```bash
sudo nano /etc/postgresql/15/main/postgresql.conf

# Trova e modifica questa riga:
listen_addresses = '*'          # Ascolta su tutte le interfacce

# O specifica gli IP:
listen_addresses = 'localhost,192.168.1.100'
```

#### Modifica pg_hba.conf
```bash
sudo nano /etc/postgresql/15/main/pg_hba.conf

# Aggiungi alla fine (PRIMA di controllare le altre regole):

# Permetti connessioni dalla rete Docker
host    all             all             172.17.0.0/16           md5

# Permetti connessioni da tutta la rete locale (usa con cautela)
host    all             all             0.0.0.0/0               md5

# O solo da IP specifico
host    all             all             192.168.1.0/24          md5
```

#### Riavvia PostgreSQL
```bash
sudo systemctl restart postgresql
sudo systemctl status postgresql
```

#### Verifica porta aperta
```bash
# PostgreSQL deve ascoltare su tutte le interfacce
sudo netstat -tlnp | grep 5432
# Output atteso: 0.0.0.0:5432 o :::5432

# O con ss
sudo ss -tlnp | grep 5432
```

---

## 🔥 Configurazione Firewall Ubuntu 24

### UFW (Uncomplicated Firewall)

```bash
# Verifica stato
sudo ufw status

# Permetti PostgreSQL dalla rete locale
sudo ufw allow from 192.168.1.0/24 to any port 5432

# O da qualsiasi IP (meno sicuro)
sudo ufw allow 5432/tcp

# Ricarica
sudo ufw reload
```

### iptables (alternativa)

```bash
# Verifica regole esistenti
sudo iptables -L -n

# Permetti PostgreSQL
sudo iptables -A INPUT -p tcp --dport 5432 -j ACCEPT

# Salva regole
sudo netfilter-persistent save
```

---

## 🐳 Connessione da Docker a PostgreSQL su Host

### Scenario 1: PostgreSQL sulla stessa macchina di Docker

**Su Linux (Ubuntu 24):**

Docker non supporta `host.docker.internal` di default. Usa l'IP del bridge Docker:

```bash
# Trova l'IP del bridge Docker
ip addr show docker0
# Output esempio: inet 172.17.0.1/16

# O usa questo comando
docker network inspect bridge | grep Gateway
```

**Configura .env:**
```env
DATABASE_URL=postgresql://user:password@172.17.0.1:5432/fhir_terminology
```

### Scenario 2: PostgreSQL su macchina remota

```env
# Usa l'IP della macchina remota
DATABASE_URL=postgresql://user:password@192.168.1.100:5432/fhir_terminology
```

### Scenario 3: Usa network host (solo Linux)

Modifica `docker-compose.yml`:

```yaml
services:
  backend:
    network_mode: "host"
    # Rimuovi ports: mapping quando usi host network
    environment:
      - DATABASE_URL=postgresql://user:password@localhost:5432/fhir_terminology
```

**Nota:** Con `network_mode: host`, il container usa direttamente la rete dell'host.

---

## 🧪 Test Connessione Database

### Test 1: Script automatico
```bash
./test-db-connection.sh
```

### Test 2: Manuale con psql
```bash
# Installa client PostgreSQL se necessario
sudo apt-get install postgresql-client

# Test connessione
psql -h 192.168.1.100 -p 5432 -U postgres -d fhir_terminology
# Inserisci password quando richiesto
```

### Test 3: Da container Docker
```bash
# Test con IP bridge Docker (Linux)
docker run --rm postgres:15-alpine psql \
  "postgresql://user:password@172.17.0.1:5432/dbname" \
  -c "SELECT version();"

# Test con IP remoto
docker run --rm postgres:15-alpine psql \
  "postgresql://user:password@192.168.1.100:5432/dbname" \
  -c "SELECT version();"
```

---

## 🔧 Risoluzione Problemi Comuni

### Problema 1: "Connection refused"

**Causa:** PostgreSQL non accetta connessioni remote

**Soluzione:**
```bash
# 1. Verifica PostgreSQL in ascolto
sudo netstat -tlnp | grep 5432

# 2. Controlla postgresql.conf
sudo grep listen_addresses /etc/postgresql/15/main/postgresql.conf

# 3. Verifica pg_hba.conf
sudo cat /etc/postgresql/15/main/pg_hba.conf | grep -v "^#" | grep -v "^$"
```

### Problema 2: "No route to host"

**Causa:** Firewall blocca la connessione

**Soluzione:**
```bash
# Test connessione porta
nc -zv 192.168.1.100 5432

# Disabilita temporaneamente firewall per test
sudo ufw disable
# Prova connessione
# Riabilita
sudo ufw enable
```

### Problema 3: "Password authentication failed"

**Causa:** Credenziali errate o utente non autorizzato

**Soluzione:**
```bash
# Connettiti come postgres
sudo -u postgres psql

# Crea utente se non esiste
CREATE USER fhir_user WITH PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE fhir_terminology TO fhir_user;

# Verifica utenti
\du
```

### Problema 4: Docker non raggiunge host

**Su Ubuntu/Linux:**

Il problema è che Docker su Linux non ha `host.docker.internal`.

**Soluzione 1 - Usa IP bridge:**
```bash
# Trova IP gateway Docker
docker network inspect bridge | grep Gateway
# Usa questo IP in DATABASE_URL

DATABASE_URL=postgresql://user:password@172.17.0.1:5432/dbname
```

**Soluzione 2 - Aggiungi extra_hosts:**

In `docker-compose.yml`:
```yaml
services:
  backend:
    extra_hosts:
      - "host.docker.internal:host-gateway"
    environment:
      - DATABASE_URL=postgresql://user:password@host.docker.internal:5432/dbname
```

**Soluzione 3 - Usa network host:**
```yaml
services:
  backend:
    network_mode: "host"
    environment:
      - DATABASE_URL=postgresql://user:password@localhost:5432/dbname
```

---

## 📋 Checklist Completa

Prima di avviare Docker:

- [ ] PostgreSQL installato e running
- [ ] `listen_addresses = '*'` in postgresql.conf
- [ ] Regola permissiva in pg_hba.conf
- [ ] PostgreSQL riavviato dopo modifiche
- [ ] Porta 5432 aperta nel firewall
- [ ] Test connessione da host funziona: `psql -h HOST -U user -d db`
- [ ] Test connessione da Docker funziona: `./test-db-connection.sh`
- [ ] DATABASE_URL corretto in .env
- [ ] Host corretto per Docker (172.17.0.1 su Linux)

---

## 🚀 Setup Rapido Completo Ubuntu 24

```bash
# 1. Installa Docker (se non installato)
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
newgrp docker

# 2. Configura PostgreSQL
sudo nano /etc/postgresql/15/main/postgresql.conf
# Imposta: listen_addresses = '*'

sudo nano /etc/postgresql/15/main/pg_hba.conf
# Aggiungi: host all all 172.17.0.0/16 md5

sudo systemctl restart postgresql

# 3. Configura Firewall
sudo ufw allow from 172.17.0.0/16 to any port 5432

# 4. Test connessione
./test-db-connection.sh

# 5. Configura .env
cp .env.docker.example .env
nano .env
# Imposta: DATABASE_URL=postgresql://user:pass@172.17.0.1:5432/dbname

# 6. Deploy
./deploy.sh
```

---

## 📞 Supporto Debugging

```bash
# Logs PostgreSQL
sudo tail -f /var/log/postgresql/postgresql-15-main.log

# Test dal container backend
docker-compose exec backend env | grep DATABASE
docker-compose exec backend psql $DATABASE_URL -c "SELECT version();"

# Logs backend
docker-compose logs -f backend

# Network info
docker network inspect fhir-terminology-network
```

---

## 🔐 Sicurezza per Produzione

**NON usare in produzione:**
- `listen_addresses = '*'` senza SSL
- `host all all 0.0.0.0/0 md5` in pg_hba.conf

**Usa invece:**
```
# postgresql.conf
ssl = on
ssl_cert_file = '/etc/ssl/certs/server.crt'
ssl_key_file = '/etc/ssl/private/server.key'

# pg_hba.conf
hostssl all all 0.0.0.0/0 md5

# .env
DATABASE_URL=postgresql://user:pass@host:5432/db?sslmode=require
```
