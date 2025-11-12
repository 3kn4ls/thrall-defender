#!/bin/bash

# Thrall Defender - DDoS Testing Suite Runner
# Ejecuta una suite completa de tests para validar el sistema de mitigación

set -e

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color
BOLD='\033[1m'

# Variables
TARGET_IP=""
TEST_DURATION=60
WAIT_BETWEEN_TESTS=30

# Banner
print_banner() {
    echo -e "${CYAN}${BOLD}"
    cat << "EOF"
╔══════════════════════════════════════════════════════════════╗
║          THRALL DEFENDER - DDoS TEST SUITE                   ║
║              Automated Testing Framework                     ║
╚══════════════════════════════════════════════════════════════╝
EOF
    echo -e "${NC}"
}

# Funciones de utilidad
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[✓]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

print_error() {
    echo -e "${RED}[✗]${NC} $1"
}

print_test_header() {
    echo -e "\n${MAGENTA}${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${MAGENTA}${BOLD} TEST $1: $2${NC}"
    echo -e "${MAGENTA}${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"
}

# Verificar privilegios root
check_root() {
    if [[ $EUID -ne 0 ]]; then
        print_error "Este script debe ejecutarse con privilegios root (sudo)"
        exit 1
    fi
    print_success "Privilegios root verificados"
}

# Verificar dependencias
check_dependencies() {
    print_info "Verificando dependencias..."

    if ! command -v python3 &> /dev/null; then
        print_error "Python3 no está instalado"
        exit 1
    fi

    if ! python3 -c "import scapy" &> /dev/null; then
        print_error "Scapy no está instalado. Ejecuta: pip install scapy"
        exit 1
    fi

    if [ ! -f "ddos_simulator.py" ]; then
        print_error "ddos_simulator.py no encontrado en el directorio actual"
        exit 1
    fi

    print_success "Todas las dependencias están instaladas"
}

# Verificar conectividad
check_connectivity() {
    print_info "Verificando conectividad con $TARGET_IP..."

    if ping -c 1 -W 2 "$TARGET_IP" &> /dev/null; then
        print_success "Target alcanzable: $TARGET_IP"
    else
        print_warning "No se puede hacer ping a $TARGET_IP (puede estar bloqueando ICMP)"
        echo -e "${YELLOW}¿Continuar de todas formas? (s/n):${NC} "
        read -r response
        if [[ ! "$response" =~ ^[sS]$ ]]; then
            exit 0
        fi
    fi
}

# Esperar entre tests
wait_between_tests() {
    local seconds=$1
    print_info "Esperando ${seconds}s antes del siguiente test..."
    for ((i=seconds; i>0; i--)); do
        echo -ne "${CYAN}\rTiempo restante: ${i}s ${NC}"
        sleep 1
    done
    echo -e "\n"
}

# Ejecutar test individual
run_test() {
    local test_num=$1
    local test_name=$2
    local attack_type=$3
    local intensity=$4
    local duration=$5
    local extra_args=$6

    print_test_header "$test_num" "$test_name"
    print_info "Tipo: $attack_type | Intensidad: $intensity | Duración: ${duration}s"

    echo -e "${YELLOW}Iniciando en 3 segundos...${NC}"
    sleep 3

    # Ejecutar test
    python3 ddos_simulator.py \
        -t "$TARGET_IP" \
        -a "$attack_type" \
        -i "$intensity" \
        -d "$duration" \
        $extra_args << EOF
sí
EOF

    print_success "Test $test_num completado"

    # Esperar entre tests (excepto el último)
    if [ "$test_num" != "8" ]; then
        wait_between_tests "$WAIT_BETWEEN_TESTS"
    fi
}

