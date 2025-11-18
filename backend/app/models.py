from sqlalchemy import Column, Integer, String, DateTime, Boolean, Float, Text, JSON
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
    detected_at = Column(DateTime, default=datetime.utcnow, index=True)
    source_ip = Column(String, index=True)
    attack_type = Column(String, index=True)  # syn_flood, udp_flood, icmp_flood, high_traffic
    severity = Column(String, index=True)  # low, medium, high, critical
    packets_per_second = Column(Float)
    bytes_per_second = Column(Float)
    duration_seconds = Column(Integer, nullable=True)
    mitigated = Column(Boolean, default=False)
    ended_at = Column(DateTime, nullable=True)
    metrics = Column(String, nullable=True)  # JSON con métricas adicionales
    country_code = Column(String, nullable=True, index=True)  # ISO country code
    country_name = Column(String, nullable=True)


class DDoSMitigationLevel(Base):
    """Niveles de mitigación DDoS preconfigurados"""
    __tablename__ = "ddos_mitigation_levels"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)  # low, medium, high, aggressive, custom
    description = Column(String)
    is_active = Column(Boolean, default=False)  # Solo uno puede estar activo

    # Thresholds
    pps_threshold = Column(Integer, default=100)
    syn_threshold = Column(Integer, default=50)
    udp_threshold = Column(Integer, default=200)
    icmp_threshold = Column(Integer, default=50)
    connection_threshold = Column(Integer, default=100)  # Conexiones simultáneas por IP

    # Rate limiting
    rate_limit_enabled = Column(Boolean, default=True)
    rate_limit_pps = Column(Integer, default=50)  # Máximo paquetes/segundo permitidos
    rate_limit_burst = Column(Integer, default=100)  # Burst permitido

    # Challenge mode
    challenge_mode = Column(String, default="none")  # none, javascript, captcha, proof_of_work
    challenge_threshold = Column(Integer, default=80)  # % del threshold para activar challenge

    # Geo-blocking
    geo_blocking_enabled = Column(Boolean, default=False)

    # Auto-mitigation
    auto_mitigate = Column(Boolean, default=True)
    mitigation_duration = Column(Integer, default=3600)  # Segundos

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class DDoSGeoRule(Base):
    """Reglas geográficas para DDoS (permitir/bloquear países)"""
    __tablename__ = "ddos_geo_rules"

    id = Column(Integer, primary_key=True, index=True)
    country_code = Column(String, index=True)  # ISO 2-letter code (ej: US, CN, RU)
    country_name = Column(String)
    action = Column(String, index=True)  # allow, block, challenge, rate_limit
    priority = Column(Integer, default=100)  # Menor número = mayor prioridad
    enabled = Column(Boolean, default=True)

    # Configuración específica para rate_limit
    custom_rate_limit = Column(Integer, nullable=True)  # PPS personalizado para este país
    custom_burst = Column(Integer, nullable=True)

    reason = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class DDoSAdvancedConfig(Base):
    """Configuración avanzada de protección DDoS"""
    __tablename__ = "ddos_advanced_config"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, default="default")

    # Pattern detection
    pattern_detection_enabled = Column(Boolean, default=True)
    pattern_threshold = Column(Integer, default=5)  # Nº de repeticiones para considerar patrón

    # Behavioral analysis
    behavioral_analysis_enabled = Column(Boolean, default=True)
    learning_period_hours = Column(Integer, default=24)  # Período de aprendizaje
    anomaly_sensitivity = Column(Float, default=2.0)  # Desviaciones estándar para anomalía

    # Connection tracking
    track_connections = Column(Boolean, default=True)
    max_connections_per_ip = Column(Integer, default=100)
    max_connections_per_port = Column(Integer, default=1000)
    connection_timeout = Column(Integer, default=300)  # Segundos

    # Packet inspection
    deep_packet_inspection = Column(Boolean, default=False)
    inspect_payload = Column(Boolean, default=False)
    malformed_packet_action = Column(String, default="drop")  # drop, log, allow

    # Response actions
    progressive_mitigation = Column(Boolean, default=True)  # Escalar gradualmente
    blackhole_enabled = Column(Boolean, default=False)  # Blackhole routing para IPs atacantes
    notify_on_attack = Column(Boolean, default=True)
    auto_create_firewall_rule = Column(Boolean, default=True)

    # Whitelisting
    whitelist_bypass_all = Column(Boolean, default=True)  # Whitelist bypassed all checks
    trusted_asn_list = Column(String, nullable=True)  # JSON list of trusted ASNs

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class DashboardSnapshot(Base):
    """
    Snapshot pre-calculado del dashboard para rendimiento óptimo.
    Actualizado por un job asíncrono cada N segundos.
    """
    __tablename__ = "dashboard_snapshots"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    # Estadísticas generales
    total_packets = Column(Integer, default=0)
    packets_last_hour = Column(Integer, default=0)
    packets_last_24h = Column(Integer, default=0)
    unique_ips = Column(Integer, default=0)
    unique_ips_last_hour = Column(Integer, default=0)
    suspicious_packets = Column(Integer, default=0)
    active_alerts = Column(Integer, default=0)

    # Top lists (JSON)
    top_ports = Column(String, default='[]')  # JSON: [{"port": 80, "count": 100}, ...]
    top_protocols = Column(String, default='[]')  # JSON: [{"protocol": "TCP", "count": 500}, ...]
    recent_ips = Column(String, default='[]')  # JSON: ["192.168.1.1", ...]
    top_sources = Column(String, default='[]')  # JSON: [{"ip": "1.2.3.4", "packets": 1000}, ...]

    # Alertas por severidad
    critical_alerts = Column(Integer, default=0)
    high_alerts = Column(Integer, default=0)
    medium_alerts = Column(Integer, default=0)
    low_alerts = Column(Integer, default=0)

    # DDoS stats
    active_ddos_attacks = Column(Integer, default=0)
    blocked_ips_count = Column(Integer, default=0)
    ddos_attacks_today = Column(Integer, default=0)

    # Firewall stats
    firewall_blocks_today = Column(Integer, default=0)
    whitelisted_ips_count = Column(Integer, default=0)
    blacklisted_ips_count = Column(Integer, default=0)

    # Tráfico (bytes)
    total_bytes_last_hour = Column(Integer, default=0)
    total_bytes_last_24h = Column(Integer, default=0)

    # Tiempo de cálculo (para métricas)
    calculation_time_ms = Column(Float, nullable=True)  # Milisegundos que tomó calcular


class AuditLog(Base):
    """
    Registro de auditoría para trazabilidad completa.
    Registra todas las acciones importantes del sistema.
    """
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)

    # Acción realizada
    action = Column(String, index=True)  # block_ip, unblock_ip, acknowledge_alert, change_config, etc.
    category = Column(String, index=True)  # firewall, ddos, alerts, config, system
    severity = Column(String, index=True)  # info, warning, critical

    # Actor
    performed_by = Column(String, default="system")  # system, admin, api, auto
    source_ip = Column(String, nullable=True)  # IP desde donde se realizó la acción
    user_agent = Column(String, nullable=True)

    # Detalles
    description = Column(Text)  # Descripción legible de la acción
    target = Column(String, nullable=True, index=True)  # IP, ID de alerta, etc.
    details = Column(String, nullable=True)  # JSON con detalles adicionales

    # Resultado
    success = Column(Boolean, default=True)
    error_message = Column(String, nullable=True)

    # Contexto adicional
    affected_resources = Column(String, nullable=True)  # JSON: ["resource1", "resource2"]
    previous_value = Column(String, nullable=True)  # Para cambios de configuración
    new_value = Column(String, nullable=True)  # Para cambios de configuración


# Aliases for compatibility
Packet = NetworkPacket
