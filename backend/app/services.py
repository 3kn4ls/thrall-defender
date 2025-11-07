from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, desc
from datetime import datetime, timedelta
from . import models, schemas
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)


class NetworkService:
    """Servicio para gestión de tráfico de red"""

    @staticmethod
    async def save_packet(db: AsyncSession, packet_data: dict) -> models.NetworkPacket:
        """Guarda un paquete en la base de datos"""
        # Verificar si es sospechoso
        is_suspicious = await NetworkService._is_suspicious(db, packet_data)
        is_blocked = await NetworkService._is_blocked(db, packet_data["source_ip"])

        packet = models.NetworkPacket(
            **packet_data,
            is_suspicious=is_suspicious,
            is_blocked=is_blocked
        )
        db.add(packet)
        await db.commit()
        await db.refresh(packet)

        # Generar alerta si es necesario
        if is_suspicious or is_blocked:
            await NetworkService._create_alert(db, packet)

        return packet

    @staticmethod
    async def _is_suspicious(db: AsyncSession, packet_data: dict) -> bool:
        """Determina si un paquete es sospechoso"""
        source_ip = packet_data["source_ip"]
        dest_port = packet_data["destination_port"]

        # Verificar si está en blacklist
        blacklist_query = select(models.IPBlacklist).where(
            models.IPBlacklist.ip_address == source_ip
        )
        result = await db.execute(blacklist_query)
        if result.scalar_one_or_none():
            return True

        # Verificar si el puerto está monitoreado con whitelist_only
        port_query = select(models.PortMonitor).where(
            and_(
                models.PortMonitor.port_number == dest_port,
                models.PortMonitor.whitelist_only == True
            )
        )
        result = await db.execute(port_query)
        port_monitor = result.scalar_one_or_none()

        if port_monitor:
            # Verificar si la IP está en whitelist
            whitelist_query = select(models.IPWhitelist).where(
                models.IPWhitelist.ip_address == source_ip
            )
            result = await db.execute(whitelist_query)
            if not result.scalar_one_or_none():
                return True

        # Detectar posible port scanning (múltiples puertos desde la misma IP en poco tiempo)
        time_threshold = datetime.utcnow() - timedelta(minutes=5)
        scan_query = select(func.count(func.distinct(models.NetworkPacket.destination_port))).where(
            and_(
                models.NetworkPacket.source_ip == source_ip,
                models.NetworkPacket.timestamp > time_threshold
            )
        )
        result = await db.execute(scan_query)
        distinct_ports = result.scalar() or 0

        if distinct_ports > 10:  # Más de 10 puertos diferentes en 5 minutos
            return True

        return False

    @staticmethod
    async def _is_blocked(db: AsyncSession, ip_address: str) -> bool:
        """Verifica si una IP está bloqueada"""
        query = select(models.IPBlacklist).where(
            models.IPBlacklist.ip_address == ip_address
        )
        result = await db.execute(query)
        return result.scalar_one_or_none() is not None

    @staticmethod
    async def _create_alert(db: AsyncSession, packet: models.NetworkPacket):
        """Crea una alerta basada en un paquete sospechoso"""
        if packet.is_blocked:
            alert_type = "blacklisted_ip"
            severity = "high"
            description = f"Traffic from blacklisted IP {packet.source_ip}"
        elif packet.is_suspicious:
            alert_type = "suspicious_activity"
            severity = "medium"
            description = f"Suspicious traffic from {packet.source_ip} to port {packet.destination_port}"
        else:
            return

        alert = models.Alert(
            alert_type=alert_type,
            severity=severity,
            source_ip=packet.source_ip,
            destination_port=packet.destination_port,
            description=description
        )
        db.add(alert)
        await db.commit()

    @staticmethod
    async def get_packets(
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100,
        source_ip: Optional[str] = None,
        protocol: Optional[str] = None,
        suspicious_only: bool = False
    ) -> List[models.NetworkPacket]:
        """Obtiene lista de paquetes con filtros"""
        query = select(models.NetworkPacket)

        conditions = []
        if source_ip:
            conditions.append(models.NetworkPacket.source_ip == source_ip)
        if protocol:
            conditions.append(models.NetworkPacket.protocol == protocol)
        if suspicious_only:
            conditions.append(models.NetworkPacket.is_suspicious == True)

        if conditions:
            query = query.where(and_(*conditions))

        query = query.order_by(desc(models.NetworkPacket.timestamp)).offset(skip).limit(limit)

        result = await db.execute(query)
        return result.scalars().all()

    @staticmethod
    async def get_statistics(db: AsyncSession) -> schemas.Stats:
        """Obtiene estadísticas del tráfico"""
        # Total de paquetes
        total_query = select(func.count(models.NetworkPacket.id))
        total_result = await db.execute(total_query)
        total_packets = total_result.scalar() or 0

        # Paquetes última hora
        hour_ago = datetime.utcnow() - timedelta(hours=1)
        hour_query = select(func.count(models.NetworkPacket.id)).where(
            models.NetworkPacket.timestamp > hour_ago
        )
        hour_result = await db.execute(hour_query)
        packets_last_hour = hour_result.scalar() or 0

        # IPs únicas
        unique_ips_query = select(func.count(func.distinct(models.NetworkPacket.source_ip)))
        unique_result = await db.execute(unique_ips_query)
        unique_ips = unique_result.scalar() or 0

        # Paquetes sospechosos
        suspicious_query = select(func.count(models.NetworkPacket.id)).where(
            models.NetworkPacket.is_suspicious == True
        )
        suspicious_result = await db.execute(suspicious_query)
        suspicious_packets = suspicious_result.scalar() or 0

        # Alertas activas
        alerts_query = select(func.count(models.Alert.id)).where(
            models.Alert.acknowledged == False
        )
        alerts_result = await db.execute(alerts_query)
        active_alerts = alerts_result.scalar() or 0

        # Top puertos
        top_ports_query = select(
            models.NetworkPacket.destination_port,
            func.count(models.NetworkPacket.id).label('count')
        ).where(
            models.NetworkPacket.timestamp > hour_ago
        ).group_by(
            models.NetworkPacket.destination_port
        ).order_by(
            desc('count')
        ).limit(5)
        top_ports_result = await db.execute(top_ports_query)
        top_ports = [{"port": row[0], "count": row[1]} for row in top_ports_result.all()]

        # Top protocolos
        top_protocols_query = select(
            models.NetworkPacket.protocol,
            func.count(models.NetworkPacket.id).label('count')
        ).where(
            models.NetworkPacket.timestamp > hour_ago
        ).group_by(
            models.NetworkPacket.protocol
        ).order_by(
            desc('count')
        ).limit(5)
        top_protocols_result = await db.execute(top_protocols_query)
        top_protocols = [{"protocol": row[0], "count": row[1]} for row in top_protocols_result.all()]

        # IPs recientes
        recent_ips_query = select(
            func.distinct(models.NetworkPacket.source_ip)
        ).where(
            models.NetworkPacket.timestamp > hour_ago
        ).limit(10)
        recent_ips_result = await db.execute(recent_ips_query)
        recent_ips = [row[0] for row in recent_ips_result.all()]

        return schemas.Stats(
            total_packets=total_packets,
            packets_last_hour=packets_last_hour,
            unique_ips=unique_ips,
            suspicious_packets=suspicious_packets,
            active_alerts=active_alerts,
            top_ports=top_ports,
            top_protocols=top_protocols,
            recent_ips=recent_ips
        )
