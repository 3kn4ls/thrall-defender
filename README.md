# Thrall Defender - Network Traffic Monitor

Herramienta de monitorización de tráfico de red en tiempo real para detectar accesos no autorizados y analizar el tráfico en puertos expuestos.

## 🏗️ Arquitectura

- **Backend**: Python + FastAPI + Scapy (captura de tráfico)
- **Frontend**: Angular 19 + Material Design + PWA
- **Base de datos**: SQLite con soporte async
- **Despliegue**: Kubernetes (k3s) en Raspberry Pi 5
- **Acceso**: `/thrall-defender/` path con Ingress

## 📁 Estructura del Proyecto

```
thrall-defender/
├── backend/              # Servicio Python FastAPI
│   ├── app/             # Código de la aplicación
│   ├── Dockerfile       # Imagen Docker del backend
│   └── requirements.txt # Dependencias Python
├── frontend/            # Aplicación Angular 19
│   ├── src/            # Código fuente
│   ├── Dockerfile      # Imagen Docker del frontend
│   └── package.json    # Dependencias npm
├── k8s/                # Manifiestos Kubernetes
│   ├── namespace.yaml
│   ├── backend/        # Recursos del backend
│   └── frontend/       # Recursos del frontend
└── docs/               # Documentación
    └── deployment.md   # Guía de despliegue
```

## 🚀 Características

### Monitorización
- ✅ Captura de tráfico en tiempo real
- ✅ Monitorización de puertos específicos
- ✅ Detección automática de IPs sospechosas
- ✅ Dashboard en tiempo real con WebSockets
- ✅ Filtrado por protocolo, puerto e IP
- ✅ Estadísticas y gráficos históricos

### Firewall y Bloqueo
- 🔥 **Bloqueo activo de IPs** con iptables
- 🔥 **Auto-bloqueo** de IPs en lista negra
- 🔥 **Auto-bloqueo por alertas** (configurable)
- 🔥 **Bloqueos temporales** con expiración automática
- 🔥 **Protección de whitelist** (IPs nunca se bloquean)
- 🔥 **Logs completos** de todas las acciones del firewall
- 🔥 **Políticas configurables** de bloqueo automático

### Protección DDoS
- 🛡️ **Detección en tiempo real** de ataques DDoS
- 🛡️ **Múltiples tipos de ataque**: SYN flood, UDP flood, ICMP flood, tráfico alto
- 🛡️ **Análisis de métricas** por IP: paquetes/s, SYN/s, UDP/s, ICMP/s
- 🛡️ **Umbrales configurables** para cada tipo de ataque
- 🛡️ **Severidad automática** basada en intensidad del ataque (low, medium, high, critical)
- 🛡️ **Mitigación automática** con rate limiting de iptables (módulo hashlimit)
- 🛡️ **Dashboard específico** con ataques activos y métricas en tiempo real
- 🛡️ **Historial completo** de ataques con estadísticas

### Alertas y Gestión
- ✅ Sistema de alertas con niveles de severidad
- ✅ Lista blanca/negra de IPs
- ✅ Configuración completa desde la interfaz web
- ✅ Exportar/importar configuración

### Interfaz y Experiencia
- 📱 **Progressive Web App (PWA)** - Instalable en cualquier dispositivo
- 📱 **Diseño Responsive** - Optimizado para móviles, tablets y escritorio
- 📱 **Modo Offline** - Service Worker con caché inteligente
- 📱 **Configuración Web** - Todo configurable desde la interfaz
- 📱 **Interfaz Amigable** - Material Design con temas personalizables
- ✅ Gestión visual de firewall desde el dashboard
- ✅ Detección de port scanning

## 📦 Despliegue Rápido

### Instalación Automática en Raspberry Pi 5 + k3s

```bash
# 1. Clonar el repositorio
git clone https://github.com/3kn4ls/thrall-defender.git
cd thrall-defender

# 2. Ejecutar el script de instalación
chmod +x scripts/install-k3s.sh
./scripts/install-k3s.sh

# 3. Acceder a la aplicación
# http://<IP-de-tu-Raspberry>/thrall-defender/
```

**📖 Guía Completa**: Ver [docs/INSTALACION_K3S.md](./docs/INSTALACION_K3S.md) para instrucciones paso a paso

### Otros Métodos de Despliegue

- **Docker Compose**: Ver [QUICKSTART.md](./QUICKSTART.md)
- **Desarrollo Local**: Ver [QUICKSTART.md](./QUICKSTART.md#opción-3-desarrollo-local-sin-docker)

## 🔐 Seguridad

La herramienta captura paquetes en modo promiscuo y gestiona reglas de firewall iptables, por lo que requiere privilegios elevados (capabilities NET_ADMIN y NET_RAW en Kubernetes).

### Bloqueo Automático

Thrall Defender puede bloquear automáticamente IPs maliciosas usando iptables:

1. **Bloqueo por Lista Negra**: IPs añadidas a la blacklist se bloquean automáticamente
2. **Bloqueo por Alertas**: IPs que generan múltiples alertas críticas se bloquean automáticamente
3. **Bloqueos Temporales**: Configura duración de bloqueos (permanentes o temporales)
4. **Whitelist Protegida**: IPs en whitelist nunca se bloquean (protección contra auto-bloqueo)

### Protección contra DDoS

El módulo de protección DDoS detecta y mitiga ataques en tiempo real:

#### Tipos de Ataques Detectados:
- **SYN Flood**: Detecta exceso de paquetes SYN/s
- **UDP Flood**: Detecta tráfico UDP anómalo
- **ICMP Flood**: Detecta ping floods
- **Tráfico Alto**: Detecta volumen anormal de paquetes/s

#### Configuración:
- **Umbrales Personalizables**: Define límites para cada tipo de ataque
- **Mitigación Automática**: Aplica rate limiting automáticamente cuando se detecta un ataque
- **Duración de Mitigación**: Configura cuánto tiempo aplicar las restricciones (60-86400 segundos)

#### Dashboard DDoS:
1. **Ataques Activos**: Visualiza ataques en curso con severidad y métricas
2. **Top Atacantes**: IPs con más tráfico en tiempo real
3. **Configuración**: Ajusta umbrales y políticas de mitigación desde la interfaz

## 📝 Licencia

MIT
