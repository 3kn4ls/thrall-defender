from sqlalchemy import Integer
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
import asyncio
import json
import logging
from contextlib import asynccontextmanager

from . import models, schemas
from .database import init_db, get_db, async_session_maker
from .services import NetworkService
from .firewall_service import FirewallService
from .ddos_service import DDoSService
from .ddos_advanced_service import DDoSAdvancedService
from .cleanup_service import CleanupService
from .packet_capture import PacketCapture

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Instancia global del capturador
packet_capture = None
active_websockets = set()
cleanup_task = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Maneja el ciclo de vida de la aplicación"""
    # Startup
    logger.info("Starting Thrall Defender Backend")
    await init_db()
    logger.info("Database initialized")

    # Inicializar firewall y protección DDoS
    async with async_session_maker() as db:
        await FirewallService.initialize(db)
        await DDoSService.initialize(db)
        await DDoSAdvancedService.initialize_defaults(db)

    # Iniciar captura de paquetes
    global packet_capture
    packet_capture = PacketCapture(interface=None)  # None = todas las interfaces
    packet_capture.set_callback(handle_packet)

    # Iniciar captura en background
    asyncio.create_task(packet_capture.start_async())
    logger.info("Packet capture started")

    # Iniciar cleanup task
    global cleanup_task
    cleanup_task = asyncio.create_task(CleanupService.start_cleanup_task())
    logger.info("Database cleanup task started")

    yield

    # Shutdown
    if packet_capture:
        packet_capture.stop()
    if cleanup_task:
        cleanup_task.cancel()
        try:
            await cleanup_task
        except asyncio.CancelledError:
            pass
    logger.info("Thrall Defender Backend stopped")


app = FastAPI(
    title="Thrall Defender API",
    description="Network Traffic Monitoring API",
    version="1.0.0",
    lifespan=lifespan
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción, especificar dominios
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


async def handle_packet(packet_data: dict):
    """Maneja un paquete capturado"""
    try:
        async with async_session_maker() as db:
            # Analizar para DDoS
            await DDoSService.analyze_packet(db, packet_data)

            # Guardar paquete
            packet = await NetworkService.save_packet(db, packet_data)

            # Enviar a todos los websockets conectados
            packet_dict = {
                "id": packet.id,
                "timestamp": packet.timestamp.isoformat(),
                "source_ip": packet.source_ip,
                "destination_ip": packet.destination_ip,
                "source_port": packet.source_port,
                "destination_port": packet.destination_port,
                "protocol": packet.protocol,
                "packet_size": packet.packet_size,
                "is_suspicious": packet.is_suspicious,
                "is_blocked": packet.is_blocked
            }

            # Enviar a websockets
            disconnected = set()
            for ws in active_websockets:
                try:
                    await ws.send_json({"type": "packet", "data": packet_dict})
                except Exception:
                    disconnected.add(ws)

            # Limpiar websockets desconectados
            active_websockets.difference_update(disconnected)

    except Exception as e:
        logger.error(f"Error handling packet: {e}")


# ========== WebSocket ==========

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket para actualizaciones en tiempo real"""
    await websocket.accept()
    active_websockets.add(websocket)
    logger.info(f"WebSocket connected. Total connections: {len(active_websockets)}")

    try:
        while True:
            # Mantener conexión viva
            await websocket.receive_text()
    except WebSocketDisconnect:
        active_websockets.discard(websocket)
        logger.info(f"WebSocket disconnected. Total connections: {len(active_websockets)}")


# ========== Endpoints REST ==========

@app.get("/")
async def root():
    """Health check"""
    return {
        "status": "ok",
        "service": "Thrall Defender",
        "version": "1.0.0",
        "capturing": packet_capture.running if packet_capture else False
    }


