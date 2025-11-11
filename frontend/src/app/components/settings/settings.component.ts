import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, FormGroup, ReactiveFormsModule, Validators } from '@angular/forms';
import { MatCardModule } from '@angular/material/card';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatButtonModule } from '@angular/material/button';
import { MatSlideToggleModule } from '@angular/material/slide-toggle';
import { MatSelectModule } from '@angular/material/select';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';
import { MatTabsModule } from '@angular/material/tabs';
import { MatSliderModule } from '@angular/material/slider';
import { MatIconModule } from '@angular/material/icon';
import { MatDividerModule } from '@angular/material/divider';

interface AppSettings {
  backend: {
    url: string;
    wsUrl: string;
    timeout: number;
  };
  ui: {
    refreshInterval: number;
    theme: 'light' | 'dark' | 'auto';
    density: 'comfortable' | 'compact';
    language: 'es' | 'en';
  };
  notifications: {
    enabled: boolean;
    alerts: boolean;
    ddosAttacks: boolean;
    newIpBlocked: boolean;
  };
  display: {
    packetsPerPage: number;
    autoRefresh: boolean;
    showCharts: boolean;
  };
}

@Component({
  selector: 'app-settings',
  standalone: true,
  imports: [
    CommonModule,
    ReactiveFormsModule,
    MatCardModule,
    MatFormFieldModule,
    MatInputModule,
    MatButtonModule,
    MatSlideToggleModule,
    MatSelectModule,
    MatSnackBarModule,
    MatTabsModule,
    MatSliderModule,
    MatIconModule,
    MatDividerModule
  ],
  templateUrl: './settings.component.html',
  styleUrls: ['./settings.component.scss']
})
export class SettingsComponent implements OnInit {
  settingsForm!: FormGroup;
  private readonly STORAGE_KEY = 'thrall_defender_settings';

  defaultSettings: AppSettings = {
    backend: {
      url: 'http://localhost:8000',
      wsUrl: 'ws://localhost:8000',
      timeout: 30000
    },
    ui: {
      refreshInterval: 5000,
      theme: 'auto',
      density: 'comfortable',
      language: 'es'
    },
    notifications: {
      enabled: true,
      alerts: true,
      ddosAttacks: true,
      newIpBlocked: true
    },
    display: {
      packetsPerPage: 50,
      autoRefresh: true,
      showCharts: true
    }
  };

  constructor(
    private fb: FormBuilder,
    private snackBar: MatSnackBar
  ) {}

  ngOnInit(): void {
    const savedSettings = this.loadSettings();

    this.settingsForm = this.fb.group({
      // Backend settings
      backendUrl: [savedSettings.backend.url, [Validators.required, Validators.pattern(/^https?:\/\/.+/)]],
      wsUrl: [savedSettings.backend.wsUrl, [Validators.required, Validators.pattern(/^wss?:\/\/.+/)]],
      timeout: [savedSettings.backend.timeout, [Validators.required, Validators.min(5000), Validators.max(60000)]],

      // UI settings
      refreshInterval: [savedSettings.ui.refreshInterval, [Validators.required, Validators.min(1000), Validators.max(60000)]],
      theme: [savedSettings.ui.theme, Validators.required],
      density: [savedSettings.ui.density, Validators.required],
      language: [savedSettings.ui.language, Validators.required],

      // Notifications
      notificationsEnabled: [savedSettings.notifications.enabled],
      alertsNotification: [savedSettings.notifications.alerts],
      ddosNotification: [savedSettings.notifications.ddosAttacks],
      ipBlockedNotification: [savedSettings.notifications.newIpBlocked],

      // Display
      packetsPerPage: [savedSettings.display.packetsPerPage, [Validators.required, Validators.min(10), Validators.max(200)]],
      autoRefresh: [savedSettings.display.autoRefresh],
      showCharts: [savedSettings.display.showCharts]
    });
  }

  private loadSettings(): AppSettings {
    try {
      const saved = localStorage.getItem(this.STORAGE_KEY);
      if (saved) {
        return { ...this.defaultSettings, ...JSON.parse(saved) };
      }
    } catch (error) {
      console.error('Error loading settings:', error);
    }
    return this.defaultSettings;
  }

  private saveSettings(settings: AppSettings): void {
    try {
      localStorage.setItem(this.STORAGE_KEY, JSON.stringify(settings));
    } catch (error) {
      console.error('Error saving settings:', error);
    }
  }

  onSave(): void {
    if (this.settingsForm.valid) {
      const formValue = this.settingsForm.value;

      const settings: AppSettings = {
        backend: {
          url: formValue.backendUrl,
          wsUrl: formValue.wsUrl,
          timeout: formValue.timeout
        },
        ui: {
          refreshInterval: formValue.refreshInterval,
          theme: formValue.theme,
          density: formValue.density,
          language: formValue.language
        },
        notifications: {
          enabled: formValue.notificationsEnabled,
          alerts: formValue.alertsNotification,
          ddosAttacks: formValue.ddosNotification,
          newIpBlocked: formValue.ipBlockedNotification
        },
        display: {
          packetsPerPage: formValue.packetsPerPage,
          autoRefresh: formValue.autoRefresh,
          showCharts: formValue.showCharts
        }
      };

      this.saveSettings(settings);
      this.snackBar.open('Configuración guardada correctamente. Recarga la página para aplicar los cambios.', 'OK', {
        duration: 5000
      });
    }
  }

  onReset(): void {
    if (confirm('¿Estás seguro de que deseas restablecer la configuración a los valores predeterminados?')) {
      this.saveSettings(this.defaultSettings);
      this.ngOnInit();
      this.snackBar.open('Configuración restablecida a valores predeterminados', 'OK', {
        duration: 3000
      });
    }
  }

  onExport(): void {
    const settings = this.loadSettings();
    const dataStr = JSON.stringify(settings, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(dataBlob);
    const link = document.createElement('a');
    link.href = url;
    link.download = 'thrall-defender-settings.json';
    link.click();
    URL.revokeObjectURL(url);

    this.snackBar.open('Configuración exportada correctamente', 'OK', {
      duration: 3000
    });
  }

  onImport(event: Event): void {
    const input = event.target as HTMLInputElement;
    if (input.files && input.files[0]) {
      const file = input.files[0];
      const reader = new FileReader();

      reader.onload = (e) => {
        try {
          const settings = JSON.parse(e.target?.result as string);
          this.saveSettings(settings);
          this.ngOnInit();
          this.snackBar.open('Configuración importada correctamente', 'OK', {
            duration: 3000
          });
        } catch (error) {
          this.snackBar.open('Error al importar la configuración', 'ERROR', {
            duration: 3000
          });
        }
      };

      reader.readAsText(file);
    }
  }

  formatLabel(value: number): string {
    return `${value / 1000}s`;
  }
}
