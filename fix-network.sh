#!/bin/bash
# Script per risolvere conflitti di network Docker Compose

set -e

echo "🔧 Fix: Conflitti Network Docker Compose"
echo "========================================"

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

# Rileva comando compose
if docker compose version &>/dev/null; then
    COMPOSE_CMD="docker compose"
else
    COMPOSE_CMD="docker-compose"
fi

echo ""
print_info "Problema rilevato:"
echo "  - Network ha label incorrette da versione precedente"
echo "  - Necessaria pulizia e ricreazione"

echo ""
echo "Soluzioni disponibili:"
echo "1) 🧹 Pulizia completa e ricreazione (RACCOMANDATO)"
echo "2) 🔍 Solo ispezione (mostra info)"
echo "3) 🗑️  Rimozione manuale network"
read -p "Scelta (1-3): " choice

case $choice in
    1)
        echo ""
        print_info "Avvio pulizia completa..."
        
        # Stop containers
        echo "1. Stop containers..."
        $COMPOSE_CMD down 2>/dev/null || true
        print_success "Containers fermati"
        
        # Rimuovi network con conflitti
        echo "2. Rimozione network con conflitti..."
        docker network rm fhir-terminology-network 2>/dev/null && \
            print_success "Network rimossa" || \
            print_warning "Network non trovata o già rimossa"
        
        # Rimuovi altre network orphan del progetto
        docker network ls | grep fhir | awk '{print $2}' | while read net; do
            docker network rm "$net" 2>/dev/null && echo "  - Rimossa: $net" || true
        done
        
        # Pulizia generale
        echo "3. Pulizia generale..."
        docker network prune -f
        print_success "Pulizia completata"
        
        # Ricrea tutto
        echo ""
        print_info "Ricreazione servizi..."
        $COMPOSE_CMD up -d
        
        echo ""
        print_success "Tutto completato!"
        echo ""
        echo "Verifica stato:"
        $COMPOSE_CMD ps
        
        echo ""
        echo "Network ricreata:"
        docker network ls | grep fhir
        ;;
        
    2)
        echo ""
        print_info "Ispezione network..."
        
        # Lista tutte le network fhir
        echo ""
        echo "Network esistenti:"
        docker network ls | grep -E "NAME|fhir"
        
        # Dettagli network problematica
        echo ""
        if docker network inspect fhir-terminology-network &>/dev/null; then
            print_info "Dettagli fhir-terminology-network:"
            docker network inspect fhir-terminology-network | grep -A 5 "Labels"
        else
            print_warning "Network fhir-terminology-network non trovata"
        fi
        
        # Mostra containers connessi
        echo ""
        print_info "Containers collegati:"
        docker ps -a | grep -E "NAME|fhir"
        ;;
        
    3)
        echo ""
        print_warning "Rimozione manuale network..."
        
        # Stop containers prima
        echo "Stop containers..."
        $COMPOSE_CMD down
        
        # Rimozione network
        echo "Rimozione network fhir-terminology-network..."
        docker network rm fhir-terminology-network 2>/dev/null && \
            print_success "Network rimossa" || \
            print_error "Impossibile rimuovere network (containers ancora connessi?)"
        
        echo ""
        echo "Per ricreare, esegui:"
        echo "  $COMPOSE_CMD up -d"
        ;;
        
    *)
        print_error "Scelta non valida"
        exit 1
        ;;
esac

echo ""
echo "✅ Operazione completata!"
echo ""
echo "💡 Suggerimenti:"
echo "  - Se vedi ancora warning, ripeti la pulizia (opzione 1)"
echo "  - Verifica: docker network ls | grep fhir"
echo "  - Test: curl http://localhost:8001/api/"
