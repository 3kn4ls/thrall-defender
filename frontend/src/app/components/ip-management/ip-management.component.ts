import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { MatTabsModule } from '@angular/material/tabs';
import { MatTableModule } from '@angular/material/table';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatInputModule } from '@angular/material/input';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatCardModule } from '@angular/material/card';
import { ApiService } from '../../services/api.service';
import { IPWhitelist, IPBlacklist } from '../../models/packet.model';

@Component({
  selector: 'app-ip-management',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    MatTabsModule,
    MatTableModule,
    MatButtonModule,
    MatIconModule,
    MatInputModule,
    MatFormFieldModule,
    MatCardModule
  ],
  templateUrl: './ip-management.component.html',
  styleUrls: ['./ip-management.component.scss']
})
export class IpManagementComponent implements OnInit {
  whitelist: IPWhitelist[] = [];
  blacklist: IPBlacklist[] = [];

  newWhitelistIp = '';
  newWhitelistDesc = '';
  newBlacklistIp = '';
  newBlacklistDesc = '';

  whitelistColumns: string[] = ['ip_address', 'description', 'created_at', 'actions'];
  blacklistColumns: string[] = ['ip_address', 'description', 'blocked_count', 'created_at', 'actions'];

  constructor(private apiService: ApiService) {}

  ngOnInit(): void {
    this.loadWhitelist();
    this.loadBlacklist();
  }

  loadWhitelist(): void {
    this.apiService.getWhitelist().subscribe({
      next: (data) => {
        this.whitelist = data;
      },
      error: (error) => {
        console.error('Error loading whitelist:', error);
      }
    });
  }

  loadBlacklist(): void {
    this.apiService.getBlacklist().subscribe({
      next: (data) => {
        this.blacklist = data;
      },
      error: (error) => {
        console.error('Error loading blacklist:', error);
      }
    });
  }

  addToWhitelist(): void {
    if (!this.newWhitelistIp) return;

    this.apiService.addToWhitelist(this.newWhitelistIp, this.newWhitelistDesc).subscribe({
      next: () => {
        this.newWhitelistIp = '';
        this.newWhitelistDesc = '';
        this.loadWhitelist();
      },
      error: (error) => {
        console.error('Error adding to whitelist:', error);
        alert('Error al añadir IP a la lista blanca');
      }
    });
  }

  removeFromWhitelist(id: number): void {
    if (!confirm('¿Estás seguro de eliminar esta IP de la lista blanca?')) return;

    this.apiService.removeFromWhitelist(id).subscribe({
      next: () => {
        this.loadWhitelist();
      },
      error: (error) => {
        console.error('Error removing from whitelist:', error);
      }
    });
  }

  addToBlacklist(): void {
    if (!this.newBlacklistIp) return;

    this.apiService.addToBlacklist(this.newBlacklistIp, this.newBlacklistDesc).subscribe({
      next: () => {
        this.newBlacklistIp = '';
        this.newBlacklistDesc = '';
        this.loadBlacklist();
      },
      error: (error) => {
        console.error('Error adding to blacklist:', error);
        alert('Error al añadir IP a la lista negra');
      }
    });
  }

  removeFromBlacklist(id: number): void {
    if (!confirm('¿Estás seguro de eliminar esta IP de la lista negra?')) return;

    this.apiService.removeFromBlacklist(id).subscribe({
      next: () => {
        this.loadBlacklist();
      },
      error: (error) => {
        console.error('Error removing from blacklist:', error);
      }
    });
  }
}
