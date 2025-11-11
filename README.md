# Thrall Defender - Network Traffic Monitor

Herramienta de monitorización de tráfico de red en tiempo real para detectar accesos no autorizados y analizar el tráfico en puertos expuestos.

## 🏗️ Arquitectura

- **Backend**: Python + FastAPI + Scapy (captura de tráfico)
- **Frontend**: Angular 19 + Material Design
- **Base de datos**: SQLite
- **Despliegue**: Kubernetes (k3s) en Raspberry Pi 5

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

### Alertas y Gestión
- ✅ Sistema de alertas con niveles de severidad
- ✅ Lista blanca/negra de IPs
- ✅ Gestión visual de firewall desde el dashboard
- ✅ Detección de port scanning

## 📦 Despliegue Rápido

Ver [docs/deployment.md](./docs/deployment.md) para instrucciones detalladas de despliegue en Raspberry Pi 5 con k3s.

## 🔐 Seguridad

La herramienta captura paquetes en modo promiscuo y gestiona reglas de firewall iptables, por lo que requiere privilegios elevados (capabilities NET_ADMIN y NET_RAW en Kubernetes).

### Bloqueo Automático

Thrall Defender puede bloquear automáticamente IPs maliciosas usando iptables:

1. **Bloqueo por Lista Negra**: IPs añadidas a la blacklist se bloquean automáticamente
2. **Bloqueo por Alertas**: IPs que generan múltiples alertas críticas se bloquean automáticamente
3. **Bloqueos Temporales**: Configura duración de bloqueos (permanentes o temporales)
4. **Whitelist Protegida**: IPs en whitelist nunca se bloquean (protección contra auto-bloqueo)

## 📝 Licencia

MIT
