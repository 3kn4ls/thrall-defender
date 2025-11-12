#!/bin/bash

# Thrall Defender - K3s Deployment Script
# Compila las imágenes Docker y las actualiza en el cluster K3s

set -e

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color
BOLD='\033[1m'

# Variables
NAMESPACE="thrall-defender"
BACKEND_IMAGE="thrall-backend:latest"
FRONTEND_IMAGE="thrall-frontend:latest"
TEMP_DIR="/tmp/thrall-images"

# Funciones de utilidad
print_banner() {
    echo -e "${CYAN}${BOLD}"
    cat << "EOF"
╔══════════════════════════════════════════════════════════════╗
║          THRALL DEFENDER - K3s Deployment Script             ║
║               Build & Update Cluster Images                  ║
╚══════════════════════════════════════════════════════════════╝
EOF
    echo -e "${NC}\n"
}

print_step() {
    echo -e "\n${BLUE}${BOLD}▶ $1${NC}"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC}  $1"
}

print_info() {
    echo -e "${CYAN}ℹ${NC}  $1"
}

# Verificar que kubectl está instalado
check_kubectl() {
    if ! command -v kubectl &> /dev/null; then
        print_error "kubectl no está instalado"
        exit 1
    fi
    print_success "kubectl encontrado"
}

# Verificar que k3s está corriendo
check_k3s() {
    if ! command -v k3s &> /dev/null; then
        print_error "k3s no está instalado"
        exit 1
    fi

    if ! systemctl is-active --quiet k3s; then
        print_error "k3s no está corriendo"
        print_info "Ejecuta: sudo systemctl start k3s"
        exit 1
    fi

    print_success "k3s está corriendo"
}

# Verificar que docker está instalado
check_docker() {
    if ! command -v docker &> /dev/null; then
        print_error "Docker no está instalado"
        exit 1
    fi
    print_success "Docker encontrado"
}

# Verificar que el namespace existe
check_namespace() {
    if ! kubectl get namespace "$NAMESPACE" &> /dev/null; then
        print_warning "Namespace $NAMESPACE no existe, creándolo..."
        kubectl create namespace "$NAMESPACE"
        print_success "Namespace $NAMESPACE creado"
    else
        print_success "Namespace $NAMESPACE existe"
    fi
}

# Compilar imagen del backend
build_backend() {
    print_step "Compilando imagen del backend..."

    if [ ! -f "backend/Dockerfile" ]; then
        print_error "backend/Dockerfile no encontrado"
        exit 1
    fi

    echo -e "${CYAN}Building: $BACKEND_IMAGE${NC}"
    docker build -t "$BACKEND_IMAGE" ./backend

    print_success "Imagen del backend compilada: $BACKEND_IMAGE"
}

# Compilar imagen del frontend
build_frontend() {
    print_step "Compilando imagen del frontend..."

    if [ ! -f "frontend/Dockerfile" ]; then
        print_error "frontend/Dockerfile no encontrado"
        exit 1
    fi

    echo -e "${CYAN}Building: $FRONTEND_IMAGE${NC}"
    docker build -t "$FRONTEND_IMAGE" ./frontend

    print_success "Imagen del frontend compilada: $FRONTEND_IMAGE"
}

# Exportar e importar imagen al containerd de k3s
import_to_k3s() {
    local image=$1
    local image_file="${image//:/-}.tar"

    print_step "Importando $image a k3s..."

    # Crear directorio temporal si no existe
    mkdir -p "$TEMP_DIR"

    # Exportar imagen de docker
    echo -e "${CYAN}Exportando imagen de Docker...${NC}"
    docker save -o "$TEMP_DIR/$image_file" "$image"
    print_success "Imagen exportada: $TEMP_DIR/$image_file"

    # Importar imagen a k3s containerd
    echo -e "${CYAN}Importando imagen a k3s containerd...${NC}"
    k3s ctr images import "$TEMP_DIR/$image_file"
    print_success "Imagen importada a k3s: $image"

    # Limpiar archivo temporal
    rm -f "$TEMP_DIR/$image_file"
}

# Reiniciar deployment para usar la nueva imagen
restart_deployment() {
    local deployment=$1

    print_step "Reiniciando deployment: $deployment..."

    kubectl rollout restart deployment "$deployment" -n "$NAMESPACE"

    echo -e "${CYAN}Esperando que el deployment esté listo...${NC}"
    kubectl rollout status deployment "$deployment" -n "$NAMESPACE" --timeout=120s

    print_success "Deployment $deployment reiniciado correctamente"
}

# Mostrar estado del cluster
show_status() {
    print_step "Estado del cluster"

    echo -e "\n${BOLD}Pods:${NC}"
    kubectl get pods -n "$NAMESPACE" -o wide

    echo -e "\n${BOLD}Services:${NC}"
    kubectl get services -n "$NAMESPACE"

    echo -e "\n${BOLD}Deployments:${NC}"
    kubectl get deployments -n "$NAMESPACE"
}

