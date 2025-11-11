# Fix: Errore "KeyError: 'ContainerConfig'" Docker Compose

## 🐛 Problema

```
KeyError: 'ContainerConfig'
```

Questo errore si verifica con **docker-compose 1.29.2** su Ubuntu 24 a causa di un bug noto.

---

## ✅ Soluzione Rapida (RACCOMANDATA)

### Passa a Docker Compose V2

```bash
# 1. Installa Docker Compose V2
sudo apt-get update
sudo apt-get install -y docker-compose-plugin

# 2. Verifica installazione
docker compose version

# 3. Pulizia
docker compose down -v

# 4. Rebuild e avvio
docker compose build
docker compose up -d
```

**Nota:** Docker Compose V2 usa `docker compose` (spazio) invece di `docker-compose` (trattino)

---

## 🔧 Soluzione Alternativa (Se non puoi aggiornare)

### Pulizia completa

```bash
# 1. Stop e rimozione
docker-compose down -v

# 2. Rimuovi container orfani
docker container prune -f

# 3. Rimuovi volumi
docker volume prune -f

# 4. Rimuovi immagini
docker image prune -af

# 5. Rebuild senza cache
docker-compose build --no-cache

# 6. Avvio
docker-compose up -d
```

---

## 🚀 Script Automatico

```bash
./fix-docker-compose.sh
# Scegli opzione 1 per aggiornare a V2 (raccomandato)
# Scegli opzione 2 per pulizia con versione attuale
```

---

## 📝 Differenze tra V1 e V2

| Feature | Docker Compose V1 | Docker Compose V2 |
|---------|-------------------|-------------------|
| Comando | `docker-compose` | `docker compose` |
| Installazione | Standalone binary | Docker plugin |
| Supporto | Deprecato | Attivo |
| Performance | Più lento | Più veloce |
| Bug | Bug noti (ContainerConfig) | Risolti |

---

## 🔍 Verifica Versione

```bash
# V1 (deprecato)
docker-compose --version
# Output: docker-compose version 1.29.2

# V2 (attuale)
docker compose version
# Output: Docker Compose version v2.x.x
```

---

## 📋 Comandi Aggiornati

**Vecchio (V1):**
```bash
docker-compose up -d
docker-compose down
docker-compose logs -f
docker-compose ps
```

**Nuovo (V2):**
```bash
docker compose up -d
docker compose down
docker compose logs -f
docker compose ps
```

---

## 🛠️ Causa del Problema

Il bug `ContainerConfig` in docker-compose 1.29.2 si verifica quando:
- C'è un'incompatibilità tra versioni di immagini Docker
- I volumi esistenti hanno metadata corrotti
- C'è un conflitto tra container esistenti e nuove configurazioni

**Docker Compose V2 risolve tutti questi problemi.**

---

## ⚠️ Se Continui a Usare V1

Modifica `docker-compose.yml` e rimuovi i volumi:

```yaml
services:
  backend:
    # Commenta volumes
    # volumes:
    #   - backend-logs:/app/logs

# Commenta volumes section
# volumes:
#   backend-logs:
```

**Nota:** Questa è solo una soluzione temporanea. È fortemente raccomandato passare a V2.

---

## 📚 Risorse

- [Docker Compose V2 Docs](https://docs.docker.com/compose/)
- [Migration Guide V1 to V2](https://docs.docker.com/compose/migrate/)
- [Ubuntu Docker Install Guide](https://docs.docker.com/engine/install/ubuntu/)

---

## ✅ Test Post-Fix

Dopo aver applicato la soluzione:

```bash
# Verifica servizi
docker compose ps

# Verifica logs
docker compose logs -f backend

# Test endpoint
curl http://localhost:8001/api/

# Test frontend
curl http://localhost:3000
```

---

## 🆘 Se il Problema Persiste

```bash
# Rimozione completa Docker
sudo apt-get purge docker-compose docker-compose-plugin
sudo apt-get autoremove

# Reinstallazione Docker e Compose V2
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo apt-get install -y docker-compose-plugin

# Verifica
docker compose version
```
