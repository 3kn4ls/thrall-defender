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

export interface BlockingPolicy {
  id: number;
  name: string;
  enabled: boolean;
  auto_block_blacklist: boolean;
  auto_block_on_alert: boolean;
  alert_threshold: number;
  block_duration_hours?: number;
  created_at: string;
  updated_at: string;
}

export interface FirewallLog {
  id: number;
  timestamp: string;
  action: string;
  ip_address: string;
  reason: string;
  success: boolean;
  performed_by: string;
  expires_at?: string;
}

export interface FirewallStats {
  total_blocked_ips: number;
  total_packets_blocked: number;
  total_bytes_blocked: number;
  whitelisted_ips: number;
  chain_name: string;
}

export interface BlockedIP {
  source: string;
  packets: number;
  bytes: number;
  rule_number: string;
}

// DDoS Protection Models
export interface DDoSConfig {
  id: number;
  name: string;
  enabled: boolean;
  pps_threshold: number;
  syn_threshold: number;
  udp_threshold: number;
  icmp_threshold: number;
  auto_mitigate: boolean;
  mitigation_duration: number;
  alert_threshold: number;
  created_at: string;
  updated_at: string;
}

export interface DDoSAttack {
  id: number;
  timestamp: string;
  source_ip: string;
  attack_type: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  packets_per_second: number;
  bytes_per_second: number;
  duration_seconds?: number;
  mitigated: boolean;
  ended_at?: string;
  metrics?: string;
}

export interface DDoSMetrics {
  ip: string;
  packets_per_second: number;
  packets_per_minute: number;
  bytes_per_second: number;
  syn_rate: number;
  udp_rate: number;
  icmp_rate: number;
  total_bytes: number;
}

export interface DDoSStats {
  active_attacks: number;
  total_attacks_today: number;
  mitigated_ips: number;
  top_attackers: DDoSMetrics[];
  attack_types_distribution: { [key: string]: number };
}

// Advanced DDoS Models
export interface DDoSMitigationLevel {
  id: number;
  name: string;
  description: string;
  is_active: boolean;
  pps_threshold: number;
  syn_threshold: number;
  udp_threshold: number;
  icmp_threshold: number;
  connection_threshold: number;
  rate_limit_enabled: boolean;
  rate_limit_pps: number;
  rate_limit_burst: number;
  challenge_mode: string;
  challenge_threshold: number;
  geo_blocking_enabled: boolean;
  auto_mitigate: boolean;
  mitigation_duration: number;
  created_at: string;
  updated_at: string;
}

export interface DDoSGeoRule {
  id: number;
  country_code: string;
  country_name: string;
  action: 'allow' | 'block' | 'challenge' | 'rate_limit';
  priority: number;
  enabled: boolean;
  custom_rate_limit?: number;
  custom_burst?: number;
  reason?: string;
  created_at: string;
  updated_at: string;
}

export interface DDoSProtectionStatus {
  protection_enabled: boolean;
  active_level?: DDoSMitigationLevel;
  geo_rules_count: number;
  active_attacks_count: number;
  total_attacks_blocked_today: number;
  current_threat_level: 'none' | 'low' | 'medium' | 'high' | 'critical';
  geoip_available: boolean;
}

export interface DDoSGeoStats {
  country_code: string;
  country_name: string;
  attack_count: number;
  blocked_count: number;
  total_packets: number;
}
