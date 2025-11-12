# DDoS Simulator - Quick Reference Card

## 🚀 Inicio Rápido

### Comando Básico
```bash
sudo python3 ddos_simulator.py -t <IP> -a <TIPO_ATAQUE> -d <SEGUNDOS>
```

### Ejemplo Inmediato
```bash
# Test rápido de 30 segundos
sudo python3 ddos_simulator.py -t 192.168.1.100 -a syn_flood -d 30
```

---

## 📋 Tipos de Ataque (-a)

| Comando | Descripción | Capa OSI | Dificultad |
|---------|-------------|----------|------------|
| `udp_flood` | UDP Flood volumétrico | L3 | ⭐⭐ Media |
| `icmp_flood` | ICMP Flood (Ping of Death) | L3 | ⭐ Baja |
| `syn_flood` | SYN Flood (agota conexiones) | L4 | ⭐⭐⭐ Alta |
| `ack_flood` | ACK Flood (paquetes inválidos) | L4 | ⭐⭐ Media |
| `http_flood` | HTTP Flood (capa aplicación) | L7 | ⭐⭐⭐⭐ Muy Alta |
| `slowloris` | Slowloris (conexiones lentas) | L7 | ⭐⭐⭐⭐ Muy Alta |
| `dns_amp` | DNS Amplification | L7 | ⭐⭐⭐ Alta |
| `multi_vector` | Ataque combinado (el más difícil) | L3-L7 | ⭐⭐⭐⭐⭐ Extrema |

---

## ⚡ Intensidades (-i)

| Intensidad | PPS Aprox | Uso |
|------------|-----------|-----|
| `low` | 200-500 | Testing básico, no debe activar mitigación |
| `medium` | 1,000-2,000 | Testing normal, debe activar rate limiting |
| `high` | 3,000-5,000 | Testing intenso, mitigación completa |
| `extreme` | 6,000+ | Estrés máximo del sistema |

---

## 🎯 Comandos Más Comunes

### 1. Test de Validación Rápido
```bash
sudo python3 ddos_simulator.py -t 192.168.1.100 -a syn_flood -i medium -d 30
```
**Uso**: Verificar que el sistema detecta ataques básicos

### 2. Test de Estrés HTTP
```bash
sudo python3 ddos_simulator.py -t 192.168.1.100 -p 80 -a http_flood -i high -d 60
```
**Uso**: Probar protección de capa 7

### 3. Slowloris con Muchas Conexiones
```bash
sudo python3 ddos_simulator.py -t 192.168.1.100 -p 80 -a slowloris -c 500 -d 120
```
**Uso**: Probar connection tracking

### 4. UDP Flood Extremo
```bash
sudo python3 ddos_simulator.py -t 192.168.1.100 -a udp_flood -i extreme -d 60
```
**Uso**: Máximo stress volumétrico

### 5. Multi-Vector (El Más Completo)
```bash
sudo python3 ddos_simulator.py -t 192.168.1.100 -a multi_vector -d 180
```
**Uso**: Test definitivo, ataca todas las capas

---

## 🛠️ Parámetros Completos

```bash
sudo python3 ddos_simulator.py \
    -t <IP>              # Target IP (requerido)
    -p <PUERTO>          # Puerto (default: 80)
    -a <TIPO>            # Tipo de ataque (requerido)
    -d <SEGUNDOS>        # Duración (default: 60)
    -i <INTENSIDAD>      # low|medium|high|extreme (default: medium)
    -c <NUM>             # Conexiones para Slowloris (default: 200)
```

---

## 📊 Scripts Auxiliares

### Suite Automatizada
```bash
sudo ./run_test_suite.sh -t 192.168.1.100
```
**Ejecuta**: Suite completa de 8 tests con menú interactivo

### Ejemplos Guiados
```bash
sudo ./examples.sh
```
**Ejecuta**: 7 ejemplos pre-configurados con explicaciones

---

## ✅ Checklist Pre-Test

Antes de ejecutar cualquier test:

- [ ] **Autorización**: Tengo permiso para este test
- [ ] **Red aislada**: No estoy en red de producción
- [ ] **Backup**: Tengo backup de datos importantes
- [ ] **Monitoreo**: Puedo ver logs y métricas del objetivo
- [ ] **Comando de parada**: Sé que Ctrl+C detiene el ataque

---

## 🎓 Escenarios por Objetivo

