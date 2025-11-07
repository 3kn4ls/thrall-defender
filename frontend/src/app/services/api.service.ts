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
  PortMonitor
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
}
