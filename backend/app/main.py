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
from .packet_capture import PacketCapture

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Instancia global del capturador
packet_capture = None
active_websockets = set()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Maneja el ciclo de vida de la aplicación"""
    # Startup
    logger.info("Starting Thrall Defender Backend")
    await init_db()
    logger.info("Database initialized")

    # Iniciar captura de paquetes
    global packet_capture
    packet_capture = PacketCapture(interface=None)  # None = todas las interfaces
    packet_capture.set_callback(handle_packet)

    # Iniciar captura en background
    asyncio.create_task(packet_capture.start_async())
    logger.info("Packet capture started")

    yield

    # Shutdown
    if packet_capture:
        packet_capture.stop()
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

    await db.delete(ip)
    await db.commit()
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

    await db.delete(ip)
    await db.commit()
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
    db: AsyncSession = Depends(get_db)
):
    """Obtiene lista de alertas"""
    from sqlalchemy import select, desc
    query = select(models.Alert).order_by(desc(models.Alert.timestamp))

    if acknowledged is not None:
        query = query.where(models.Alert.acknowledged == acknowledged)

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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
