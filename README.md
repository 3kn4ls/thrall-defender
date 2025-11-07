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

- ✅ Captura de tráfico en tiempo real
- ✅ Monitorización de puertos específicos
- ✅ Detección de IPs sospechosas
- ✅ Dashboard en tiempo real con WebSockets
- ✅ Alertas configurables
- ✅ Filtrado por protocolo, puerto e IP
- ✅ Estadísticas y gráficos históricos
- ✅ Lista blanca/negra de IPs

## 📦 Despliegue Rápido

Ver [docs/deployment.md](./docs/deployment.md) para instrucciones detalladas de despliegue en Raspberry Pi 5 con k3s.

## 🔐 Seguridad

La herramienta captura paquetes en modo promiscuo, por lo que requiere privilegios elevados (capabilities NET_ADMIN y NET_RAW en Kubernetes).

## 📝 Licencia

MIT