# Suite de tests completa
run_full_suite() {
    print_info "${BOLD}Iniciando suite completa de tests${NC}"
    print_info "Target: $TARGET_IP"
    print_info "Duración por test: ${TEST_DURATION}s"
    print_info "Espera entre tests: ${WAIT_BETWEEN_TESTS}s"

    local total_time=$((TEST_DURATION * 8 + WAIT_BETWEEN_TESTS * 7))
    print_warning "Tiempo total estimado: ~$((total_time / 60)) minutos"

    echo -e "\n${YELLOW}${BOLD}¿Iniciar suite completa? (sí/no):${NC} "
    read -r response
    if [[ ! "$response" =~ ^[sS][iíÍ]$ ]]; then
        print_info "Suite cancelada"
        exit 0
    fi

    # Test 1: UDP Flood (Medium)
    run_test "1" "UDP Flood - Ataque Volumétrico Básico" "udp_flood" "medium" "$TEST_DURATION"

    # Test 2: SYN Flood (High)
    run_test "2" "SYN Flood - Agotamiento de Conexiones" "syn_flood" "high" "$TEST_DURATION"

    # Test 3: HTTP Flood (Medium)
    run_test "3" "HTTP Flood - Ataque Capa 7" "http_flood" "medium" "$TEST_DURATION"

    # Test 4: ICMP Flood (Low)
    run_test "4" "ICMP Flood - Ping of Death" "icmp_flood" "low" "$TEST_DURATION"

    # Test 5: ACK Flood (Medium)
    run_test "5" "ACK Flood - Paquetes Inválidos" "ack_flood" "medium" "$TEST_DURATION"

    # Test 6: Slowloris (300 conexiones)
    run_test "6" "Slowloris - Agotamiento de Conexiones Lento" "slowloris" "" "$TEST_DURATION" "-c 300"

    # Test 7: UDP Flood (Extreme)
    run_test "7" "UDP Flood - Intensidad Extrema" "udp_flood" "extreme" "$TEST_DURATION"

    # Test 8: Multi-Vector (El más difícil)
    run_test "8" "Multi-Vector - Ataque Combinado" "multi_vector" "" "$TEST_DURATION"
}

# Test rápido
run_quick_test() {
    print_info "Ejecutando test rápido (30s cada uno)..."

    # Test 1: SYN Flood
    run_test "1" "SYN Flood Rápido" "syn_flood" "medium" "30"

    # Test 2: HTTP Flood
    wait_between_tests 15
    run_test "2" "HTTP Flood Rápido" "http_flood" "medium" "30"

    print_success "Test rápido completado"
}

# Test de estrés
run_stress_test() {
    print_warning "TEST DE ESTRÉS - Ataque sostenido de alta intensidad"
    print_info "Duración: 5 minutos"

    echo -e "${YELLOW}${BOLD}Este test es muy intenso. ¿Continuar? (sí/no):${NC} "
    read -r response
    if [[ ! "$response" =~ ^[sS][iíÍ]$ ]]; then
        print_info "Test cancelado"
        exit 0
    fi

    run_test "STRESS" "Multi-Vector Sostenido" "multi_vector" "" "300"

    print_success "Test de estrés completado"
}

# Test de validación de mitigación
run_mitigation_validation() {
    print_info "Test de Validación de Mitigación"
    print_warning "Este test verifica que la mitigación se activa correctamente"

    # Fase 1: Ataque bajo (no debe activar mitigación)
    print_test_header "FASE 1" "Ataque de Baja Intensidad"
    print_info "Objetivo: Verificar que el tráfico normal no se bloquea"
    run_test "1" "Tráfico Normal" "syn_flood" "low" "30"

    # Fase 2: Ataque alto (debe activar mitigación)
    wait_between_tests 20
    print_test_header "FASE 2" "Ataque de Alta Intensidad"
    print_info "Objetivo: Verificar que la mitigación se activa"
    run_test "2" "Ataque DDoS Real" "multi_vector" "" "60"

    print_success "Validación completada"
    echo -e "\n${CYAN}Verifica en Thrall Defender:${NC}"
    echo "  - Fase 1: Sin alertas críticas"
    echo "  - Fase 2: Alertas críticas y mitigación activa"
}

# Menú interactivo
show_menu() {
    echo -e "${CYAN}${BOLD}Selecciona el tipo de test:${NC}\n"
    echo "  1) Suite Completa (8 tests, ~40 minutos)"
    echo "  2) Test Rápido (2 tests, ~1 minuto)"
    echo "  3) Test de Estrés (1 test intenso, 5 minutos)"
    echo "  4) Validación de Mitigación (2 fases)"
    echo "  5) Test Individual (seleccionar manualmente)"
    echo "  0) Salir"
    echo -e "\n${YELLOW}Opción:${NC} "
}

