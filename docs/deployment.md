# Guía de Despliegue en Raspberry Pi 5 con k3s

Esta guía proporciona instrucciones paso a paso para desplegar Thrall Defender en una Raspberry Pi 5 con un SSD y k3s.

## 📋 Requisitos Previos

- Raspberry Pi 5 con 4GB RAM o más
- SSD externo conectado a la Raspberry Pi
- Raspberry Pi OS Lite (64-bit) instalado
- Conexión a Internet
- Acceso SSH o terminal local

## 🔧 Preparación del Sistema

### 1. Actualizar el Sistema

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y git curl
```

### 2. Configurar el SSD como almacenamiento principal

Si el SSD está montado en `/mnt/ssd`:

```bash
# Crear directorio de trabajo
sudo mkdir -p /mnt/ssd/k3s
sudo chown -R $USER:$USER /mnt/ssd/k3s

# Enlace simbólico para k3s
sudo mkdir -p /var/lib/rancher
sudo ln -s /mnt/ssd/k3s /var/lib/rancher/k3s
```

### 3. Instalar k3s

```bash
# Instalación de k3s con configuración optimizada para Raspberry Pi
curl -sfL https://get.k3s.io | sh -s - \
  --write-kubeconfig-mode 644 \
  --disable traefik \
  --disable servicelb \
  --data-dir /mnt/ssd/k3s

# Verificar instalación
sudo systemctl status k3s

# Configurar kubectl para el usuario actual
mkdir -p ~/.kube
sudo cp /etc/rancher/k3s/k3s.yaml ~/.kube/config
sudo chown $USER:$USER ~/.kube/config
export KUBECONFIG=~/.kube/config

# Verificar cluster
kubectl get nodes
```

## 🐳 Construcción de Imágenes Docker

### 1. Instalar Docker (si no está instalado)

```bash
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
newgrp docker

# Verificar
docker --version
```

### 2. Clonar el Repositorio

```bash
cd ~
git clone https://github.com/3kn4ls/thrall-defender.git
cd thrall-defender
```

### 3. Construir Imagen del Backend

```bash
cd backend
docker build -t thrall-backend:latest .
cd ..
```

**Nota**: La construcción puede tardar varios minutos en Raspberry Pi.

### 4. Construir Imagen del Frontend

```bash
cd frontend
docker build -t thrall-frontend:latest .
cd ..
```

**Nota**: La construcción de Angular puede tardar 10-15 minutos en Raspberry Pi 5.

### 5. Importar Imágenes a k3s

```bash
# Guardar imágenes
docker save thrall-backend:latest | sudo k3s ctr images import -
docker save thrall-frontend:latest | sudo k3s ctr images import -

# Verificar
sudo k3s ctr images ls | grep thrall
```

## 🚀 Despliegue en Kubernetes

### 1. Crear el Namespace

```bash
kubectl apply -f k8s/namespace.yaml
```

### 2. Desplegar el Backend

```bash
# ConfigMap
kubectl apply -f k8s/backend/configmap.yaml

# PersistentVolumeClaim
kubectl apply -f k8s/backend/pvc.yaml

# Deployment
kubectl apply -f k8s/backend/deployment.yaml

# Service
kubectl apply -f k8s/backend/service.yaml

# Verificar
kubectl get pods -n thrall-defender
kubectl logs -n thrall-defender -l app=thrall-backend -f
```

**Importante**: El backend necesita privilegios NET_ADMIN y NET_RAW para capturar paquetes. Esto está configurado en el Deployment.

### 3. Desplegar el Frontend

```bash
# Deployment
kubectl apply -f k8s/frontend/deployment.yaml

# Service
kubectl apply -f k8s/frontend/service.yaml

# Verificar
kubectl get pods -n thrall-defender
```

### 4. Verificar el Despliegue

```bash
# Ver todos los recursos
kubectl get all -n thrall-defender

# Ver logs del backend
kubectl logs -n thrall-defender -l app=thrall-backend

# Ver logs del frontend
kubectl logs -n thrall-defender -l app=thrall-frontend
```

## 🌐 Acceso a la Aplicación

### Opción 1: Port Forward (para pruebas rápidas)

```bash
# Frontend
kubectl port-forward -n thrall-defender svc/thrall-frontend 8080:80 --address 0.0.0.0

