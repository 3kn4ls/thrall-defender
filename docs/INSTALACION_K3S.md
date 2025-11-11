# 🚀 Guía de Instalación en Raspberry Pi 5 con k3s

Esta guía te llevará paso a paso en el proceso de instalación de Thrall Defender en tu Raspberry Pi 5 con k3s.

## 📋 Requisitos Previos

- **Hardware**: Raspberry Pi 5 con SSD conectado
- **Sistema Operativo**: Raspberry Pi OS (64-bit) o Ubuntu Server 22.04+
- **Acceso**: SSH habilitado y acceso root/sudo
- **Conexión**: Internet estable

## 🛠️ Paso 1: Preparar el Sistema

### 1.1 Actualizar el Sistema

```bash
sudo apt update && sudo apt upgrade -y
sudo reboot
```

### 1.2 Verificar Arquitectura

```bash
uname -m
# Debe mostrar: aarch64 o arm64
```

## 📦 Paso 2: Instalar k3s

### 2.1 Instalar k3s (Método Fácil)

```bash
curl -sfL https://get.k3s.io | sh -
```

### 2.2 Verificar Instalación

```bash
sudo k3s kubectl get nodes
# Deberías ver tu nodo en estado "Ready"
```

### 2.3 Configurar kubectl (Opcional, para usar sin sudo)

```bash
mkdir -p ~/.kube
sudo cp /etc/rancher/k3s/k3s.yaml ~/.kube/config
sudo chown $USER:$USER ~/.kube/config
chmod 600 ~/.kube/config
export KUBECONFIG=~/.kube/config

# Añadir al .bashrc para hacerlo permanente
echo 'export KUBECONFIG=~/.kube/config' >> ~/.bashrc
```

## 📥 Paso 3: Desplegar Thrall Defender

### 3.1 Clonar el Repositorio

```bash
cd ~
git clone https://github.com/3kn4ls/thrall-defender.git
cd thrall-defender
```

### 3.2 Ejecutar el Script de Instalación Automática

```bash
chmod +x scripts/install-k3s.sh
./scripts/install-k3s.sh
```

El script automáticamente:
- ✅ Crea el namespace `thrall-defender`
- ✅ Construye las imágenes Docker para ARM64
- ✅ Despliega el backend con permisos de red
- ✅ Despliega el frontend con nginx
- ✅ Configura el Ingress para acceso vía `/thrall-defender`
- ✅ Crea los volúmenes persistentes

### 3.3 Verificar el Despliegue

```bash
# Ver el estado de los pods
sudo k3s kubectl get pods -n thrall-defender

# Deberías ver algo como:
# NAME                              READY   STATUS    RESTARTS   AGE
# thrall-backend-xxxxx-xxxxx        1/1     Running   0          2m
# thrall-frontend-xxxxx-xxxxx       1/1     Running   0          2m
```

### 3.4 Ver los Logs (Si hay problemas)

```bash
# Logs del backend
sudo k3s kubectl logs -n thrall-defender -l app=thrall-backend --tail=50

# Logs del frontend
sudo k3s kubectl logs -n thrall-defender -l app=thrall-frontend --tail=50
```

## 🌐 Paso 4: Acceder a la Aplicación

### Método 1: Acceso Local (IP de la Raspberry Pi)

La aplicación estará disponible automáticamente en:

```
http://<IP-de-tu-Raspberry>/thrall-defender/
```

**Ejemplo:**
```
http://192.168.1.100/thrall-defender/
```

### Método 2: Port Forward (Para pruebas rápidas)

```bash
sudo k3s kubectl port-forward -n thrall-defender svc/thrall-frontend 8080:80 --address 0.0.0.0
```

Luego accede a:
```
http://<IP-de-tu-Raspberry>:8080/thrall-defender/
```

### Encontrar la IP de tu Raspberry Pi

```bash
hostname -I | awk '{print $1}'
```

## ⚙️ Paso 5: Configuración Inicial

### 5.1 Primera vez en la aplicación

1. Abre tu navegador y ve a `http://<IP-Raspberry>/thrall-defender/`
2. Ve a la pestaña **"Configuración"**
3. Verifica que la URL del backend sea correcta
4. Ajusta los intervalos de actualización según tus necesidades

### 5.2 Configurar Firewall y DDoS

1. Ve a **"Gestión de IPs"** → **"Lista Blanca"**
2. Añade las IPs de tus dispositivos de confianza:
   ```
   - Tu IP local (ej: 192.168.1.50)
   - IP del router (ej: 192.168.1.1)
   - IP de la Raspberry (para evitar auto-bloqueo)
   ```

