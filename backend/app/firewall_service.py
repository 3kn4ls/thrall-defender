from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, desc
from datetime import datetime, timedelta
from . import models, schemas
from .firewall_manager import FirewallManager
from typing import List, Optional
import logging
import asyncio

logger = logging.getLogger(__name__)


class FirewallService:
    """Servicio para gestión del firewall y bloqueo automático"""

    @staticmethod
    async def initialize(db: AsyncSession):
        """Inicializa el firewall y carga políticas"""
        # Inicializar iptables
        success = FirewallManager.initialize()

        if not success:
            logger.warning("Failed to initialize firewall manager")
            return False

        # Cargar IPs de whitelist en el firewall
        whitelist_query = select(models.IPWhitelist)
        result = await db.execute(whitelist_query)
        whitelisted_ips = result.scalars().all()

        for ip_record in whitelisted_ips:
            FirewallManager.add_whitelist_ip(ip_record.ip_address)
            logger.info(f"Added {ip_record.ip_address} to firewall whitelist")

        # Bloquear IPs de blacklist si la política está activa
        policy = await FirewallService.get_default_policy(db)
        if policy and policy.auto_block_blacklist:
            await FirewallService.sync_blacklist_to_firewall(db)

        # Iniciar tarea de limpieza de bloqueos temporales
        asyncio.create_task(FirewallService.cleanup_expired_blocks(db))

        logger.info("Firewall service initialized successfully")
        return True

    @staticmethod
    async def get_default_policy(db: AsyncSession) -> Optional[models.BlockingPolicy]:
        """Obtiene o crea la política por defecto"""
        query = select(models.BlockingPolicy).where(
            models.BlockingPolicy.name == "default"
        )
        result = await db.execute(query)
        policy = result.scalar_one_or_none()

        if not policy:
            # Crear política por defecto
            policy = models.BlockingPolicy(
                name="default",
                enabled=True,
                auto_block_blacklist=True,
                auto_block_on_alert=False,
                alert_threshold=3,
                block_duration_hours=None
            )
            db.add(policy)
            await db.commit()
            await db.refresh(policy)
            logger.info("Created default blocking policy")

        return policy

    @staticmethod
    async def sync_blacklist_to_firewall(db: AsyncSession) -> int:
        """Sincroniza blacklist con firewall"""
        blacklist_query = select(models.IPBlacklist)
        result = await db.execute(blacklist_query)
        blacklisted_ips = result.scalars().all()

        blocked_count = 0
        for ip_record in blacklisted_ips:
            success = await FirewallService.block_ip(
                db,
                ip_record.ip_address,
                reason=f"Blacklisted: {ip_record.description or 'No description'}",
                performed_by="system"
            )
            if success:
                blocked_count += 1

        logger.info(f"Synced {blocked_count} blacklisted IPs to firewall")
        return blocked_count

    @staticmethod
    async def block_ip(
        db: AsyncSession,
        ip_address: str,
        reason: str = "Manual block",
        performed_by: str = "manual",
        duration_hours: Optional[int] = None
    ) -> bool:
        """
        Bloquea una IP usando el firewall

        Args:
            db: Sesión de base de datos
            ip_address: IP a bloquear
            reason: Razón del bloqueo
            performed_by: Quién realizó el bloqueo (manual, system, policy)
            duration_hours: Duración del bloqueo en horas (None = permanente)

        Returns:
            True si se bloqueó exitosamente
        """
        # Intentar bloquear en firewall
        success = FirewallManager.block_ip(ip_address, comment=reason[:50])

        # Calcular expiración si es temporal
        expires_at = None
        if duration_hours and success:
            expires_at = datetime.utcnow() + timedelta(hours=duration_hours)

        # Registrar en log
        log_entry = models.FirewallLog(
            action="block" if performed_by == "manual" else "auto_block",
            ip_address=ip_address,
            reason=reason,
            success=success,
            performed_by=performed_by,
            expires_at=expires_at
        )
        db.add(log_entry)
        await db.commit()

        if success:
            logger.info(f"Blocked IP {ip_address}: {reason} (expires: {expires_at})")
        else:
            logger.error(f"Failed to block IP {ip_address}")

        return success

    @staticmethod
    async def unblock_ip(
        db: AsyncSession,
        ip_address: str,
        reason: str = "Manual unblock",
        performed_by: str = "manual"
    ) -> bool:
        """
        Desbloquea una IP

        Args:
            db: Sesión de base de datos
            ip_address: IP a desbloquear
            reason: Razón del desbloqueo
            performed_by: Quién realizó el desbloqueo

        Returns:
            True si se desbloqueó exitosamente
        """
        # Desbloquear en firewall
        success = FirewallManager.unblock_ip(ip_address)

        # Registrar en log
        log_entry = models.FirewallLog(
            action="unblock" if performed_by == "manual" else "auto_unblock",
            ip_address=ip_address,
            reason=reason,
            success=success,
            performed_by=performed_by
        )
        db.add(log_entry)
        await db.commit()

        if success:
            logger.info(f"Unblocked IP {ip_address}: {reason}")
        else:
            logger.warning(f"Failed to unblock IP {ip_address}")

        return success

    @staticmethod
    async def check_auto_block(db: AsyncSession, ip_address: str, alert: models.Alert):
        """
        Verifica si se debe bloquear automáticamente una IP según las políticas

        Args:
            db: Sesión de base de datos
            ip_address: IP a verificar
            alert: Alerta que disparó la verificación
        """
        # Obtener política activa
        policy = await FirewallService.get_default_policy(db)

        if not policy or not policy.enabled:
            return

        # Si está en blacklist y auto_block_blacklist está activo
        if policy.auto_block_blacklist:
            blacklist_query = select(models.IPBlacklist).where(
                models.IPBlacklist.ip_address == ip_address
            )
            result = await db.execute(blacklist_query)
            if result.scalar_one_or_none():
                await FirewallService.block_ip(
                    db,
                    ip_address,
                    reason=f"Auto-block: Blacklisted IP",
                    performed_by="policy",
                    duration_hours=policy.block_duration_hours
                )
                return

        # Si auto_block_on_alert está activo, contar alertas
        if policy.auto_block_on_alert and alert.severity in ['high', 'critical']:
            # Contar alertas de esta IP en las últimas 24 horas
            time_threshold = datetime.utcnow() - timedelta(hours=24)
            alert_count_query = select(func.count(models.Alert.id)).where(
                and_(
                    models.Alert.source_ip == ip_address,
                    models.Alert.timestamp > time_threshold,
                    models.Alert.severity.in_(['high', 'critical'])
                )
            )
            result = await db.execute(alert_count_query)
            alert_count = result.scalar() or 0

            if alert_count >= policy.alert_threshold:
                await FirewallService.block_ip(
                    db,
                    ip_address,
                    reason=f"Auto-block: {alert_count} critical alerts in 24h",
                    performed_by="policy",
                    duration_hours=policy.block_duration_hours
                )

    @staticmethod
    async def cleanup_expired_blocks(db: AsyncSession):
        """Tarea periódica que desbloquea IPs con bloqueos expirados"""
        while True:
            try:
                await asyncio.sleep(300)  # Ejecutar cada 5 minutos

                # Buscar bloqueos expirados
                now = datetime.utcnow()
                expired_query = select(models.FirewallLog).where(
                    and_(
                        models.FirewallLog.action.in_(['block', 'auto_block']),
                        models.FirewallLog.expires_at.isnot(None),
                        models.FirewallLog.expires_at <= now,
                        models.FirewallLog.success == True
                    )
                ).order_by(models.FirewallLog.timestamp)

                result = await db.execute(expired_query)
                expired_blocks = result.scalars().all()

                for block in expired_blocks:
                    # Verificar si no hay un bloqueo más reciente
                    recent_query = select(models.FirewallLog).where(
                        and_(
                            models.FirewallLog.ip_address == block.ip_address,
                            models.FirewallLog.timestamp > block.timestamp,
                            models.FirewallLog.action.in_(['block', 'auto_block']),
                            models.FirewallLog.success == True
                        )
                    )
                    recent_result = await db.execute(recent_query)
                    if recent_result.scalar_one_or_none():
                        continue  # Hay un bloqueo más reciente, no desbloquear

                    # Desbloquear
                    await FirewallService.unblock_ip(
                        db,
                        block.ip_address,
                        reason="Temporary block expired",
                        performed_by="system"
                    )

            except Exception as e:
                logger.error(f"Error in cleanup_expired_blocks: {e}")

    @staticmethod
    async def get_firewall_logs(
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100,
        ip_address: Optional[str] = None,
        action: Optional[str] = None
    ) -> List[models.FirewallLog]:
        """Obtiene logs del firewall"""
        query = select(models.FirewallLog).order_by(desc(models.FirewallLog.timestamp))

        conditions = []
        if ip_address:
            conditions.append(models.FirewallLog.ip_address == ip_address)
        if action:
            conditions.append(models.FirewallLog.action == action)

        if conditions:
            query = query.where(and_(*conditions))

        query = query.offset(skip).limit(limit)

        result = await db.execute(query)
        return result.scalars().all()

    @staticmethod
    async def get_blocked_ips_from_firewall() -> List[dict]:
        """Obtiene IPs bloqueadas directamente del firewall"""
        return FirewallManager.get_blocked_ips()

    @staticmethod
    def get_firewall_statistics() -> dict:
        """Obtiene estadísticas del firewall"""
        return FirewallManager.get_statistics()

    @staticmethod
    async def on_whitelist_added(db: AsyncSession, ip_address: str):
        """Callback cuando se añade una IP a la whitelist"""
        # Añadir a firewall whitelist
        FirewallManager.add_whitelist_ip(ip_address)

        # Si está bloqueada, desbloquear
        if FirewallManager.is_blocked(ip_address):
            await FirewallService.unblock_ip(
                db,
                ip_address,
                reason="Added to whitelist",
                performed_by="system"
            )

    @staticmethod
    async def on_whitelist_removed(db: AsyncSession, ip_address: str):
        """Callback cuando se elimina una IP de la whitelist"""
        FirewallManager.remove_whitelist_ip(ip_address)

    @staticmethod
    async def on_blacklist_added(db: AsyncSession, ip_address: str, description: str):
        """Callback cuando se añade una IP a la blacklist"""
        policy = await FirewallService.get_default_policy(db)

        if policy and policy.enabled and policy.auto_block_blacklist:
            await FirewallService.block_ip(
                db,
                ip_address,
                reason=f"Blacklisted: {description or 'No description'}",
                performed_by="system",
                duration_hours=policy.block_duration_hours
            )

    @staticmethod
    async def on_blacklist_removed(db: AsyncSession, ip_address: str):
        """Callback cuando se elimina una IP de la blacklist"""
        # Opcionalmente desbloquear si fue bloqueada por blacklist
        # Por ahora no desbloqueamos automáticamente por seguridad
        logger.info(f"IP {ip_address} removed from blacklist (not auto-unblocking)")
