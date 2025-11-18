"""
Dashboard Cache Service
=======================
Servicio asíncrono que pre-calcula las estadísticas del dashboard
para mejorar el rendimiento. En lugar de calcular stats en cada request,
el frontend lee el último snapshot calculado.

Inspirado en: Datadog, Grafana, Splunk
"""

import asyncio
import json
import time
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, delete
from sqlalchemy.future import select as future_select

from . import models, schemas
from .database import async_session


class DashboardCacheService:
    """Servicio para calcular y cachear estadísticas del dashboard"""

    @classmethod
    async def calculate_and_save_snapshot(cls, db: AsyncSession) -> models.DashboardSnapshot:
        """
        Calcula todas las estadísticas y guarda un snapshot.
        Este método es llamado periódicamente por el job asíncrono.
        """
        start_time = time.time()

        # Timestamps para cálculos
        now = datetime.utcnow()
        hour_ago = now - timedelta(hours=1)
        day_ago = now - timedelta(hours=24)
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

        # ========== PAQUETES ==========
        # Total paquetes
        total_packets_query = select(func.count(models.NetworkPacket.id))
        total_packets_result = await db.execute(total_packets_query)
        total_packets = total_packets_result.scalar() or 0

        # Paquetes última hora
        packets_hour_query = select(func.count(models.NetworkPacket.id)).where(
            models.NetworkPacket.timestamp > hour_ago
        )
        packets_hour_result = await db.execute(packets_hour_query)
        packets_last_hour = packets_hour_result.scalar() or 0

        # Paquetes últimas 24h
        packets_24h_query = select(func.count(models.NetworkPacket.id)).where(
            models.NetworkPacket.timestamp > day_ago
        )
        packets_24h_result = await db.execute(packets_24h_query)
        packets_last_24h = packets_24h_result.scalar() or 0

        # ========== IPs ÚNICAS ==========
        # IPs únicas total
        unique_ips_query = select(func.count(func.distinct(models.NetworkPacket.source_ip)))
        unique_ips_result = await db.execute(unique_ips_query)
        unique_ips = unique_ips_result.scalar() or 0

        # IPs únicas última hora
        unique_ips_hour_query = select(func.count(func.distinct(models.NetworkPacket.source_ip))).where(
            models.NetworkPacket.timestamp > hour_ago
        )
        unique_ips_hour_result = await db.execute(unique_ips_hour_query)
        unique_ips_last_hour = unique_ips_hour_result.scalar() or 0

        # ========== PAQUETES SOSPECHOSOS ==========
        suspicious_query = select(func.count(models.NetworkPacket.id)).where(
            models.NetworkPacket.is_suspicious == True
        )
        suspicious_result = await db.execute(suspicious_query)
        suspicious_packets = suspicious_result.scalar() or 0

        # ========== ALERTAS ==========
        # Alertas activas (no reconocidas)
        active_alerts_query = select(func.count(models.Alert.id)).where(
            models.Alert.acknowledged == False
        )
        active_alerts_result = await db.execute(active_alerts_query)
        active_alerts = active_alerts_result.scalar() or 0

        # Alertas por severidad (no reconocidas)
        critical_alerts_query = select(func.count(models.Alert.id)).where(
            models.Alert.acknowledged == False,
            models.Alert.severity == 'critical'
        )
        critical_result = await db.execute(critical_alerts_query)
        critical_alerts = critical_result.scalar() or 0

        high_alerts_query = select(func.count(models.Alert.id)).where(
            models.Alert.acknowledged == False,
            models.Alert.severity == 'high'
        )
        high_result = await db.execute(high_alerts_query)
        high_alerts = high_result.scalar() or 0

        medium_alerts_query = select(func.count(models.Alert.id)).where(
            models.Alert.acknowledged == False,
            models.Alert.severity == 'medium'
        )
        medium_result = await db.execute(medium_alerts_query)
        medium_alerts = medium_result.scalar() or 0

        low_alerts_query = select(func.count(models.Alert.id)).where(
            models.Alert.acknowledged == False,
            models.Alert.severity == 'low'
        )
        low_result = await db.execute(low_alerts_query)
        low_alerts = low_result.scalar() or 0

        # ========== TOP PUERTOS ==========
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

        # ========== TOP PROTOCOLOS ==========
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

        # ========== IPs RECIENTES ==========
        recent_ips_query = select(
            func.distinct(models.NetworkPacket.source_ip)
        ).where(
            models.NetworkPacket.timestamp > hour_ago
        ).limit(10)
        recent_ips_result = await db.execute(recent_ips_query)
        recent_ips = [row[0] for row in recent_ips_result.all()]

        # ========== TOP SOURCES (IPs con más paquetes) ==========
        top_sources_query = select(
            models.NetworkPacket.source_ip,
            func.count(models.NetworkPacket.id).label('packets')
        ).where(
            models.NetworkPacket.timestamp > hour_ago
        ).group_by(
            models.NetworkPacket.source_ip
        ).order_by(
            desc('packets')
        ).limit(10)
        top_sources_result = await db.execute(top_sources_query)
        top_sources = [{"ip": row[0], "packets": row[1]} for row in top_sources_result.all()]

        # ========== DDOS ==========
        # Ataques DDoS activos
        active_ddos_query = select(func.count(models.DDoSAttack.id)).where(
            models.DDoSAttack.mitigated == False
        )
        active_ddos_result = await db.execute(active_ddos_query)
        active_ddos_attacks = active_ddos_result.scalar() or 0

        # Ataques DDoS hoy
        ddos_today_query = select(func.count(models.DDoSAttack.id)).where(
            models.DDoSAttack.timestamp >= today_start
        )
        ddos_today_result = await db.execute(ddos_today_query)
        ddos_attacks_today = ddos_today_result.scalar() or 0

        # ========== FIREWALL ==========
        # Logs de firewall hoy
        firewall_logs_query = select(func.count(models.FirewallLog.id)).where(
            models.FirewallLog.timestamp >= today_start,
            models.FirewallLog.action.in_(['block', 'auto_block'])
        )
        firewall_logs_result = await db.execute(firewall_logs_query)
        firewall_blocks_today = firewall_logs_result.scalar() or 0

        # IPs en whitelist
        whitelist_query = select(func.count(models.IPWhitelist.id))
        whitelist_result = await db.execute(whitelist_query)
        whitelisted_ips_count = whitelist_result.scalar() or 0

        # IPs en blacklist
        blacklist_query = select(func.count(models.IPBlacklist.id))
        blacklist_result = await db.execute(blacklist_query)
        blacklisted_ips_count = blacklist_result.scalar() or 0

        # IPs bloqueadas (estimación basada en blacklist)
        blocked_ips_count = blacklisted_ips_count

        # ========== BYTES (estimación) ==========
        # Bytes última hora
        bytes_hour_query = select(func.sum(models.NetworkPacket.packet_size)).where(
            models.NetworkPacket.timestamp > hour_ago
        )
        bytes_hour_result = await db.execute(bytes_hour_query)
        total_bytes_last_hour = bytes_hour_result.scalar() or 0

        # Bytes últimas 24h
        bytes_24h_query = select(func.sum(models.NetworkPacket.packet_size)).where(
            models.NetworkPacket.timestamp > day_ago
        )
        bytes_24h_result = await db.execute(bytes_24h_query)
        total_bytes_last_24h = bytes_24h_result.scalar() or 0

        # Calcular tiempo de ejecución
        calculation_time = (time.time() - start_time) * 1000  # milisegundos

        # ========== CREAR SNAPSHOT ==========
        snapshot = models.DashboardSnapshot(
            total_packets=total_packets,
            packets_last_hour=packets_last_hour,
            packets_last_24h=packets_last_24h,
            unique_ips=unique_ips,
            unique_ips_last_hour=unique_ips_last_hour,
            suspicious_packets=suspicious_packets,
            active_alerts=active_alerts,
            top_ports=json.dumps(top_ports),
            top_protocols=json.dumps(top_protocols),
            recent_ips=json.dumps(recent_ips),
            top_sources=json.dumps(top_sources),
            critical_alerts=critical_alerts,
            high_alerts=high_alerts,
            medium_alerts=medium_alerts,
            low_alerts=low_alerts,
            active_ddos_attacks=active_ddos_attacks,
            blocked_ips_count=blocked_ips_count,
            ddos_attacks_today=ddos_attacks_today,
            firewall_blocks_today=firewall_blocks_today,
            whitelisted_ips_count=whitelisted_ips_count,
            blacklisted_ips_count=blacklisted_ips_count,
            total_bytes_last_hour=total_bytes_last_hour,
            total_bytes_last_24h=total_bytes_last_24h,
            calculation_time_ms=calculation_time
        )

        db.add(snapshot)
        await db.commit()
        await db.refresh(snapshot)

        print(f"✓ Dashboard snapshot created in {calculation_time:.2f}ms")

        return snapshot

    @classmethod
    async def get_latest_snapshot(cls, db: AsyncSession) -> models.DashboardSnapshot | None:
        """Obtiene el snapshot más reciente"""
        query = select(models.DashboardSnapshot).order_by(desc(models.DashboardSnapshot.created_at)).limit(1)
        result = await db.execute(query)
        return result.scalar_one_or_none()

    @classmethod
    async def cleanup_old_snapshots(cls, db: AsyncSession, keep_last: int = 100):
        """
        Limpia snapshots antiguos, manteniendo solo los últimos N.
        Evita que la tabla crezca infinitamente.
        """
        # Obtener el ID del snapshot número 'keep_last'
        subquery = select(models.DashboardSnapshot.id).order_by(
            desc(models.DashboardSnapshot.created_at)
        ).limit(keep_last).offset(keep_last - 1)

        result = await db.execute(subquery)
        cutoff_row = result.scalar_one_or_none()

        if cutoff_row:
            # Borrar todos los snapshots anteriores a ese ID
            delete_query = delete(models.DashboardSnapshot).where(
                models.DashboardSnapshot.id < cutoff_row
            )
            result = await db.execute(delete_query)
            await db.commit()

            deleted_count = result.rowcount
            if deleted_count > 0:
                print(f"✓ Cleaned up {deleted_count} old dashboard snapshots")


async def dashboard_cache_job():
    """
    Job asíncrono que ejecuta periódicamente el cálculo del dashboard.
    Se ejecuta en background durante toda la vida de la aplicación.
    """
    print("🚀 Dashboard cache job started")

    while True:
        try:
            async with async_session() as db:
                # Calcular y guardar snapshot
                await DashboardCacheService.calculate_and_save_snapshot(db)

                # Limpiar snapshots antiguos (mantener últimos 100)
                await DashboardCacheService.cleanup_old_snapshots(db, keep_last=100)

        except Exception as e:
            print(f"❌ Error in dashboard cache job: {e}")

        # Esperar 10 segundos antes del próximo cálculo
        # Ajusta este valor según tus necesidades (10s = muy frecuente, 30s = normal, 60s = conservador)
        await asyncio.sleep(10)
