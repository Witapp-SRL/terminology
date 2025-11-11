#!/bin/bash
# Script per pull delle immagini Docker con retry automatico

echo "📥 Download Immagini Docker per FHIR Terminology Service"
echo "========================================================"

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_success() { echo -e "${GREEN}✓ $1${NC}"; }
print_error() { echo -e "${RED}✗ $1${NC}"; }
print_warning() { echo -e "${YELLOW}⚠ $1${NC}"; }

# Lista immagini necessarie
images=(
    "node:20.11.1-alpine3.19"
    "nginx:1.25-alpine"
    "postgres:15-alpine"
    "python:3.11-slim"
)

MAX_RETRIES=5
RETRY_DELAY=10

echo ""
echo "📦 Immagini da scaricare:"
for img in "${images[@]}"; do
    echo "  - $img"
done

echo ""
read -p "Avviare download? (y/n): " confirm
if [ "$confirm" != "y" ]; then
    echo "Operazione annullata"
    exit 0
fi

echo ""
successful=0
failed=0

for img in "${images[@]}"; do
    echo ""
    echo "📥 Download: $img"
    
    # Verifica se già presente
    if docker images | grep -q "${img%%:*}.*${img##*:}"; then
        print_warning "Già presente, salto..."
        ((successful++))
        continue
    fi
    
    # Retry loop
    success=false
    for attempt in $(seq 1 $MAX_RETRIES); do
        echo "  Tentativo $attempt/$MAX_RETRIES..."
        
        if docker pull $img 2>&1 | tee /tmp/docker-pull.log; then
            print_success "Download completato!"
            success=true
            ((successful++))
            break
        else
            if [ $attempt -lt $MAX_RETRIES ]; then
                print_warning "Fallito, riprovo tra $RETRY_DELAY secondi..."
                sleep $RETRY_DELAY
            fi
        fi
    done
    
    if [ "$success" = false ]; then
        print_error "Impossibile scaricare $img dopo $MAX_RETRIES tentativi"
        ((failed++))
    fi
done

echo ""
echo "=========================================="
echo "📊 Riepilogo:"
print_success "Successo: $successful/${#images[@]}"
if [ $failed -gt 0 ]; then
    print_error "Falliti: $failed/${#images[@]}"
fi

if [ $failed -eq 0 ]; then
    echo ""
    print_success "Tutte le immagini scaricate!"
    echo ""
    echo "🚀 Prossimi passi:"
    echo "  1. docker compose build"
    echo "  2. docker compose up -d"
    echo ""
    
    read -p "Vuoi eseguire il build ora? (y/n): " do_build
    if [ "$do_build" = "y" ]; then
        echo ""
        echo "🏗️  Building..."
        docker compose build
        
        echo ""
        echo "🚀 Starting..."
        docker compose up -d
        
        echo ""
        print_success "Deployment completato!"
        docker compose ps
    fi
else
    echo ""
    print_error "Alcune immagini non sono state scaricate."
    echo ""
    echo "💡 Soluzioni:"
    echo "  1. Riprova: $0"
    echo "  2. Configura DNS: ./fix-docker-hub-connection.sh (opzione 1)"
    echo "  3. Usa mirror: ./fix-docker-hub-connection.sh (opzione 2)"
    echo "  4. Verifica firewall: sudo ufw status"
    echo "  5. Controlla proxy se in rete corporate"
fi

echo ""
echo "📝 Immagini attualmente disponibili:"
docker images | grep -E "node|nginx|postgres|python" | grep -E "20|1.25|15|3.11"