3. Ve a **"Firewall"** → **"Políticas de Bloqueo"**
4. Configura el auto-bloqueo según tus necesidades

5. Ve a **"Protección DDoS"** → **"Configuración"**
6. Ajusta los umbrales de detección

## 🔄 Comandos Útiles

### Ver Estado del Sistema

```bash
# Estado general
./scripts/status.sh

# O manualmente:
sudo k3s kubectl get all -n thrall-defender
```

### Ver Logs en Tiempo Real

```bash
./scripts/logs.sh

# O manualmente:
sudo k3s kubectl logs -n thrall-defender -l app=thrall-backend -f
```

### Reiniciar Servicios

```bash
# Reiniciar backend
sudo k3s kubectl rollout restart deployment/thrall-backend -n thrall-defender

# Reiniciar frontend
sudo k3s kubectl rollout restart deployment/thrall-frontend -n thrall-defender
```

### Actualizar la Aplicación

```bash
# 1. Obtener últimos cambios
git pull origin main

# 2. Re-ejecutar el script de instalación
./scripts/install-k3s.sh
```

### Desinstalar

```bash
./scripts/uninstall.sh

# O manualmente:
sudo k3s kubectl delete namespace thrall-defender
```

## 🐛 Solución de Problemas

### Problema: Los pods no inician

**Síntoma:** Estado `Pending` o `CrashLoopBackOff`

**Solución:**
```bash
# Ver detalles del pod
sudo k3s kubectl describe pod <nombre-del-pod> -n thrall-defender

# Ver eventos
sudo k3s kubectl get events -n thrall-defender --sort-by='.lastTimestamp'
```

### Problema: No puedo acceder a la aplicación

**Síntoma:** Error de conexión en el navegador

**Solución:**
```bash
# 1. Verificar que los servicios estén running
sudo k3s kubectl get svc -n thrall-defender

# 2. Verificar el ingress
sudo k3s kubectl get ingress -n thrall-defender

# 3. Hacer port-forward temporal
sudo k3s kubectl port-forward -n thrall-defender svc/thrall-frontend 8080:80 --address 0.0.0.0
# Prueba acceder a http://<IP>:8080/thrall-defender/
```

### Problema: Backend no captura paquetes

**Síntoma:** No se ven paquetes en el dashboard

**Solución:**
```bash
# 1. Verificar que el pod tiene los capabilities necesarios
sudo k3s kubectl get pod -n thrall-defender -o yaml | grep -A 5 capabilities

# 2. Ver logs del backend
sudo k3s kubectl logs -n thrall-defender -l app=thrall-backend --tail=100

# 3. El deployment debe tener:
# capabilities:
#   add:
#   - NET_ADMIN
#   - NET_RAW
```

### Problema: Errores de permisos en el SSD

**Síntoma:** Pods no pueden escribir en el volumen persistente

**Solución:**
```bash
# Verificar permisos del directorio de datos
sudo ls -la /var/lib/rancher/k3s/storage/

# Si es necesario, ajustar permisos
sudo chmod -R 777 /var/lib/rancher/k3s/storage/
```

## 📊 Monitoring y Logs

### Ver Uso de Recursos

```bash
# CPU y memoria de los pods
sudo k3s kubectl top pods -n thrall-defender

# Uso de nodos
sudo k3s kubectl top nodes
```

### Acceder a la Shell de un Pod

```bash
# Backend
sudo k3s kubectl exec -it -n thrall-defender deployment/thrall-backend -- /bin/bash

# Frontend
sudo k3s kubectl exec -it -n thrall-defender deployment/thrall-frontend -- /bin/sh
```

## 🔐 Seguridad

### Habilitar HTTPS (Opcional pero Recomendado)

Para habilitar HTTPS con Let's Encrypt:

1. Instala cert-manager:
```bash
sudo k3s kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.0/cert-manager.yaml
```

2. Configura un certificado SSL (documentación completa en `docs/ssl-setup.md`)

## 📞 Soporte

Si tienes problemas:

1. Revisa los logs: `./scripts/logs.sh`
2. Consulta esta guía de solución de problemas
3. Abre un issue en GitHub: https://github.com/3kn4ls/thrall-defender/issues

## 🎉 ¡Listo!

Tu instalación de Thrall Defender está completa. Puedes acceder a:

```
http://<IP-de-tu-Raspberry>/thrall-defender/
```

**Próximos Pasos:**
1. Configura las listas blanca/negra
2. Ajusta los umbrales de DDoS
3. Habilita el auto-bloqueo de firewall
4. Monitoriza tu red en tiempo real
