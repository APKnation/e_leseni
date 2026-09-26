import { Component, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { AuthService } from '../../core/auth.service';
import { ApiService } from '../../core/api.service';

@Component({
  imports: [CommonModule, FormsModule, RouterLink],
  selector: 'app-profile',
  templateUrl: './profile.html',
})
export class Profile {
  protected readonly auth = inject(AuthService);
  private readonly api = inject(ApiService);

  protected readonly user = this.auth.currentUser;

  protected readonly editing = signal(false);
  protected readonly saving = signal(false);
  
  protected readonly successMessage = signal('');
  protected readonly errorMessage = signal('');

  protected readonly formData = signal({
    first_name: '',
    last_name: '',
    email: '',
    phone_number: '',
    nida_number: '',
  });

  protected startEditing(): void {
    const u = this.user();
    if (u) {
      this.formData.set({
        first_name: u.first_name || '',
        last_name: u.last_name || '',
        email: u.email || '',
        phone_number: u.phone_number || '',
        nida_number: u.nida_number || '',
      });
      this.editing.set(true);
      this.errorMessage.set('');
      this.successMessage.set('');
    }
  }

  protected cancelEditing(): void {
    this.editing.set(false);
    this.errorMessage.set('');
  }

  protected saveProfile(): void {
    if (this.saving()) return;
    this.saving.set(true);
    this.errorMessage.set('');

    this.api.updateProfile(this.formData()).subscribe({
      next: (updatedUser) => {
        // Need to update auth service current user somehow
        this.auth.refreshUser().subscribe();
        
        this.saving.set(false);
        this.editing.set(false);
        this.successMessage.set('Profile updated successfully.');
        setTimeout(() => this.successMessage.set(''), 3000);
      },
      error: (err) => {
        this.saving.set(false);
        this.errorMessage.set(err.error?.detail || 'Failed to update profile.');
      },
    });
  }
}
