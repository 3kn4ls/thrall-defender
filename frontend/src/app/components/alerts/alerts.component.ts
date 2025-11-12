import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { MatTableModule } from '@angular/material/table';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatChipsModule } from '@angular/material/chips';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatSelectModule } from '@angular/material/select';
import { MatButtonToggleModule } from '@angular/material/button-toggle';
import { MatPaginatorModule, PageEvent } from '@angular/material/paginator';
import { MatCardModule } from '@angular/material/card';
import { MatExpansionModule } from '@angular/material/expansion';
import { MatTooltipModule } from '@angular/material/tooltip';
import { MatBadgeModule } from '@angular/material/badge';
import { Subject, interval } from 'rxjs';
import { takeUntil } from 'rxjs/operators';
import { ApiService } from '../../services/api.service';
import { Alert, Packet } from '../../models/packet.model';

interface AlertStats {
  total: number;
  critical: number;
  high: number;
  medium: number;
  low: number;
  unacknowledged: number;
  by_type: { [key: string]: number };
}

@Component({
  selector: 'app-alerts',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    MatTableModule,
    MatButtonModule,
    MatIconModule,
    MatChipsModule,
    MatFormFieldModule,
    MatInputModule,
    MatSelectModule,
    MatButtonToggleModule,
    MatPaginatorModule,
    MatCardModule,
    MatExpansionModule,
    MatTooltipModule,
    MatBadgeModule
  ],
  templateUrl: './alerts.component.html',
  styleUrls: ['./alerts.component.scss']
})
export class AlertsComponent implements OnInit, OnDestroy {
  // Alerts data
  alerts: Alert[] = [];
  filteredAlerts: Alert[] = [];
  displayedAlerts: Alert[] = [];
  loading = false;

  // Pagination
  pageSize = 20;
  pageIndex = 0;
  totalAlerts = 0;

  // Filters
  selectedSeverity = 'all';
  selectedType = 'all';
  selectedStatus = 'unacknowledged'; // Show only unacknowledged by default
  searchIP = '';

  // Available filter options
  severities = ['all', 'critical', 'high', 'medium', 'low'];
  alertTypes: string[] = [];
  statusOptions = [
    { value: 'all', label: 'Todas' },
    { value: 'unacknowledged', label: 'No Reconocidas' },
    { value: 'acknowledged', label: 'Reconocidas' }
  ];

  // Stats
  stats: AlertStats = {
    total: 0,
    critical: 0,
    high: 0,
    medium: 0,
    low: 0,
    unacknowledged: 0,
    by_type: {}
  };

  // Suspect packets for analysis
  suspectPackets: { [alertId: number]: Packet[] } = {};
  loadingPackets: { [alertId: number]: boolean } = {};

  // Table columns
  displayedColumns: string[] = ['timestamp', 'severity', 'type', 'source', 'port', 'description', 'actions'];

  // Auto-refresh
  private destroy$ = new Subject<void>();
  autoRefresh = true;

  constructor(private apiService: ApiService) {}