@app.get("/api/packets", response_model=List[schemas.Packet])
async def get_packets(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    source_ip: Optional[str] = None,
    protocol: Optional[str] = None,
    suspicious_only: bool = False,
    db: AsyncSession = Depends(get_db)
):
    """Obtiene lista de paquetes capturados"""
    packets = await NetworkService.get_packets(
        db, skip, limit, source_ip, protocol, suspicious_only
    )
    return packets


@app.get("/api/stats", response_model=schemas.Stats)
async def get_statistics(db: AsyncSession = Depends(get_db)):
    """Obtiene estadísticas del tráfico"""
    return await NetworkService.get_statistics(db)


# ========== IP Whitelist ==========

@app.get("/api/whitelist", response_model=List[schemas.IPWhitelist])
async def get_whitelist(db: AsyncSession = Depends(get_db)):
    """Obtiene lista blanca de IPs"""
    from sqlalchemy import select
    result = await db.execute(select(models.IPWhitelist))
    return result.scalars().all()


@app.post("/api/whitelist", response_model=schemas.IPWhitelist)
async def add_to_whitelist(
    ip: schemas.IPWhitelistCreate,
    db: AsyncSession = Depends(get_db)
):
    """Añade una IP a la lista blanca"""
    db_ip = models.IPWhitelist(**ip.dict())
    db.add(db_ip)
    try:
        await db.commit()
        await db.refresh(db_ip)

        # Notificar al firewall
        await FirewallService.on_whitelist_added(db, db_ip.ip_address)

        return db_ip
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@app.delete("/api/whitelist/{ip_id}")
async def remove_from_whitelist(ip_id: int, db: AsyncSession = Depends(get_db)):
    """Elimina una IP de la lista blanca"""
    from sqlalchemy import select
    result = await db.execute(
        select(models.IPWhitelist).where(models.IPWhitelist.id == ip_id)
    )
    ip = result.scalar_one_or_none()
    if not ip:
        raise HTTPException(status_code=404, detail="IP not found")

    ip_address = ip.ip_address
    await db.delete(ip)
    await db.commit()

    # Notificar al firewall
    await FirewallService.on_whitelist_removed(db, ip_address)

    return {"status": "deleted"}


# ========== IP Blacklist ==========

@app.get("/api/blacklist", response_model=List[schemas.IPBlacklist])
async def get_blacklist(db: AsyncSession = Depends(get_db)):
    """Obtiene lista negra de IPs"""
    from sqlalchemy import select
    result = await db.execute(select(models.IPBlacklist))
    return result.scalars().all()


@app.post("/api/blacklist", response_model=schemas.IPBlacklist)
async def add_to_blacklist(
    ip: schemas.IPBlacklistCreate,
    db: AsyncSession = Depends(get_db)
):
    """Añade una IP a la lista negra"""
    db_ip = models.IPBlacklist(**ip.dict())
    db.add(db_ip)
    try:
        await db.commit()
        await db.refresh(db_ip)

        # Notificar al firewall para bloqueo automático
        await FirewallService.on_blacklist_added(db, db_ip.ip_address, db_ip.description or "")

        return db_ip
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@app.delete("/api/blacklist/{ip_id}")
async def remove_from_blacklist(ip_id: int, db: AsyncSession = Depends(get_db)):
    """Elimina una IP de la lista negra"""
    from sqlalchemy import select
    result = await db.execute(
        select(models.IPBlacklist).where(models.IPBlacklist.id == ip_id)
    )
    ip = result.scalar_one_or_none()
    if not ip:
        raise HTTPException(status_code=404, detail="IP not found")

    ip_address = ip.ip_address
    await db.delete(ip)
    await db.commit()

    # Notificar al firewall
    await FirewallService.on_blacklist_removed(db, ip_address)

    return {"status": "deleted"}


# ========== Port Monitors ==========

@app.get("/api/monitors", response_model=List[schemas.PortMonitor])
async def get_port_monitors(db: AsyncSession = Depends(get_db)):
    """Obtiene lista de puertos monitoreados"""
    from sqlalchemy import select
    result = await db.execute(select(models.PortMonitor))
    return result.scalars().all()


