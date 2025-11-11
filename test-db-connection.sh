#!/bin/bash
# Script per testare la connessione al database PostgreSQL esterno

set -e

echo "🔌 Test Connessione Database PostgreSQL Esterno"
echo "==============================================="

# Colori
GREEN='\033[0;32m'
RED='\033[0;31m'
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

# Funzione per estrarre parametri da DATABASE_URL
parse_database_url() {
    local url=$1
    
    # Formato: postgresql://user:password@host:port/database
    # Rimuovi il prefisso postgresql://
    url="${url#postgresql://}"
    
    # Estrai user:password
    local userpass="${url%%@*}"
    DB_USER="${userpass%%:*}"
    DB_PASSWORD="${userpass#*:}"
    
    # Estrai host:port/database
    local hostdb="${url#*@}"
    local hostport="${hostdb%%/*}"
    DB_HOST="${hostport%%:*}"
    DB_PORT="${hostport#*:}"
    DB_NAME="${hostdb#*/}"
    
    # Rimuovi parametri query se presenti
    DB_NAME="${DB_NAME%%\?*}"
}

# Carica .env se esiste
if [ -f ".env" ]; then
    export $(cat .env | grep -v '^#' | xargs)
    print_success ".env caricato"
else
    print_warning ".env non trovato"
    echo ""
    echo "Inserisci manualmente i dati di connessione:"
fi

# Se DATABASE_URL è presente, parsalo
if [ ! -z "$DATABASE_URL" ]; then
    print_info "DATABASE_URL trovato: ${DATABASE_URL%%:*}://***"
    parse_database_url "$DATABASE_URL"
else
    # Input manuale
    echo ""
    read -p "Host PostgreSQL (es. 192.168.1.100): " DB_HOST
    read -p "Porta (default 5432): " DB_PORT
    DB_PORT=${DB_PORT:-5432}
    read -p "Nome Database: " DB_NAME
    read -p "Username: " DB_USER
    read -s -p "Password: " DB_PASSWORD
    echo ""
fi

echo ""
echo "📋 Parametri connessione:"
echo "   Host: $DB_HOST"
echo "   Porta: $DB_PORT"
echo "   Database: $DB_NAME"
echo "   User: $DB_USER"
echo "   Password: ${DB_PASSWORD:0:3}***"

# Test 1: Verifica che psql sia installato
echo ""
echo "🔍 Test 1: Verifica strumenti..."

if ! command -v psql &> /dev/null; then
    print_error "psql non installato"
    echo ""
    echo "Installa PostgreSQL client:"
    echo "  Ubuntu/Debian: sudo apt-get install postgresql-client"
    echo "  macOS: brew install postgresql"
    echo ""
    
    # Prova con Docker se disponibile
    if command -v docker &> /dev/null; then
        print_info "Uso Docker per testare..."
        USE_DOCKER=true
    else
        exit 1
    fi
else
    print_success "psql installato: $(psql --version)"
    USE_DOCKER=false
fi

# Test 2: Test connessione di rete
echo ""
echo "🌐 Test 2: Connettività di rete..."

if command -v nc &> /dev/null; then
    if nc -z -w5 $DB_HOST $DB_PORT 2>/dev/null; then
        print_success "Porta $DB_PORT su $DB_HOST è raggiungibile"
    else
        print_error "Impossibile raggiungere $DB_HOST:$DB_PORT"
        echo ""
        print_info "Possibili cause:"
        echo "  1. Firewall blocca la connessione"
        echo "  2. PostgreSQL non accetta connessioni remote"
        echo "  3. Host o porta errati"
        exit 1
    fi
elif command -v telnet &> /dev/null; then
    timeout 5 telnet $DB_HOST $DB_PORT 2>&1 | grep -q "Connected" && \
        print_success "Porta $DB_PORT su $DB_HOST è raggiungibile" || \
        print_error "Impossibile raggiungere $DB_HOST:$DB_PORT"
else
    print_warning "nc/telnet non disponibili, salto test connettività"
fi

# Test 3: Test autenticazione PostgreSQL
echo ""
echo "🔐 Test 3: Autenticazione database..."

