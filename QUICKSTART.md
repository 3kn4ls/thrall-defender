# 🚀 Guía de Inicio Rápido

## Opción 1: Desarrollo Local con Docker Compose

### Requisitos
- Docker y Docker Compose instalados
- Permisos de root/sudo (necesario para captura de paquetes)

### Pasos

```bash
# 1. Clonar repositorio
git clone https://github.com/3kn4ls/thrall-defender.git
cd thrall-defender

# 2. Iniciar servicios
docker-compose up -d

# 3. Verificar que están corriendo
docker-compose ps

# 4. Ver logs
docker-compose logs -f

# 5. Acceder a la aplicación
# http://localhost
```

### Comandos Útiles

```bash
# Detener servicios
docker-compose down

# Reconstruir imágenes
docker-compose build

# Ver logs de un servicio específico
docker-compose logs -f backend
docker-compose logs -f frontend

# Reiniciar un servicio
docker-compose restart backend
```

---

## Opción 2: Despliegue en Raspberry Pi 5 con k3s

### Script Automático

```bash
# 1. Clonar repositorio
git clone https://github.com/3kn4ls/thrall-defender.git
cd thrall-defender

# 2. Ejecutar script de despliegue
./scripts/build-and-deploy.sh

# 3. Verificar estado
./scripts/status.sh

# 4. Ver logs
./scripts/logs.sh
```

### Acceso a la Aplicación

#### Port Forward (rápido para pruebas)
```bash
kubectl port-forward -n thrall-defender svc/thrall-frontend 8080:80 --address 0.0.0.0
# Acceder a http://<IP-RASPBERRY>:8080
```

#### LoadBalancer (recomendado)
```bash
# Obtener IP externa
kubectl get svc -n thrall-defender thrall-frontend

# Acceder directamente a la IP mostrada
```

### Scripts de Gestión

```bash
# Ver estado completo
./scripts/status.sh

# Ver logs
./scripts/logs.sh

# Desinstalar
./scripts/uninstall.sh
```

---

## Opción 3: Desarrollo Local sin Docker

### Backend

```bash
cd backend

# Crear entorno virtual
python3 -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt

# Ejecutar (requiere sudo para captura de paquetes)
sudo venv/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Frontend

```bash
cd frontend

# Instalar dependencias
npm install

# Ejecutar en modo desarrollo
npm start

# Acceder a http://localhost:4200
```

---

## 📊 Primeros Pasos en la Aplicación

1. **Dashboard Principal**
   - Verás estadísticas en tiempo real del tráfico de red
   - Paquetes totales, paquetes por hora, IPs únicas, etc.

2. **Pestaña "Tráfico en Tiempo Real"**
   - Lista de todos los paquetes capturados
   - Filtros por IP, protocolo, estado

3. **Pestaña "Alertas"**
   - Alertas de seguridad generadas automáticamente
   - Marca alertas como reconocidas

4. **Pestaña "Gestión de IPs"**
   - **Lista Blanca**: Añade IPs de confianza
   - **Lista Negra**: Bloquea IPs sospechosas

## 🔧 Configuración Inicial Recomendada

### 1. Añadir IPs de Confianza a Lista Blanca

```
Ejemplo:
- 192.168.1.1 - Gateway/Router
- 192.168.1.100 - PC Principal
- 192.168.1.101 - Laptop
```

### 2. Configurar Puertos a Monitorizar

Si tienes puertos expuestos en tu router, añádelos para monitorización específica:

```
Ejemplos comunes:
- Puerto 22 (SSH)
- Puerto 80 (HTTP)
- Puerto 443 (HTTPS)
- Puerto 3389 (RDP)
```

### 3. Monitorizar Actividad Sospechosa

La aplicación detecta automáticamente:
- ✅ IPs en lista negra
- ✅ Port scanning (múltiples puertos desde la misma IP)
- ✅ Acceso desde IPs no autorizadas a puertos protegidos
- ✅ Patrones anómalos de tráfico

### 4. Configurar Firewall y Bloqueo Automático 🔥

La pestaña **"Firewall"** te permite:

#### Bloqueo Manual de IPs
```
1. Ir a pestaña "Firewall"
2. Ingresar IP a bloquear
3. Añadir razón (opcional)
4. Configurar duración (vacío = permanente)
5. Click en "Bloquear"
```

#### Políticas de Auto-Bloqueo
```
1. Ir a "Firewall" → "Políticas de Bloqueo"
2. Configurar:
   - ✅ Auto-bloquear IPs en lista negra
   - ✅ Auto-bloquear por alertas (número de alertas)
   - ✅ Duración de bloqueos temporales
3. Guardar configuración
```

#### Ver IPs Bloqueadas
```
- En tiempo real desde "Firewall" → "IPs Bloqueadas Activas"
- Muestra paquetes y datos bloqueados
- Permite desbloquear con un click
```

#### Logs del Firewall
```
- Historial completo de todas las acciones
- Bloqueos automáticos y manuales
- Desbloqueos y expiraciones
```

**⚠️ Importante**:
- Las IPs en **whitelist** nunca se bloquean (protección contra auto-bloqueo)
- Añade tu IP a la whitelist antes de habilitar auto-bloqueo
- Los bloqueos se aplican a nivel de iptables del sistema

## 🆘 Problemas Comunes

### Backend no captura paquetes
- **Causa**: Falta de permisos
- **Solución**: Ejecutar con `sudo` o configurar capabilities

### Frontend no conecta con Backend
- **Causa**: CORS o URL incorrecta
- **Solución**: Verificar `environment.ts` y que backend esté corriendo

### Base de datos corrupta
- **Solución**: Eliminar archivo `.db` y reiniciar

## 📚 Documentación Completa

Para instrucciones detalladas de despliegue en Raspberry Pi, consulta:
- [docs/deployment.md](./docs/deployment.md)

## 🔗 Enlaces Útiles

- **Repositorio**: https://github.com/3kn4ls/thrall-defender
- **Issues**: https://github.com/3kn4ls/thrall-defender/issues
- **Documentación k3s**: https://docs.k3s.io
