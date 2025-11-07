import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatTableModule } from '@angular/material/table';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatChipsModule } from '@angular/material/chips';
import { ApiService } from '../../services/api.service';
import { Alert } from '../../models/packet.model';

@Component({
  selector: 'app-alerts',
  standalone: true,
  imports: [CommonModule, MatTableModule, MatButtonModule, MatIconModule, MatChipsModule],
  template: `
    <div class="alerts">
      <h3>Alertas de Seguridad</h3>

      <div class="table-container">
        <table mat-table [dataSource]="alerts" class="full-width">
          <ng-container matColumnDef="timestamp">
            <th mat-header-cell *matHeaderCellDef>Tiempo</th>
            <td mat-cell *matCellDef="let alert">
              {{ alert.timestamp | date:'dd/MM/yyyy HH:mm' }}
            </td>
          </ng-container>

          <ng-container matColumnDef="severity">
            <th mat-header-cell *matHeaderCellDef>Severidad</th>
            <td mat-cell *matCellDef="let alert">
              <mat-chip [class]="'alert-severity ' + alert.severity">
                {{ alert.severity | uppercase }}
              </mat-chip>
            </td>
          </ng-container>

          <ng-container matColumnDef="type">
            <th mat-header-cell *matHeaderCellDef>Tipo</th>
            <td mat-cell *matCellDef="let alert">
              {{ alert.alert_type }}
            </td>
          </ng-container>

          <ng-container matColumnDef="source">
            <th mat-header-cell *matHeaderCellDef>IP Origen</th>
            <td mat-cell *matCellDef="let alert">
              {{ alert.source_ip }}
            </td>
          </ng-container>

          <ng-container matColumnDef="description">
            <th mat-header-cell *matHeaderCellDef>Descripción</th>
            <td mat-cell *matCellDef="let alert">
              {{ alert.description }}
            </td>
          </ng-container>

          <ng-container matColumnDef="actions">
            <th mat-header-cell *matHeaderCellDef>Acciones</th>
            <td mat-cell *matCellDef="let alert">
              <button
                mat-button
                color="primary"
                *ngIf="!alert.acknowledged"
                (click)="acknowledgeAlert(alert.id)">
                <mat-icon>check</mat-icon>
                Reconocer
              </button>
              <span *ngIf="alert.acknowledged" style="color: #4caf50;">
                <mat-icon style="font-size: 18px; vertical-align: middle;">check_circle</mat-icon>
                Reconocida
              </span>
            </td>
          </ng-container>

          <tr mat-header-row *matHeaderRowDef="displayedColumns"></tr>
          <tr mat-row *matRowDef="let row; columns: displayedColumns;"></tr>
        </table>
      </div>

      <div *ngIf="alerts.length === 0" class="no-data">
        <mat-icon>notifications_off</mat-icon>
        <p>No hay alertas</p>
      </div>
    </div>
  `,
  styles: [`
    .alerts {
      h3 {
        margin-top: 0;
        margin-bottom: 16px;
      }
    }

    .table-container {
      overflow-x: auto;
      max-height: 500px;
      overflow-y: auto;
    }

    table {
      width: 100%;
    }

    .no-data {
      text-align: center;
      padding: 40px;
      color: #999;

      mat-icon {
        font-size: 48px;
        width: 48px;
        height: 48px;
      }
    }
  `]
})
export class AlertsComponent implements OnInit {
  alerts: Alert[] = [];
  displayedColumns: string[] = ['timestamp', 'severity', 'type', 'source', 'description', 'actions'];

  constructor(private apiService: ApiService) {}

  ngOnInit(): void {
    this.loadAlerts();
  }

  loadAlerts(): void {
    this.apiService.getAlerts().subscribe({
      next: (alerts) => {
        this.alerts = alerts;
      },
      error: (error) => {
        console.error('Error loading alerts:', error);
      }
    });
  }

  acknowledgeAlert(id: number): void {
    this.apiService.acknowledgeAlert(id).subscribe({
      next: () => {
        this.loadAlerts();
      },
      error: (error) => {
        console.error('Error acknowledging alert:', error);
      }
    });
  }
}
