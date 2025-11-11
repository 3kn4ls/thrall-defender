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

### 🚀 Instalación Automática (RECOMENDADO)

```bash
# 1. Clonar repositorio
git clone https://github.com/3kn4ls/thrall-defender.git
cd thrall-defender

# 2. Ejecutar script de instalación (instala k3s si no está presente)
chmod +x scripts/install-k3s.sh
./scripts/install-k3s.sh

# 3. Acceder a la aplicación
# http://<IP-de-tu-Raspberry>/thrall-defender/
```

**📖 Para guía paso a paso detallada, ver [docs/INSTALACION_K3S.md](./docs/INSTALACION_K3S.md)**

### Scripts Alternativos

```bash
# Si k3s ya está instalado y solo quieres actualizar
./scripts/build-and-deploy.sh

# Verificar estado
./scripts/status.sh

# Ver logs
./scripts/logs.sh
```

### Acceso a la Aplicación

#### Método Principal (Ingress)
La aplicación estará disponible automáticamente en:
```
http://<IP-de-tu-Raspberry>/thrall-defender/
```

#### Port Forward (para pruebas)
```bash
kubectl port-forward -n thrall-defender svc/thrall-frontend 8080:80 --address 0.0.0.0
# Acceder a http://<IP-RASPBERRY>:8080/thrall-defender/
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

### 5. Configurar Protección DDoS 🛡️

La pestaña **"Protección DDoS"** ofrece detección y mitigación automática de ataques:

#### Ver Ataques Activos
```
1. Ir a pestaña "Protección DDoS"
2. Ver estadísticas principales:
   - Ataques activos en este momento
   - Total de ataques detectados hoy
   - IPs mitigadas actualmente
3. En la sub-pestaña "Ataques Activos":
   - Lista de ataques en curso con severidad
   - Tipo de ataque (SYN Flood, UDP Flood, ICMP Flood, Tráfico Alto)
   - Paquetes por segundo
   - Botón para mitigar manualmente
```

#### Top Atacantes en Tiempo Real
```
1. Ir a "Top Atacantes"
2. Ver las IPs con más tráfico:
   - Paquetes por segundo totales
   - Tasa de SYN/s
   - Tasa de UDP/s
   - Tasa de ICMP/s
3. Útil para identificar patrones antes de que se conviertan en ataques
```

#### Configurar Umbrales y Mitigación Automática
```
1. Ir a "Configuración"
2. Habilitar/deshabilitar protección DDoS
3. Ajustar umbrales de detección:
   - Paquetes/segundo (default: 100)
   - SYN/segundo (default: 50)
   - UDP/segundo (default: 200)
   - ICMP/segundo (default: 50)
4. Configurar mitigación automática:
   - ✅ Habilitar auto-mitigación
   - ⏱️ Duración de mitigación (60-86400 segundos)
5. Guardar configuración
```

#### Cómo Funciona la Mitigación
```
Cuando se detecta un ataque:
1. Se registra en la base de datos con severidad
2. Se crea una alerta automática
3. Si auto-mitigación está habilitada:
   - Se aplica rate limiting con iptables hashlimit
   - Limita la tasa de paquetes desde la IP atacante
   - Se mantiene durante el tiempo configurado
4. Aparece en "Ataques Activos" con estado "Mitigado"
```

**💡 Recomendaciones**:
- Ajusta los umbrales según tu tráfico normal
- Habilita auto-mitigación para respuesta inmediata
- Monitoriza "Top Atacantes" para detectar patrones
- Los umbrales muy bajos pueden generar falsos positivos

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
