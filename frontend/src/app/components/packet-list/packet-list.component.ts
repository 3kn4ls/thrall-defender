import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatTableModule } from '@angular/material/table';
import { MatChipsModule } from '@angular/material/chips';
import { MatIconModule } from '@angular/material/icon';
import { Packet } from '../../models/packet.model';

@Component({
  selector: 'app-packet-list',
  standalone: true,
  imports: [CommonModule, MatTableModule, MatChipsModule, MatIconModule],
  template: `
    <div class="packet-list">
      <h3>Paquetes Recientes</h3>
      <div class="table-container">
        <table mat-table [dataSource]="packets" class="full-width">
          <ng-container matColumnDef="timestamp">
            <th mat-header-cell *matHeaderCellDef>Tiempo</th>
            <td mat-cell *matCellDef="let packet">
              {{ packet.timestamp | date:'HH:mm:ss' }}
            </td>
          </ng-container>

          <ng-container matColumnDef="source">
            <th mat-header-cell *matHeaderCellDef>Origen</th>
            <td mat-cell *matCellDef="let packet">
              {{ packet.source_ip }}:{{ packet.source_port }}
            </td>
          </ng-container>

          <ng-container matColumnDef="destination">
            <th mat-header-cell *matHeaderCellDef>Destino</th>
            <td mat-cell *matCellDef="let packet">
              {{ packet.destination_ip }}:{{ packet.destination_port }}
            </td>
          </ng-container>

          <ng-container matColumnDef="protocol">
            <th mat-header-cell *matHeaderCellDef>Protocolo</th>
            <td mat-cell *matCellDef="let packet">
              <mat-chip>{{ packet.protocol }}</mat-chip>
            </td>
          </ng-container>

          <ng-container matColumnDef="size">
            <th mat-header-cell *matHeaderCellDef>Tamaño</th>
            <td mat-cell *matCellDef="let packet">
              {{ packet.packet_size }} bytes
            </td>
          </ng-container>

          <ng-container matColumnDef="status">
            <th mat-header-cell *matHeaderCellDef>Estado</th>
            <td mat-cell *matCellDef="let packet">
              <mat-chip
                [class.suspicious]="packet.is_suspicious && !packet.is_blocked"
                [class.blocked]="packet.is_blocked"
                [class.normal]="!packet.is_suspicious && !packet.is_blocked"
                class="status-chip">
                <mat-icon *ngIf="packet.is_blocked">block</mat-icon>
                <mat-icon *ngIf="packet.is_suspicious && !packet.is_blocked">warning</mat-icon>
                <mat-icon *ngIf="!packet.is_suspicious && !packet.is_blocked">check_circle</mat-icon>
                {{ packet.is_blocked ? 'Bloqueado' : (packet.is_suspicious ? 'Sospechoso' : 'Normal') }}
              </mat-chip>
            </td>
          </ng-container>

          <tr mat-header-row *matHeaderRowDef="displayedColumns"></tr>
          <tr mat-row *matRowDef="let row; columns: displayedColumns;"></tr>
        </table>
      </div>

      <div *ngIf="packets.length === 0" class="no-data">
        <mat-icon>info</mat-icon>
        <p>No hay paquetes para mostrar</p>
      </div>
    </div>
  `,
  styles: [`
    .packet-list {
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

    .status-chip {
      display: inline-flex;
      align-items: center;
      gap: 4px;

      mat-icon {
        font-size: 16px;
        width: 16px;
        height: 16px;
      }
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
export class PacketListComponent {
  @Input() packets: Packet[] = [];

  displayedColumns: string[] = ['timestamp', 'source', 'destination', 'protocol', 'size', 'status'];
}