# Acceder desde tu navegador
# http://<IP-RASPBERRY>:8080
```

### Opción 2: LoadBalancer (recomendado)

El servicio frontend está configurado como LoadBalancer. En k3s, necesitas instalar MetalLB:

```bash
# Instalar MetalLB
kubectl apply -f https://raw.githubusercontent.com/metallb/metallb/v0.14.0/config/manifests/metallb-native.yaml

# Crear configuración de IP pool
cat <<EOF | kubectl apply -f -
apiVersion: metallb.io/v1beta1
kind: IPAddressPool
metadata:
  name: first-pool
  namespace: metallb-system
spec:
  addresses:
  - 192.168.1.240-192.168.1.250  # Ajustar a tu red
---
apiVersion: metallb.io/v1beta1
kind: L2Advertisement
metadata:
  name: example
  namespace: metallb-system
spec:
  ipAddressPools:
  - first-pool
EOF

# Obtener IP externa
kubectl get svc -n thrall-defender thrall-frontend
```

Accede a la aplicación usando la IP externa mostrada.

### Opción 3: Ingress con Traefik

```bash
# Instalar Traefik
helm repo add traefik https://helm.traefik.io/traefik
helm repo update
helm install traefik traefik/traefik -n kube-system

# Aplicar Ingress
kubectl apply -f k8s/ingress.yaml

# Agregar entrada en /etc/hosts (en tu PC)
echo "<IP-RASPBERRY> thrall-defender.local" | sudo tee -a /etc/hosts

# Acceder
# http://thrall-defender.local
```

## 🔍 Monitorización y Troubleshooting

### Verificar Estado del Cluster

```bash
# Nodos
kubectl get nodes

# Pods
kubectl get pods -n thrall-defender -o wide

# Servicios
kubectl get svc -n thrall-defender

# Logs en tiempo real
kubectl logs -n thrall-defender -l app=thrall-backend -f
```

### Problemas Comunes

#### 1. Backend no inicia - Error de permisos

**Síntoma**: Logs muestran "Permission denied" para captura de paquetes.

**Solución**: Verificar que el Deployment tenga las capabilities correctas:

```bash
kubectl describe pod -n thrall-defender <nombre-pod-backend>
# Buscar securityContext con NET_ADMIN y NET_RAW
```

#### 2. Imágenes no se encuentran

**Síntoma**: `ImagePullBackOff` en los pods.

**Solución**: Reimportar las imágenes:

```bash
docker save thrall-backend:latest | sudo k3s ctr images import -
docker save thrall-frontend:latest | sudo k3s ctr images import -
```

#### 3. Backend no captura paquetes

**Síntoma**: Dashboard muestra 0 paquetes.

**Solución**: Verificar que hostNetwork esté habilitado:

```bash
kubectl get pod -n thrall-defender <pod-backend> -o yaml | grep hostNetwork
# Debe mostrar: hostNetwork: true
```

#### 4. Frontend no conecta con Backend

**Síntoma**: Error de conexión en navegador.

**Solución**: Verificar que el servicio backend esté accesible:

```bash
kubectl exec -n thrall-defender <pod-frontend> -- curl http://thrall-backend:8000/
```

#### 5. Base de datos se pierde al reiniciar

**Síntoma**: Datos se pierden después de reiniciar pods.

**Solución**: Verificar que el PVC esté montado correctamente:

```bash
kubectl get pvc -n thrall-defender
kubectl describe pvc -n thrall-defender thrall-backend-data
```

### Comandos Útiles

```bash
# Reiniciar un deployment
kubectl rollout restart deployment/thrall-backend -n thrall-defender

# Escalar replicas (solo frontend, backend debe ser 1)
kubectl scale deployment/thrall-frontend --replicas=2 -n thrall-defender

# Ver eventos
kubectl get events -n thrall-defender --sort-by='.lastTimestamp'

# Ejecutar shell en un pod
kubectl exec -it -n thrall-defender <nombre-pod> -- /bin/sh

