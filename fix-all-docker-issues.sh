#!/bin/bash
# Script all-in-one per risolvere tutti i problemi Docker comuni

set -e

echo "🔧 FHIR Terminology - Docker Fix All"
echo "====================================="

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_success() { echo -e "${GREEN}✓ $1${NC}"; }
print_error() { echo -e "${RED}✗ $1${NC}"; }
print_warning() { echo -e "${YELLOW}⚠ $1${NC}"; }
print_info() { echo -e "${BLUE}ℹ $1${NC}"; }

# Rileva Docker Compose
if docker compose version &>/dev/null; then
    COMPOSE_CMD="docker compose"
    print_success "Docker Compose V2 rilevato"
elif command -v docker-compose &>/dev/null; then
    COMPOSE_CMD="docker-compose"
    print_warning "Docker Compose V1 rilevato (raccomandato aggiornare)"
else
    print_error "Docker Compose non trovato!"
    exit 1
fi

echo ""
print_info "Questo script risolverà:"
echo "  1. ✅ Errore ContainerConfig (docker-compose V1)"
echo "  2. ✅ Warning 'version' obsolete"
echo "  3. ✅ Network label conflicts"
echo "  4. ✅ Bcrypt/Passlib compatibility"
echo "  5. ✅ Cache e volumi corrotti"

echo ""
read -p "Continuare con pulizia completa? (y/n): " confirm

if [ "$confirm" != "y" ]; then
    echo "Operazione annullata"
    exit 0
fi

echo ""
echo "🧹 Fase 1: Pulizia completa..."

# Stop tutti i servizi
print_info "Stop containers..."
$COMPOSE_CMD down -v 2>/dev/null || true

# Rimuovi containers del progetto
print_info "Rimozione containers FHIR..."
docker ps -a | grep fhir-terminology | awk '{print $1}' | xargs -r docker rm -f 2>/dev/null || true

# Rimuovi network con conflitti
print_info "Rimozione network..."
docker network rm fhir-terminology-network 2>/dev/null || true
docker network prune -f

# Rimuovi volumi del progetto
print_info "Rimozione volumi..."
docker volume ls | grep fhir | awk '{print $2}' | xargs -r docker volume rm 2>/dev/null || true

# Rimuovi immagini del progetto
print_info "Rimozione immagini vecchie..."
docker images | grep -E "fhir-terminology|fhir-backend|fhir-frontend" | awk '{print $3}' | xargs -r docker rmi -f 2>/dev/null || true

# Pulizia generale
print_info "Pulizia sistema Docker..."
docker system prune -f

print_success "Pulizia completata"

echo ""
echo "🏗️  Fase 2: Rebuild completo..."

# Rebuild senza cache
print_info "Build backend (con bcrypt 4.0.1)..."
$COMPOSE_CMD build backend --no-cache --pull

print_info "Build frontend (con Node 20)..."
$COMPOSE_CMD build frontend --no-cache --pull

print_success "Build completato"

echo ""
echo "🚀 Fase 3: Avvio servizi..."

$COMPOSE_CMD up -d

echo ""
print_info "Attendo avvio servizi (15 secondi)..."
sleep 15

echo ""
echo "📊 Stato finale:"
$COMPOSE_CMD ps

echo ""
echo "🔍 Verifica health:"

# Check backend
if curl -s http://localhost:8001/api/ > /dev/null; then
    print_success "Backend risponde su http://localhost:8001/api/"
else
    print_error "Backend non risponde"
    echo "Controlla logs: docker compose logs backend"
fi

# Check frontend
if curl -s http://localhost:3000 > /dev/null; then
    print_success "Frontend risponde su http://localhost:3000"
else
    print_error "Frontend non risponde"
    echo "Controlla logs: docker compose logs frontend"
fi

echo ""
echo "📝 Verifica logs per errori:"
echo ""

# Mostra ultimi logs backend
print_info "Ultimi log backend:"
$COMPOSE_CMD logs --tail=10 backend

echo ""
read -p "Vuoi vedere logs completi backend? (y/n): " show_logs

if [ "$show_logs" = "y" ]; then
    $COMPOSE_CMD logs backend | tail -50
fi

echo ""
echo "✅ Fix completato!"
echo ""
echo "🎯 Prossimi passi:"
echo "  1. Verifica servizi: docker compose ps"
echo "  2. Test login: http://localhost:3000 (admin/admin123)"
echo "  3. Test API: curl http://localhost:8001/api/metadata"
echo ""
echo "📚 Documentazione:"
echo "  - FIX_CONTAINERCONFIG_ERROR.md"
echo "  - FIX_DOCKER_WARNINGS.md"
echo "  - FIX_BCRYPT_ERROR.md"
echo "  - DEPLOYMENT.md"
