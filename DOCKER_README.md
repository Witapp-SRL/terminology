# FHIR Terminology Service - Docker Quick Start

## 🚀 Avvio Rapido

### Opzione 1: Con PostgreSQL Esterno (Produzione)

```bash
# 1. Copia e configura variabili d'ambiente
cp .env.docker.example .env
nano .env  # Modifica con i tuoi valori

# 2. Avvia con script automatico
./deploy.sh

# Oppure manualmente:
docker-compose build
docker-compose up -d
```

### Opzione 2: Con PostgreSQL Incluso (Sviluppo)

```bash
# 1. Usa docker-compose.dev.yml
docker-compose -f docker-compose.dev.yml up -d

# Include PostgreSQL + Backend + Frontend + pgAdmin
```

## 📍 Accesso ai Servizi

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8001/api
- **API Metadata**: http://localhost:8001/api/metadata
- **pgAdmin** (solo dev): http://localhost:5050

## 🔑 Credenziali Default

**Admin User:**
- Username: `admin`
- Password: `admin123`

**pgAdmin** (solo dev):
- Email: `admin@admin.com`
- Password: `admin`

## 📋 Comandi Utili

```bash
# Stato servizi
docker-compose ps

# Logs
docker-compose logs -f
docker-compose logs -f backend
docker-compose logs -f frontend

# Restart
docker-compose restart

# Stop
docker-compose stop

# Rimozione completa
docker-compose down -v

# Rebuild dopo modifiche
docker-compose build --no-cache
docker-compose up -d --force-recreate
```

## 🔧 Inizializzazione Database

```bash
# Entra nel container backend
docker-compose exec backend bash

# Esegui migrazioni
python database/run_migration.py

# Carica dati di esempio
python seed_data_medical.py

# Crea admin user
python create_admin.py

# Esci
exit
```

## 🐛 Troubleshooting

### Backend non si avvia
```bash
# Verifica logs
docker-compose logs backend

# Verifica database connection
docker-compose exec backend psql $DATABASE_URL -c "SELECT version();"
```

### Frontend non carica
```bash
# Rebuild con nuova configurazione
docker-compose build frontend --no-cache
docker-compose up -d frontend
```

### Database connection error
Verifica in `.env`:
- `DATABASE_URL` corretto
- PostgreSQL accetta connessioni remote
- Porta 5432 aperta nel firewall

## 📚 Documentazione Completa

- [DEPLOYMENT.md](./DEPLOYMENT.md) - Guida completa al deployment
- [FHIR_API_DOCUMENTATION.md](./FHIR_API_DOCUMENTATION.md) - API Reference

## 🔐 Sicurezza per Produzione

1. Cambia `SECRET_KEY` in `.env`
2. Usa password sicure per database
3. Limita `CORS_ORIGINS` ai tuoi domini
4. Implementa HTTPS con reverse proxy
5. Backup regolari del database

## 📈 Monitoring

```bash
# Health check
docker-compose ps

# Resource usage
docker stats

# Logs in tempo reale
docker-compose logs -f --tail=100
```

## 🆘 Supporto

Per problemi o domande:
1. Controlla i logs: `docker-compose logs -f`
2. Verifica configurazione: `docker-compose config`
3. Consulta [DEPLOYMENT.md](./DEPLOYMENT.md)
