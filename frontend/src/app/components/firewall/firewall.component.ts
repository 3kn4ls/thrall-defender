import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { MatCardModule } from '@angular/material/card';
import { MatTableModule } from '@angular/material/table';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatInputModule } from '@angular/material/input';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatTabsModule } from '@angular/material/tabs';
import { MatSlideToggleModule } from '@angular/material/slide-toggle';
import { MatChipsModule } from '@angular/material/chips';
import { MatDividerModule } from '@angular/material/divider';
import { ApiService } from '../../services/api.service';
import { BlockedIP, FirewallLog, FirewallStats, BlockingPolicy } from '../../models/packet.model';

@Component({
  selector: 'app-firewall',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    MatCardModule,
    MatTableModule,
    MatButtonModule,
    MatIconModule,
    MatInputModule,
    MatFormFieldModule,
    MatTabsModule,
    MatSlideToggleModule,
    MatChipsModule,
    MatDividerModule
  ],
  templateUrl: './firewall.component.html',
  styleUrls: ['./firewall.component.scss']
})
export class FirewallComponent implements OnInit {
  blockedIPs: BlockedIP[] = [];
  firewallLogs: FirewallLog[] = [];
  firewallStats?: FirewallStats;
  policy?: BlockingPolicy;

  blockIpAddress = '';
  blockReason = '';
  blockDurationHours?: number;

  unblockIpAddress = '';

  blockedColumns: string[] = ['source', 'packets', 'bytes', 'actions'];
  logsColumns: string[] = ['timestamp', 'action', 'ip_address', 'reason', 'performed_by', 'success'];

  constructor(private apiService: ApiService) {}

  ngOnInit(): void {
    this.loadData();
  }

  loadData(): void {
    this.loadBlockedIPs();
    this.loadFirewallLogs();
    this.loadFirewallStats();
    this.loadPolicy();
  }

  loadBlockedIPs(): void {
    this.apiService.getBlockedIPs().subscribe({
      next: (ips) => {
        this.blockedIPs = ips;
      },
      error: (error) => {
        console.error('Error loading blocked IPs:', error);
      }
    });
  }

  loadFirewallLogs(): void {
    this.apiService.getFirewallLogs(0, 50).subscribe({
      next: (logs) => {
        this.firewallLogs = logs;
      },
      error: (error) => {
        console.error('Error loading firewall logs:', error);
      }
    });
  }

  loadFirewallStats(): void {
    this.apiService.getFirewallStats().subscribe({
      next: (stats) => {
        this.firewallStats = stats;
      },
      error: (error) => {
        console.error('Error loading firewall stats:', error);
      }
    });
  }

  loadPolicy(): void {
    this.apiService.getPolicyByName('default').subscribe({
      next: (policy) => {
        this.policy = policy;
      },
      error: (error) => {
        console.error('Error loading policy:', error);
      }
    });
  }

  blockIP(): void {
    if (!this.blockIpAddress) return;

    this.apiService.blockIP(
      this.blockIpAddress,
      this.blockReason || 'Manual block',
      this.blockDurationHours
    ).subscribe({
      next: () => {
        alert(`IP ${this.blockIpAddress} bloqueada exitosamente`);
        this.blockIpAddress = '';
        this.blockReason = '';
        this.blockDurationHours = undefined;
        this.loadData();
      },
      error: (error) => {
        console.error('Error blocking IP:', error);
        alert(`Error al bloquear IP: ${error.error?.detail || error.message}`);
      }
    });
  }

  unblockIP(ipAddress?: string): void {
    const ip = ipAddress || this.unblockIpAddress;
    if (!ip) return;

    if (!confirm(`¿Estás seguro de desbloquear ${ip}?`)) return;

    this.apiService.unblockIP(ip, 'Manual unblock').subscribe({
      next: () => {
        alert(`IP ${ip} desbloqueada exitosamente`);
        if (!ipAddress) {
          this.unblockIpAddress = '';
        }
        this.loadData();
      },
      error: (error) => {
        console.error('Error unblocking IP:', error);
        alert(`Error al desbloquear IP: ${error.error?.detail || error.message}`);
      }
    });
  }

  updatePolicy(): void {
    if (!this.policy) return;

    this.apiService.updatePolicy(this.policy.id, {
      enabled: this.policy.enabled,
      auto_block_blacklist: this.policy.auto_block_blacklist,
      auto_block_on_alert: this.policy.auto_block_on_alert,
      alert_threshold: this.policy.alert_threshold,
      block_duration_hours: this.policy.block_duration_hours
    }).subscribe({
      next: () => {
        alert('Política actualizada exitosamente');
      },
      error: (error) => {
        console.error('Error updating policy:', error);
        alert(`Error al actualizar política: ${error.error?.detail || error.message}`);
      }
    });
  }

  formatBytes(bytes: number): string {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
  }

  getActionColor(action: string): string {
    if (action.includes('block')) return 'warn';
    if (action.includes('unblock')) return 'primary';
    return 'accent';
  }

  getSuccessIcon(success: boolean): string {
    return success ? 'check_circle' : 'error';
  }
}
