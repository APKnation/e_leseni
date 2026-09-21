import { Component, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';

import { AuthService } from '../../core/auth.service';

@Component({
  imports: [FormsModule, RouterLink],
  selector: 'app-login',
  templateUrl: './login.html',
})
export class Login {
  private readonly auth = inject(AuthService);
  private readonly router = inject(Router);
  private readonly route = inject(ActivatedRoute);

  protected readonly username = signal('');
  protected readonly password = signal('');
  protected readonly submitting = signal(false);
  protected readonly errorMessage = signal('');

  protected submit(): void {
    if (this.submitting()) return;
    this.submitting.set(true);
    this.errorMessage.set('');

    this.auth.login(this.username(), this.password()).subscribe({
      next: () => {
        // Staff land on their role workspace; applicants on the dashboard.
        const returnUrl = this.route.snapshot.queryParamMap.get('returnUrl') ?? this.auth.homeRoute();
        void this.router.navigateByUrl(returnUrl);
      },
      error: () => {
        this.errorMessage.set('Invalid username or password.');
        this.submitting.set(false);
      },
    });
  }
}
