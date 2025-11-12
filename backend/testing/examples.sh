#!/bin/bash

# Thrall Defender - DDoS Testing Examples
# Scripts de ejemplo para testing rápido

# CONFIGURACIÓN
TARGET="192.168.1.100"  # Cambiar a la IP de tu Thrall Defender
SIMULATOR="./ddos_simulator.py"

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${CYAN}Thrall Defender - Ejemplos de Testing DDoS${NC}\n"

# Verificar que se ejecuta con sudo
if [[ $EUID -ne 0 ]]; then
    echo -e "${RED}Error: Debe ejecutarse con sudo${NC}"
    exit 1
fi

# =============================================================================
# EJEMPLO 1: Test básico de validación
# =============================================================================
example_1() {
    echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}EJEMPLO 1: Test Básico de Validación (30 segundos)${NC}"
    echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}\n"

    echo "Este test valida que tu sistema detecta un ataque SYN flood básico."
    echo -e "Duración: 30 segundos\n"

    python3 $SIMULATOR -t $TARGET -a syn_flood -i medium -d 30 << EOF
sí
EOF

    echo -e "\n${CYAN}✓ Test completado${NC}"
    echo "Verifica en Thrall Defender:"
    echo "  - Panel de alertas debe mostrar alertas nuevas"
    echo "  - Panel DDoS debe mostrar threat level elevado"
    echo "  - Firewall debe haber bloqueado algunas IPs"
}

# =============================================================================
# EJEMPLO 2: Comparación de intensidades
# =============================================================================
example_2() {
    echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}EJEMPLO 2: Comparación de Intensidades${NC}"
    echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}\n"

    echo "Este ejemplo ejecuta 3 ataques UDP con diferentes intensidades."
    echo -e "Objetivo: Ver cómo responde el sistema a diferentes niveles de ataque.\n"

    # Low intensity
    echo -e "${CYAN}Test 1/3: Intensidad BAJA (20s)${NC}"
    python3 $SIMULATOR -t $TARGET -a udp_flood -i low -d 20 << EOF
sí
EOF

    echo -e "\n${YELLOW}Esperando 15 segundos...${NC}\n"
    sleep 15

    # Medium intensity
    echo -e "${CYAN}Test 2/3: Intensidad MEDIA (20s)${NC}"
    python3 $SIMULATOR -t $TARGET -a udp_flood -i medium -d 20 << EOF
sí
EOF

    echo -e "\n${YELLOW}Esperando 15 segundos...${NC}\n"
    sleep 15

    # High intensity
    echo -e "${CYAN}Test 3/3: Intensidad ALTA (20s)${NC}"
    python3 $SIMULATOR -t $TARGET -a udp_flood -i high -d 20 << EOF
sí
EOF

    echo -e "\n${CYAN}✓ Comparación completada${NC}"
    echo "Compara en Thrall Defender:"
    echo "  - Número de alertas generadas en cada fase"
    echo "  - Velocidad de respuesta del sistema"
    echo "  - Threshold de activación de la mitigación"
}

# =============================================================================
# EJEMPLO 3: Test de capa de aplicación
# =============================================================================
example_3() {
    echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}EJEMPLO 3: Ataque de Capa de Aplicación (HTTP Flood)${NC}"
    echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}\n"

    echo "HTTP Flood simula peticiones legítimas a nivel de aplicación."
    echo "Este tipo de ataque es más difícil de detectar y bloquear."
    echo -e "Duración: 60 segundos\n"

    python3 $SIMULATOR -t $TARGET -p 80 -a http_flood -i high -d 60 << EOF
sí
EOF

    echo -e "\n${CYAN}✓ Test completado${NC}"
    echo "Verifica:"
    echo "  - ¿El sistema detecta el patrón anómalo?"
    echo "  - ¿Las peticiones HTTP se clasifican como ataque?"
    echo "  - ¿El servidor web sigue respondiendo?"
}

# =============================================================================
# EJEMPLO 4: Slowloris - Ataque sigiloso
# =============================================================================
example_4() {
    echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}EJEMPLO 4: Slowloris - Ataque de Bajo Perfil${NC}"
    echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}\n"

    echo "Slowloris mantiene conexiones abiertas con bajo tráfico."
    echo "Es difícil de detectar porque parece tráfico legítimo lento."
    echo -e "Conexiones: 300 | Duración: 2 minutos\n"

    python3 $SIMULATOR -t $TARGET -p 80 -a slowloris -c 300 -d 120 << EOF
sí
EOF

    echo -e "\n${CYAN}✓ Test completado${NC}"
    echo "Verifica:"
    echo "  - ¿Connection tracking detecta el patrón?"
    echo "  - ¿El servidor agota su pool de conexiones?"
    echo "  - ¿Nuevas conexiones legítimas son posibles?"
}

# =============================================================================
# EJEMPLO 5: El test definitivo - Multi-Vector
# =============================================================================
example_5() {
    echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}EJEMPLO 5: Multi-Vector Attack - El Desafío Definitivo${NC}"
    echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}\n"

    echo -e "${YELLOW}⚠️  ADVERTENCIA: Este es el test más intenso${NC}"
    echo "Combina SYN Flood + UDP Flood + HTTP Flood simultáneamente."
    echo "Ataca múltiples capas del modelo OSI al mismo tiempo."
    echo -e "Duración: 2 minutos\n"

    echo -e "${YELLOW}¿Continuar con el test más intenso? (s/n): ${NC}"
    read -r confirm
    if [[ ! "$confirm" =~ ^[sS]$ ]]; then
        echo "Test cancelado."
        return
    fi

    python3 $SIMULATOR -t $TARGET -a multi_vector -d 120 << EOF
