import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environment';
import {
  Packet,
  Stats,
  Alert,
  IPWhitelist,
  IPBlacklist,
  PortMonitor,
  BlockingPolicy,
  FirewallLog,
  FirewallStats,
  BlockedIP,
  DDoSMitigationLevel,
  DDoSGeoRule,
  DDoSProtectionStatus,
  DDoSGeoStats,
  DDoSConfig,
  DDoSAttack,
  DDoSMetrics,
  DDoSStats
} from '../models/packet.model';

@Injectable({
  providedIn: 'root'
})
export class ApiService {
  private apiUrl = environment.apiUrl;

  constructor(private http: HttpClient) {}

  // Packets
  getPackets(
    skip: number = 0,
    limit: number = 100,
    sourceIp?: string,
    protocol?: string,
    suspiciousOnly: boolean = false
  ): Observable<Packet[]> {
    let params = new HttpParams()
      .set('skip', skip.toString())
      .set('limit', limit.toString());

    if (sourceIp) {
      params = params.set('source_ip', sourceIp);
    }
    if (protocol) {
      params = params.set('protocol', protocol);
    }
    if (suspiciousOnly) {
      params = params.set('suspicious_only', 'true');
    }

    return this.http.get<Packet[]>(`${this.apiUrl}/packets`, { params });
  }

  // Statistics
  getStatistics(): Observable<Stats> {
    return this.http.get<Stats>(`${this.apiUrl}/stats`);
  }

  // Whitelist
  getWhitelist(): Observable<IPWhitelist[]> {
    return this.http.get<IPWhitelist[]>(`${this.apiUrl}/whitelist`);
  }

  addToWhitelist(ip: string, description?: string): Observable<IPWhitelist> {
    return this.http.post<IPWhitelist>(`${this.apiUrl}/whitelist`, {
      ip_address: ip,
      description
    });
  }

  removeFromWhitelist(id: number): Observable<any> {
    return this.http.delete(`${this.apiUrl}/whitelist/${id}`);
  }

  // Blacklist
  getBlacklist(): Observable<IPBlacklist[]> {
    return this.http.get<IPBlacklist[]>(`${this.apiUrl}/blacklist`);
  }

  addToBlacklist(ip: string, description?: string): Observable<IPBlacklist> {
    return this.http.post<IPBlacklist>(`${this.apiUrl}/blacklist`, {
      ip_address: ip,
      description
    });
  }

  removeFromBlacklist(id: number): Observable<any> {
    return this.http.delete(`${this.apiUrl}/blacklist/${id}`);
  }

  // Port Monitors
  getPortMonitors(): Observable<PortMonitor[]> {
    return this.http.get<PortMonitor[]>(`${this.apiUrl}/monitors`);
  }

  addPortMonitor(monitor: Partial<PortMonitor>): Observable<PortMonitor> {
    return this.http.post<PortMonitor>(`${this.apiUrl}/monitors`, monitor);
  }

  removePortMonitor(id: number): Observable<any> {
    return this.http.delete(`${this.apiUrl}/monitors/${id}`);
  }

  // Alerts
  getAlerts(acknowledged?: boolean): Observable<Alert[]> {
    let params = new HttpParams();
    if (acknowledged !== undefined) {
      params = params.set('acknowledged', acknowledged.toString());
    }
    return this.http.get<Alert[]>(`${this.apiUrl}/alerts`, { params });
  }

  acknowledgeAlert(id: number): Observable<any> {
    return this.http.patch(`${this.apiUrl}/alerts/${id}/acknowledge`, {});
  }

  // Firewall
  blockIP(ipAddress: string, reason?: string, durationHours?: number): Observable<any> {
    return this.http.post(`${this.apiUrl}/firewall/block`, {
      ip_address: ipAddress,
      reason,
      duration_hours: durationHours
    });
  }

  unblockIP(ipAddress: string, reason?: string): Observable<any> {
    return this.http.post(`${this.apiUrl}/firewall/unblock`, {
      ip_address: ipAddress,
      reason
    });
  }

  getBlockedIPs(): Observable<BlockedIP[]> {
    return this.http.get<BlockedIP[]>(`${this.apiUrl}/firewall/blocked-ips`);
  }

  getFirewallStats(): Observable<FirewallStats> {
    return this.http.get<FirewallStats>(`${this.apiUrl}/firewall/stats`);
  }

