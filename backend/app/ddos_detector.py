import asyncio
import logging
from datetime import datetime, timedelta
from collections import defaultdict, deque
from typing import Dict, Tuple, Optional
import subprocess

logger = logging.getLogger(__name__)


class TrafficAnalyzer:
    """Analiza el tráfico en tiempo real para detectar patrones de DDoS"""

    def __init__(self):
        # Ventanas de tiempo para análisis
        self.packet_counts = defaultdict(lambda: deque(maxlen=1000))  # Últimos 1000 paquetes por IP
        self.connection_attempts = defaultdict(lambda: deque(maxlen=500))  # Intentos de conexión
        self.byte_counts = defaultdict(int)  # Bytes por IP

        # Tracking por protocolo
        self.syn_counts = defaultdict(lambda: deque(maxlen=200))
        self.udp_counts = defaultdict(lambda: deque(maxlen=200))
        self.icmp_counts = defaultdict(lambda: deque(maxlen=100))

        # Timestamps para limpiar datos antiguos
        self.last_cleanup = datetime.utcnow()

    def analyze_packet(self, packet_data: dict) -> dict:
        """
        Analiza un paquete y retorna métricas de DDoS

        Returns:
            dict con indicadores de DDoS
        """
        source_ip = packet_data['source_ip']
        protocol = packet_data['protocol']
        timestamp = datetime.utcnow()
        packet_size = packet_data.get('packet_size', 0)

        # Registrar paquete
        self.packet_counts[source_ip].append(timestamp)
        self.byte_counts[source_ip] += packet_size

        # Tracking por protocolo
        if protocol == 'TCP':
            flags = packet_data.get('flags', '')
            if 'S' in flags and 'A' not in flags:  # SYN flag sin ACK
                self.syn_counts[source_ip].append(timestamp)
        elif protocol == 'UDP':
            self.udp_counts[source_ip].append(timestamp)
        elif protocol == 'ICMP':
            self.icmp_counts[source_ip].append(timestamp)

        # Calcular métricas
        metrics = self._calculate_metrics(source_ip)

        # Limpiar datos antiguos periódicamente
        if (timestamp - self.last_cleanup).seconds > 300:  # Cada 5 minutos
            self._cleanup_old_data()
            self.last_cleanup = timestamp

        return metrics

    def _calculate_metrics(self, ip: str) -> dict:
        """Calcula métricas de tráfico para una IP"""
        now = datetime.utcnow()

        # Paquetes por segundo (últimos 10 segundos)
        packets_10s = self._count_recent(self.packet_counts[ip], seconds=10)
        pps = packets_10s / 10.0

        # Paquetes por minuto
        packets_60s = self._count_recent(self.packet_counts[ip], seconds=60)
        ppm = packets_60s

        # SYN flood detection
        syn_10s = self._count_recent(self.syn_counts[ip], seconds=10)
        syn_rate = syn_10s / 10.0

        # UDP flood detection
        udp_10s = self._count_recent(self.udp_counts[ip], seconds=10)
        udp_rate = udp_10s / 10.0

        # ICMP flood detection
        icmp_10s = self._count_recent(self.icmp_counts[ip], seconds=10)
        icmp_rate = icmp_10s / 10.0

        # Bytes por segundo
        total_bytes = self.byte_counts[ip]
        bps = total_bytes / 60.0 if packets_60s > 0 else 0  # Promedio último minuto

        return {
            'ip': ip,
            'packets_per_second': round(pps, 2),
            'packets_per_minute': packets_60s,
            'bytes_per_second': round(bps, 2),
            'syn_rate': round(syn_rate, 2),
            'udp_rate': round(udp_rate, 2),
            'icmp_rate': round(icmp_rate, 2),
            'total_bytes': total_bytes
        }

    def _count_recent(self, timestamps: deque, seconds: int) -> int:
        """Cuenta timestamps recientes dentro de la ventana de tiempo"""
        if not timestamps:
            return 0

        cutoff = datetime.utcnow() - timedelta(seconds=seconds)
        return sum(1 for ts in timestamps if ts > cutoff)

    def _cleanup_old_data(self):
        """Limpia datos antiguos para liberar memoria"""
        cutoff = datetime.utcnow() - timedelta(minutes=10)

        # Limpiar paquetes antiguos
        for ip in list(self.packet_counts.keys()):
            # Filtrar timestamps antiguos
            self.packet_counts[ip] = deque(
                (ts for ts in self.packet_counts[ip] if ts > cutoff),
                maxlen=1000
            )

            # Si no quedan datos, eliminar entrada
            if not self.packet_counts[ip]:
                del self.packet_counts[ip]
                self.byte_counts.pop(ip, None)

        # Limpiar protocolo específico
        for ip in list(self.syn_counts.keys()):
            self.syn_counts[ip] = deque(
                (ts for ts in self.syn_counts[ip] if ts > cutoff),
                maxlen=200
            )
            if not self.syn_counts[ip]:
                del self.syn_counts[ip]

        for ip in list(self.udp_counts.keys()):
            self.udp_counts[ip] = deque(
                (ts for ts in self.udp_counts[ip] if ts > cutoff),
                maxlen=200
            )
            if not self.udp_counts[ip]:
                del self.udp_counts[ip]

        for ip in list(self.icmp_counts.keys()):
            self.icmp_counts[ip] = deque(
                (ts for ts in self.icmp_counts[ip] if ts > cutoff),
                maxlen=100
            )
            if not self.icmp_counts[ip]:
                del self.icmp_counts[ip]

    def get_top_ips(self, limit: int = 10) -> list:
        """Obtiene las IPs con más tráfico"""
        ip_metrics = []

        for ip in self.packet_counts.keys():
            metrics = self._calculate_metrics(ip)
            ip_metrics.append(metrics)

        # Ordenar por paquetes por segundo
        ip_metrics.sort(key=lambda x: x['packets_per_second'], reverse=True)

        return ip_metrics[:limit]

    def get_metrics_for_ip(self, ip: str) -> Optional[dict]:
        """Obtiene métricas para una IP específica"""
        if ip not in self.packet_counts:
            return None

        return self._calculate_metrics(ip)


