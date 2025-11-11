import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, FormGroup, ReactiveFormsModule, Validators, FormsModule } from '@angular/forms';
import { MatCardModule } from '@angular/material/card';
import { MatTabsModule } from '@angular/material/tabs';
import { MatTableModule } from '@angular/material/table';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatChipsModule } from '@angular/material/chips';
import { MatDividerModule } from '@angular/material/divider';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatSelectModule } from '@angular/material/select';
import { MatSlideToggleModule } from '@angular/material/slide-toggle';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';
import { MatTooltipModule } from '@angular/material/tooltip';
import { Subject, interval } from 'rxjs';
import { takeUntil } from 'rxjs/operators';

import { ApiService } from '../../services/api.service';
import {
  DDoSMitigationLevel,
  DDoSGeoRule,
  DDoSProtectionStatus,
  DDoSGeoStats,
  DDoSConfig,
  DDoSAttack,
  DDoSStats
} from '../../models/packet.model';

@Component({
  selector: 'app-ddos',
  standalone: true,
  imports: [
    CommonModule,
    ReactiveFormsModule,
    FormsModule,
    MatCardModule,
    MatTabsModule,
    MatTableModule,
    MatButtonModule,
    MatIconModule,
    MatChipsModule,
    MatFormFieldModule,
    MatInputModule,
    MatSelectModule,
    MatSlideToggleModule,
    MatDividerModule,
    MatProgressSpinnerModule,
    MatSnackBarModule,
    MatTooltipModule
  ],
  templateUrl: './ddos.component.html',
  styleUrls: ['./ddos.component.scss']
})
export class DdosComponent implements OnInit, OnDestroy {
  protectionStatus?: DDoSProtectionStatus;
  mitigationLevels: DDoSMitigationLevel[] = [];
  geoRules: DDoSGeoRule[] = [];
  geoStats: DDoSGeoStats[] = [];
  geoRuleForm!: FormGroup;
  showGeoRuleForm = false;
  config?: DDoSConfig;
  stats?: DDoSStats;
  activeAttacks: DDoSAttack[] = [];
  loading = true;
  attackColumns = ['timestamp', 'source_ip', 'attack_type', 'severity', 'pps', 'actions'];
  geoRuleColumns = ['country', 'action', 'priority', 'enabled', 'actions'];
  geoStatsColumns = ['country', 'attacks', 'blocked', 'packets'];
  availableCountries = [
    { code: 'US', name: 'United States' },
    { code: 'CN', name: 'China' },
    { code: 'RU', name: 'Russia' },
    { code: 'BR', name: 'Brazil' },
    { code: 'IN', name: 'India' },
    { code: 'KR', name: 'South Korea' },
    { code: 'JP', name: 'Japan' },
    { code: 'DE', name: 'Germany' },
    { code: 'GB', name: 'United Kingdom' },
    { code: 'FR', name: 'France' }
  ];
  private destroy$ = new Subject<void>();

  constructor(
    private apiService: ApiService,
    private snackBar: MatSnackBar,
    private fb: FormBuilder
  ) {
    this.geoRuleForm = this.fb.group({
      country_code: ['', Validators.required],
      country_name: ['', Validators.required],
      action: ['block', Validators.required],
      priority: [100, [Validators.required, Validators.min(1)]],
      enabled: [true],
      custom_rate_limit: [null],
      reason: ['']
    });
  }

