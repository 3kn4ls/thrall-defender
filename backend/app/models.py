from sqlalchemy import Column, Integer, String, DateTime, Boolean, Float
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()


class NetworkPacket(Base):
    """Modelo para almacenar paquetes de red capturados"""
    __tablename__ = "network_packets"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    source_ip = Column(String, index=True)
    destination_ip = Column(String, index=True)
    source_port = Column(Integer, index=True)
    destination_port = Column(Integer, index=True)
    protocol = Column(String, index=True)
    packet_size = Column(Integer)
    flags = Column(String, nullable=True)
    payload_preview = Column(String, nullable=True)
    is_blocked = Column(Boolean, default=False)
    is_suspicious = Column(Boolean, default=False, index=True)


class IPWhitelist(Base):
    """IPs en lista blanca"""
    __tablename__ = "ip_whitelist"

    id = Column(Integer, primary_key=True, index=True)
    ip_address = Column(String, unique=True, index=True)
    description = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class IPBlacklist(Base):
    """IPs en lista negra"""
    __tablename__ = "ip_blacklist"

    id = Column(Integer, primary_key=True, index=True)
    ip_address = Column(String, unique=True, index=True)
    description = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    blocked_count = Column(Integer, default=0)


class PortMonitor(Base):
    """Puertos a monitorizar"""
    __tablename__ = "port_monitors"

    id = Column(Integer, primary_key=True, index=True)
    port_number = Column(Integer, unique=True, index=True)
    protocol = Column(String)  # tcp, udp, both
    description = Column(String, nullable=True)
    alert_enabled = Column(Boolean, default=True)
    whitelist_only = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class Alert(Base):
    """Alertas generadas"""
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    alert_type = Column(String, index=True)  # suspicious_ip, port_scan, blacklisted_ip, etc.
    severity = Column(String, index=True)  # low, medium, high, critical
    source_ip = Column(String, index=True)
    destination_port = Column(Integer, nullable=True)
    description = Column(String)
    acknowledged = Column(Boolean, default=False)


class BlockingPolicy(Base):
    """Políticas de bloqueo automático"""
    __tablename__ = "blocking_policies"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    enabled = Column(Boolean, default=True)
    auto_block_blacklist = Column(Boolean, default=True)
    auto_block_on_alert = Column(Boolean, default=False)
    alert_threshold = Column(Integer, default=3)  # Número de alertas antes de bloquear
    block_duration_hours = Column(Integer, nullable=True)  # None = permanente
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class FirewallLog(Base):
    """Log de acciones del firewall"""
    __tablename__ = "firewall_logs"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    action = Column(String, index=True)  # block, unblock, auto_block, auto_unblock
    ip_address = Column(String, index=True)
    reason = Column(String)
    success = Column(Boolean, default=True)
    performed_by = Column(String, default="system")  # system, manual, policy
    expires_at = Column(DateTime, nullable=True)  # Para bloqueos temporales


class DDoSConfig(Base):
    """Configuración de protección DDoS"""
    __tablename__ = "ddos_config"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    enabled = Column(Boolean, default=True)
    pps_threshold = Column(Integer, default=100)  # Paquetes por segundo
    syn_threshold = Column(Integer, default=50)   # SYN por segundo
    udp_threshold = Column(Integer, default=200)  # UDP por segundo
    icmp_threshold = Column(Integer, default=50)  # ICMP por segundo
    auto_mitigate = Column(Boolean, default=True)
    mitigation_duration = Column(Integer, default=3600)  # Segundos
    alert_threshold = Column(Integer, default=80)  # Porcentaje del threshold
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class DDoSAttack(Base):
    """Registro de ataques DDoS detectados"""
    __tablename__ = "ddos_attacks"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    source_ip = Column(String, index=True)
    attack_type = Column(String, index=True)  # syn_flood, udp_flood, icmp_flood, high_traffic
    severity = Column(String, index=True)  # low, medium, high, critical
    packets_per_second = Column(Float)
    bytes_per_second = Column(Float)
    duration_seconds = Column(Integer, nullable=True)
    mitigated = Column(Boolean, default=False)
    ended_at = Column(DateTime, nullable=True)
    metrics = Column(String, nullable=True)  # JSON con métricas adicionales
