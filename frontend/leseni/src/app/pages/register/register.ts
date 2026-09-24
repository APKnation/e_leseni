import { Component, inject, signal, computed } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';

import { AuthService } from '../../core/auth.service';

@Component({
  imports: [FormsModule, RouterLink],
  selector: 'app-register',
  templateUrl: './register.html',
})
export class Register {
  private readonly auth = inject(AuthService);
  private readonly router = inject(Router);

  protected readonly form = signal({
    first_name: '',
    last_name: '',
    username: '',
    email: '',
    phone_number: '',
    nida_number: '',
    password: '',
  });
  protected readonly confirmPassword = signal('');
  protected readonly submitting = signal(false);
  protected readonly errorMessage = signal('');

  protected readonly passwordMismatch = computed(
    () => this.confirmPassword() !== '' && this.form().password !== this.confirmPassword(),
  );

  protected update(field: keyof ReturnType<typeof this.form>, value: string): void {
    this.form.update((f) => ({ ...f, [field]: value }));
  }

  protected submit(): void {
    if (this.submitting()) return;

    if (this.form().password !== this.confirmPassword()) {
      this.errorMessage.set('Passwords do not match. Please check and try again.');
      return;
    }

    this.submitting.set(true);
    this.errorMessage.set('');

    this.auth.register(this.form()).subscribe({
      next: () =>
        this.auth.login(this.form().username, this.form().password).subscribe({
          next: () => void this.router.navigate(['/dashboard']),
          error: () => void this.router.navigate(['/login']),
        }),
      error: (err) => {
        const detail = err?.error ? Object.values(err.error).flat()[0] : null;
        this.errorMessage.set(
          typeof detail === 'string' ? detail : 'Registration failed. Please check your details.',
        );
        this.submitting.set(false);
      },
    });
  }
}