sí
EOF

    echo -e "\n${CYAN}✓ Test completado${NC}"
    echo "Este es el test más completo. Verifica:"
    echo "  - Threat level debe llegar a HIGH o CRITICAL"
    echo "  - Múltiples tipos de alertas generadas"
    echo "  - Sistema debe seguir siendo accesible"
    echo "  - Mitigación activa en múltiples niveles"
}

# =============================================================================
# EJEMPLO 6: Test de niveles de mitigación
# =============================================================================
example_6() {
    echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}EJEMPLO 6: Validar Niveles de Mitigación${NC}"
    echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}\n"

    echo "Este test te guiará para probar los diferentes niveles de mitigación."
    echo ""

    echo -e "${CYAN}PASO 1: Activa el nivel LOW en Thrall Defender${NC}"
    echo "  Panel DDoS → Mitigation Level → LOW"
    echo -e "Presiona Enter cuando esté listo..."
    read

    echo -e "\n${CYAN}Ejecutando ataque con nivel LOW...${NC}"
    python3 $SIMULATOR -t $TARGET -a syn_flood -i high -d 30 << EOF
sí
EOF

    echo -e "\n${YELLOW}Esperando 20 segundos...${NC}\n"
    sleep 20

    echo -e "${CYAN}PASO 2: Activa el nivel AGGRESSIVE en Thrall Defender${NC}"
    echo "  Panel DDoS → Mitigation Level → AGGRESSIVE"
    echo -e "Presiona Enter cuando esté listo..."
    read

    echo -e "\n${CYAN}Ejecutando mismo ataque con nivel AGGRESSIVE...${NC}"
    python3 $SIMULATOR -t $TARGET -a syn_flood -i high -d 30 << EOF
sí
EOF

    echo -e "\n${CYAN}✓ Test completado${NC}"
    echo "Compara los resultados:"
    echo "  - Nivel LOW: Mayor tolerancia, más tráfico pasa"
    echo "  - Nivel AGGRESSIVE: Bloqueo rápido y agresivo"
    echo "  - Revisa número de paquetes bloqueados en cada caso"
}

# =============================================================================
# EJEMPLO 7: Test de persistencia
# =============================================================================
example_7() {
    echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}EJEMPLO 7: Test de Persistencia (Ataque Prolongado)${NC}"
    echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}\n"

    echo "Ataque sostenido de 5 minutos para validar:"
    echo "  - Sistema mantiene protección en el tiempo"
    echo "  - No hay degradación de rendimiento"
    echo "  - Cleanup automático funciona correctamente"
    echo ""

    echo -e "${YELLOW}Este test durará 5 minutos. ¿Continuar? (s/n): ${NC}"
    read -r confirm
    if [[ ! "$confirm" =~ ^[sS]$ ]]; then
        echo "Test cancelado."
        return
    fi

    python3 $SIMULATOR -t $TARGET -a multi_vector -d 300 << EOF
sí
EOF

    echo -e "\n${CYAN}✓ Test completado${NC}"
    echo "Durante el ataque, deberías haber observado:"
    echo "  - Dashboard siempre accesible"
    echo "  - Alertas generándose continuamente"
    echo "  - Sistema respondiendo sin lag"
    echo "  - Uso de recursos (CPU/RAM) estable"
}

# =============================================================================
# MENÚ PRINCIPAL
# =============================================================================
show_menu() {
    echo -e "\n${CYAN}═══════════════════════════════════════════════════════════${NC}"
    echo -e "${CYAN}        EJEMPLOS DE TESTING - THRALL DEFENDER${NC}"
    echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}\n"

    echo "Selecciona un ejemplo para ejecutar:"
    echo ""
    echo "  1) Test Básico de Validación (30s) - Rápido"
    echo "  2) Comparación de Intensidades (3 tests)"
    echo "  3) HTTP Flood - Ataque Capa 7 (60s)"
    echo "  4) Slowloris - Ataque Sigiloso (2min)"
    echo "  5) Multi-Vector - Test Definitivo (2min)"
    echo "  6) Validar Niveles de Mitigación (guiado)"
    echo "  7) Test de Persistencia (5min)"
    echo ""
    echo "  8) Ejecutar TODOS los ejemplos secuencialmente"
    echo "  0) Salir"
    echo ""
    echo -e "${YELLOW}Opción: ${NC}"
}

run_all() {
    echo -e "${CYAN}Ejecutando TODOS los ejemplos...${NC}\n"
    example_1
    sleep 30
    example_2
    sleep 30
    example_3
    sleep 30
    example_4
    sleep 30
    example_5
    sleep 30
    example_6
    sleep 30
    example_7
    echo -e "\n${GREEN}✓ Todos los ejemplos completados${NC}"
}

# Script principal
main() {
    # Verificar configuración
    echo -e "${YELLOW}Target configurado: $TARGET${NC}"
    echo -e "${YELLOW}¿Es correcta esta IP? (s/n): ${NC}"
    read -r confirm
    if [[ ! "$confirm" =~ ^[sS]$ ]]; then
        echo "Edita la variable TARGET en este script con la IP correcta."
        exit 0
    fi

    while true; do
        show_menu
        read -r choice

        case $choice in
            1) example_1 ;;
            2) example_2 ;;
            3) example_3 ;;
            4) example_4 ;;
            5) example_5 ;;
            6) example_6 ;;
            7) example_7 ;;
            8) run_all ;;
            0)
                echo -e "${CYAN}Saliendo...${NC}"
                exit 0
                ;;
            *)
                echo -e "${RED}Opción inválida${NC}"
                ;;
        esac
    done
}

main