### Validar Rate Limiting
```bash
# Bajo (no debe bloquear)
sudo python3 ddos_simulator.py -t 192.168.1.100 -a syn_flood -i low -d 30

# Alto (debe bloquear)
sudo python3 ddos_simulator.py -t 192.168.1.100 -a syn_flood -i extreme -d 30
```

### Probar Niveles de Mitigación
```bash
# 1. Activar nivel LOW en Thrall Defender
sudo python3 ddos_simulator.py -t 192.168.1.100 -a udp_flood -i high -d 60

# 2. Activar nivel AGGRESSIVE
sudo python3 ddos_simulator.py -t 192.168.1.100 -a udp_flood -i high -d 60

# Comparar resultados
```

### Validar Geo-Blocking
```bash
# Ataque con IPs aleatorias (simulan múltiples países)
sudo python3 ddos_simulator.py -t 192.168.1.100 -a http_flood -i high -d 90
```

### Test de Persistencia
```bash
# Ataque sostenido 5 minutos
sudo python3 ddos_simulator.py -t 192.168.1.100 -a multi_vector -d 300
```

---

## 📈 Qué Esperar en Thrall Defender

### Durante el Ataque

| Panel | Qué Buscar |
|-------|------------|
| **Dashboard** | Spike en gráfico de tráfico, contador de paquetes aumentando |
| **Alertas** | Nuevas alertas apareciendo, clasificadas por severidad |
| **DDoS** | Threat level elevándose (medium→high→critical) |
| **Firewall** | IPs bloqueándose, reglas iptables creándose |

### Métricas Clave

```
✓ Alertas generadas > 0
✓ Threat level ≥ medium
✓ IPs bloqueadas > 0
✓ Rate limiting activo
✓ Sistema sigue accesible
```

---

## 🐛 Troubleshooting Rápido

### "Script requiere privilegios root"
```bash
# Solución: Usar sudo
sudo python3 ddos_simulator.py ...
```

### "Scapy no está instalado"
```bash
pip install scapy
# O
sudo pip3 install scapy
```

### "Network is unreachable"
```bash
# Verificar conectividad
ping 192.168.1.100

# Verificar que estás en la misma red
ip addr show
```

### Tasas bajas de paquetes
```bash
# Aumentar intensidad
-i extreme

# O ejecutar múltiples instancias en paralelo
sudo python3 ddos_simulator.py -t IP -a syn_flood -i extreme -d 60 &
sudo python3 ddos_simulator.py -t IP -a udp_flood -i extreme -d 60 &
```

---

## ⏱️ Tiempos Recomendados

| Propósito | Duración |
|-----------|----------|
| Test rápido de validación | 20-30s |
| Test normal | 60s |
| Test de estrés | 120-300s |
| Test de persistencia | 300-600s |

---

## 🔥 Top 3 Tests Esenciales

### 1. Validación Básica (MUST RUN)
```bash
sudo python3 ddos_simulator.py -t 192.168.1.100 -a syn_flood -i medium -d 30
```

### 2. Prueba de Capa 7 (RECOMMENDED)
```bash
sudo python3 ddos_simulator.py -t 192.168.1.100 -a http_flood -i high -d 60
```

### 3. Test Definitivo (ADVANCED)
```bash
sudo python3 ddos_simulator.py -t 192.168.1.100 -a multi_vector -d 180
```

---

## 📞 Ayuda Adicional

- **Documentación completa**: Ver `README.md`
- **Ejemplos guiados**: Ejecutar `./examples.sh`
- **Suite automatizada**: Ejecutar `./run_test_suite.sh`

---

## ⚠️ Recordatorio Legal

**SOLO usar en:**
- ✅ Tu propia infraestructura
- ✅ Redes aisladas de testing
- ✅ Con autorización escrita

**NUNCA usar en:**
- ❌ Sistemas de terceros sin permiso
- ❌ Redes de producción
- ❌ Internet público

---

## 💡 Tips Pro

1. **Monitorear recursos**: Usa `htop` durante el test
2. **Logs en tiempo real**: `tail -f /var/log/syslog`
3. **Múltiples terminales**: Una para ataque, otra para monitoreo
4. **Anotar métricas**: Documenta PPS, alertas generadas, tiempo de respuesta
5. **Tests incrementales**: Empezar con low, subir gradualmente

---

**Versión**: 1.0
**Última actualización**: 2025-11-12
**Thrall Defender** - Professional Network Monitoring Tool
