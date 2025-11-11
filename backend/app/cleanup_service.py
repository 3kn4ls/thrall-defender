"""
Database cleanup service for purging old records
Runs periodically to keep database size manageable
"""
import asyncio
from datetime import datetime, timedelta
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from app.database import async_session_maker
from app import models

logger = logging.getLogger(__name__)


class CleanupService:
    """Service for cleaning up old database records"""

    # Retention periods (in hours)
    RETENTION_PERIODS = {
        'packets': 48,          # 48 hours for packets
        'alerts': 48,           # 48 hours for alerts
        'ddos_attacks': 48,     # 48 hours for DDoS attack records
        'firewall_logs': 48,    # 48 hours for firewall logs
        'stats_cache': 24       # 24 hours for cached stats
    }

    # Cleanup interval in seconds (run every 6 hours)
    CLEANUP_INTERVAL = 6 * 60 * 60

    @classmethod
    async def cleanup_old_records(cls, db: AsyncSession) -> dict:
        """
        Clean up old records from all tables
        Returns dict with cleanup statistics
        """
        logger.info("Starting database cleanup...")
        stats = {}

        try:
            # Clean up packets
            cutoff_time = datetime.utcnow() - timedelta(hours=cls.RETENTION_PERIODS['packets'])
            result = await db.execute(
                delete(models.Packet).where(models.Packet.timestamp < cutoff_time)
            )
            stats['packets_deleted'] = result.rowcount
            logger.info(f"Deleted {result.rowcount} old packets")

            # Clean up alerts
            cutoff_time = datetime.utcnow() - timedelta(hours=cls.RETENTION_PERIODS['alerts'])
            result = await db.execute(
                delete(models.Alert).where(
                    models.Alert.created_at < cutoff_time,
                    models.Alert.acknowledged == True  # Only delete acknowledged alerts
                )
            )
            stats['alerts_deleted'] = result.rowcount
            logger.info(f"Deleted {result.rowcount} old alerts")

            # Clean up DDoS attack records (keep unmitigated attacks)
            cutoff_time = datetime.utcnow() - timedelta(hours=cls.RETENTION_PERIODS['ddos_attacks'])
            result = await db.execute(
                delete(models.DDoSAttack).where(
                    models.DDoSAttack.detected_at < cutoff_time,
                    models.DDoSAttack.mitigated == True
                )
            )
            stats['ddos_attacks_deleted'] = result.rowcount
            logger.info(f"Deleted {result.rowcount} old DDoS attack records")

            # Clean up firewall logs
            cutoff_time = datetime.utcnow() - timedelta(hours=cls.RETENTION_PERIODS['firewall_logs'])
            result = await db.execute(
                delete(models.FirewallLog).where(models.FirewallLog.timestamp < cutoff_time)
            )
            stats['firewall_logs_deleted'] = result.rowcount
            logger.info(f"Deleted {result.rowcount} old firewall logs")

            await db.commit()

            stats['cleanup_time'] = datetime.utcnow().isoformat()
            stats['success'] = True

            logger.info(f"Database cleanup completed: {stats}")
            return stats

        except Exception as e:
            logger.error(f"Error during database cleanup: {e}")
            await db.rollback()
            stats['success'] = False
            stats['error'] = str(e)
            return stats

    @classmethod
    async def start_cleanup_task(cls):
        """
        Start background task for periodic cleanup
        This runs indefinitely until the application shuts down
        """
        logger.info(f"Starting cleanup task (runs every {cls.CLEANUP_INTERVAL / 3600} hours)")

        while True:
            try:
                # Wait for the interval
                await asyncio.sleep(cls.CLEANUP_INTERVAL)

                # Run cleanup
                async with async_session_maker() as db:
                    await cls.cleanup_old_records(db)

            except asyncio.CancelledError:
                logger.info("Cleanup task cancelled")
                break
            except Exception as e:
                logger.error(f"Error in cleanup task: {e}")
                # Continue running even if there's an error
                await asyncio.sleep(60)  # Wait a minute before retrying

    @classmethod
    async def get_database_stats(cls, db: AsyncSession) -> dict:
        """
        Get current database statistics
        """
        stats = {}

        try:
            # Count records in each table
            result = await db.execute(select(models.Packet))
            stats['total_packets'] = len(result.scalars().all())

            result = await db.execute(select(models.Alert))
            stats['total_alerts'] = len(result.scalars().all())

            result = await db.execute(select(models.DDoSAttack))
            stats['total_ddos_attacks'] = len(result.scalars().all())

            result = await db.execute(select(models.FirewallLog))
            stats['total_firewall_logs'] = len(result.scalars().all())

            # Get oldest records
            result = await db.execute(
                select(models.Packet).order_by(models.Packet.timestamp.asc()).limit(1)
            )
            oldest_packet = result.scalar_one_or_none()
            if oldest_packet:
                stats['oldest_packet'] = oldest_packet.timestamp.isoformat()

            return stats

        except Exception as e:
            logger.error(f"Error getting database stats: {e}")
            return {'error': str(e)}
