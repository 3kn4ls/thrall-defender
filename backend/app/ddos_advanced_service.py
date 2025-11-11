"""
Advanced DDoS Protection Service
Professional-grade DDoS mitigation with multiple levels, geo-blocking, and pattern detection
"""
import logging
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Tuple
from collections import defaultdict, deque
from sqlalchemy import select, update, and_, or_, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app import models, schemas
from app.geoip_service import GeoIPService
from app.firewall_manager import FirewallManager

logger = logging.getLogger(__name__)


class DDoSAdvancedService:
    """Advanced DDoS protection service with professional features"""

    # Default mitigation levels
    DEFAULT_LEVELS = {
        "low": {
            "name": "low",
            "description": "Protección básica - Umbrales altos, adecuado para tráfico normal",
            "pps_threshold": 200,
            "syn_threshold": 100,
            "udp_threshold": 400,
            "icmp_threshold": 100,
            "connection_threshold": 200,
            "rate_limit_enabled": True,
            "rate_limit_pps": 100,
            "rate_limit_burst": 200,
            "challenge_mode": "none",
            "geo_blocking_enabled": False,
            "auto_mitigate": True,
            "mitigation_duration": 1800
        },
        "medium": {
            "name": "medium",
            "description": "Protección estándar - Balance entre seguridad y usabilidad",
            "pps_threshold": 100,
            "syn_threshold": 50,
            "udp_threshold": 200,
            "icmp_threshold": 50,
            "connection_threshold": 100,
            "rate_limit_enabled": True,
            "rate_limit_pps": 50,
            "rate_limit_burst": 100,
            "challenge_mode": "none",
            "geo_blocking_enabled": False,
            "auto_mitigate": True,
            "mitigation_duration": 3600
        },
        "high": {
            "name": "high",
            "description": "Alta protección - Umbrales estrictos, puede afectar tráfico legítimo",
            "pps_threshold": 50,
            "syn_threshold": 25,
            "udp_threshold": 100,
            "icmp_threshold": 25,
            "connection_threshold": 50,
            "rate_limit_enabled": True,
            "rate_limit_pps": 25,
            "rate_limit_burst": 50,
            "challenge_mode": "javascript",
            "challenge_threshold": 70,
            "geo_blocking_enabled": True,
            "auto_mitigate": True,
            "mitigation_duration": 7200
        },
        "aggressive": {
            "name": "aggressive",
            "description": "Máxima protección - Solo para ataques severos, afectará usabilidad",
            "pps_threshold": 20,
            "syn_threshold": 10,
            "udp_threshold": 40,
            "icmp_threshold": 10,
            "connection_threshold": 20,
            "rate_limit_enabled": True,
            "rate_limit_pps": 10,
            "rate_limit_burst": 20,
            "challenge_mode": "proof_of_work",
            "challenge_threshold": 50,
            "geo_blocking_enabled": True,
            "auto_mitigate": True,
            "mitigation_duration": 14400
        }
    }

    @classmethod
    async def initialize_defaults(cls, db: AsyncSession):
        """Initialize default mitigation levels and config"""
        logger.info("Initializing DDoS advanced protection defaults")

        # Create default mitigation levels
        for level_name, level_data in cls.DEFAULT_LEVELS.items():
            result = await db.execute(
                select(models.DDoSMitigationLevel).where(
                    models.DDoSMitigationLevel.name == level_name
                )
            )
            existing = result.scalar_one_or_none()

            if not existing:
                level = models.DDoSMitigationLevel(**level_data)
                # Set medium as default active
                if level_name == "medium":
                    level.is_active = True
                db.add(level)
                logger.info(f"Created mitigation level: {level_name}")

        # Create default advanced config
        result = await db.execute(
            select(models.DDoSAdvancedConfig).where(
                models.DDoSAdvancedConfig.name == "default"
            )
        )
        existing_config = result.scalar_one_or_none()

        if not existing_config:
            config = models.DDoSAdvancedConfig(name="default")
            db.add(config)
            logger.info("Created default advanced DDoS config")

        await db.commit()
        logger.info("DDoS advanced protection initialized")

    @classmethod
    async def get_active_level(cls, db: AsyncSession) -> Optional[models.DDoSMitigationLevel]:
        """Get the currently active mitigation level"""
        result = await db.execute(
            select(models.DDoSMitigationLevel).where(
                models.DDoSMitigationLevel.is_active == True
            )
        )
        return result.scalar_one_or_none()

    @classmethod
    async def set_active_level(cls, db: AsyncSession, level_name: str) -> bool:
        """Set a mitigation level as active"""
        try:
            # Deactivate all levels
            await db.execute(
                update(models.DDoSMitigationLevel).values(is_active=False)
            )

            # Activate selected level
            result = await db.execute(
                update(models.DDoSMitigationLevel)
                .where(models.DDoSMitigationLevel.name == level_name)
                .values(is_active=True)
            )

            await db.commit()

            if result.rowcount > 0:
                logger.info(f"Activated mitigation level: {level_name}")
                return True
            else:
                logger.warning(f"Mitigation level not found: {level_name}")
                return False

        except Exception as e:
            logger.error(f"Error setting active level: {e}")
            await db.rollback()
            return False

