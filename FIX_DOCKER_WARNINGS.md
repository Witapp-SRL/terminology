# Fix: Warning Docker Compose V2

## ⚠️ Warning Comuni

### 1. "attribute `version` is obsolete"

**Warning completo:**
```
the attribute `version` is obsolete, it will be ignored, please remove it to avoid potential confusion
```

**Causa:** In Docker Compose V2, `version: '3.8'` non è più necessario.

**Fix:** ✅ **GIÀ APPLICATO**
```yaml
# PRIMA (obsoleto)
version: '3.8'
services:
  ...

# DOPO (corretto)
services:
  ...
```

**Stato:** Il docker-compose.yml è già stato aggiornato. Questo warning non apparirà più al prossimo avvio.

---

### 2. "network has incorrect label"

**Warning completo:**
```
network fhir-terminology-network was found but has incorrect label 
com.docker.compose.network set to "fhir-terminology-network" (expected: "fhir-network")
```

**Causa:** Network esistente da versione precedente con label incompatibili.

**Fix RAPIDO:**
```bash
# Metodo 1: Script automatico (RACCOMANDATO)
./fix-network.sh
# Opzione 1: Pulizia completa

# Metodo 2: Manuale
docker compose down
docker network rm fhir-terminology-network
docker compose up -d
```

---

## 🚀 Soluzione Completa (1 minuto)

```bash
# 1. Stop servizi
docker compose down

# 2. Rimuovi network problematica
docker network rm fhir-terminology-network

# 3. Pulizia generale (opzionale)
docker network prune -f

# 4. Restart pulito
docker compose up -d

# 5. Verifica (nessun warning)
docker compose ps
```

---

## 🔍 Verifica che Tutto Funzioni

```bash
# Network ricreata correttamente
docker network ls | grep fhir

# Containers running
docker compose ps

# Test backend
curl http://localhost:8001/api/

# Test frontend
curl http://localhost:3000
```

---

## 📋 Perché Questi Warning?

### Version Obsolete
Docker Compose V2 ha reso `version:` opzionale perché:
- ✅ Auto-detect features basato su sintassi
- ✅ Backward compatibility automatica
- ✅ Meno confusione per gli utenti

### Network Label Mismatch
Quando passi da V1 a V2 o ricostruisci:
- Network esistenti mantengono vecchie label
- V2 usa un sistema di label diverso
- Soluzione: ricrea network da zero

---

## 🛠️ Prevenzione Futura

**Sempre usare questi comandi per pulizia:**
```bash
# Prima di rebuild/restart
docker compose down

# Invece di solo stop
docker compose stop  # ❌ Lascia network attive
docker compose down  # ✅ Pulisce tutto
```

---

## 📝 Checklist Fix

- [x] Rimosso `version:` dal docker-compose.yml ✅
- [ ] Eseguito pulizia network
- [ ] Riavviato con `docker compose up -d`
- [ ] Verificato assenza warning
- [ ] Testato backend e frontend

---

## 🎯 Comandi Quick Reference

```bash
# Fix completo in un comando
docker compose down && docker network prune -f && docker compose up -d

# O usa lo script
./fix-network.sh

# Verifica
docker compose ps
docker network ls | grep fhir
```

---

## 🆘 Se Warning Persistono

```bash
# Nuclear option - reset completo
docker compose down -v
docker network prune -f
docker volume prune -f
docker system prune -f

# Rebuild da zero
docker compose build --no-cache
docker compose up -d
```

---

## ✅ Dopo il Fix

**Warning da aspettarsi:**
- ❌ "attribute version is obsolete" → Risolto ✅
- ❌ "network has incorrect label" → Dopo fix-network.sh ✅

**Output pulito:**
```bash
$ docker compose up -d
[+] Running 3/3
 ✔ Network fhir-terminology-network  Created
 ✔ Container wait-for-db             Started  
 ✔ Container fhir-terminology-backend Started
 ✔ Container fhir-terminology-frontend Started
```

---

## 💡 Best Practices V2

1. **Non usare `version:`** nei file compose
2. **Sempre `docker compose down`** prima di rebuild
3. **Network names** devono essere uniche per progetto
4. **Pulizia periodica** con `docker system prune`

---

## 📚 Risorse

- [Docker Compose V2 Migration Guide](https://docs.docker.com/compose/migrate/)
- [Compose Spec (No Version)](https://docs.docker.com/compose/compose-file/)
- Script: `./fix-network.sh`
