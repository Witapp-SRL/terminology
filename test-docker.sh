#!/bin/bash
# Script per testare il build Docker localmente

set -e

echo "🔍 Test Build Docker - FHIR Terminology Service"
echo "=============================================="

# Colori
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

# Test 1: Verifica file necessari
echo ""
echo "📋 Verifica file necessari..."

if [ ! -f "backend/Dockerfile" ]; then
    print_error "backend/Dockerfile non trovato"
    exit 1
fi
print_success "backend/Dockerfile trovato"

if [ ! -f "frontend/Dockerfile" ]; then
    print_error "frontend/Dockerfile non trovato"
    exit 1
fi
print_success "frontend/Dockerfile trovato"

if [ ! -f "docker-compose.yml" ]; then
    print_error "docker-compose.yml non trovato"
    exit 1
fi
print_success "docker-compose.yml trovato"

if [ ! -f "backend/requirements.txt" ]; then
    print_error "backend/requirements.txt non trovato"
    exit 1
fi
print_success "backend/requirements.txt trovato"

if [ ! -f "frontend/package.json" ]; then
    print_error "frontend/package.json non trovato"
    exit 1
fi
print_success "frontend/package.json trovato"

# Test 2: Verifica Docker
echo ""
echo "🐳 Verifica Docker..."

if ! command -v docker &> /dev/null; then
    print_error "Docker non installato"
    exit 1
fi
print_success "Docker installato: $(docker --version)"

if ! command -v docker-compose &> /dev/null; then
    print_error "Docker Compose non installato"
    exit 1
fi
print_success "Docker Compose installato: $(docker-compose --version)"

# Test 3: Verifica configurazione docker-compose
echo ""
echo "⚙️  Verifica configurazione docker-compose..."

docker-compose config > /dev/null 2>&1
if [ $? -eq 0 ]; then
    print_success "docker-compose.yml valido"
else
    print_error "docker-compose.yml non valido"
    exit 1
fi

# Test 4: Build Backend (opzionale)
echo ""
read -p "Vuoi testare il build del backend? (y/n): " test_backend

if [ "$test_backend" = "y" ]; then
    echo "🏗️  Building backend..."
    docker build -t fhir-backend-test ./backend
    if [ $? -eq 0 ]; then
        print_success "Backend build completato"
    else
        print_error "Backend build fallito"
        exit 1
    fi
fi

# Test 5: Build Frontend (opzionale)
echo ""
read -p "Vuoi testare il build del frontend? (y/n): " test_frontend

if [ "$test_frontend" = "y" ]; then
    echo "🏗️  Building frontend..."
    docker build -t fhir-frontend-test \
        --build-arg REACT_APP_BACKEND_URL=http://localhost:8001 \
        ./frontend
    if [ $? -eq 0 ]; then
        print_success "Frontend build completato"
    else
        print_error "Frontend build fallito"
        exit 1
    fi
fi

# Test 6: Verifica .env
echo ""
if [ ! -f ".env" ]; then
    echo "⚠️  File .env non trovato"
    read -p "Vuoi creare .env da template? (y/n): " create_env
    if [ "$create_env" = "y" ]; then
        cp .env.docker.example .env
        print_success ".env creato da template"
        echo "❗ IMPORTANTE: Modifica .env con le tue configurazioni"
    fi
else
    print_success ".env presente"
fi

echo ""
echo "✅ Tutti i test completati!"
echo ""
echo "🚀 Prossimi passi:"
echo "1. Configura .env con le tue credenziali database"
echo "2. Esegui: docker-compose build"
echo "3. Esegui: docker-compose up -d"
echo "4. Accedi a http://localhost:3000"
