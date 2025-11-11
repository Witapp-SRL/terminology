# Fix: TLS Handshake Timeout Docker Hub

## 🐛 Problema

```
failed to resolve source metadata for docker.io/library/node:20-alpine: 
net/http: TLS handshake timeout
```

**Causa:** Impossibile connettersi a Docker Hub per scaricare le immagini base.

**Possibili motivi:**
1. Problemi di rete/firewall
2. Rate limiting Docker Hub
3. Configurazione DNS
4. Timeout rete lenta
5. Firewall corporate/proxy

---

## ✅ Soluzioni (in ordine di efficacia)

### Soluzione 1: Pre-download Immagini (RACCOMANDATO)

```bash
# Pull manuale delle immagini necessarie con retry
docker pull node:20.11.1-alpine3.19
docker pull nginx:1.25-alpine  
docker pull postgres:15-alpine

# Poi build (userà cache locale)
docker compose build
docker compose up -d
```

**Vantaggi:** Funziona anche con connessione lenta/instabile

---

### Soluzione 2: Script Automatico

```bash
./fix-docker-hub-connection.sh

# Menu opzioni:
# 1) Configura DNS alternativo (8.8.8.8, 1.1.1.1)
# 2) Configura mirror Docker Hub
# 3) Pull manuale con retry
# 4) Usa tag specifici (GIÀ FATTO)
# 5) Aumenta timeout
# 6) Build con retry automatico
```

---

### Soluzione 3: Configura Docker Daemon

Crea/modifica `/etc/docker/daemon.json`:

```json
{
  "registry-mirrors": [
    "https://mirror.gcr.io"
  ],
  "max-concurrent-downloads": 3,
  "dns": ["8.8.8.8", "8.8.4.4"],
  "insecure-registries": []
}
```

Riavvia Docker:
```bash
sudo systemctl restart docker
docker compose build
```

---

### Soluzione 4: Usa DNS Alternativi

```bash
# Temporaneo (test)
echo "nameserver 8.8.8.8" | sudo tee /etc/resolv.conf
echo "nameserver 1.1.1.1" | sudo tee -a /etc/resolv.conf

# Permanente (Ubuntu 24)
sudo nano /etc/systemd/resolved.conf

# Aggiungi:
[Resolve]
DNS=8.8.8.8 1.1.1.1
FallbackDNS=8.8.4.4

# Riavvia
sudo systemctl restart systemd-resolved
```

---

### Soluzione 5: Build con Retry e Timeout

```bash
# Build con timeout aumentato
export DOCKER_BUILDKIT=1
export BUILDKIT_PROGRESS=plain

# Retry loop
for i in {1..5}; do
    echo "Tentativo $i/5..."
    docker compose build && break
    sleep 10
done
```

---

### Soluzione 6: Usa Immagini Locali Pre-scaricate

```bash
# Script per pre-scaricare tutto
cat > pull-images.sh <<'EOF'
#!/bin/bash
images=(
    "node:20.11.1-alpine3.19"
    "nginx:1.25-alpine"
    "postgres:15-alpine"
    "python:3.11-slim"
)

for img in "${images[@]}"; do
    echo "Scarico $img..."
    for attempt in {1..5}; do
        docker pull $img && break
        echo "Retry $attempt/5..."
        sleep 10
    done
done
EOF

chmod +x pull-images.sh
./pull-images.sh
```

---

## 🌐 Fix Proxy/Corporate Network

Se sei dietro un proxy corporate:

```bash
# Configura proxy per Docker
sudo mkdir -p /etc/systemd/system/docker.service.d

cat <<EOF | sudo tee /etc/systemd/system/docker.service.d/http-proxy.conf
[Service]
Environment="HTTP_PROXY=http://proxy.corporate.com:8080"
Environment="HTTPS_PROXY=http://proxy.corporate.com:8080"
Environment="NO_PROXY=localhost,127.0.0.1"
EOF

# Reload e restart
sudo systemctl daemon-reload
sudo systemctl restart docker
```

---

## 🔍 Diagnosi Avanzata

```bash
# Test connessione Docker Hub
curl -v https://registry-1.docker.io/v2/

# Test DNS
nslookup registry-1.docker.io
dig registry-1.docker.io

# Verifica route
traceroute registry-1.docker.io

# Docker daemon config
docker info | grep -A 10 "Registry"

# Logs Docker daemon
sudo journalctl -u docker.service --since "10 minutes ago"
```

---

## ⚡ Quick Fix (One-Liner)

```bash
# Pull + Build + Up con retry
(docker pull node:20.11.1-alpine3.19 && docker pull nginx:1.25-alpine && docker pull postgres:15-alpine) && docker compose build && docker compose up -d
```

---

## 🛠️ Workaround: Build Senza Network

Se il problema persiste, usa immagini già scaricate:

1. **Scarica le immagini** su un'altra macchina con buona connessione
2. **Esporta** le immagini:
   ```bash
   docker save node:20.11.1-alpine3.19 -o node-20-alpine.tar
   docker save nginx:1.25-alpine -o nginx-alpine.tar
   docker save postgres:15-alpine -o postgres-15-alpine.tar
   ```
3. **Trasferisci** i file .tar alla tua macchina
4. **Importa**:
   ```bash
   docker load -i node-20-alpine.tar
   docker load -i nginx-alpine.tar
   docker load -i postgres-15-alpine.tar
   ```
5. **Build** (userà cache locale):
   ```bash
   docker compose build
   ```

---

## 🔧 Fix Definitivo (Tutti i Metodi)

```bash
# 1. DNS
echo "nameserver 8.8.8.8" | sudo tee /etc/resolv.conf
echo "nameserver 1.1.1.1" | sudo tee -a /etc/resolv.conf

# 2. Docker daemon
sudo systemctl restart docker

# 3. Pull con retry
for img in node:20.11.1-alpine3.19 nginx:1.25-alpine postgres:15-alpine; do
    for i in {1..5}; do
        docker pull $img && break || sleep 10
    done
done

# 4. Build
docker compose build

# 5. Up
docker compose up -d
```

---

## 📋 Checklist Risoluzione

- [ ] Verifica connessione: `ping 8.8.8.8`
- [ ] Test DNS: `nslookup registry-1.docker.io`
- [ ] Test HTTPS: `curl -I https://registry-1.docker.io/v2/`
- [ ] Configura DNS (8.8.8.8, 1.1.1.1)
- [ ] Pull manuale immagini
- [ ] Riavvia Docker daemon
- [ ] Retry build
- [ ] Verifica firewall/proxy

---

## 🆘 Se Nulla Funziona

**Opzione A: Usa VPN**
```bash
# Se dietro firewall restrictive, usa VPN
# Poi riprova build
```

**Opzione B: Usa mirror alternativo**
```bash
# Aliyun mirror (Cina)
# Tencent mirror
# Azure China mirror
```

**Opzione C: Build offline**
```bash
# Scarica immagini altrove e importa (vedi sopra)
```

---

## ✅ Verifica Post-Fix

```bash
# Immagini scaricate
docker images | grep -E "node|nginx|postgres"

# Build senza errori
docker compose build

# Servizi running
docker compose up -d
docker compose ps
```

---

## 📚 Risorse

- [Docker Hub Status](https://status.docker.com/)
- [Docker Daemon Config](https://docs.docker.com/engine/reference/commandline/dockerd/)
- [Registry Mirrors](https://docs.docker.com/registry/recipes/mirror/)