@app.post("/api/monitors", response_model=schemas.PortMonitor)
async def add_port_monitor(
    monitor: schemas.PortMonitorCreate,
    db: AsyncSession = Depends(get_db)
):
    """Añade un puerto para monitorear"""
    db_monitor = models.PortMonitor(**monitor.dict())
    db.add(db_monitor)
    try:
        await db.commit()
        await db.refresh(db_monitor)

        # Reiniciar captura con nuevos puertos
        if packet_capture:
            all_ports = [m.port_number for m in (await get_port_monitors(db))]
            packet_capture.ports = all_ports

        return db_monitor
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@app.delete("/api/monitors/{monitor_id}")
async def remove_port_monitor(monitor_id: int, db: AsyncSession = Depends(get_db)):
    """Elimina un puerto monitoreado"""
    from sqlalchemy import select
    result = await db.execute(
        select(models.PortMonitor).where(models.PortMonitor.id == monitor_id)
    )
    monitor = result.scalar_one_or_none()
    if not monitor:
        raise HTTPException(status_code=404, detail="Monitor not found")

    await db.delete(monitor)
    await db.commit()
    return {"status": "deleted"}


# ========== Alerts ==========

@app.get("/api/alerts", response_model=List[schemas.Alert])
async def get_alerts(
    acknowledged: Optional[bool] = None,
    limit: int = 1000,
    offset: int = 0,
    db: AsyncSession = Depends(get_db)
):
    """
    Obtiene lista de alertas con paginación
    - acknowledged: filtrar por estado de reconocimiento (opcional)
    - limit: número máximo de resultados (default: 1000, max: 5000)
    - offset: número de registros a saltar (default: 0)
    """
    from sqlalchemy import select, desc

    # Limitar el máximo de resultados para evitar problemas de memoria
    limit = min(limit, 5000)

    query = select(models.Alert).order_by(desc(models.Alert.timestamp))

    if acknowledged is not None:
        query = query.where(models.Alert.acknowledged == acknowledged)

    # Aplicar límite y offset
    query = query.limit(limit).offset(offset)

    result = await db.execute(query)
    return result.scalars().all()


