from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, desc
from datetime import datetime, timedelta
from . import models, schemas
from .ddos_detector import DDoSDetector
from .firewall_service import FirewallService
from typing import List, Optional
import logging
import json

logger = logging.getLogger(__name__)

# Instancia global del detector
ddos_detector: Optional[DDoSDetector] = None


class DDoSService:
    """Servicio para gestión de protección DDoS"""

    @staticmethod
    async def initialize(db: AsyncSession):
        """Inicializa el servicio de protección DDoS"""
        global ddos_detector

        # Obtener o crear configuración
        config = await DDoSService.get_default_config(db)

        # Crear detector con configuración
        ddos_detector = DDoSDetector({
            'enabled': config.enabled,
            'pps_threshold': config.pps_threshold,
            'syn_threshold': config.syn_threshold,
            'udp_threshold': config.udp_threshold,
            'icmp_threshold': config.icmp_threshold,
            'auto_mitigate': config.auto_mitigate,
            'mitigation_duration': config.mitigation_duration,
            'alert_threshold': config.alert_threshold,
        })

        logger.info("DDoS protection initialized")
        return True

    @staticmethod
    async def get_default_config(db: AsyncSession) -> models.DDoSConfig:
        """Obtiene o crea la configuración por defecto"""
        query = select(models.DDoSConfig).where(
            models.DDoSConfig.name == "default"
        )
        result = await db.execute(query)
        config = result.scalar_one_or_none()

        if not config:
            # Crear configuración por defecto
            config = models.DDoSConfig(
                name="default",
                enabled=True,
                pps_threshold=100,
                syn_threshold=50,
                udp_threshold=200,
                icmp_threshold=50,
                auto_mitigate=True,
                mitigation_duration=3600,
                alert_threshold=80
            )
            db.add(config)
            await db.commit()
            await db.refresh(config)
            logger.info("Created default DDoS protection config")

        return config

    @staticmethod
    async def analyze_packet(db: AsyncSession, packet_data: dict):
        """
        Analiza un paquete para detectar DDoS

        Args:
            db: Sesión de base de datos
            packet_data: Datos del paquete capturado
        """
        if not ddos_detector:
            return

        # Analizar paquete
        is_ddos, attack_info = ddos_detector.analyze_packet(packet_data)

        if is_ddos and attack_info:
            # Registrar ataque en base de datos
            await DDoSService._record_attack(db, attack_info)

            # Crear alerta
            await DDoSService._create_ddos_alert(db, attack_info)

            # Auto-mitigación si está habilitada
            if ddos_detector.config['auto_mitigate']:
                await DDoSService.mitigate_attack(
                    db,
                    attack_info['ip'],
                    attack_info['type']
                )

    @staticmethod
    async def _record_attack(db: AsyncSession, attack_info: dict):
        """Registra un ataque DDoS en la base de datos"""
        try:
            # Verificar si ya existe un ataque activo de esta IP
            query = select(models.DDoSAttack).where(
                and_(
                    models.DDoSAttack.source_ip == attack_info['ip'],
                    models.DDoSAttack.ended_at.is_(None)
                )
            )
            result = await db.execute(query)
            existing_attack = result.scalar_one_or_none()

            if existing_attack:
                # Actualizar ataque existente
                existing_attack.packets_per_second = attack_info['metrics']['packets_per_second']
                existing_attack.bytes_per_second = attack_info['metrics']['bytes_per_second']
                existing_attack.severity = attack_info['severity']
                existing_attack.metrics = json.dumps(attack_info['metrics'])
            else:
                # Crear nuevo registro de ataque
                attack = models.DDoSAttack(
                    source_ip=attack_info['ip'],
                    attack_type=attack_info['type'],
                    severity=attack_info['severity'],
                    packets_per_second=attack_info['metrics']['packets_per_second'],
                    bytes_per_second=attack_info['metrics']['bytes_per_second'],
                    mitigated=False,
                    metrics=json.dumps(attack_info['metrics'])
                )
                db.add(attack)

            await db.commit()

        except Exception as e:
            logger.error(f"Error recording DDoS attack: {e}")
            await db.rollback()

    @staticmethod
    async def _create_ddos_alert(db: AsyncSession, attack_info: dict):
        """Crea una alerta de DDoS"""
        try:
            # Verificar si ya hay una alerta reciente de esta IP
            cutoff = datetime.utcnow() - timedelta(minutes=5)
            query = select(models.Alert).where(
                and_(
                    models.Alert.source_ip == attack_info['ip'],
                    models.Alert.alert_type == 'ddos_attack',
                    models.Alert.timestamp > cutoff
                )
            )
            result = await db.execute(query)
            if result.scalar_one_or_none():
                return  # Ya existe alerta reciente

            # Crear alerta
            alert = models.Alert(
                alert_type='ddos_attack',
                severity=attack_info['severity'],
                source_ip=attack_info['ip'],
                description=f"DDoS attack detected: {attack_info['type']} "
                           f"({attack_info['metrics']['packets_per_second']:.1f} pps)"
            )
            db.add(alert)
            await db.commit()

        except Exception as e:
            logger.error(f"Error creating DDoS alert: {e}")
            await db.rollback()

    @staticmethod
    async def mitigate_attack(db: AsyncSession, ip: str, attack_type: str) -> bool:
        """
        Mitiga un ataque DDoS aplicando rate limiting

        Args:
            db: Sesión de base de datos
            ip: IP atacante
            attack_type: Tipo de ataque

        Returns:
            True si se mitigó exitosamente
        """
        if not ddos_detector:
            return False

        # Aplicar rate limiting
        success = await ddos_detector.apply_rate_limiting(ip, attack_type)

        if success:
            # Actualizar registro de ataque
            query = select(models.DDoSAttack).where(
                and_(
                    models.DDoSAttack.source_ip == ip,
                    models.DDoSAttack.ended_at.is_(None)
                )
            ).order_by(desc(models.DDoSAttack.timestamp))

            result = await db.execute(query)
            attack = result.scalar_one_or_none()

            if attack:
                attack.mitigated = True
                await db.commit()

            logger.info(f"Mitigated DDoS attack from {ip} ({attack_type})")

        return success

    @staticmethod
    async def end_attack(db: AsyncSession, ip: str):
        """Marca un ataque como finalizado"""
        query = select(models.DDoSAttack).where(
            and_(
                models.DDoSAttack.source_ip == ip,
                models.DDoSAttack.ended_at.is_(None)
            )
        )
        result = await db.execute(query)
        attack = result.scalar_one_or_none()

        if attack:
            attack.ended_at = datetime.utcnow()
            attack.duration_seconds = int((attack.ended_at - attack.timestamp).total_seconds())
            await db.commit()

            # Limpiar del detector
            if ddos_detector:
                ddos_detector.clear_attack(ip)

    @staticmethod
    async def get_active_attacks(db: AsyncSession) -> List[models.DDoSAttack]:
        """Obtiene lista de ataques activos"""
        query = select(models.DDoSAttack).where(
            models.DDoSAttack.ended_at.is_(None)
        ).order_by(desc(models.DDoSAttack.timestamp))

        result = await db.execute(query)
        return result.scalars().all()

    @staticmethod
    async def get_attack_history(
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100,
        ip: Optional[str] = None
    ) -> List[models.DDoSAttack]:
        """Obtiene historial de ataques"""
        query = select(models.DDoSAttack).order_by(desc(models.DDoSAttack.timestamp))

        if ip:
            query = query.where(models.DDoSAttack.source_ip == ip)

        query = query.offset(skip).limit(limit)

        result = await db.execute(query)
        return result.scalars().all()

    @staticmethod
    async def get_ddos_statistics(db: AsyncSession) -> schemas.DDoSStats:
        """Obtiene estadísticas de DDoS"""
        # Ataques activos
        active_query = select(func.count(models.DDoSAttack.id)).where(
            models.DDoSAttack.ended_at.is_(None)
        )
        active_result = await db.execute(active_query)
        active_attacks = active_result.scalar() or 0

        # Ataques de hoy
        today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        today_query = select(func.count(models.DDoSAttack.id)).where(
            models.DDoSAttack.timestamp >= today
        )
        today_result = await db.execute(today_query)
        total_attacks_today = today_result.scalar() or 0

        # IPs mitigadas
        mitigated_ips = len(ddos_detector.mitigated_ips) if ddos_detector else 0

        # Top atacantes (últimas 24 horas)
        top_attackers = []
        if ddos_detector:
            top_attackers_data = ddos_detector.get_top_attackers(limit=10)
            top_attackers = [schemas.DDoSMetrics(**data) for data in top_attackers_data]

        # Distribución de tipos de ataque (últimas 24 horas)
        yesterday = datetime.utcnow() - timedelta(hours=24)
        types_query = select(
            models.DDoSAttack.attack_type,
            func.count(models.DDoSAttack.id).label('count')
        ).where(
            models.DDoSAttack.timestamp >= yesterday
        ).group_by(models.DDoSAttack.attack_type)

        types_result = await db.execute(types_query)
        attack_types_distribution = {
            row[0]: row[1] for row in types_result.all()
        }

        return schemas.DDoSStats(
            active_attacks=active_attacks,
            total_attacks_today=total_attacks_today,
            mitigated_ips=mitigated_ips,
            top_attackers=top_attackers,
            attack_types_distribution=attack_types_distribution
        )

    @staticmethod
    async def update_config(db: AsyncSession, config_id: int, updates: dict) -> models.DDoSConfig:
        """Actualiza la configuración de DDoS"""
        query = select(models.DDoSConfig).where(models.DDoSConfig.id == config_id)
        result = await db.execute(query)
        config = result.scalar_one_or_none()

        if not config:
            raise ValueError("Config not found")

        # Actualizar campos
        for field, value in updates.items():
            if value is not None:
                setattr(config, field, value)

        config.updated_at = datetime.utcnow()
        await db.commit()
        await db.refresh(config)

        # Actualizar detector
        if ddos_detector:
            ddos_detector.update_config({
                'enabled': config.enabled,
                'pps_threshold': config.pps_threshold,
                'syn_threshold': config.syn_threshold,
                'udp_threshold': config.udp_threshold,
                'icmp_threshold': config.icmp_threshold,
                'auto_mitigate': config.auto_mitigate,
                'mitigation_duration': config.mitigation_duration,
                'alert_threshold': config.alert_threshold,
            })

        return config

    @staticmethod
    def get_real_time_metrics(ip: Optional[str] = None):
        """Obtiene métricas en tiempo real del detector"""
        if not ddos_detector:
            return []

        if ip:
            metrics = ddos_detector.analyzer.get_metrics_for_ip(ip)
            return [schemas.DDoSMetrics(**metrics)] if metrics else []
        else:
            top_ips = ddos_detector.get_top_attackers(limit=20)
            return [schemas.DDoSMetrics(**data) for data in top_ips]
