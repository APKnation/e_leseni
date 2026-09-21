import { Component, inject } from '@angular/core';
import { Router, RouterLink, RouterOutlet } from '@angular/router';

import { AuthService, ROLE_LABELS } from './core/auth.service';

@Component({
  imports: [RouterOutlet, RouterLink],
  selector: 'app-root',
  styleUrl: './app.css',
  templateUrl: './app.html',
})
export class App {
  protected readonly auth = inject(AuthService);
  protected readonly roleLabel = ROLE_LABELS;
  protected readonly year = new Date().getFullYear();
  private readonly router = inject(Router);

  protected logout(): void {
    this.auth.logout();
    void this.router.navigate(['/']);
  }
}
