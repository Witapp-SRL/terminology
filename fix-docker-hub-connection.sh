#!/bin/bash
# Script per diagnosticare e risolvere problemi di connessione Docker Hub

set -e

echo "🔍 Diagnosi Connessione Docker Hub"
echo "==================================="

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_success() { echo -e "${GREEN}✓ $1${NC}"; }
print_error() { echo -e "${RED}✗ $1${NC}"; }
print_warning() { echo -e "${YELLOW}⚠ $1${NC}"; }
print_info() { echo -e "${BLUE}ℹ $1${NC}"; }

# Test 1: Connessione internet
echo ""
echo "🌐 Test 1: Connessione internet..."
if ping -c 1 8.8.8.8 &>/dev/null; then
    print_success "Connessione internet OK"
else
    print_error "Nessuna connessione internet"
    exit 1
fi

# Test 2: DNS resolution
echo ""
echo "🔍 Test 2: Risoluzione DNS..."
if nslookup registry-1.docker.io &>/dev/null || host registry-1.docker.io &>/dev/null; then
    print_success "DNS risolve registry-1.docker.io"
    IP=$(host registry-1.docker.io | grep "has address" | head -1 | awk '{print $4}')
    echo "   IP: $IP"
else
    print_error "Impossibile risolvere registry-1.docker.io"
    print_info "Provo con DNS alternativo..."
    echo "nameserver 8.8.8.8" | sudo tee /etc/resolv.conf.tmp
    echo "nameserver 1.1.1.1" | sudo tee -a /etc/resolv.conf.tmp
fi

# Test 3: Connessione HTTPS a Docker Hub
echo ""
echo "🔐 Test 3: Connessione HTTPS Docker Hub..."
if curl -I --max-time 10 https://registry-1.docker.io/v2/ &>/dev/null; then
    print_success "HTTPS a Docker Hub funziona"
else
    print_error "Timeout connessione HTTPS a Docker Hub"
    echo ""
    print_info "Possibili cause:"
    echo "  1. Firewall blocca HTTPS (porta 443)"
    echo "  2. Proxy/corporate network"
    echo "  3. Rate limiting Docker Hub"
    echo "  4. Problemi temporanei Docker Hub"
fi

# Test 4: Docker daemon
echo ""
echo "🐳 Test 4: Docker daemon..."
if docker info &>/dev/null; then
    print_success "Docker daemon attivo"
else
    print_error "Docker daemon non risponde"
    exit 1
fi

# Test 5: Prova pull di un'immagine piccola
echo ""
echo "📦 Test 5: Pull test image..."
if timeout 30 docker pull hello-world &>/dev/null; then
    print_success "Pull immagini Docker funziona"
else
    print_error "Impossibile scaricare immagini da Docker Hub"
fi

echo ""
echo "🔧 Soluzioni disponibili:"
echo "1) 🌐 Configura DNS alternativo"
echo "2) 🪞 Usa mirror Docker Hub"
echo "3) 📥 Pull manuale immagini necessarie"
echo "4) 🏷️  Usa tag specifici invece di 'latest'"
echo "5) ⏱️  Aumenta timeout Docker"
echo "6) 🔄 Retry pull con loop"
echo "0) ❌ Esci"

read -p "Scelta (0-6): " choice

case $choice in
    1)
        echo ""
        print_info "Configurazione DNS alternativo..."
        
        # Backup DNS attuale
        sudo cp /etc/resolv.conf /etc/resolv.conf.backup
        
        # Imposta DNS Google e Cloudflare
        echo "nameserver 8.8.8.8" | sudo tee /etc/resolv.conf
        echo "nameserver 8.8.4.4" | sudo tee -a /etc/resolv.conf
        echo "nameserver 1.1.1.1" | sudo tee -a /etc/resolv.conf
        
        print_success "DNS configurato"
        
        # Restart Docker
        sudo systemctl restart docker
        
        print_info "Riprova il build ora"
        ;;
        
    2)
        echo ""
        print_info "Configurazione mirror Docker Hub..."
        
        # Crea o modifica daemon.json
        sudo mkdir -p /etc/docker
        
        cat <<EOF | sudo tee /etc/docker/daemon.json
{
  "registry-mirrors": [
    "https://mirror.gcr.io",
    "https://docker.mirrors.ustc.edu.cn"
  ],
  "max-concurrent-downloads": 10
}
EOF
        
        # Restart Docker
        sudo systemctl restart docker
        
        print_success "Mirror configurati"
        print_info "Riprova il build ora"
        ;;
        
    3)
        echo ""
        print_info "Pull manuale immagini necessarie..."
        
        echo "Scarico immagini di base (può richiedere tempo)..."
        
        # Pull con retry
        for i in {1..3}; do
            echo "Tentativo $i/3..."
            
            docker pull node:20-alpine && print_success "✓ node:20-alpine" && break
            sleep 5
        done
        
        for i in {1..3}; do
            docker pull nginx:alpine && print_success "✓ nginx:alpine" && break
            sleep 5
        done
        
        for i in {1..3}; do
            docker pull postgres:15-alpine && print_success "✓ postgres:15-alpine" && break
            sleep 5
        done
        
        print_success "Immagini scaricate"
        print_info "Ora puoi eseguire: docker compose build"
        ;;
        
    4)
        echo ""
        print_info "Aggiorno Dockerfile con tag specifici..."
        
        # Aggiorna frontend Dockerfile
        sed -i 's/FROM node:20-alpine/FROM node:20.11.1-alpine3.19/' frontend/Dockerfile
        sed -i 's/FROM nginx:alpine/FROM nginx:1.25-alpine/' frontend/Dockerfile
        
        print_success "Dockerfile aggiornati con tag specifici"
        print_info "Riprova: docker compose build"
        ;;
        
    5)
        echo ""
        print_info "Aumento timeout Docker daemon..."
        
        sudo mkdir -p /etc/docker
        
        # Leggi daemon.json esistente o crea nuovo
        if [ -f /etc/docker/daemon.json ]; then
            sudo cp /etc/docker/daemon.json /etc/docker/daemon.json.backup
        fi
        
        cat <<EOF | sudo tee /etc/docker/daemon.json
{
  "max-concurrent-downloads": 3,
  "max-concurrent-uploads": 3,
  "default-address-pools": [
    {
      "base": "172.17.0.0/16",
      "size": 24
    }
  ]
}
EOF
        
        sudo systemctl restart docker
        sleep 5
        
        print_success "Timeout aumentati"
        print_info "Riprova il build"
        ;;
        
    6)
        echo ""
        print_info "Build con retry automatico..."
        
        MAX_RETRIES=3
        for i in $(seq 1 $MAX_RETRIES); do
            echo ""
            echo "🔄 Tentativo $i/$MAX_RETRIES..."
            
            if docker compose build --no-cache 2>&1; then
                print_success "Build completato!"
                docker compose up -d
                exit 0
            else
                print_warning "Build fallito, riprovo tra 10 secondi..."
                sleep 10
            fi
        done
        
        print_error "Build fallito dopo $MAX_RETRIES tentativi"
        ;;
        
    0)
        echo "Uscita..."
        exit 0
        ;;
        
    *)
        print_error "Scelta non valida"
        exit 1
        ;;
esac

echo ""
echo "✅ Operazione completata!"
echo ""
echo "🔄 Se ancora problemi, prova:"
echo "  1. Riavvia Docker: sudo systemctl restart docker"
echo "  2. Riavvia sistema: sudo reboot"
echo "  3. Controlla connessione: ping registry-1.docker.io"
echo "  4. Usa un VPN se dietro firewall corporate"
