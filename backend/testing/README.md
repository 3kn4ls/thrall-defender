# DDoS Simulator - Testing Tool

## ⚠️ ADVERTENCIA LEGAL

**IMPORTANTE**: Esta herramienta está diseñada EXCLUSIVAMENTE para testing en entornos controlados y aislados. El uso de esta herramienta contra sistemas sin autorización expresa es **ILEGAL** y puede resultar en:

- Cargos criminales bajo leyes de ciberseguridad
- Responsabilidad civil por daños
- Multas significativas
- Penas de prisión

**Solo usar en:**
- Tu propia infraestructura de red
- Entornos de laboratorio aislados
- Con autorización escrita explícita
- Para propósitos educativos y de testing

---

## 📋 Descripción

Herramienta profesional de simulación de ataques DDoS diseñada para probar y validar sistemas de mitigación como Thrall Defender. Implementa múltiples vectores de ataque utilizados en ataques DDoS reales.

## 🎯 Tipos de Ataques Implementados

### 1. **UDP Flood** (Volumétrico)
Inunda el objetivo con paquetes UDP a puertos aleatorios.
- **Capa**: Network (L3)
- **Dificultad de mitigación**: Media
- **Consumo de ancho de banda**: Alto
- **Características**:
  - IPs de origen falsificadas (spoofing)
  - Puertos destino aleatorios
  - Payload variable (64-1024 bytes)
  - Alta tasa de paquetes por segundo

### 2. **ICMP Flood** (Ping of Death variant)
Envía paquetes ICMP de gran tamaño para agotar recursos.
- **Capa**: Network (L3)
- **Dificultad de mitigación**: Baja-Media
- **Características**:
  - Payloads grandes (1000-5000 bytes)
  - Puede fragmentar paquetes
  - IPs falsificadas

### 3. **SYN Flood** (Protocol Attack)
Ataque clásico de agotamiento de conexiones TCP.
- **Capa**: Transport (L4)
- **Dificultad de mitigación**: Media-Alta
- **Características**:
  - Envía SYN sin completar handshake
  - Agota tabla de conexiones
  - Puertos de origen aleatorios
  - Números de secuencia aleatorios

### 4. **ACK Flood** (Protocol Attack)
Inunda con paquetes ACK de conexiones inexistentes.
- **Capa**: Transport (L4)
- **Dificultad de mitigación**: Media
- **Características**:
  - Paquetes ACK inválidos
  - Fuerza procesamiento del stack TCP
  - IPs y puertos aleatorios

### 5. **HTTP Flood** (Application Layer)
Ataque de capa 7 con peticiones HTTP válidas.
- **Capa**: Application (L7)
- **Dificultad de mitigación**: Alta
- **Características**:
  - Peticiones HTTP GET/POST legítimas
  - User-Agents realistas
  - Múltiples paths objetivo
  - Difícil distinguir de tráfico legítimo

### 6. **Slowloris** (Application Layer)
Ataque de bajo ancho de banda pero muy efectivo.
- **Capa**: Application (L7)
- **Dificultad de mitigación**: Alta
- **Características**:
  - Mantiene conexiones abiertas
  - Bajo consumo de recursos del atacante
  - Headers HTTP parciales
  - Keep-alive periódico
  - Agota conexiones disponibles del servidor

### 7. **DNS Amplification** (Amplification Attack)
Simula ataque de amplificación DNS.
- **Capa**: Application (L7)
- **Dificultad de mitigación**: Media-Alta
- **Características**:
  - Amplificación de tráfico
  - Queries tipo ANY
  - IP de origen falsificada

### 8. **Multi-Vector Attack** (Avanzado)
Combina múltiples tipos de ataque simultáneamente.
- **Dificultad de mitigación**: Muy Alta
- **Características**:
  - SYN Flood + UDP Flood + HTTP Flood simultáneos
  - Dificulta la mitigación al atacar múltiples capas
  - Requiere estrategias de defensa coordinadas

---

## 🚀 Instalación

### Requisitos Previos

```bash
# Python 3.8 o superior
python3 --version

# Scapy (manipulación de paquetes)
pip install scapy
```

### Instalación

```bash
cd backend/testing
chmod +x ddos_simulator.py
```

---

## 💻 Uso

### Sintaxis General

```bash
sudo python3 ddos_simulator.py -t <TARGET_IP> -a <ATTACK_TYPE> [OPTIONS]
```

