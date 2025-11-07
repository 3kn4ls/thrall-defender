import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatCardModule } from '@angular/material/card';
import { MatGridListModule } from '@angular/material/grid-list';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatTabsModule } from '@angular/material/tabs';
import { Subject, interval } from 'rxjs';
import { takeUntil } from 'rxjs/operators';

import { ApiService } from '../../services/api.service';
import { WebsocketService } from '../../services/websocket.service';
import { Stats, Packet } from '../../models/packet.model';
import { PacketListComponent } from '../packet-list/packet-list.component';
import { AlertsComponent } from '../alerts/alerts.component';
import { IpManagementComponent } from '../ip-management/ip-management.component';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [
    CommonModule,
    MatCardModule,
    MatGridListModule,
    MatProgressSpinnerModule,
    MatTabsModule,
    PacketListComponent,
    AlertsComponent,
    IpManagementComponent
  ],
  templateUrl: './dashboard.component.html',
  styleUrls: ['./dashboard.component.scss']
})
export class DashboardComponent implements OnInit, OnDestroy {
  stats?: Stats;
  recentPackets: Packet[] = [];
  isConnected = false;
  loading = true;

  private destroy$ = new Subject<void>();

  constructor(
    private apiService: ApiService,
    private wsService: WebsocketService
  ) {}

  ngOnInit(): void {
    this.loadStatistics();
    this.loadRecentPackets();

    // Actualizar estadísticas cada 5 segundos
    interval(5000)
      .pipe(takeUntil(this.destroy$))
      .subscribe(() => this.loadStatistics());

    // Escuchar paquetes en tiempo real
    this.wsService.packets$
      .pipe(takeUntil(this.destroy$))
      .subscribe(packet => {
        this.recentPackets.unshift(packet);
        if (this.recentPackets.length > 50) {
          this.recentPackets.pop();
        }
      });

    // Estado de conexión WebSocket
    this.wsService.connected$
      .pipe(takeUntil(this.destroy$))
      .subscribe(connected => {
        this.isConnected = connected;
      });
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  private loadStatistics(): void {
    this.apiService.getStatistics().subscribe({
      next: (stats) => {
        this.stats = stats;
        this.loading = false;
      },
      error: (error) => {
        console.error('Error loading statistics:', error);
        this.loading = false;
      }
    });
  }

  private loadRecentPackets(): void {
    this.apiService.getPackets(0, 50).subscribe({
      next: (packets) => {
        this.recentPackets = packets;
      },
      error: (error) => {
        console.error('Error loading packets:', error);
      }
    });
  }
}
