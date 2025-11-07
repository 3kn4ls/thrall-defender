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
