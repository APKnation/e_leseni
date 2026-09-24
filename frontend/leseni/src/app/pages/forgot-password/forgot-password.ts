import { Component, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';

import { AuthService } from '../../core/auth.service';

type Step = 'verify' | 'reset' | 'done';

@Component({
  imports: [FormsModule, RouterLink],
  selector: 'app-forgot-password',
  templateUrl: './forgot-password.html',
})
export class ForgotPassword {
  private readonly auth = inject(AuthService);
  private readonly router = inject(Router);

  protected readonly step = signal<Step>('verify');
  protected readonly submitting = signal(false);
  protected readonly errorMessage = signal('');

  // Step 1
  protected readonly username = signal('');
  protected readonly phone = signal('');

  // Step 2 (token received from step 1)
  protected readonly token = signal('');
  protected readonly newPassword = signal('');
  protected readonly confirmPassword = signal('');

  protected readonly passwordMismatch = () =>
    this.confirmPassword() !== '' && this.newPassword() !== this.confirmPassword();

  protected submitVerify(): void {
    if (this.submitting()) return;
    this.submitting.set(true);
    this.errorMessage.set('');

    this.auth.passwordResetRequest(this.username(), this.phone()).subscribe({
      next: (res) => {
        this.token.set(res.token);
        this.step.set('reset');
        this.submitting.set(false);
      },
      error: (err) => {
        const detail = err?.error
          ? (Object.values(err.error).flat()[0] as string)
          : 'Could not verify your account. Please check your details.';
        this.errorMessage.set(typeof detail === 'string' ? detail : 'Verification failed.');
        this.submitting.set(false);
      },
    });
  }

  protected submitReset(): void {
    if (this.submitting()) return;
    if (this.newPassword() !== this.confirmPassword()) {
      this.errorMessage.set('Passwords do not match.');
      return;
    }
    this.submitting.set(true);
    this.errorMessage.set('');

    this.auth.passwordResetConfirm(this.token(), this.newPassword()).subscribe({
      next: () => {
        this.step.set('done');
        this.submitting.set(false);
      },
      error: (err) => {
        const detail = err?.error?.token?.[0] ?? err?.error?.new_password?.[0] ?? 'Reset failed. Please try again.';
        this.errorMessage.set(detail);
        this.submitting.set(false);
      },
    });
  }
}
