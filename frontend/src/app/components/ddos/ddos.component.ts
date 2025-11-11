import { Component, OnInit, OnDestroy } from '@angular/core';
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
import { Subject, interval } from 'rxjs';
import { takeUntil } from 'rxjs/operators';

import { ApiService } from '../../services/api.service';
import { DDoSConfig, DDoSAttack, DDoSMetrics, DDoSStats } from '../../models/packet.model';

@Component({
  selector: 'app-ddos',
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
    MatChipsModule
  ],
  templateUrl: './ddos.component.html',
  styleUrls: ['./ddos.component.scss']
})
export class DdosComponent implements OnInit, OnDestroy {
  config?: DDoSConfig;
  stats?: DDoSStats;
  activeAttacks: DDoSAttack[] = [];
  attackHistory: DDoSAttack[] = [];
  topAttackers: DDoSMetrics[] = [];

  attackColumns: string[] = ['timestamp', 'source_ip', 'attack_type', 'severity', 'pps', 'actions'];
  historyColumns: string[] = ['timestamp', 'source_ip', 'attack_type', 'severity', 'duration', 'mitigated'];
  metricsColumns: string[] = ['ip', 'pps', 'syn_rate', 'udp_rate', 'icmp_rate'];

  private destroy$ = new Subject<void>();

  constructor(private apiService: ApiService) {}

  ngOnInit(): void {
    this.loadData();

    // Actualizar datos cada 5 segundos
    interval(5000)
      .pipe(takeUntil(this.destroy$))
      .subscribe(() => {
        this.loadRealTimeData();
      });
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  loadData(): void {
    this.loadConfig();
    this.loadStats();
    this.loadActiveAttacks();
    this.loadAttackHistory();
    this.loadTopAttackers();
  }

  loadRealTimeData(): void {
    this.loadStats();
    this.loadActiveAttacks();
    this.loadTopAttackers();
  }

  loadConfig(): void {
    this.apiService.getDDoSConfig().subscribe({
      next: (config) => {
        this.config = config;
      },
      error: (error) => {
        console.error('Error loading DDoS config:', error);
      }
    });
  }

  loadStats(): void {
    this.apiService.getDDoSStats().subscribe({
      next: (stats) => {
        this.stats = stats;
      },
      error: (error) => {
        console.error('Error loading DDoS stats:', error);
      }
    });
  }

  loadActiveAttacks(): void {
    this.apiService.getActiveDDoSAttacks().subscribe({
      next: (attacks) => {
        this.activeAttacks = attacks;
      },
      error: (error) => {
        console.error('Error loading active attacks:', error);
      }
    });
  }

  loadAttackHistory(): void {
    this.apiService.getDDoSAttackHistory(0, 50).subscribe({
      next: (attacks) => {
        this.attackHistory = attacks;
      },
      error: (error) => {
        console.error('Error loading attack history:', error);
      }
    });
  }

  loadTopAttackers(): void {
    this.apiService.getDDoSMetrics().subscribe({
      next: (metrics) => {
        this.topAttackers = metrics;
      },
      error: (error) => {
        console.error('Error loading top attackers:', error);
      }
    });
  }

  updateConfig(): void {
    if (!this.config) return;

    this.apiService.updateDDoSConfig(this.config.id, {
      enabled: this.config.enabled,
      pps_threshold: this.config.pps_threshold,
      syn_threshold: this.config.syn_threshold,
      udp_threshold: this.config.udp_threshold,
      icmp_threshold: this.config.icmp_threshold,
      auto_mitigate: this.config.auto_mitigate,
      mitigation_duration: this.config.mitigation_duration,
      alert_threshold: this.config.alert_threshold
    }).subscribe({
      next: () => {
        alert('Configuración actualizada');
      },
      error: (error) => {
        console.error('Error updating config:', error);
        alert('Error al actualizar configuración');
      }
    });
  }

  mitigateAttack(attack: DDoSAttack): void {
    if (!confirm(`¿Mitigar ataque de ${attack.source_ip}?`)) return;

    this.apiService.mitigateDDoSAttack(attack.source_ip, attack.attack_type).subscribe({
      next: () => {
        alert('Ataque mitigado');
        this.loadRealTimeData();
      },
      error: (error) => {
        console.error('Error mitigating attack:', error);
        alert('Error al mitigar ataque');
      }
    });
  }

  endAttack(ip: string): void {
    this.apiService.endDDoSAttack(ip).subscribe({
      next: () => {
        this.loadRealTimeData();
      },
      error: (error) => {
        console.error('Error ending attack:', error);
      }
    });
  }

  getSeverityColor(severity: string): string {
    const colors: any = {
      'critical': '#d32f2f',
      'high': '#f57c00',
      'medium': '#fbc02d',
      'low': '#7cb342'
    };
    return colors[severity] || '#999';
  }

  getAttackTypeName(type: string): string {
    const names: any = {
      'syn_flood': 'SYN Flood',
      'udp_flood': 'UDP Flood',
      'icmp_flood': 'ICMP Flood',
      'high_traffic': 'Tráfico Alto'
    };
    return names[type] || type;
  }

  formatBytes(bytes: number): string {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
  }

  formatDuration(seconds?: number): string {
    if (!seconds) return '-';
    if (seconds < 60) return `${seconds}s`;
    if (seconds < 3600) return `${Math.floor(seconds / 60)}m`;
    return `${Math.floor(seconds / 3600)}h ${Math.floor((seconds % 3600) / 60)}m`;
  }
}