  ngOnInit(): void {
    this.loadAlerts();

    // Auto-refresh every 10 seconds if enabled
    interval(10000)
      .pipe(takeUntil(this.destroy$))
      .subscribe(() => {
        if (this.autoRefresh) {
          this.loadAlerts();
        }
      });
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  loadAlerts(): void {
    this.loading = true;
    // Load all alerts (we'll filter client-side for better UX)
    this.apiService.getAlerts().subscribe({
      next: (alerts) => {
        this.alerts = alerts;
        this.calculateStats();
        this.extractAlertTypes();
        this.applyFilters();
        this.loading = false;
      },
      error: (error) => {
        console.error('Error loading alerts:', error);
        this.loading = false;
      }
    });
  }

  calculateStats(): void {
    this.stats = {
      total: this.alerts.length,
      critical: 0,
      high: 0,
      medium: 0,
      low: 0,
      unacknowledged: 0,
      by_type: {}
    };

    this.alerts.forEach(alert => {
      // Count by severity
      if (alert.severity === 'critical') this.stats.critical++;
      else if (alert.severity === 'high') this.stats.high++;
      else if (alert.severity === 'medium') this.stats.medium++;
      else if (alert.severity === 'low') this.stats.low++;

      // Count unacknowledged
      if (!alert.acknowledged) this.stats.unacknowledged++;

      // Count by type
      if (!this.stats.by_type[alert.alert_type]) {
        this.stats.by_type[alert.alert_type] = 0;
      }
      this.stats.by_type[alert.alert_type]++;
    });
  }

  extractAlertTypes(): void {
    const types = new Set(this.alerts.map(a => a.alert_type));
    this.alertTypes = ['all', ...Array.from(types)];
  }

  applyFilters(): void {
    let filtered = [...this.alerts];

    // Filter by severity
    if (this.selectedSeverity !== 'all') {
      filtered = filtered.filter(a => a.severity === this.selectedSeverity);
    }

    // Filter by type
    if (this.selectedType !== 'all') {
      filtered = filtered.filter(a => a.alert_type === this.selectedType);
    }

    // Filter by status
    if (this.selectedStatus === 'unacknowledged') {
      filtered = filtered.filter(a => !a.acknowledged);
    } else if (this.selectedStatus === 'acknowledged') {
      filtered = filtered.filter(a => a.acknowledged);
    }

    // Filter by IP
    if (this.searchIP.trim()) {
      const searchTerm = this.searchIP.trim().toLowerCase();
      filtered = filtered.filter(a =>
        a.source_ip.toLowerCase().includes(searchTerm)
      );
    }

    // Sort by timestamp (newest first)
    filtered.sort((a, b) =>
      new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
    );

    this.filteredAlerts = filtered;
    this.totalAlerts = filtered.length;
    this.updateDisplayedAlerts();
  }

  updateDisplayedAlerts(): void {
    const startIndex = this.pageIndex * this.pageSize;
    const endIndex = startIndex + this.pageSize;
    this.displayedAlerts = this.filteredAlerts.slice(startIndex, endIndex);
  }

  onPageChange(event: PageEvent): void {
    this.pageIndex = event.pageIndex;
    this.pageSize = event.pageSize;
    this.updateDisplayedAlerts();
  }

  onFilterChange(): void {
    this.pageIndex = 0; // Reset to first page
    this.applyFilters();
  }

  acknowledgeAlert(id: number): void {
    this.apiService.acknowledgeAlert(id).subscribe({
      next: () => {
        // Update locally
        const alert = this.alerts.find(a => a.id === id);
        if (alert) {
          alert.acknowledged = true;
        }
        this.calculateStats();
        this.applyFilters();
      },
      error: (error) => {
        console.error('Error acknowledging alert:', error);
      }
    });
  }

  acknowledgeAll(): void {
    if (confirm(`¿Reconocer todas las ${this.stats.unacknowledged} alertas no reconocidas?`)) {
      const unacknowledgedIds = this.alerts
        .filter(a => !a.acknowledged)
        .map(a => a.id);

      // Acknowledge them one by one (you could batch this in the backend)
      let completed = 0;
      unacknowledgedIds.forEach(id => {
        this.apiService.acknowledgeAlert(id).subscribe({
          next: () => {
            completed++;
            if (completed === unacknowledgedIds.length) {
              this.loadAlerts();
            }
          }
        });
      });
    }
  }

  loadSuspectPackets(alert: Alert): void {
    if (this.suspectPackets[alert.id]) {
      // Already loaded, toggle expansion
      return;
    }

    this.loadingPackets[alert.id] = true;

    // Load packets from this IP around the alert time
    this.apiService.getPackets(0, 50).subscribe({
      next: (packets) => {
        // Filter packets from the source IP within 1 minute of alert
        const alertTime = new Date(alert.timestamp).getTime();
        const oneMinute = 60 * 1000;

        this.suspectPackets[alert.id] = packets.filter(p => {
          const packetTime = new Date(p.timestamp).getTime();
          return p.source_ip === alert.source_ip &&
                 Math.abs(packetTime - alertTime) <= oneMinute;
        });

        this.loadingPackets[alert.id] = false;
      },
      error: (error) => {
        console.error('Error loading packets:', error);
        this.loadingPackets[alert.id] = false;
      }
    });
  }

  getSeverityColor(severity: string): string {
    const colors: any = {
      'critical': '#f44336',
      'high': '#ff5722',
      'medium': '#ff9800',
      'low': '#fbc02d'
    };
    return colors[severity] || '#9e9e9e';
  }

  getAlertTypeIcon(type: string): string {
    const icons: any = {
      'suspicious_ip': 'warning',
      'port_scan': 'bug_report',
      'blacklisted_ip': 'block',
      'ddos_attack': 'security',
      'brute_force': 'vpn_key',
      'unusual_traffic': 'trending_up'
    };
    return icons[type] || 'notification_important';
  }

  getAlertTypeLabel(type: string): string {
    const labels: any = {
      'suspicious_ip': 'IP Sospechosa',
      'port_scan': 'Escaneo de Puertos',
      'blacklisted_ip': 'IP en Lista Negra',
      'ddos_attack': 'Ataque DDoS',
      'brute_force': 'Fuerza Bruta',
      'unusual_traffic': 'Tráfico Inusual'
    };
    return labels[type] || type;
  }
}