if [ "$USE_DOCKER" = true ]; then
    # Test con Docker
    docker run --rm postgres:15-alpine psql \
        "postgresql://$DB_USER:$DB_PASSWORD@$DB_HOST:$DB_PORT/$DB_NAME" \
        -c "SELECT version();" 2>/dev/null
else
    # Test con psql locale
    PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME \
        -c "SELECT version();" 2>/dev/null
fi

if [ $? -eq 0 ]; then
    print_success "Connessione database riuscita!"
else
    print_error "Connessione database fallita"
    echo ""
    print_info "Possibili cause:"
    echo "  1. Credenziali errate (user/password)"
    echo "  2. Database non esiste"
    echo "  3. PostgreSQL non configurato per connessioni remote"
    echo ""
    echo "📝 Configurazione PostgreSQL richiesta:"
    echo ""
    echo "1. Modifica postgresql.conf:"
    echo "   listen_addresses = '*'"
    echo ""
    echo "2. Modifica pg_hba.conf (aggiungi):"
    echo "   host    all    all    0.0.0.0/0    md5"
    echo "   # O solo la tua rete Docker:"
    echo "   host    all    all    172.17.0.0/16    md5"
    echo ""
    echo "3. Riavvia PostgreSQL:"
    echo "   sudo systemctl restart postgresql"
    echo ""
    exit 1
fi

# Test 4: Verifica tabelle (opzionale)
echo ""
read -p "Vuoi verificare le tabelle esistenti? (y/n): " check_tables

if [ "$check_tables" = "y" ]; then
    echo ""
    echo "📊 Tabelle esistenti:"
    
    if [ "$USE_DOCKER" = true ]; then
        docker run --rm postgres:15-alpine psql \
            "postgresql://$DB_USER:$DB_PASSWORD@$DB_HOST:$DB_PORT/$DB_NAME" \
            -c "\dt" 2>/dev/null
    else
        PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME \
            -c "\dt" 2>/dev/null
    fi
fi

# Test 5: Test da Docker container
echo ""
read -p "Vuoi testare la connessione da un container Docker? (y/n): " test_docker

if [ "$test_docker" = "y" ]; then
    echo ""
    echo "🐳 Test da Docker container..."
    
    # Determina l'host corretto per Docker
    echo ""
    print_info "Quale host userà Docker?"
    echo "1) host.docker.internal (raccomandato per Mac/Windows)"
    echo "2) 172.17.0.1 (gateway Docker su Linux)"
    echo "3) $DB_HOST (usa host attuale)"
    read -p "Scelta (1-3): " docker_host_choice
    
    case $docker_host_choice in
        1) DOCKER_DB_HOST="host.docker.internal" ;;
        2) DOCKER_DB_HOST="172.17.0.1" ;;
        3) DOCKER_DB_HOST="$DB_HOST" ;;
        *) DOCKER_DB_HOST="host.docker.internal" ;;
    esac
    
    echo "Test connessione da container con host: $DOCKER_DB_HOST"
    
    docker run --rm postgres:15-alpine psql \
        "postgresql://$DB_USER:$DB_PASSWORD@$DOCKER_DB_HOST:$DB_PORT/$DB_NAME" \
        -c "SELECT 'Docker connection OK' as result;" 2>/dev/null
    
    if [ $? -eq 0 ]; then
        print_success "Connessione da Docker riuscita!"
        echo ""
        print_info "Usa questo in .env:"
        echo "DATABASE_URL=postgresql://$DB_USER:$DB_PASSWORD@$DOCKER_DB_HOST:$DB_PORT/$DB_NAME"
    else
        print_error "Connessione da Docker fallita"
        echo ""
        print_info "Prova un host diverso o configura PostgreSQL per accettare connessioni da Docker"
    fi
fi

echo ""
echo "✅ Test completati!"
echo ""
echo "📝 Prossimi passi:"
echo "1. Se tutti i test sono OK, aggiorna .env con:"
echo "   DATABASE_URL=postgresql://$DB_USER:$DB_PASSWORD@[HOST_CORRETTO]:$DB_PORT/$DB_NAME"
echo ""
echo "2. Avvia i container:"
echo "   docker-compose up -d"
echo ""
echo "3. Verifica logs:"
echo "   docker-compose logs -f backend"