**Nota**: Requiere `sudo` para acceso a raw sockets.

### Parámetros

| Parámetro | Descripción | Valores | Default |
|-----------|-------------|---------|---------|
| `-t, --target` | IP objetivo (requerido) | IPv4 | - |
| `-p, --port` | Puerto objetivo | 1-65535 | 80 |
| `-a, --attack` | Tipo de ataque (requerido) | Ver tipos | - |
| `-d, --duration` | Duración en segundos | > 0 | 60 |
| `-i, --intensity` | Intensidad | low, medium, high, extreme | medium |
| `-c, --connections` | Conexiones (solo Slowloris) | > 0 | 200 |

### Tipos de Ataque (`-a`)

- `udp_flood` - UDP Flood
- `icmp_flood` - ICMP Flood
- `syn_flood` - SYN Flood
- `ack_flood` - ACK Flood
- `http_flood` - HTTP Flood
- `slowloris` - Slowloris Attack
- `dns_amp` - DNS Amplification
- `multi_vector` - Multi-Vector Attack

---

## 📖 Ejemplos de Uso

### 1. Test Básico - SYN Flood (30 segundos)

```bash
sudo python3 ddos_simulator.py \
    -t 192.168.1.100 \
    -a syn_flood \
    -d 30 \
    -i medium
```

### 2. UDP Flood Intenso (2 minutos)

```bash
sudo python3 ddos_simulator.py \
    -t 192.168.1.100 \
    -a udp_flood \
    -d 120 \
    -i extreme
```

### 3. HTTP Flood contra servidor web

```bash
sudo python3 ddos_simulator.py \
    -t 192.168.1.100 \
    -p 80 \
    -a http_flood \
    -d 60 \
    -i high
```

### 4. Slowloris con 500 conexiones

```bash
sudo python3 ddos_simulator.py \
    -t 192.168.1.100 \
    -p 80 \
    -a slowloris \
    -d 300 \
    -c 500
```

### 5. Multi-Vector Attack (el más desafiante)

```bash
sudo python3 ddos_simulator.py \
    -t 192.168.1.100 \
    -a multi_vector \
    -d 180
```

### 6. ICMP Flood de baja intensidad

```bash
sudo python3 ddos_simulator.py \
    -t 192.168.1.100 \
    -a icmp_flood \
    -d 45 \
    -i low
```

---

## 🧪 Escenarios de Testing

### Escenario 1: Validación de Rate Limiting

**Objetivo**: Verificar que el rate limiting funciona correctamente

```bash
# Paso 1: Ataque de baja intensidad (debe pasar)
sudo python3 ddos_simulator.py -t 192.168.1.100 -a syn_flood -i low -d 30

# Paso 2: Ataque de alta intensidad (debe bloquearse)
sudo python3 ddos_simulator.py -t 192.168.1.100 -a syn_flood -i extreme -d 30
```

**Validación en Thrall Defender**:
- El ataque de baja intensidad debe permitir tráfico (< threshold)
- El ataque de alta intensidad debe activar rate limiting
- Verificar alertas generadas
- Comprobar que IPs son bloqueadas temporalmente

### Escenario 2: Niveles de Mitigación

**Objetivo**: Probar los 4 niveles de mitigación (low, medium, high, aggressive)

```bash
# Con nivel LOW activo
sudo python3 ddos_simulator.py -t 192.168.1.100 -a udp_flood -i medium -d 60

# Cambiar a nivel HIGH en Thrall Defender

# Con nivel HIGH activo
sudo python3 ddos_simulator.py -t 192.168.1.100 -a udp_flood -i medium -d 60
```

**Validación**:
- Nivel LOW: Mayor tolerancia, menos bloqueos
- Nivel HIGH: Bloqueo más agresivo, threshold más bajo
- Comparar número de paquetes bloqueados

### Escenario 3: Geo-Blocking

**Objetivo**: Verificar bloqueo por país (si GeoIP está configurado)

```bash
# Ataque con IPs aleatorias (incluye países bloqueados)
sudo python3 ddos_simulator.py -t 192.168.1.100 -a http_flood -i high -d 60
```

**Validación**:
- Verificar en stats geo que se detectan países
- Si tienes países bloqueados configurados, validar bloqueos

### Escenario 4: Ataque Sostenido

**Objetivo**: Validar que el sistema mantiene la protección en el tiempo

