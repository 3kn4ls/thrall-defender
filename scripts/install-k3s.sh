#!/bin/bash

# Thrall Defender - Script de Instalación Automática para k3s
# ============================================================

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
NAMESPACE="thrall-defender"
REGISTRY="docker.io"  # Change if using private registry

echo -e "${BLUE}╔════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   Thrall Defender - Instalación Automática k3s    ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════╝${NC}"
echo ""

# Function to print section headers
print_section() {
    echo -e "\n${BLUE}▶ $1${NC}"
    echo "─────────────────────────────────────────────────────"
}

# Function to print success
print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

# Function to print error
print_error() {
    echo -e "${RED}✗ $1${NC}"
}

# Function to print warning
print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

# Check if running on supported architecture
print_section "Verificando Sistema"
ARCH=$(uname -m)
echo "Arquitectura detectada: $ARCH"

if [[ "$ARCH" != "aarch64" && "$ARCH" != "arm64" && "$ARCH" != "x86_64" ]]; then
    print_error "Arquitectura no soportada: $ARCH"
    exit 1
fi
print_success "Arquitectura compatible"

# Check if k3s is installed
if ! command -v k3s &> /dev/null; then
    print_warning "k3s no está instalado"
    echo "Instalando k3s..."
    curl -sfL https://get.k3s.io | sh -

    # Wait for k3s to be ready
    echo "Esperando a que k3s esté listo..."
    sleep 10
    print_success "k3s instalado correctamente"
else
    print_success "k3s ya está instalado"
fi

# Check if kubectl works
if ! sudo k3s kubectl version &> /dev/null; then
    print_error "No se puede conectar con k3s"
    exit 1
fi

# Create namespace
print_section "Configurando Namespace"
if sudo k3s kubectl get namespace $NAMESPACE &> /dev/null; then
    print_warning "Namespace '$NAMESPACE' ya existe"
else
    sudo k3s kubectl create namespace $NAMESPACE
    print_success "Namespace '$NAMESPACE' creado"
fi

# Build Docker images
print_section "Construyendo Imágenes Docker"

# Check if Docker is available
if command -v docker &> /dev/null; then
    print_success "Docker encontrado"

    # Import images to k3s
    echo "Construyendo imagen del backend..."
    cd backend
    sudo docker build -t thrall-backend:latest .
    sudo docker save thrall-backend:latest | sudo k3s ctr images import -
    cd ..
    print_success "Imagen backend importada a k3s"

    echo "Construyendo imagen del frontend..."
    cd frontend
    sudo docker build -t thrall-frontend:latest .
    sudo docker save thrall-frontend:latest | sudo k3s ctr images import -
    cd ..
    print_success "Imagen frontend importada a k3s"
else
    print_warning "Docker no encontrado. Instalando Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    rm get-docker.sh
    print_success "Docker instalado"

    # Build images
    echo "Construyendo imágenes..."
    cd backend
    sudo docker build -t thrall-backend:latest .
    sudo docker save thrall-backend:latest | sudo k3s ctr images import -
    cd ../frontend
    sudo docker build -t thrall-frontend:latest .
    sudo docker save thrall-frontend:latest | sudo k3s ctr images import -
    cd ..
    print_success "Imágenes construidas e importadas"
fi

# Deploy backend
print_section "Desplegando Backend"
sudo k3s kubectl apply -f k8s/backend/deployment.yaml
sudo k3s kubectl apply -f k8s/backend/service.yaml
print_success "Backend desplegado"

# Deploy frontend
print_section "Desplegando Frontend"
sudo k3s kubectl apply -f k8s/frontend/deployment.yaml
sudo k3s kubectl apply -f k8s/frontend/service.yaml
print_success "Frontend desplegado"

# Deploy ingress
print_section "Configurando Ingress"
sudo k3s kubectl apply -f k8s/ingress.yaml
print_success "Ingress configurado"

# Wait for pods to be ready
print_section "Esperando a que los Pods estén listos"
echo "Esto puede tomar unos minutos..."

# Wait for backend
echo -n "Backend: "
sudo k3s kubectl wait --for=condition=ready pod -l app=thrall-backend -n $NAMESPACE --timeout=300s
print_success "Backend listo"

# Wait for frontend
echo -n "Frontend: "
sudo k3s kubectl wait --for=condition=ready pod -l app=thrall-frontend -n $NAMESPACE --timeout=300s
print_success "Frontend listo"

# Get node IP
print_section "Información de Acceso"
NODE_IP=$(hostname -I | awk '{print $1}')

echo ""
echo -e "${GREEN}╔════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║          ¡Instalación Completada! 🎉               ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BLUE}Accede a la aplicación en:${NC}"
echo -e "${GREEN}   http://${NODE_IP}/thrall-defender/${NC}"
echo ""
echo -e "${BLUE}Comandos útiles:${NC}"
echo "   Ver pods:    sudo k3s kubectl get pods -n $NAMESPACE"
echo "   Ver logs:    ./scripts/logs.sh"
echo "   Ver estado:  ./scripts/status.sh"
echo ""
echo -e "${YELLOW}Nota: Es recomendable configurar la lista blanca en 'Gestión de IPs'${NC}"
echo -e "${YELLOW}      antes de habilitar el auto-bloqueo del firewall.${NC}"
echo ""