class DDoSDetector:
    """Detecta y mitiga ataques DDoS"""

    def __init__(self, config: dict = None):
        self.config = config or self._default_config()
        self.analyzer = TrafficAnalyzer()
        self.active_attacks = {}  # IP -> attack info
        self.mitigated_ips = set()  # IPs bajo mitigación

    def _default_config(self) -> dict:
        """Configuración por defecto para detección de DDoS"""
        return {
            'enabled': True,
            'pps_threshold': 100,  # Paquetes por segundo
            'syn_threshold': 50,   # SYN por segundo
            'udp_threshold': 200,  # UDP por segundo
            'icmp_threshold': 50,  # ICMP por segundo
            'auto_mitigate': True,
            'mitigation_duration': 3600,  # 1 hora en segundos
            'alert_threshold': 80,  # % del threshold para alertar
        }

    def update_config(self, config: dict):
        """Actualiza configuración"""
        self.config.update(config)

    def analyze_packet(self, packet_data: dict) -> Tuple[bool, Optional[dict]]:
        """
        Analiza un paquete para detectar DDoS

        Returns:
            (is_ddos, attack_info)
        """
        if not self.config['enabled']:
            return False, None

        # Analizar métricas
        metrics = self.analyzer.analyze_packet(packet_data)
        source_ip = packet_data['source_ip']

        # Detectar diferentes tipos de ataque
        attack_type = None
        severity = 'low'

        # SYN Flood
        if metrics['syn_rate'] > self.config['syn_threshold']:
            attack_type = 'syn_flood'
            severity = self._calculate_severity(
                metrics['syn_rate'],
                self.config['syn_threshold']
            )

        # UDP Flood
        elif metrics['udp_rate'] > self.config['udp_threshold']:
            attack_type = 'udp_flood'
            severity = self._calculate_severity(
                metrics['udp_rate'],
                self.config['udp_threshold']
            )

        # ICMP Flood
        elif metrics['icmp_rate'] > self.config['icmp_threshold']:
            attack_type = 'icmp_flood'
            severity = self._calculate_severity(
                metrics['icmp_rate'],
                self.config['icmp_threshold']
            )

        # Generic high traffic
        elif metrics['packets_per_second'] > self.config['pps_threshold']:
            attack_type = 'high_traffic'
            severity = self._calculate_severity(
                metrics['packets_per_second'],
                self.config['pps_threshold']
            )

        # Si se detectó ataque
        if attack_type:
            attack_info = {
                'ip': source_ip,
                'type': attack_type,
                'severity': severity,
                'metrics': metrics,
                'timestamp': datetime.utcnow()
            }

            # Registrar ataque activo
            self.active_attacks[source_ip] = attack_info

            return True, attack_info

        return False, None

    def _calculate_severity(self, current: float, threshold: float) -> str:
        """Calcula la severidad del ataque basado en el threshold"""
        ratio = current / threshold

        if ratio >= 5:
            return 'critical'
        elif ratio >= 3:
            return 'high'
        elif ratio >= 1.5:
            return 'medium'
        else:
            return 'low'

    async def apply_rate_limiting(self, ip: str, attack_type: str) -> bool:
        """
        Aplica rate limiting usando iptables hashlimit

        Args:
            ip: IP a limitar
            attack_type: Tipo de ataque detectado

        Returns:
            True si se aplicó exitosamente
        """
        try:
            # Determinar límite según tipo de ataque
            if attack_type == 'syn_flood':
                limit = f"{self.config['syn_threshold']}/sec"
                protocol = 'tcp'
                flags = '--tcp-flags SYN,ACK,FIN,RST SYN'
            elif attack_type == 'udp_flood':
                limit = f"{self.config['udp_threshold']}/sec"
                protocol = 'udp'
                flags = ''
            elif attack_type == 'icmp_flood':
                limit = f"{self.config['icmp_threshold']}/sec"
                protocol = 'icmp'
                flags = ''
            else:
                limit = f"{self.config['pps_threshold']}/sec"
                protocol = 'all'
                flags = ''

            # Aplicar rate limit con iptables hashlimit
            cmd = [
                'iptables', '-A', 'THRALL_DEFENDER',
                '-s', ip,
                '-m', 'hashlimit',
                '--hashlimit-above', limit,
                '--hashlimit-mode', 'srcip',
                '--hashlimit-name', f'ddos_{attack_type}',
                '-j', 'DROP'
            ]

            if protocol != 'all':
                cmd.insert(4, '-p')
                cmd.insert(5, protocol)

            if flags:
                cmd.extend(flags.split())

            # Ejecutar comando
            result = subprocess.run(cmd, capture_output=True, timeout=10)

            if result.returncode == 0:
                self.mitigated_ips.add(ip)
                logger.info(f"Applied rate limiting to {ip} for {attack_type}")
                return True
            else:
                logger.error(f"Failed to apply rate limiting: {result.stderr.decode()}")
                return False

        except Exception as e:
            logger.error(f"Error applying rate limiting: {e}")
            return False

    def get_active_attacks(self) -> list:
        """Obtiene lista de ataques activos"""
        return [
            {
                **attack,
                'timestamp': attack['timestamp'].isoformat()
            }
            for attack in self.active_attacks.values()
        ]

    def get_top_attackers(self, limit: int = 10) -> list:
        """Obtiene las IPs con más tráfico sospechoso"""
        return self.analyzer.get_top_ips(limit)

    def clear_attack(self, ip: str):
        """Limpia el registro de un ataque"""
        self.active_attacks.pop(ip, None)

    def is_under_mitigation(self, ip: str) -> bool:
        """Verifica si una IP está bajo mitigación"""
        return ip in self.mitigated_ips