@app.patch("/api/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(alert_id: int, db: AsyncSession = Depends(get_db)):
    """Marca una alerta como reconocida"""
    from sqlalchemy import select
    result = await db.execute(
        select(models.Alert).where(models.Alert.id == alert_id)
    )
    alert = result.scalar_one_or_none()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    alert.acknowledged = True
    await db.commit()
    return {"status": "acknowledged"}


# ========== Firewall Management ==========

@app.post("/api/firewall/block")
async def block_ip_endpoint(
    request: schemas.BlockIPRequest,
    db: AsyncSession = Depends(get_db)
):
    """Bloquea una IP manualmente"""
    success = await FirewallService.block_ip(
        db,
        request.ip_address,
        reason=request.reason or "Manual block",
        performed_by="manual",
        duration_hours=request.duration_hours
    )

    if not success:
        raise HTTPException(status_code=400, detail="Failed to block IP. Check if IP is whitelisted or invalid.")

    return {"status": "blocked", "ip_address": request.ip_address}


@app.post("/api/firewall/unblock")
async def unblock_ip_endpoint(
    request: schemas.UnblockIPRequest,
    db: AsyncSession = Depends(get_db)
):
    """Desbloquea una IP manualmente"""
    success = await FirewallService.unblock_ip(
        db,
        request.ip_address,
        reason=request.reason or "Manual unblock",
        performed_by="manual"
    )

    if not success:
        raise HTTPException(status_code=400, detail="Failed to unblock IP or IP was not blocked.")

    return {"status": "unblocked", "ip_address": request.ip_address}


@app.get("/api/firewall/blocked-ips", response_model=List[schemas.BlockedIP])
async def get_blocked_ips():
    """Obtiene lista de IPs bloqueadas actualmente en el firewall"""
    blocked_ips = await FirewallService.get_blocked_ips_from_firewall()

    return [
        schemas.BlockedIP(
            source=ip['source'],
            packets=int(ip['packets']),
            bytes=int(ip['bytes']),
            rule_number=ip['rule_number']
        )
        for ip in blocked_ips
    ]


@app.get("/api/firewall/stats", response_model=schemas.FirewallStats)
async def get_firewall_stats():
    """Obtiene estadísticas del firewall"""
    stats = FirewallService.get_firewall_statistics()
    return schemas.FirewallStats(**stats)


@app.get("/api/firewall/logs", response_model=List[schemas.FirewallLog])
async def get_firewall_logs(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    ip_address: Optional[str] = None,
    action: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """Obtiene logs de acciones del firewall"""
    logs = await FirewallService.get_firewall_logs(db, skip, limit, ip_address, action)
    return logs


# ========== Blocking Policies ==========

@app.get("/api/policies", response_model=List[schemas.BlockingPolicy])
async def get_policies(db: AsyncSession = Depends(get_db)):
    """Obtiene políticas de bloqueo"""
    from sqlalchemy import select
    result = await db.execute(select(models.BlockingPolicy))
    return result.scalars().all()


@app.get("/api/policies/{policy_id}", response_model=schemas.BlockingPolicy)
async def get_policy(policy_id: int, db: AsyncSession = Depends(get_db)):
    """Obtiene una política específica"""
    from sqlalchemy import select
    result = await db.execute(
        select(models.BlockingPolicy).where(models.BlockingPolicy.id == policy_id)
    )
    policy = result.scalar_one_or_none()
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")
    return policy


@app.get("/api/policies/name/{policy_name}", response_model=schemas.BlockingPolicy)
async def get_policy_by_name(policy_name: str, db: AsyncSession = Depends(get_db)):
    """Obtiene una política por nombre"""
    from sqlalchemy import select
    result = await db.execute(
        select(models.BlockingPolicy).where(models.BlockingPolicy.name == policy_name)
    )
    policy = result.scalar_one_or_none()
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")
    return policy


@app.patch("/api/policies/{policy_id}", response_model=schemas.BlockingPolicy)
async def update_policy(
    policy_id: int,
    policy_update: schemas.BlockingPolicyUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Actualiza una política de bloqueo"""
    from sqlalchemy import select
    result = await db.execute(
        select(models.BlockingPolicy).where(models.BlockingPolicy.id == policy_id)
    )
    policy = result.scalar_one_or_none()
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")

    # Actualizar campos
    update_data = policy_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(policy, field, value)

    policy.updated_at = datetime.utcnow()

    await db.commit()
    await db.refresh(policy)
    return policy


@app.post("/api/policies", response_model=schemas.BlockingPolicy)
async def create_policy(
    policy: schemas.BlockingPolicyCreate,
    db: AsyncSession = Depends(get_db)
):
    """Crea una nueva política de bloqueo"""
    db_policy = models.BlockingPolicy(**policy.dict())
    db.add(db_policy)
    try:
        await db.commit()
        await db.refresh(db_policy)
        return db_policy
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


# ========== DDoS Protection ==========

@app.get("/api/ddos/config", response_model=schemas.DDoSConfig)
async def get_ddos_config(db: AsyncSession = Depends(get_db)):
    """Obtiene configuración de protección DDoS"""
    return await DDoSService.get_default_config(db)


@app.patch("/api/ddos/config/{config_id}", response_model=schemas.DDoSConfig)
async def update_ddos_config(
    config_id: int,
    config_update: schemas.DDoSConfigUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Actualiza configuración de protección DDoS"""
    try:
        updates = config_update.dict(exclude_unset=True)
        return await DDoSService.update_config(db, config_id, updates)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.get("/api/ddos/attacks/active", response_model=List[schemas.DDoSAttack])
async def get_active_ddos_attacks(db: AsyncSession = Depends(get_db)):
    """Obtiene ataques DDoS activos"""
    return await DDoSService.get_active_attacks(db)


@app.get("/api/ddos/attacks/history", response_model=List[schemas.DDoSAttack])
async def get_ddos_attack_history(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    ip: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """Obtiene historial de ataques DDoS"""
    return await DDoSService.get_attack_history(db, skip, limit, ip)


@app.get("/api/ddos/stats", response_model=schemas.DDoSStats)
async def get_ddos_statistics(db: AsyncSession = Depends(get_db)):
    """Obtiene estadísticas de DDoS"""
    return await DDoSService.get_ddos_statistics(db)


@app.get("/api/ddos/metrics", response_model=List[schemas.DDoSMetrics])
async def get_ddos_metrics(ip: Optional[str] = None):
    """Obtiene métricas en tiempo real de tráfico"""
    return DDoSService.get_real_time_metrics(ip)


@app.post("/api/ddos/mitigate")
async def mitigate_ddos_attack(
    request: schemas.MitigateIPRequest,
    db: AsyncSession = Depends(get_db)
):
    """Mitiga manualmente un ataque DDoS"""
    success = await DDoSService.mitigate_attack(
        db,
        request.ip_address,
        request.attack_type
    )

    if not success:
        raise HTTPException(status_code=400, detail="Failed to mitigate attack")

    return {"status": "mitigated", "ip_address": request.ip_address}


@app.post("/api/ddos/attacks/{ip}/end")
async def end_ddos_attack(ip: str, db: AsyncSession = Depends(get_db)):
    """Marca un ataque DDoS como finalizado"""
    await DDoSService.end_attack(db, ip)
    return {"status": "ended", "ip_address": ip}


# ============================================================================
# CLEANUP ENDPOINTS
# ============================================================================

@app.post("/api/cleanup/run")
async def run_cleanup(db: AsyncSession = Depends(get_db)):
    """Ejecuta limpieza manual de la base de datos"""
    stats = await CleanupService.cleanup_old_records(db)
    return stats


@app.get("/api/cleanup/stats")
async def get_cleanup_stats(db: AsyncSession = Depends(get_db)):
    """Obtiene estadísticas de la base de datos"""
    stats = await CleanupService.get_database_stats(db)
    return stats


@app.get("/api/cleanup/config")
async def get_cleanup_config():
    """Obtiene la configuración de retención de datos"""
    return {
        "retention_periods": CleanupService.RETENTION_PERIODS,
        "cleanup_interval_hours": CleanupService.CLEANUP_INTERVAL / 3600
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)


# ============================================================================
# ADVANCED DDOS ENDPOINTS
# ============================================================================

@app.get("/api/ddos/levels", response_model=List[schemas.DDoSMitigationLevel])
async def get_mitigation_levels(db: AsyncSession = Depends(get_db)):
    """Obtiene todos los niveles de mitigación"""
    from app.ddos_advanced_service import DDoSAdvancedService
    result = await db.execute(select(models.DDoSMitigationLevel))
    levels = result.scalars().all()
    return levels


@app.post("/api/ddos/levels/{level_name}/activate")
async def activate_level(level_name: str, db: AsyncSession = Depends(get_db)):
    """Activa un nivel de mitigación"""
    from app.ddos_advanced_service import DDoSAdvancedService
    success = await DDoSAdvancedService.set_active_level(db, level_name)
    if not success:
        raise HTTPException(status_code=404, detail="Level not found")
    return {"status": "activated", "level": level_name}


@app.get("/api/ddos/geo-rules", response_model=List[schemas.DDoSGeoRule])
async def get_geo_rules(db: AsyncSession = Depends(get_db)):
    """Obtiene todas las reglas geográficas"""
    result = await db.execute(
        select(models.DDoSGeoRule).order_by(models.DDoSGeoRule.priority)
    )
    return result.scalars().all()


@app.post("/api/ddos/geo-rules", response_model=schemas.DDoSGeoRule)
async def create_geo_rule(rule: schemas.DDoSGeoRuleCreate, db: AsyncSession = Depends(get_db)):
    """Crea una nueva regla geográfica"""
    db_rule = models.DDoSGeoRule(**rule.dict())
    db.add(db_rule)
    await db.commit()
    await db.refresh(db_rule)
    return db_rule


@app.delete("/api/ddos/geo-rules/{rule_id}")
async def delete_geo_rule(rule_id: int, db: AsyncSession = Depends(get_db)):
    """Elimina una regla geográfica"""
    result = await db.execute(
        select(models.DDoSGeoRule).where(models.DDoSGeoRule.id == rule_id)
    )
    rule = result.scalar_one_or_none()
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    await db.delete(rule)
    await db.commit()
    return {"status": "deleted"}


@app.get("/api/ddos/protection-status", response_model=schemas.DDoSProtectionStatus)
async def get_protection_status(db: AsyncSession = Depends(get_db)):
    """Obtiene el estado actual de la protección DDoS"""
    from app.ddos_advanced_service import DDoSAdvancedService
    from app.geoip_service import GeoIPService
    
    # Get active level
    active_level = await DDoSAdvancedService.get_active_level(db)
    
    # Count geo rules
    result = await db.execute(select(func.count(models.DDoSGeoRule.id)))
    geo_rules_count = result.scalar()
    
    # Count active attacks (last hour)
    one_hour_ago = datetime.utcnow() - timedelta(hours=1)
    result = await db.execute(
        select(func.count(models.DDoSAttack.id)).where(
            and_(
                models.DDoSAttack.detected_at >= one_hour_ago,
                models.DDoSAttack.mitigated == False
            )
        )
    )
    active_attacks = result.scalar()
    
    # Count blocked today
    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    result = await db.execute(
        select(func.count(models.DDoSAttack.id)).where(
            and_(
                models.DDoSAttack.detected_at >= today,
                models.DDoSAttack.mitigated == True
            )
        )
    )
    blocked_today = result.scalar()
    
    # Determine threat level
    if active_attacks >= 10:
        threat_level = "critical"
    elif active_attacks >= 5:
        threat_level = "high"
    elif active_attacks >= 2:
        threat_level = "medium"
    elif active_attacks >= 1:
        threat_level = "low"
    else:
        threat_level = "none"
    
    return {
        "protection_enabled": active_level is not None,
        "active_level": active_level,
        "geo_rules_count": geo_rules_count,
        "active_attacks_count": active_attacks,
        "total_attacks_blocked_today": blocked_today,
        "current_threat_level": threat_level,
        "geoip_available": GeoIPService._reader is not None
    }


@app.get("/api/ddos/geo-stats")
async def get_geo_stats(db: AsyncSession = Depends(get_db), limit: int = 10):
    """Obtiene estadísticas de ataques por país"""
    # Get attacks from last 24 hours grouped by country
    yesterday = datetime.utcnow() - timedelta(hours=24)
    
    result = await db.execute(
        select(
            models.DDoSAttack.country_code,
            models.DDoSAttack.country_name,
            func.count(models.DDoSAttack.id).label('attack_count'),
            func.sum(func.cast(models.DDoSAttack.mitigated, Integer)).label('blocked_count'),
            func.sum(models.DDoSAttack.packets_per_second).label('total_packets')
        )
        .where(models.DDoSAttack.detected_at >= yesterday)
        .where(models.DDoSAttack.country_code.isnot(None))
        .group_by(models.DDoSAttack.country_code, models.DDoSAttack.country_name)
        .order_by(desc('attack_count'))
        .limit(limit)
    )
    
    stats = []
    for row in result:
        stats.append({
            "country_code": row.country_code,
            "country_name": row.country_name,
            "attack_count": row.attack_count,
            "blocked_count": row.blocked_count or 0,
            "total_packets": int(row.total_packets or 0)
        })
    
    return stats

