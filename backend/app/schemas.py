from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class PacketBase(BaseModel):
    source_ip: str
    destination_ip: str
    source_port: int
    destination_port: int
    protocol: str
    packet_size: int
    flags: Optional[str] = None
    payload_preview: Optional[str] = None


class PacketCreate(PacketBase):
    pass


class Packet(PacketBase):
    id: int
    timestamp: datetime
    is_blocked: bool
    is_suspicious: bool

    class Config:
        from_attributes = True


class IPWhitelistBase(BaseModel):
    ip_address: str
    description: Optional[str] = None


class IPWhitelistCreate(IPWhitelistBase):
    pass


class IPWhitelist(IPWhitelistBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class IPBlacklistBase(BaseModel):
    ip_address: str
    description: Optional[str] = None


class IPBlacklistCreate(IPBlacklistBase):
    pass


class IPBlacklist(IPBlacklistBase):
    id: int
    created_at: datetime
    blocked_count: int

    class Config:
        from_attributes = True


class PortMonitorBase(BaseModel):
    port_number: int
    protocol: str = Field(..., pattern="^(tcp|udp|both)$")
    description: Optional[str] = None
    alert_enabled: bool = True
    whitelist_only: bool = False


class PortMonitorCreate(PortMonitorBase):
    pass


class PortMonitor(PortMonitorBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class AlertBase(BaseModel):
    alert_type: str
    severity: str = Field(..., pattern="^(low|medium|high|critical)$")
    source_ip: str
    destination_port: Optional[int] = None
    description: str


class AlertCreate(AlertBase):
    pass


class Alert(AlertBase):
    id: int
    timestamp: datetime
    acknowledged: bool

    class Config:
        from_attributes = True


class Stats(BaseModel):
    """Estadísticas en tiempo real"""
    total_packets: int
    packets_last_hour: int
    unique_ips: int
    suspicious_packets: int
    active_alerts: int
    top_ports: list[dict]
    top_protocols: list[dict]
    recent_ips: list[str]


class BlockingPolicyBase(BaseModel):
    name: str
    enabled: bool = True
    auto_block_blacklist: bool = True
    auto_block_on_alert: bool = False
    alert_threshold: int = Field(default=3, ge=1, le=100)
    block_duration_hours: Optional[int] = Field(default=None, ge=1)


class BlockingPolicyCreate(BlockingPolicyBase):
    pass


class BlockingPolicyUpdate(BaseModel):
    enabled: Optional[bool] = None
    auto_block_blacklist: Optional[bool] = None
    auto_block_on_alert: Optional[bool] = None
    alert_threshold: Optional[int] = Field(default=None, ge=1, le=100)
    block_duration_hours: Optional[int] = Field(default=None, ge=1)


class BlockingPolicy(BlockingPolicyBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class FirewallLogBase(BaseModel):
    action: str
    ip_address: str
    reason: str
    performed_by: str = "system"
    expires_at: Optional[datetime] = None


class FirewallLogCreate(FirewallLogBase):
    success: bool = True


class FirewallLog(FirewallLogBase):
    id: int
    timestamp: datetime
    success: bool

    class Config:
        from_attributes = True


class FirewallStats(BaseModel):
    """Estadísticas del firewall"""
    total_blocked_ips: int
    total_packets_blocked: int
    total_bytes_blocked: int
    whitelisted_ips: int
    chain_name: str


class BlockIPRequest(BaseModel):
    ip_address: str
    reason: Optional[str] = "Manual block"
    duration_hours: Optional[int] = None


class UnblockIPRequest(BaseModel):
    ip_address: str
    reason: Optional[str] = "Manual unblock"


class BlockedIP(BaseModel):
    """IP bloqueada con estadísticas"""
    source: str
    packets: int
    bytes: int
    rule_number: str


# ========== DDoS Protection Schemas ==========

class DDoSConfigBase(BaseModel):
    name: str
    enabled: bool = True
    pps_threshold: int = Field(default=100, ge=10, le=10000)
    syn_threshold: int = Field(default=50, ge=5, le=1000)
    udp_threshold: int = Field(default=200, ge=10, le=5000)
    icmp_threshold: int = Field(default=50, ge=5, le=1000)
    auto_mitigate: bool = True
    mitigation_duration: int = Field(default=3600, ge=60, le=86400)
    alert_threshold: int = Field(default=80, ge=50, le=100)


class DDoSConfigCreate(DDoSConfigBase):
    pass


class DDoSConfigUpdate(BaseModel):
    enabled: Optional[bool] = None
    pps_threshold: Optional[int] = Field(default=None, ge=10, le=10000)
    syn_threshold: Optional[int] = Field(default=None, ge=5, le=1000)
    udp_threshold: Optional[int] = Field(default=None, ge=10, le=5000)
    icmp_threshold: Optional[int] = Field(default=None, ge=5, le=1000)
    auto_mitigate: Optional[bool] = None
    mitigation_duration: Optional[int] = Field(default=None, ge=60, le=86400)
    alert_threshold: Optional[int] = Field(default=None, ge=50, le=100)


class DDoSConfig(DDoSConfigBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DDoSAttackBase(BaseModel):
    source_ip: str
    attack_type: str
    severity: str
    packets_per_second: float
    bytes_per_second: float


class DDoSAttackCreate(DDoSAttackBase):
    metrics: Optional[str] = None


class DDoSAttack(DDoSAttackBase):
    id: int
    timestamp: datetime
    duration_seconds: Optional[int] = None
    mitigated: bool
    ended_at: Optional[datetime] = None
    metrics: Optional[str] = None

    class Config:
        from_attributes = True


class DDoSMetrics(BaseModel):
    """Métricas de tráfico para una IP"""
    ip: str
    packets_per_second: float
    packets_per_minute: int
    bytes_per_second: float
    syn_rate: float
    udp_rate: float
    icmp_rate: float
    total_bytes: int


class DDoSStats(BaseModel):
    """Estadísticas globales de DDoS"""
    active_attacks: int
    total_attacks_today: int
    mitigated_ips: int
    top_attackers: list[DDoSMetrics]
    attack_types_distribution: dict


class MitigateIPRequest(BaseModel):
    ip_address: str
    attack_type: str
    reason: Optional[str] = "DDoS attack detected"