# Test individual
run_individual_test() {
    echo -e "\n${CYAN}${BOLD}Selecciona el tipo de ataque:${NC}\n"
    echo "  1) UDP Flood"
    echo "  2) ICMP Flood"
    echo "  3) SYN Flood"
    echo "  4) ACK Flood"
    echo "  5) HTTP Flood"
    echo "  6) Slowloris"
    echo "  7) DNS Amplification"
    echo "  8) Multi-Vector"
    echo -e "\n${YELLOW}Opción:${NC} "
    read -r attack_choice

    case $attack_choice in
        1) attack_type="udp_flood" ;;
        2) attack_type="icmp_flood" ;;
        3) attack_type="syn_flood" ;;
        4) attack_type="ack_flood" ;;
        5) attack_type="http_flood" ;;
        6) attack_type="slowloris" ;;
        7) attack_type="dns_amp" ;;
        8) attack_type="multi_vector" ;;
        *) print_error "Opción inválida"; return ;;
    esac

    if [ "$attack_type" != "multi_vector" ] && [ "$attack_type" != "slowloris" ]; then
        echo -e "\n${CYAN}Intensidad (low/medium/high/extreme):${NC} "
        read -r intensity
        intensity=${intensity:-medium}
    else
        intensity=""
    fi

    echo -e "${CYAN}Duración en segundos (default: 60):${NC} "
    read -r duration
    duration=${duration:-60}

    run_test "INDIVIDUAL" "$attack_type" "$attack_type" "$intensity" "$duration"
}

# Main
main() {
    print_banner

    # Verificaciones previas
    check_root
    check_dependencies

    # Solicitar IP objetivo si no se proporcionó
    if [ -z "$TARGET_IP" ]; then
        echo -e "${YELLOW}IP del objetivo (Thrall Defender):${NC} "
        read -r TARGET_IP
    fi

    if [ -z "$TARGET_IP" ]; then
        print_error "Debe especificar una IP objetivo"
        exit 1
    fi

    check_connectivity

    # Mostrar menú
    while true; do
        show_menu
        read -r choice

        case $choice in
            1)
                run_full_suite
                break
                ;;
            2)
                run_quick_test
                break
                ;;
            3)
                run_stress_test
                break
                ;;
            4)
                run_mitigation_validation
                break
                ;;
            5)
                run_individual_test
                break
                ;;
            0)
                print_info "Saliendo..."
                exit 0
                ;;
            *)
                print_error "Opción inválida"
                ;;
        esac
    done

    # Resumen final
    echo -e "\n${GREEN}${BOLD}╔══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}${BOLD}║                   TESTING COMPLETADO                         ║${NC}"
    echo -e "${GREEN}${BOLD}╚══════════════════════════════════════════════════════════════╝${NC}\n"

    echo -e "${CYAN}Próximos pasos:${NC}"
    echo "  1. Revisar el dashboard de Thrall Defender"
    echo "  2. Analizar las alertas generadas"
    echo "  3. Verificar que la mitigación funcionó correctamente"
    echo "  4. Revisar logs del sistema"
    echo "  5. Validar reglas de firewall creadas"
    echo ""
    print_info "Para más información, ver: README.md"
}

# Parsear argumentos
while [[ $# -gt 0 ]]; do
    case $1 in
        -t|--target)
            TARGET_IP="$2"
            shift 2
            ;;
        -d|--duration)
            TEST_DURATION="$2"
            shift 2
            ;;
        -w|--wait)
            WAIT_BETWEEN_TESTS="$2"
            shift 2
            ;;
        -h|--help)
            echo "Uso: $0 [-t TARGET_IP] [-d DURATION] [-w WAIT_TIME]"
            echo ""
            echo "Opciones:"
            echo "  -t, --target       IP del objetivo"
            echo "  -d, --duration     Duración de cada test en segundos (default: 60)"
            echo "  -w, --wait         Tiempo de espera entre tests (default: 30)"
            echo "  -h, --help         Mostrar esta ayuda"
            exit 0
            ;;
        *)
            print_error "Opción desconocida: $1"
            exit 1
            ;;
    esac
done

main
