import subprocess
import logging
import re
from typing import List, Optional, Tuple
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class FirewallRule:
    """Representa una regla de firewall"""
    def __init__(self, ip_address: str, chain: str = "INPUT", action: str = "DROP"):
        self.ip_address = ip_address
        self.chain = chain
        self.action = action


class FirewallManager:
    """Gestiona reglas de firewall usando iptables"""

    CHAIN_NAME = "THRALL_DEFENDER"
    WHITELIST_IPS = set()  # IPs que nunca deben bloquearse

    @classmethod
    def initialize(cls):
        """Inicializa la cadena personalizada de iptables"""
        try:
            # Crear cadena personalizada si no existe
            result = subprocess.run(
                ['iptables', '-L', cls.CHAIN_NAME, '-n'],
                capture_output=True,
                text=True
            )

            if result.returncode != 0:
                # Crear nueva cadena
                subprocess.run(['iptables', '-N', cls.CHAIN_NAME], check=True)
                logger.info(f"Created iptables chain: {cls.CHAIN_NAME}")

                # Insertar referencia a la cadena en INPUT
                subprocess.run(
                    ['iptables', '-I', 'INPUT', '1', '-j', cls.CHAIN_NAME],
                    check=True
                )
                logger.info(f"Linked {cls.CHAIN_NAME} to INPUT chain")
            else:
                logger.info(f"iptables chain {cls.CHAIN_NAME} already exists")

            # Añadir IPs del sistema a whitelist automáticamente
            cls._add_system_ips_to_whitelist()

            return True

        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to initialize firewall: {e}")
            return False
        except PermissionError:
            logger.error("Permission denied. Need root/CAP_NET_ADMIN to manage iptables")
            return False

    @classmethod
    def _add_system_ips_to_whitelist(cls):
        """Añade IPs del sistema a la whitelist automáticamente"""
        try:
            # Localhost
            cls.WHITELIST_IPS.add("127.0.0.1")
            cls.WHITELIST_IPS.add("::1")

            # Obtener IP local
            result = subprocess.run(
                ['hostname', '-I'],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                local_ips = result.stdout.strip().split()
                for ip in local_ips:
                    cls.WHITELIST_IPS.add(ip)
                    logger.info(f"Added system IP to whitelist: {ip}")

        except Exception as e:
            logger.warning(f"Could not auto-detect system IPs: {e}")

    @classmethod
    def add_whitelist_ip(cls, ip_address: str):
        """Añade una IP a la whitelist de protección"""
        cls.WHITELIST_IPS.add(ip_address)
        logger.info(f"Added {ip_address} to firewall whitelist")

    @classmethod
    def remove_whitelist_ip(cls, ip_address: str):
        """Elimina una IP de la whitelist"""
        cls.WHITELIST_IPS.discard(ip_address)
        logger.info(f"Removed {ip_address} from firewall whitelist")

    @classmethod
    def is_whitelisted(cls, ip_address: str) -> bool:
        """Verifica si una IP está en la whitelist"""
        return ip_address in cls.WHITELIST_IPS

    @classmethod
    def block_ip(cls, ip_address: str, comment: str = "") -> bool:
        """
        Bloquea una IP usando iptables

        Args:
            ip_address: IP a bloquear
            comment: Comentario opcional para la regla

        Returns:
            True si se bloqueó exitosamente, False si no
        """
        # Verificar whitelist
        if cls.is_whitelisted(ip_address):
            logger.warning(f"Cannot block whitelisted IP: {ip_address}")
            return False

        # Validar formato de IP
        if not cls._is_valid_ip(ip_address):
            logger.error(f"Invalid IP address format: {ip_address}")
            return False

        # Verificar si ya está bloqueada
        if cls.is_blocked(ip_address):
            logger.info(f"IP {ip_address} is already blocked")
            return True

        try:
            # Construir comando
            cmd = [
                'iptables',
                '-A', cls.CHAIN_NAME,
                '-s', ip_address,
                '-j', 'DROP'
            ]

            # Añadir comentario si está disponible
            if comment:
                cmd.extend(['-m', 'comment', '--comment', comment[:255]])

            # Ejecutar comando
            subprocess.run(cmd, check=True, timeout=10)
            logger.info(f"Blocked IP: {ip_address}")
            return True

        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to block IP {ip_address}: {e}")
            return False
        except Exception as e:
            logger.error(f"Error blocking IP {ip_address}: {e}")
            return False

    @classmethod
    def unblock_ip(cls, ip_address: str) -> bool:
        """
        Desbloquea una IP

        Args:
            ip_address: IP a desbloquear

        Returns:
            True si se desbloqueó exitosamente, False si no
        """
        if not cls._is_valid_ip(ip_address):
            logger.error(f"Invalid IP address format: {ip_address}")
            return False

        try:
            # Construir comando para eliminar regla
            cmd = [
                'iptables',
                '-D', cls.CHAIN_NAME,
                '-s', ip_address,
                '-j', 'DROP'
            ]

            # Ejecutar comando
            subprocess.run(cmd, check=True, timeout=10)
            logger.info(f"Unblocked IP: {ip_address}")
            return True

        except subprocess.CalledProcessError:
            logger.warning(f"IP {ip_address} was not blocked or rule not found")
            return False
        except Exception as e:
            logger.error(f"Error unblocking IP {ip_address}: {e}")
            return False

    @classmethod
    def is_blocked(cls, ip_address: str) -> bool:
        """
        Verifica si una IP está bloqueada

        Args:
            ip_address: IP a verificar

        Returns:
            True si está bloqueada, False si no
        """
        try:
            result = subprocess.run(
                ['iptables', '-L', cls.CHAIN_NAME, '-n', '--line-numbers'],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode == 0:
                # Buscar la IP en la salida
                for line in result.stdout.split('\n'):
                    if ip_address in line and 'DROP' in line:
                        return True

            return False

        except Exception as e:
            logger.error(f"Error checking if IP is blocked: {e}")
            return False

    @classmethod
    def get_blocked_ips(cls) -> List[dict]:
        """
        Obtiene lista de IPs bloqueadas

        Returns:
            Lista de diccionarios con información de IPs bloqueadas
        """
        blocked_ips = []

        try:
            result = subprocess.run(
                ['iptables', '-L', cls.CHAIN_NAME, '-n', '-v', '--line-numbers'],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode == 0:
                lines = result.stdout.split('\n')[2:]  # Skip header lines

                for line in lines:
                    if 'DROP' in line:
                        parts = line.split()
                        if len(parts) >= 8:
                            blocked_ips.append({
                                'rule_number': parts[0],
                                'packets': parts[1],
                                'bytes': parts[2],
                                'target': parts[3],
                                'protocol': parts[4],
                                'source': parts[7],
                                'destination': parts[8] if len(parts) > 8 else 'anywhere'
                            })

        except Exception as e:
            logger.error(f"Error getting blocked IPs: {e}")

        return blocked_ips

    @classmethod
    def flush_all_rules(cls) -> bool:
        """
        Elimina todas las reglas de la cadena personalizada

        Returns:
            True si se eliminaron exitosamente, False si no
        """
        try:
            subprocess.run(['iptables', '-F', cls.CHAIN_NAME], check=True, timeout=10)
            logger.info(f"Flushed all rules from {cls.CHAIN_NAME}")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to flush rules: {e}")
            return False

    @classmethod
    def _is_valid_ip(cls, ip_address: str) -> bool:
        """
        Valida formato de dirección IP

        Args:
            ip_address: IP a validar

        Returns:
            True si es válida, False si no
        """
        # IPv4 simple validation
        ipv4_pattern = re.compile(r'^(\d{1,3}\.){3}\d{1,3}$')

        if ipv4_pattern.match(ip_address):
            parts = ip_address.split('.')
            return all(0 <= int(part) <= 255 for part in parts)

        # TODO: Add IPv6 validation if needed
        return False

    @classmethod
    def get_statistics(cls) -> dict:
        """
        Obtiene estadísticas del firewall

        Returns:
            Diccionario con estadísticas
        """
        blocked_ips = cls.get_blocked_ips()

        total_packets_blocked = sum(int(ip.get('packets', 0)) for ip in blocked_ips)
        total_bytes_blocked = sum(int(ip.get('bytes', 0)) for ip in blocked_ips)

        return {
            'total_blocked_ips': len(blocked_ips),
            'total_packets_blocked': total_packets_blocked,
            'total_bytes_blocked': total_bytes_blocked,
            'whitelisted_ips': len(cls.WHITELIST_IPS),
            'chain_name': cls.CHAIN_NAME
        }

    @classmethod
    def cleanup(cls):
        """Limpia la cadena personalizada y reglas"""
        try:
            # Eliminar referencia de INPUT
            subprocess.run(
                ['iptables', '-D', 'INPUT', '-j', cls.CHAIN_NAME],
                capture_output=True
            )

            # Flush reglas
            subprocess.run(['iptables', '-F', cls.CHAIN_NAME], capture_output=True)

            # Eliminar cadena
            subprocess.run(['iptables', '-X', cls.CHAIN_NAME], capture_output=True)

            logger.info(f"Cleaned up firewall chain {cls.CHAIN_NAME}")

        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
