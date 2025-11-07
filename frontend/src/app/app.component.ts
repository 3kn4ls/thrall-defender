import { Component } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { MatToolbarModule } from '@angular/material/toolbar';
import { MatIconModule } from '@angular/material/icon';
import { MatButtonModule } from '@angular/material/button';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [
    RouterOutlet,
    MatToolbarModule,
    MatIconModule,
    MatButtonModule
  ],
  template: `
    <mat-toolbar color="primary">
      <mat-icon>shield</mat-icon>
      <span style="margin-left: 10px;">Thrall Defender</span>
      <span class="spacer"></span>
      <span style="font-size: 14px; opacity: 0.8;">Network Traffic Monitor</span>
    </mat-toolbar>
    <router-outlet></router-outlet>
  `,
  styles: [`
    :host {
      display: block;
      height: 100vh;
      overflow: hidden;
    }
  `]
})
export class AppComponent {
  title = 'Thrall Defender';
}