# Limpiar recursos temporales
cleanup() {
    if [ -d "$TEMP_DIR" ]; then
        rm -rf "$TEMP_DIR"
    fi
}

# Verificar si se deben compilar componentes específicos
COMPILE_BACKEND=true
COMPILE_FRONTEND=true

while [[ $# -gt 0 ]]; do
    case $1 in
        -b|--backend-only)
            COMPILE_FRONTEND=false
            shift
            ;;
        -f|--frontend-only)
            COMPILE_BACKEND=false
            shift
            ;;
        -s|--skip-build)
            COMPILE_BACKEND=false
            COMPILE_FRONTEND=false
            shift
            ;;
        -h|--help)
            echo "Uso: $0 [OPCIONES]"
            echo ""
            echo "Opciones:"
            echo "  -b, --backend-only    Solo compilar y actualizar backend"
            echo "  -f, --frontend-only   Solo compilar y actualizar frontend"
            echo "  -s, --skip-build      Saltar compilación (solo reiniciar deployments)"
            echo "  -h, --help            Mostrar esta ayuda"
            echo ""
            echo "Ejemplos:"
            echo "  $0                    # Compilar y actualizar todo"
            echo "  $0 -b                 # Solo backend"
            echo "  $0 -f                 # Solo frontend"
            echo "  $0 -s                 # Solo reiniciar deployments"
            exit 0
            ;;
        *)
            print_error "Opción desconocida: $1"
            echo "Usa -h o --help para ver las opciones disponibles"
            exit 1
            ;;
    esac
done

# Main
main() {
    print_banner

    # Verificaciones previas
    print_step "Verificando requisitos..."
    check_docker
    check_kubectl
    check_k3s
    check_namespace

    # Timestamp de inicio
    START_TIME=$(date +%s)

    # Compilar e importar backend
    if [ "$COMPILE_BACKEND" = true ]; then
        build_backend
        import_to_k3s "$BACKEND_IMAGE"
        restart_deployment "thrall-backend"
    else
        print_info "Saltando compilación del backend"
    fi

    # Compilar e importar frontend
    if [ "$COMPILE_FRONTEND" = true ]; then
        build_frontend
        import_to_k3s "$FRONTEND_IMAGE"
        restart_deployment "thrall-frontend"
    else
        print_info "Saltando compilación del frontend"
    fi

    # Si se saltó la compilación pero se quiere reiniciar
    if [ "$COMPILE_BACKEND" = false ] && [ "$COMPILE_FRONTEND" = false ]; then
        print_warning "Modo skip-build: Reiniciando deployments sin compilar..."
        restart_deployment "thrall-backend"
        restart_deployment "thrall-frontend"
    fi

    # Limpiar temporales
    cleanup

    # Calcular tiempo transcurrido
    END_TIME=$(date +%s)
    ELAPSED=$((END_TIME - START_TIME))

    # Mostrar estado final
    show_status

    # Resumen
    echo -e "\n${GREEN}${BOLD}╔══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}${BOLD}║              DEPLOYMENT COMPLETADO EXITOSAMENTE              ║${NC}"
    echo -e "${GREEN}${BOLD}╚══════════════════════════════════════════════════════════════╝${NC}\n"

    echo -e "${CYAN}Tiempo total: ${BOLD}${ELAPSED}s${NC}"

    if [ "$COMPILE_BACKEND" = true ]; then
        echo -e "${GREEN}✓${NC} Backend compilado e importado: $BACKEND_IMAGE"
    fi

    if [ "$COMPILE_FRONTEND" = true ]; then
        echo -e "${GREEN}✓${NC} Frontend compilado e importado: $FRONTEND_IMAGE"
    fi

    echo -e "\n${CYAN}Próximos pasos:${NC}"
    echo "  • Verificar que los pods están corriendo:"
    echo "    ${YELLOW}kubectl get pods -n $NAMESPACE${NC}"
    echo ""
    echo "  • Ver logs del backend:"
    echo "    ${YELLOW}kubectl logs -f -n $NAMESPACE deployment/thrall-backend${NC}"
    echo ""
    echo "  • Ver logs del frontend:"
    echo "    ${YELLOW}kubectl logs -f -n $NAMESPACE deployment/thrall-frontend${NC}"
    echo ""
    echo "  • Acceder a la aplicación:"
    echo "    ${YELLOW}http://<IP-RASPBERRY>/${NC}"
    echo ""
}

# Trap para limpiar en caso de error
trap cleanup EXIT

# Verificar que se ejecuta desde la raíz del proyecto
if [ ! -d "backend" ] || [ ! -d "frontend" ] || [ ! -d "k8s" ]; then
    print_error "Este script debe ejecutarse desde la raíz del proyecto"
    print_info "Cambia al directorio del proyecto y ejecuta: ./deploy-k3s.sh"
    exit 1
fi

# Ejecutar
main