  getFirewallLogs(skip: number = 0, limit: number = 100, ipAddress?: string, action?: string): Observable<FirewallLog[]> {
    let params = new HttpParams()
      .set('skip', skip.toString())
      .set('limit', limit.toString());

    if (ipAddress) {
      params = params.set('ip_address', ipAddress);
    }
    if (action) {
      params = params.set('action', action);
    }

    return this.http.get<FirewallLog[]>(`${this.apiUrl}/firewall/logs`, { params });
  }

  // Policies
  getPolicies(): Observable<BlockingPolicy[]> {
    return this.http.get<BlockingPolicy[]>(`${this.apiUrl}/policies`);
  }

  getPolicy(id: number): Observable<BlockingPolicy> {
    return this.http.get<BlockingPolicy>(`${this.apiUrl}/policies/${id}`);
  }

  getPolicyByName(name: string): Observable<BlockingPolicy> {
    return this.http.get<BlockingPolicy>(`${this.apiUrl}/policies/name/${name}`);
  }

  updatePolicy(id: number, policy: Partial<BlockingPolicy>): Observable<BlockingPolicy> {
    return this.http.patch<BlockingPolicy>(`${this.apiUrl}/policies/${id}`, policy);
  }

  // DDoS Protection
  getDDoSConfig(): Observable<DDoSConfig> {
    return this.http.get<DDoSConfig>(`${this.apiUrl}/ddos/config`);
  }

  updateDDoSConfig(id: number, config: Partial<DDoSConfig>): Observable<DDoSConfig> {
    return this.http.patch<DDoSConfig>(`${this.apiUrl}/ddos/config/${id}`, config);
  }

  getActiveDDoSAttacks(): Observable<DDoSAttack[]> {
    return this.http.get<DDoSAttack[]>(`${this.apiUrl}/ddos/attacks/active`);
  }

  getDDoSAttackHistory(skip: number = 0, limit: number = 100, ip?: string): Observable<DDoSAttack[]> {
    let params = new HttpParams()
      .set('skip', skip.toString())
      .set('limit', limit.toString());

    if (ip) {
      params = params.set('ip', ip);
    }

    return this.http.get<DDoSAttack[]>(`${this.apiUrl}/ddos/attacks/history`, { params });
  }

  getDDoSStats(): Observable<DDoSStats> {
    return this.http.get<DDoSStats>(`${this.apiUrl}/ddos/stats`);
  }

  getDDoSMetrics(ip?: string): Observable<DDoSMetrics[]> {
    let params = new HttpParams();
    if (ip) {
      params = params.set('ip', ip);
    }
    return this.http.get<DDoSMetrics[]>(`${this.apiUrl}/ddos/metrics`, { params });
  }

  mitigateDDoSAttack(ipAddress: string, attackType: string, reason?: string): Observable<any> {
    return this.http.post(`${this.apiUrl}/ddos/mitigate`, {
      ip_address: ipAddress,
      attack_type: attackType,
      reason
    });
  }

  endDDoSAttack(ip: string): Observable<any> {
    return this.http.post(`${this.apiUrl}/ddos/attacks/${ip}/end`, {});
  }
}

  // Advanced DDoS Methods
  getMitigationLevels(): Observable<DDoSMitigationLevel[]> {
    return this.http.get<DDoSMitigationLevel[]>(`${this.apiUrl}/ddos/levels`);
  }

  activateMitigationLevel(levelName: string): Observable<any> {
    return this.http.post(`${this.apiUrl}/ddos/levels/${levelName}/activate`, {});
  }

  getGeoRules(): Observable<DDoSGeoRule[]> {
    return this.http.get<DDoSGeoRule[]>(`${this.apiUrl}/ddos/geo-rules`);
  }

  createGeoRule(rule: any): Observable<DDoSGeoRule> {
    return this.http.post<DDoSGeoRule>(`${this.apiUrl}/ddos/geo-rules`, rule);
  }

  deleteGeoRule(ruleId: number): Observable<any> {
    return this.http.delete(`${this.apiUrl}/ddos/geo-rules/${ruleId}`);
  }

  getDDoSProtectionStatus(): Observable<DDoSProtectionStatus> {
    return this.http.get<DDoSProtectionStatus>(`${this.apiUrl}/ddos/protection-status`);
  }

  getDDoSGeoStats(): Observable<DDoSGeoStats[]> {
    return this.http.get<DDoSGeoStats[]>(`${this.apiUrl}/ddos/geo-stats`);
  }
}
