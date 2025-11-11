"""
GeoIP Service for IP geolocation
Uses MaxMind GeoLite2 database if available
"""
import logging
from pathlib import Path
from typing import Optional, Dict
import os

try:
    import geoip2.database
    import geoip2.errors
    GEOIP2_AVAILABLE = True
except ImportError:
    GEOIP2_AVAILABLE = False

logger = logging.getLogger(__name__)


class GeoIPService:
    """Service for IP geolocation using MaxMind GeoLite2"""

    _reader = None
    _initialized = False

    # Possible locations for GeoLite2-Country database
    DATABASE_PATHS = [
        "/usr/share/GeoIP/GeoLite2-Country.mmdb",
        "/var/lib/GeoIP/GeoLite2-Country.mmdb",
        "./GeoLite2-Country.mmdb",
        "../GeoLite2-Country.mmdb",
        "./data/GeoLite2-Country.mmdb",
    ]

    @classmethod
    def initialize(cls):
        """Initialize the GeoIP database reader"""
        if cls._initialized:
            return

        if not GEOIP2_AVAILABLE:
            logger.warning("geoip2 library not available. Country detection disabled.")
            cls._initialized = True
            return

        # Try to find the database
        for db_path in cls.DATABASE_PATHS:
            if os.path.exists(db_path):
                try:
                    cls._reader = geoip2.database.Reader(db_path)
                    logger.info(f"GeoIP database loaded from: {db_path}")
                    cls._initialized = True
                    return
                except Exception as e:
                    logger.error(f"Error loading GeoIP database from {db_path}: {e}")
                    continue

        logger.warning(
            "GeoLite2 database not found. Country detection disabled. "
            "Download from https://dev.maxmind.com/geoip/geolite2-free-geolocation-data "
            "and place in one of: " + ", ".join(cls.DATABASE_PATHS)
        )
        cls._initialized = True

    @classmethod
    def get_country(cls, ip_address: str) -> Optional[Dict[str, str]]:
        """
        Get country information for an IP address

        Returns:
            Dict with country_code, country_name, continent_code, or None if unavailable
        """
        if not cls._initialized:
            cls.initialize()

        if not cls._reader:
            return None

        try:
            response = cls._reader.country(ip_address)
            return {
                "country_code": response.country.iso_code or "UNKNOWN",
                "country_name": response.country.name or "Unknown",
                "continent_code": response.continent.code or "UNKNOWN",
                "continent_name": response.continent.name or "Unknown",
            }
        except geoip2.errors.AddressNotFoundError:
            logger.debug(f"IP {ip_address} not found in GeoIP database")
            return {
                "country_code": "PRIVATE",
                "country_name": "Private/Local Network",
                "continent_code": "PRIVATE",
                "continent_name": "Private Network",
            }
        except Exception as e:
            logger.error(f"Error looking up IP {ip_address}: {e}")
            return None

    @classmethod
    def is_from_country(cls, ip_address: str, country_codes: list) -> bool:
        """
        Check if IP is from one of the specified countries

        Args:
            ip_address: IP address to check
            country_codes: List of ISO 2-letter country codes (e.g., ['US', 'GB'])

        Returns:
            True if IP is from one of the countries, False otherwise
        """
        country = cls.get_country(ip_address)
        if not country:
            return False

        return country.get("country_code") in [code.upper() for code in country_codes]

    @classmethod
    def close(cls):
        """Close the GeoIP database reader"""
        if cls._reader:
            cls._reader.close()
            cls._reader = None
            cls._initialized = False
            logger.info("GeoIP database closed")


# Initialize on import
GeoIPService.initialize()
