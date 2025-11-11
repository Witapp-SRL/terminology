#!/bin/bash
# Script per il deployment rapido del FHIR Terminology Service

set -e

echo "🚀 FHIR Terminology Service - Deployment Script"
echo "================================================"

# Colori per output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Funzioni helper
print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

# Verifica prerequisiti
echo ""
echo "📋 Verifica prerequisiti..."

if ! command -v docker &> /dev/null; then
    print_error "Docker non trovato. Installare Docker prima di continuare."
    exit 1
fi
print_success "Docker installato"

# Rileva quale versione di docker-compose è disponibile
COMPOSE_CMD=""
if docker compose version &> /dev/null; then
    COMPOSE_CMD="docker compose"
    print_success "Docker Compose V2 installato (raccomandato)"
elif command -v docker-compose &> /dev/null; then
    COMPOSE_CMD="docker-compose"
    print_warning "Docker Compose V1 rilevato (versione vecchia)"
    print_warning "Raccomandato: aggiorna a V2 con './fix-docker-compose.sh'"
else
    print_error "Docker Compose non trovato. Installare Docker Compose."
    exit 1
fi
print_success "Usando: $COMPOSE_CMD"

# Verifica file .env
echo ""
echo "⚙️  Verifica configurazione..."

if [ ! -f ".env" ]; then
    print_warning ".env non trovato. Creo da template..."
    cp .env.docker.example .env
    print_warning "IMPORTANTE: Modifica il file .env con le tue configurazioni!"
    read -p "Premi ENTER per aprire .env con nano (o CTRL+C per uscire)..."
    nano .env
fi
print_success "File .env presente"

# Verifica connessione database
echo ""
echo "🔌 Verifica connessione database..."

# Estrai DATABASE_URL da .env
export $(cat .env | grep DATABASE_URL | xargs)

if [ -z "$DATABASE_URL" ]; then
    print_error "DATABASE_URL non configurato in .env"
    exit 1
fi

print_success "DATABASE_URL configurato"

# Menu principale
echo ""
echo "Seleziona operazione:"
echo "1) 🏗️  Build e primo avvio (fresh install)"
echo "2) 🔄 Restart servizi"
echo "3) 🛑 Stop servizi"
echo "4) 📊 Mostra stato"
echo "5) 📝 Mostra logs"
echo "6) 🗑️  Rimuovi tutto (attenzione!)"
echo "7) ⚡ Build e restart (dopo modifiche)"
echo "8) 🔧 Inizializza database"
echo "9) 👤 Crea utente admin"
echo "0) ❌ Esci"

read -p "Scelta: " choice

case $choice in
    1)
        echo ""
        echo "🏗️  Build e avvio del sistema..."
        
        # Build immagini
        echo "Building Docker images..."
        docker-compose build
        print_success "Build completata"
        
        # Avvio servizi
        echo "Avvio servizi..."
        docker-compose up -d
        print_success "Servizi avviati"
        
        # Attendi che i servizi siano pronti
        echo "Attendo che i servizi siano pronti..."
        sleep 10
        
        # Mostra stato
        docker-compose ps
        
        echo ""
        print_success "Deployment completato!"
        echo ""
        echo "📍 Accedi ai servizi:"
        echo "   Frontend: http://localhost:3000"
        echo "   Backend:  http://localhost:8001/api"
        echo "   API Docs: http://localhost:8001/api/metadata"
        echo ""
        print_warning "PROSSIMO PASSO: Esegui l'inizializzazione del database (opzione 8)"
        ;;
        
    2)
        echo ""
        echo "🔄 Restart servizi..."
        docker-compose restart
        print_success "Servizi riavviati"
        docker-compose ps
        ;;
        
    3)
        echo ""
        echo "🛑 Stop servizi..."
        docker-compose stop
        print_success "Servizi fermati"
        ;;
        
    4)
        echo ""
        echo "📊 Stato servizi:"
        docker-compose ps
        ;;
        
    5)
        echo ""
        echo "📝 Logs (CTRL+C per uscire):"
        echo "Quale servizio?"
        echo "1) Tutti"
        echo "2) Backend"
        echo "3) Frontend"
        read -p "Scelta: " log_choice
        
        case $log_choice in
            1) docker-compose logs -f ;;
            2) docker-compose logs -f backend ;;
            3) docker-compose logs -f frontend ;;
            *) print_error "Scelta non valida" ;;
        esac
        ;;
        
    6)
        echo ""
        print_warning "ATTENZIONE: Questa operazione rimuoverà tutti i container!"
        read -p "Sei sicuro? (yes/no): " confirm
        if [ "$confirm" = "yes" ]; then
            echo "🗑️  Rimozione in corso..."
            docker-compose down -v
            print_success "Tutto rimosso"
        else
            print_warning "Operazione annullata"
        fi
        ;;
        
    7)
        echo ""
        echo "⚡ Rebuild e restart..."
        docker-compose build --no-cache
        docker-compose up -d --force-recreate
        print_success "Build e restart completati"
        docker-compose ps
        ;;
        
    8)
        echo ""
        echo "🔧 Inizializzazione database..."
        
        # Verifica che il backend sia running
        if [ "$(docker-compose ps -q backend)" = "" ]; then
            print_error "Backend non in esecuzione. Avvialo prima (opzione 1)"
            exit 1
        fi
        
        echo "Eseguo migrazioni database..."
        docker-compose exec backend python database/run_migration.py || print_warning "Migrazioni già eseguite"
        
        echo "Carico dati di esempio..."
        docker-compose exec backend python seed_data_medical.py || print_warning "Dati già caricati"
        
        print_success "Database inizializzato"
        ;;
        
    9)
        echo ""
        echo "👤 Creazione utente admin..."
        
        if [ "$(docker-compose ps -q backend)" = "" ]; then
            print_error "Backend non in esecuzione. Avvialo prima (opzione 1)"
            exit 1
        fi
        
        read -p "Username (default: admin): " admin_user
        admin_user=${admin_user:-admin}
        
        read -p "Email (default: admin@example.com): " admin_email
        admin_email=${admin_email:-admin@example.com}
        
        read -s -p "Password (default: admin123): " admin_pass
        admin_pass=${admin_pass:-admin123}
        echo ""
        
        docker-compose exec backend python create_admin.py "$admin_user" "$admin_email" "$admin_pass" "Administrator"
        
        echo ""
        print_success "Utente admin creato!"
        echo "Username: $admin_user"
        echo "Password: [nascosta]"
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