```bash
# Ataque de 10 minutos
sudo python3 ddos_simulator.py -t 192.168.1.100 -a syn_flood -i high -d 600
```

**Validación**:
- Sistema debe mantener protección durante todo el ataque
- No debe haber degradación de rendimiento
- Cleanup debe funcionar (registros > 48h purgados)

### Escenario 5: Multi-Vector (Prueba Definitiva)

**Objetivo**: Probar capacidad de mitigación bajo ataque complejo

```bash
# Ataque multi-vector de 5 minutos
sudo python3 ddos_simulator.py -t 192.168.1.100 -a multi_vector -d 300
```

**Validación**:
- Sistema debe detectar múltiples tipos de ataque
- Dashboard debe mostrar threat level "high" o "critical"
- Mitigación debe activarse en múltiples capas
- Verificar que el servicio sigue respondiendo

### Escenario 6: Slowloris (Agotamiento de Conexiones)

**Objetivo**: Validar protección contra ataques de bajo perfil

```bash
# Slowloris con muchas conexiones
sudo python3 ddos_simulator.py -t 192.168.1.100 -p 80 -a slowloris -c 1000 -d 300
```

**Validación**:
- Sistema debe detectar conexiones anómalas
- Connection tracking debe identificar el patrón
- Servidor debe seguir aceptando conexiones legítimas

---

## 📊 Interpretación de Resultados

### Métricas del Simulador

Durante la ejecución, el simulador muestra:

```
[14:30:45] SYN FLOOD | Packets: 125,430 | Rate: 2,090 pps | Time: 60.0s
```

- **Packets**: Total de paquetes enviados
- **Rate (pps)**: Paquetes por segundo
- **Time**: Tiempo transcurrido

### Qué Verificar en Thrall Defender

1. **Dashboard Principal**:
   - Gráfico de tráfico debe mostrar spike
   - Contador de paquetes debe aumentar
   - Alertas activas debe incrementar

2. **Panel de Alertas**:
   - Deben aparecer alertas con severidad apropiada
   - Clasificación correcta del tipo de ataque
   - IP de origen (aunque sean falsificadas)
   - Análisis de paquetes sospechosos

3. **Panel DDoS**:
   - Threat level debe elevarse (medium/high/critical)
   - Contador de ataques activos debe aumentar
   - Stats geográficas deben actualizarse
   - Nivel de mitigación activo debe reflejarse

4. **Firewall/Blocking**:
   - IPs atacantes deben bloquearse
   - Reglas iptables deben crearse
   - Rate limiting debe aplicarse

5. **Rendimiento**:
   - Backend debe seguir respondiendo
   - Frontend debe mantenerse accesible
   - Base de datos no debe saturarse
   - CPU/Memoria en niveles aceptables

---

## 🛡️ Configuración Recomendada de Testing

### Red Aislada

```
┌─────────────────┐
│  Raspberry Pi   │
│ Thrall Defender │  IP: 192.168.100.1
└────────┬────────┘
         │
    ┌────┴────┐
    │ Switch  │  Red Aislada
    └────┬────┘  192.168.100.0/24
         │
┌────────┴────────┐
│   Test Machine  │
│  DDoS Simulator │  IP: 192.168.100.10
└─────────────────┘
```

**Importante**:
- Usar red física aislada o VLANs
- NO conectar a Internet durante tests
- NO apuntar a dispositivos en producción

### Máquina de Testing

**Especificaciones mínimas**:
- RAM: 2GB
- CPU: 2 cores
- OS: Linux (Ubuntu/Debian)
- Permisos: root/sudo

### Preparación del Objetivo (Thrall Defender)

1. Hacer backup de la base de datos
2. Asegurar que hay espacio en disco suficiente
3. Monitorear recursos del sistema:
   ```bash
   htop
   # O
   watch -n 1 "free -h && df -h"
   ```

4. Tener logs accesibles:
   ```bash
   tail -f /var/log/syslog
   ```

---

## 🔍 Troubleshooting

### Error: "Este script requiere privilegios root"

**Solución**: Ejecutar con `sudo`

```bash
sudo python3 ddos_simulator.py ...
```

### Error: "Scapy no está instalado"

**Solución**: Instalar Scapy

```bash
pip install scapy
# O con permisos root
sudo pip3 install scapy
```

### Error: "Network is unreachable"

