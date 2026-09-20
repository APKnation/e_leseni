import { Component, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';

import { AuthService } from '../../core/auth.service';

@Component({
  imports: [FormsModule, RouterLink],
  selector: 'app-login',
  templateUrl: './login.html',
})
export class Login {
  private readonly auth = inject(AuthService);
  private readonly router = inject(Router);

  protected readonly username = signal('');
  protected readonly password = signal('');
  protected readonly submitting = signal(false);
  protected readonly errorMessage = signal('');

  protected submit(): void {
    if (this.submitting()) return;
    this.submitting.set(true);
    this.errorMessage.set('');

    this.auth.login(this.username(), this.password()).subscribe({
      next: () => void this.router.navigate(['/dashboard']),
      error: () => {
        this.errorMessage.set('Invalid username or password.');
        this.submitting.set(false);
      },
    });
  }
}
