import { Component, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterLink, Router } from '@angular/router';
import { AuthService } from '../../core/auth.service';
import { ApiService } from '../../core/api.service';

type ActiveTab = 'view' | 'edit' | 'password';

@Component({
  imports: [CommonModule, FormsModule, RouterLink],
  selector: 'app-profile',
  templateUrl: './profile.html',
})
export class Profile {
  protected readonly auth = inject(AuthService);
  private readonly api = inject(ApiService);
  private readonly router = inject(Router);

  protected readonly user = this.auth.currentUser;

  protected readonly activeTab = signal<ActiveTab>('view');
  protected readonly saving = signal(false);
  protected readonly successMessage = signal('');
  protected readonly errorMessage = signal('');

  // ── Edit profile form ────────────────────────────────────────────────────
  protected readonly formData = signal({
    first_name: '',
    last_name: '',
    email: '',
    phone_number: '',
    nida_number: '',
  });

  protected openEdit(): void {
    const u = this.user();
    if (u) {
      this.formData.set({
        first_name: u.first_name || '',
        last_name: u.last_name || '',
        email: u.email || '',
        phone_number: u.phone_number || '',
        nida_number: u.nida_number || '',
      });
    }
    this.clearMessages();
    this.activeTab.set('edit');
  }

  protected saveProfile(): void {
    if (this.saving()) return;
    this.saving.set(true);
    this.clearMessages();

    this.api.updateProfile(this.formData()).subscribe({
      next: (updatedUser) => {
        this.auth.updateUserSession(updatedUser);
        this.saving.set(false);
        this.activeTab.set('view');
        this.successMessage.set('Profile updated successfully.');
        setTimeout(() => this.successMessage.set(''), 4000);
      },
      error: (err) => {
        this.saving.set(false);
        const detail = err.error
          ? Object.values(err.error).flat().join(' ')
          : 'Failed to update profile.';
        this.errorMessage.set(String(detail));
      },
    });
  }

  // ── Change password form ─────────────────────────────────────────────────
  protected readonly pwForm = signal({
    current_password: '',
    new_password: '',
    confirm_password: '',
  });

  protected openPassword(): void {
    this.pwForm.set({ current_password: '', new_password: '', confirm_password: '' });
    this.clearMessages();
    this.activeTab.set('password');
  }

  protected changePassword(): void {
    const f = this.pwForm();
    if (f.new_password !== f.confirm_password) {
      this.errorMessage.set('New passwords do not match.');
      return;
    }
    if (this.saving()) return;
    this.saving.set(true);
    this.clearMessages();

    this.api.changePassword(f.current_password, f.new_password).subscribe({
      next: () => {
        this.saving.set(false);
        // Force logout — tokens are now invalid
        this.auth.logout();
        this.router.navigateByUrl('/login?changed=1');
      },
      error: (err) => {
        this.saving.set(false);
        const detail = err.error?.current_password?.[0]
          ?? err.error?.new_password?.[0]
          ?? err.error?.detail
          ?? 'Failed to change password.';
        this.errorMessage.set(String(detail));
      },
    });
  }

  private clearMessages(): void {
    this.successMessage.set('');
    this.errorMessage.set('');
  }
}