**Causa**: IP objetivo no accesible

**Solución**:
1. Verificar conectividad:
   ```bash
   ping 192.168.1.100
   ```
2. Verificar que están en la misma red
3. Verificar firewall del host objetivo

### Warning: "Can't import packet sniffing module"

**Solución**: Instalar dependencias de Scapy

```bash
sudo apt-get install tcpdump
```

### El ataque no tiene efecto visible

**Posibles causas**:
1. **Intensidad muy baja**: Probar con `-i high` o `-i extreme`
2. **Duración muy corta**: Usar `-d 120` o más
3. **Target tiene protección previa**: Verificar firewall/iptables del objetivo
4. **Red limitando tráfico**: Puede haber limitaciones en switches/routers

### Tasas de paquetes bajas

**Optimización**:
1. Usar `multi_vector` para máximo impacto
2. Aumentar intensidad a `extreme`
3. Ejecutar múltiples instancias del script en paralelo:
   ```bash
   # Terminal 1
   sudo python3 ddos_simulator.py -t 192.168.1.100 -a syn_flood -i extreme -d 120 &

   # Terminal 2
   sudo python3 ddos_simulator.py -t 192.168.1.100 -a udp_flood -i extreme -d 120 &
   ```

---

## 📈 Intensidades y Rates Esperados

| Intensidad | UDP Flood | SYN Flood | HTTP Flood |
|------------|-----------|-----------|------------|
| **low** | ~200 pps | ~200 pps | ~100 pps |
| **medium** | ~1,000 pps | ~1,000 pps | ~400 pps |
| **high** | ~3,000 pps | ~3,000 pps | ~1,000 pps |
| **extreme** | ~6,000+ pps | ~6,000+ pps | ~2,000 pps |

*Nota: Los rates reales dependen del hardware y sistema operativo*

---

## 🎓 Conceptos de DDoS (Educativo)

### ¿Por qué son efectivos estos ataques?

1. **UDP Flood**: No requiere handshake, permite spoofing fácil
2. **SYN Flood**: Agota tabla de conexiones semi-abiertas
3. **HTTP Flood**: Difícil distinguir de tráfico legítimo
4. **Slowloris**: Bajo costo para atacante, alto impacto
5. **Multi-Vector**: Divide recursos de defensa

### Técnicas de Mitigación

1. **Rate Limiting**: Limitar pps por IP
2. **SYN Cookies**: Validar handshake sin estado
3. **Challenge-Response**: CAPTCHA, JS challenge
4. **Geo-Blocking**: Bloquear países sospechosos
5. **Pattern Detection**: Identificar comportamiento anómalo
6. **Connection Tracking**: Detectar conexiones lentas

---

## 🔐 Mejores Prácticas de Seguridad

1. ✅ **Siempre** obtener autorización por escrito
2. ✅ **Siempre** usar en redes aisladas
3. ✅ **Nunca** ejecutar contra infraestructura ajena
4. ✅ **Documentar** todos los tests realizados
5. ✅ **Notificar** al equipo sobre tests planificados
6. ✅ **Monitorear** el sistema objetivo durante tests
7. ✅ **Tener plan** de rollback si algo falla

---

## 📝 Checklist de Testing

Antes de cada test:
- [ ] Tengo autorización para este test
- [ ] La red está aislada
- [ ] Tengo backup de datos críticos
- [ ] Estoy monitoreando recursos del sistema
- [ ] Sé cómo detener el ataque (Ctrl+C)
- [ ] Tengo logs accesibles para análisis

Durante el test:
- [ ] Monitoreo CPU/RAM del objetivo
- [ ] Reviso logs en tiempo real
- [ ] Observo dashboard de Thrall Defender
- [ ] Anoto métricas relevantes
- [ ] Verifico que alertas se generan

Después del test:
- [ ] Analizo resultados en Thrall Defender
- [ ] Verifico que reglas de firewall se crearon
- [ ] Confirmo que bloqueos funcionaron
- [ ] Documento hallazgos
- [ ] Limpio reglas temporales si es necesario

---

## 🤝 Soporte

Para reportar issues o sugerencias sobre el simulador, contacta al desarrollador del proyecto Thrall Defender.

---

## 📄 Licencia

Este software es solo para propósitos educativos y de testing. El autor no se hace responsable del uso indebido de esta herramienta.

**USE AT YOUR OWN RISK - TESTING ONLY**
