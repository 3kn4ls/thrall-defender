"""
Audit Service
=============
Sistema de auditoría completo para trazabilidad de todas las acciones.
Registra quién hizo qué, cuándo y desde dónde.

Inspirado en: Splunk, AWS CloudTrail, Azure Activity Log
"""

import json
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, Dict, Any, List

from . import models, schemas


class AuditService:
    """Servicio centralizado para auditoría y trazabilidad"""

    @classmethod
    async def log(
        cls,
        db: AsyncSession,
        action: str,
        category: str,
        description: str,
        severity: str = "info",
        performed_by: str = "system",
        source_ip: Optional[str] = None,
        user_agent: Optional[str] = None,
        target: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        success: bool = True,
        error_message: Optional[str] = None,
        affected_resources: Optional[List[str]] = None,
        previous_value: Optional[str] = None,
        new_value: Optional[str] = None
    ) -> models.AuditLog:
        """
        Registra una acción en el log de auditoría.

        Args:
            action: Acción realizada (ej: "block_ip", "acknowledge_alert")
            category: Categoría (firewall, ddos, alerts, config, system)
            description: Descripción legible de la acción
            severity: info, warning, critical
            performed_by: Quién realizó la acción (system, admin, api, auto)
            source_ip: IP desde donde se realizó
            user_agent: User agent del cliente
            target: Recurso afectado (ej: IP, ID de alerta)
            details: Diccionario con detalles adicionales (será JSON)
            success: Si la acción fue exitosa
            error_message: Mensaje de error si falló
            affected_resources: Lista de recursos afectados
            previous_value: Valor anterior (para cambios de config)
            new_value: Valor nuevo (para cambios de config)
        """
        audit_log = models.AuditLog(
            action=action,
            category=category,
            severity=severity,
            performed_by=performed_by,
            source_ip=source_ip,
            user_agent=user_agent,
            description=description,
            target=target,
            details=json.dumps(details) if details else None,
            success=success,
            error_message=error_message,
            affected_resources=json.dumps(affected_resources) if affected_resources else None,
            previous_value=previous_value,
            new_value=new_value
        )

        db.add(audit_log)
        await db.commit()
        await db.refresh(audit_log)

        return audit_log

    # ========== MÉTODOS HELPER PARA ACCIONES COMUNES ==========

    @classmethod
    async def log_firewall_block(
        cls,
        db: AsyncSession,
        ip_address: str,
        reason: str,
        performed_by: str = "system",
        source_ip: Optional[str] = None,
        duration_hours: Optional[int] = None
    ):
        """Registra un bloqueo de firewall"""
        details = {"duration_hours": duration_hours} if duration_hours else None

        return await cls.log(
            db=db,
            action="block_ip",
            category="firewall",
            description=f"IP {ip_address} bloqueada: {reason}",
            severity="warning",
            performed_by=performed_by,
            source_ip=source_ip,
            target=ip_address,
            details=details
        )

    @classmethod
    async def log_firewall_unblock(
        cls,
        db: AsyncSession,
        ip_address: str,
        reason: str,
        performed_by: str = "system",
        source_ip: Optional[str] = None
    ):
        """Registra un desbloqueo de firewall"""
        return await cls.log(
            db=db,
            action="unblock_ip",
            category="firewall",
            description=f"IP {ip_address} desbloqueada: {reason}",
            severity="info",
            performed_by=performed_by,
            source_ip=source_ip,
            target=ip_address
        )

    @classmethod
    async def log_alert_acknowledged(
        cls,
        db: AsyncSession,
        alert_id: int,
        alert_type: str,
        source_ip_alert: str,
        performed_by: str = "system",
        source_ip: Optional[str] = None
    ):
        """Registra que una alerta fue reconocida"""
        return await cls.log(
            db=db,
            action="acknowledge_alert",
            category="alerts",
            description=f"Alerta #{alert_id} ({alert_type}) de {source_ip_alert} reconocida",
            severity="info",
            performed_by=performed_by,
            source_ip=source_ip,
            target=str(alert_id)
        )

    @classmethod
    async def log_ddos_mitigation_started(
        cls,
        db: AsyncSession,
        target_ip: str,
        attack_type: str,
        severity: str = "critical",
        performed_by: str = "system"
    ):
        """Registra inicio de mitigación DDoS"""
        return await cls.log(
            db=db,
            action="ddos_mitigation_start",
            category="ddos",
            description=f"Mitigación DDoS iniciada contra {target_ip} (tipo: {attack_type})",
            severity=severity,
            performed_by=performed_by,
            target=target_ip,
            details={"attack_type": attack_type}
        )

    @classmethod
    async def log_ddos_mitigation_ended(
        cls,
        db: AsyncSession,
        target_ip: str,
        attack_type: str,
        duration_seconds: int,
        performed_by: str = "system"
    ):
        """Registra fin de mitigación DDoS"""
        return await cls.log(
            db=db,
            action="ddos_mitigation_end",
            category="ddos",
            description=f"Mitigación DDoS finalizada para {target_ip} (duración: {duration_seconds}s)",
            severity="warning",
            performed_by=performed_by,
            target=target_ip,
            details={"attack_type": attack_type, "duration_seconds": duration_seconds}
        )

    @classmethod
    async def log_config_change(
        cls,
        db: AsyncSession,
        config_name: str,
        previous_value: str,
        new_value: str,
        performed_by: str = "admin",
        source_ip: Optional[str] = None
    ):
        """Registra un cambio de configuración"""
        return await cls.log(
            db=db,
            action="config_change",
            category="config",
            description=f"Configuración '{config_name}' modificada",
            severity="warning",
            performed_by=performed_by,
            source_ip=source_ip,
            target=config_name,
            previous_value=previous_value,
            new_value=new_value
        )

    @classmethod
    async def log_whitelist_add(
        cls,
        db: AsyncSession,
        ip_address: str,
        description: str,
        performed_by: str = "admin",
        source_ip: Optional[str] = None
    ):
        """Registra añadir IP a whitelist"""
        return await cls.log(
            db=db,
            action="whitelist_add",
            category="firewall",
            description=f"IP {ip_address} añadida a whitelist: {description}",
            severity="info",
            performed_by=performed_by,
            source_ip=source_ip,
            target=ip_address
        )

    @classmethod
    async def log_blacklist_add(
        cls,
        db: AsyncSession,
        ip_address: str,
        description: str,
        performed_by: str = "admin",
        source_ip: Optional[str] = None
    ):
        """Registra añadir IP a blacklist"""
        return await cls.log(
            db=db,
            action="blacklist_add",
            category="firewall",
            description=f"IP {ip_address} añadida a blacklist: {description}",
            severity="warning",
            performed_by=performed_by,
            source_ip=source_ip,
            target=ip_address
        )

    @classmethod
    async def log_system_event(
        cls,
        db: AsyncSession,
        event: str,
        description: str,
        severity: str = "info",
        details: Optional[Dict[str, Any]] = None
    ):
        """Registra un evento del sistema"""
        return await cls.log(
            db=db,
            action=event,
            category="system",
            description=description,
            severity=severity,
            performed_by="system",
            details=details
        )

    @classmethod
    async def log_error(
        cls,
        db: AsyncSession,
        action: str,
        error_message: str,
        category: str = "system",
        details: Optional[Dict[str, Any]] = None
    ):
        """Registra un error"""
        return await cls.log(
            db=db,
            action=action,
            category=category,
            description=f"Error en {action}",
            severity="critical",
            performed_by="system",
            success=False,
            error_message=error_message,
            details=details
        )