# Ver uso de recursos
kubectl top pods -n thrall-defender
kubectl top nodes
```

## 🔄 Actualización de la Aplicación

### Actualizar Backend

```bash
cd ~/thrall-defender/backend
# Hacer cambios en el código
docker build -t thrall-backend:latest .
docker save thrall-backend:latest | sudo k3s ctr images import -
kubectl rollout restart deployment/thrall-backend -n thrall-defender
```

### Actualizar Frontend

```bash
cd ~/thrall-defender/frontend
# Hacer cambios en el código
docker build -t thrall-frontend:latest .
docker save thrall-frontend:latest | sudo k3s ctr images import -
kubectl rollout restart deployment/thrall-frontend -n thrall-defender
```

## 🛡️ Seguridad y Mejores Prácticas

### 1. Configurar Firewall

```bash
sudo apt install ufw
sudo ufw allow 22/tcp      # SSH
sudo ufw allow 6443/tcp    # k3s API
sudo ufw allow 80/tcp      # HTTP
sudo ufw allow 443/tcp     # HTTPS
sudo ufw enable
```

### 2. Limitar Acceso a la API de Kubernetes

```bash
# Solo permitir acceso local
sudo systemctl edit k3s
# Añadir:
# [Service]
# Environment="K3S_KUBECONFIG_MODE=640"
```

### 3. Configurar Alertas por Email (opcional)

Editar `backend/app/main.py` para añadir notificaciones SMTP cuando se generen alertas críticas.

### 4. Backup de la Base de Datos

```bash
# Crear script de backup
cat > /home/pi/backup-thrall.sh <<'EOF'
#!/bin/bash
BACKUP_DIR="/mnt/ssd/backups/thrall"
DATE=$(date +%Y%m%d_%H%M%S)
mkdir -p $BACKUP_DIR

# Obtener nombre del pod backend
POD=$(kubectl get pod -n thrall-defender -l app=thrall-backend -o jsonpath='{.items[0].metadata.name}')

# Copiar base de datos
kubectl cp thrall-defender/$POD:/data/thrall_defender.db $BACKUP_DIR/thrall_defender_$DATE.db

# Mantener solo últimos 7 días
find $BACKUP_DIR -name "*.db" -mtime +7 -delete
EOF

chmod +x /home/pi/backup-thrall.sh

# Añadir a crontab (backup diario a las 2 AM)
(crontab -l 2>/dev/null; echo "0 2 * * * /home/pi/backup-thrall.sh") | crontab -
```

## 📊 Monitorización Avanzada (opcional)

### Instalar Prometheus y Grafana

```bash
# Añadir Helm repo
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update

# Instalar Prometheus
helm install prometheus prometheus-community/kube-prometheus-stack -n monitoring --create-namespace

# Acceder a Grafana
kubectl port-forward -n monitoring svc/prometheus-grafana 3000:80 --address 0.0.0.0
# Usuario: admin
# Password: prom-operator
```

## 🎯 Configuración Inicial de la Aplicación

Una vez desplegada la aplicación:

1. **Acceder al Dashboard**: Abre tu navegador y ve a la IP de tu servicio

2. **Añadir Puertos a Monitorizar**:
   - Ve a la pestaña "Gestión de IPs"
   - Añade los puertos que tienes expuestos en tu router

3. **Configurar Lista Blanca**:
   - Añade las IPs de tus dispositivos conocidos
   - Esto evitará alertas de falsos positivos

4. **Configurar Lista Negra**:
   - Añade IPs sospechosas o conocidas como maliciosas
   - El tráfico de estas IPs se marcará automáticamente

5. **Monitorizar en Tiempo Real**:
   - La pestaña "Tráfico en Tiempo Real" mostrará todos los paquetes
   - Los paquetes sospechosos se marcarán en naranja
   - Los paquetes bloqueados se marcarán en rojo

## 📝 Notas Adicionales

- **Rendimiento**: En Raspberry Pi 5, el sistema puede manejar ~1000-2000 paquetes/segundo sin problemas
- **Almacenamiento**: La base de datos crece aproximadamente 1MB por cada 10,000 paquetes
- **Memoria**: Se recomienda mínimo 2GB RAM libre para la aplicación
- **Red**: El backend captura en modo promiscuo, asegúrate de que tu switch soporta port mirroring si quieres capturar todo el tráfico de red

## 🆘 Soporte

Si encuentras problemas:

1. Revisa los logs: `kubectl logs -n thrall-defender <nombre-pod>`
2. Verifica los eventos: `kubectl get events -n thrall-defender`
3. Comprueba el estado de los recursos: `kubectl get all -n thrall-defender`
4. Revisa la documentación de k3s: https://docs.k3s.io

## 🔗 Referencias

- [Documentación k3s](https://docs.k3s.io)
- [Documentación Kubernetes](https://kubernetes.io/docs)
- [FastAPI](https://fastapi.tiangolo.com)
- [Angular](https://angular.io)
- [Scapy](https://scapy.net)