  ngOnInit(): void {
    this.loadAllData();
    interval(5000).pipe(takeUntil(this.destroy$)).subscribe(() => this.loadRealTimeData());
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  loadAllData(): void {
    this.loading = true;
    this.loadProtectionStatus();
    this.loadMitigationLevels();
    this.loadGeoRules();
    this.loadGeoStats();
    this.loadConfig();
    this.loadStats();
    this.loadActiveAttacks();
    this.loading = false;
  }

  loadRealTimeData(): void {
    this.loadProtectionStatus();
    this.loadActiveAttacks();
    this.loadStats();
    this.loadGeoStats();
  }

  loadProtectionStatus(): void {
    this.apiService.getDDoSProtectionStatus().subscribe({
      next: (status) => this.protectionStatus = status,
      error: (error) => console.error('Error:', error)
    });
  }

  loadMitigationLevels(): void {
    this.apiService.getMitigationLevels().subscribe({
      next: (levels) => this.mitigationLevels = levels,
      error: (error) => console.error('Error:', error)
    });
  }

  loadGeoRules(): void {
    this.apiService.getGeoRules().subscribe({
      next: (rules) => this.geoRules = rules,
      error: (error) => console.error('Error:', error)
    });
  }

  loadGeoStats(): void {
    this.apiService.getDDoSGeoStats().subscribe({
      next: (stats) => this.geoStats = stats,
      error: (error) => console.error('Error:', error)
    });
  }

  loadConfig(): void {
    this.apiService.getDDoSConfig().subscribe({
      next: (config) => this.config = config,
      error: (error) => console.error('Error:', error)
    });
  }

  loadStats(): void {
    this.apiService.getDDoSStats().subscribe({
      next: (stats) => this.stats = stats,
      error: (error) => console.error('Error:', error)
    });
  }

  loadActiveAttacks(): void {
    this.apiService.getActiveDDoSAttacks().subscribe({
      next: (attacks) => this.activeAttacks = attacks,
      error: (error) => console.error('Error:', error)
    });
  }

  activateLevel(levelName: string): void {
    this.apiService.activateMitigationLevel(levelName).subscribe({
      next: () => {
        this.snackBar.open(`Nivel ${levelName} activado`, 'OK', { duration: 3000 });
        this.loadProtectionStatus();
        this.loadMitigationLevels();
      },
      error: () => this.snackBar.open('Error al activar nivel', 'ERROR', { duration: 3000 })
    });
  }

  onCountrySelect(event: any): void {
    const country = this.availableCountries.find(c => c.code === event.value);
    if (country) {
      this.geoRuleForm.patchValue({ country_name: country.name });
    }
  }

  createGeoRule(): void {
    if (this.geoRuleForm.valid) {
      this.apiService.createGeoRule(this.geoRuleForm.value).subscribe({
        next: () => {
          this.snackBar.open('Regla creada', 'OK', { duration: 3000 });
          this.loadGeoRules();
          this.showGeoRuleForm = false;
          this.geoRuleForm.reset({ action: 'block', priority: 100, enabled: true });
        },
        error: () => this.snackBar.open('Error al crear regla', 'ERROR', { duration: 3000 })
      });
    }
  }

  deleteGeoRule(ruleId: number): void {
    if (confirm('¿Eliminar esta regla?')) {
      this.apiService.deleteGeoRule(ruleId).subscribe({
        next: () => {
          this.snackBar.open('Regla eliminada', 'OK', { duration: 3000 });
          this.loadGeoRules();
        },
        error: () => this.snackBar.open('Error', 'ERROR', { duration: 3000 })
      });
    }
  }

  mitigateAttack(attack: DDoSAttack): void {
    this.apiService.mitigateDDoSAttack({ ip_address: attack.source_ip, attack_type: attack.attack_type }).subscribe({
      next: () => {
        this.snackBar.open(`Ataque mitigado`, 'OK', { duration: 3000 });
        this.loadActiveAttacks();
        this.loadProtectionStatus();
      },
      error: () => this.snackBar.open('Error', 'ERROR', { duration: 3000 })
    });
  }

  endAttack(ip: string): void {
    this.apiService.endDDoSAttack(ip).subscribe({
      next: () => {
        this.snackBar.open('Ataque finalizado', 'OK', { duration: 3000 });
        this.loadActiveAttacks();
      },
      error: () => this.snackBar.open('Error', 'ERROR', { duration: 3000 })
    });
  }

  getAttackTypeName(attackType: string): string {
    const types: { [key: string]: string } = {
      'syn_flood': 'SYN Flood',
      'udp_flood': 'UDP Flood',
      'icmp_flood': 'ICMP Flood',
      'high_pps': 'Alto PPS'
    };
    return types[attackType] || attackType;
  }

  updateConfig(): void {
    if (this.config) {
      this.apiService.updateDDoSConfig(this.config.id, this.config).subscribe({
        next: () => {
          this.snackBar.open('Configuración actualizada', 'OK', { duration: 3000 });
          this.loadConfig();
        },
        error: () => this.snackBar.open('Error al actualizar', 'ERROR', { duration: 3000 })
      });
    }
  }

  getThreatLevelColor(level: string): string {
    const colors: any = {
      'none': '#4caf50',
      'low': '#8bc34a',
      'medium': '#ff9800',
      'high': '#ff5722',
      'critical': '#f44336'
    };
    return colors[level] || '#9e9e9e';
  }

  getSeverityColor(severity: string): string {
    return this.getThreatLevelColor(severity);
  }

  getActionColor(action: string): string {
    const colors: any = {
      'allow': '#4caf50',
      'block': '#f44336',
      'challenge': '#ff9800',
      'rate_limit': '#2196f3'
    };
    return colors[action] || '#9e9e9e';
  }
}
