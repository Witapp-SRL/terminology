#!/bin/bash
# Script per risolvere l'errore ContainerConfig e aggiornare Docker Compose

set -e

echo "🔧 Fix: Errore ContainerConfig Docker Compose"
echo "=============================================="

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

echo ""
print_info "Problema rilevato: docker-compose 1.29.2 ha un bug con ContainerConfig"
echo ""

# Verifica versione docker-compose
COMPOSE_VERSION=$(docker-compose --version 2>/dev/null || echo "unknown")
echo "Versione corrente: $COMPOSE_VERSION"

echo ""
echo "Scegli la soluzione:"
echo "1) 🚀 Installa Docker Compose V2 (RACCOMANDATO)"
echo "2) 🧹 Pulizia completa e riprova con versione attuale"
echo "3) 📝 Mostra solo i comandi (esegui manualmente)"
read -p "Scelta (1-3): " choice

case $choice in
    1)
        echo ""
        print_info "Installazione Docker Compose V2..."
        
        # Verifica se Docker Compose V2 è già installato
        if docker compose version &>/dev/null; then
            print_success "Docker Compose V2 già installato!"
            docker compose version
        else
            # Installa Docker Compose V2 come plugin
            echo "Installazione Docker Compose V2 come plugin..."
            
            # Per Ubuntu 24
            sudo apt-get update
            sudo apt-get install -y docker-compose-plugin
            
            print_success "Docker Compose V2 installato!"
            docker compose version
        fi
        
        echo ""
        print_info "Ora usa 'docker compose' (senza trattino) invece di 'docker-compose'"
        echo ""
        
        # Pulizia prima del restart
        print_info "Pulizia container e volumi vecchi..."
        docker compose down -v 2>/dev/null || docker-compose down -v 2>/dev/null || true
        
        # Rimuovi container orfani
        docker container prune -f
        
        print_success "Pulizia completata"
        
        echo ""
        print_info "Avvio con Docker Compose V2..."
        docker compose build
        docker compose up -d
        
        echo ""
        print_success "Deployment completato!"
        docker compose ps
        ;;
        
    2)
        echo ""
        print_warning "Pulizia completa in corso..."
        
        # Stop tutti i container
        docker-compose down -v 2>/dev/null || true
        
        # Rimuovi container del progetto
        docker ps -a | grep fhir-terminology | awk '{print $1}' | xargs -r docker rm -f
        
        # Rimuovi volumi
        docker volume ls | grep fhir | awk '{print $2}' | xargs -r docker volume rm
        
        # Rimuovi immagini vecchie
        docker images | grep fhir | awk '{print $3}' | xargs -r docker rmi -f
        
        # Prune completo
        docker system prune -af --volumes
        
        print_success "Pulizia completata"
        
        echo ""
        print_info "Rebuild completo..."
        docker-compose build --no-cache
        
        echo ""
        print_info "Avvio servizi..."
        docker-compose up -d
        
        echo ""
        print_success "Deployment completato!"
        docker-compose ps
        ;;
        
    3)
        echo ""
        print_info "Comandi da eseguire manualmente:"
        echo ""
        echo "# OPZIONE A: Installa Docker Compose V2 (RACCOMANDATO)"
        echo "sudo apt-get update"
        echo "sudo apt-get install -y docker-compose-plugin"
        echo "docker compose version"
        echo ""
        echo "# Poi usa 'docker compose' invece di 'docker-compose':"
        echo "docker compose down -v"
        echo "docker compose build"
        echo "docker compose up -d"
        echo ""
        echo "# OPZIONE B: Pulizia completa con docker-compose attuale"
        echo "docker-compose down -v"
        echo "docker container prune -f"
        echo "docker volume prune -f"
        echo "docker image prune -af"
        echo "docker-compose build --no-cache"
        echo "docker-compose up -d"
        ;;
        
    *)
        print_error "Scelta non valida"
        exit 1
        ;;
esac

echo ""
print_info "📚 Documentazione:"
echo "  - Docker Compose V1 (docker-compose): Deprecato"
echo "  - Docker Compose V2 (docker compose): Versione attuale"
echo ""
print_info "Da ora in poi usa:"
echo "  docker compose up -d      # invece di docker-compose up -d"
echo "  docker compose down       # invece di docker-compose down"
echo "  docker compose logs -f    # invece di docker-compose logs -f"
