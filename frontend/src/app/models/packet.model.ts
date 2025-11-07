export interface Packet {
  id: number;
  timestamp: string;
  source_ip: string;
  destination_ip: string;
  source_port: number;
  destination_port: number;
  protocol: string;
  packet_size: number;
  flags?: string;
  payload_preview?: string;
  is_blocked: boolean;
  is_suspicious: boolean;
}

export interface Stats {
  total_packets: number;
  packets_last_hour: number;
  unique_ips: number;
  suspicious_packets: number;
  active_alerts: number;
  top_ports: { port: number; count: number }[];
  top_protocols: { protocol: string; count: number }[];
  recent_ips: string[];
}

export interface Alert {
  id: number;
  timestamp: string;
  alert_type: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  source_ip: string;
  destination_port?: number;
  description: string;
  acknowledged: boolean;
}

export interface IPWhitelist {
  id: number;
  ip_address: string;
  description?: string;
  created_at: string;
}

export interface IPBlacklist {
  id: number;
  ip_address: string;
  description?: string;
  created_at: string;
  blocked_count: number;
}

export interface PortMonitor {
  id: number;
  port_number: number;
  protocol: 'tcp' | 'udp' | 'both';
  description?: string;
  alert_enabled: boolean;
  whitelist_only: boolean;
  created_at: string;
}
