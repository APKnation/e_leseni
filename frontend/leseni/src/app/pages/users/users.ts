import { Component, OnInit, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';

import { ApiService } from '../../core/api.service';
import { AuthService, CreateUserData, ROLE_LABELS, User, UserRole } from '../../core/auth.service';
import { LGA } from '../../core/models';

interface UserFormData {
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  phone_number: string;
  role: UserRole;
  lga: number | null;
  password: string;
  is_active: boolean;
}

const BLANK_USER_FORM: UserFormData = {
  username: '',
  email: '',
  first_name: '',
  last_name: '',
  phone_number: '',
  role: 'OFFICER',
  lga: null,
  password: '',
  is_active: true,
};

@Component({
  imports: [CommonModule, FormsModule, RouterLink],
  selector: 'app-users',
  templateUrl: './users.html',
})
export class Users implements OnInit {
  protected readonly api = inject(ApiService);
  protected readonly auth = inject(AuthService);

  protected readonly users = signal<User[]>([]);
  protected readonly lgas = signal<LGA[]>([]);
  protected readonly loading = signal(false);
  protected readonly saving = signal(false);

  // Filters
  protected readonly searchQuery = signal('');
  protected readonly roleFilter = signal<string>('');
  protected readonly lgaFilter = signal<string>('');
  protected readonly statusFilter = signal<string>('');

  // Messages
  protected readonly successMessage = signal('');
  protected readonly errorMessage = signal('');
  protected readonly actionInProgressId = signal<number | null>(null);

  // Create Modal
  protected readonly showCreateModal = signal(false);
  protected readonly createForm = signal<UserFormData>({ ...BLANK_USER_FORM });

  // Edit Modal
  protected readonly editingUser = signal<User | null>(null);
  protected readonly editForm = signal<Partial<UserFormData>>({});

  // Reset Password Modal
  protected readonly resetUser = signal<User | null>(null);
  protected readonly newPassword = signal('');

  protected readonly ROLE_LABELS = ROLE_LABELS;
  protected readonly ALL_ROLES: UserRole[] = ['OFFICER', 'INSPECTOR', 'APPROVER', 'ADMIN', 'APPLICANT'];

  ngOnInit(): void {
    this.loadLgas();
    this.loadUsers();
  }

  loadLgas(): void {
    this.api.lgas().subscribe({
      next: (page) => this.lgas.set(page.results),
      error: () => {},
    });
  }

  loadUsers(): void {
    this.loading.set(true);
    const params: {
      role?: string;
      lga?: number | string;
      search?: string;
      is_active?: boolean;
    } = {};

    if (this.roleFilter()) params.role = this.roleFilter();
    if (this.lgaFilter()) params.lga = this.lgaFilter();
    if (this.searchQuery().trim()) params.search = this.searchQuery().trim();
    if (this.statusFilter() === 'active') params.is_active = true;
    if (this.statusFilter() === 'inactive') params.is_active = false;

    this.api.users(params).subscribe({
      next: (page) => {
        this.users.set(page.results);
        this.loading.set(false);
      },
      error: (err) => {
        this.errorMessage.set(err?.error?.detail ?? 'Failed to load user directory.');
        this.loading.set(false);
      },
    });
  }

  onFilterChange(): void {
    this.loadUsers();
  }

  // ── Create User ──────────────────────────────────────────────────────────

  openCreateModal(): void {
    this.createForm.set({ ...BLANK_USER_FORM });
    this.clearMessages();
    this.showCreateModal.set(true);
  }

  closeCreateModal(): void {
    this.showCreateModal.set(false);
    this.createForm.set({ ...BLANK_USER_FORM });
  }

  submitCreate(): void {
    const form = this.createForm();
    if (!form.username.trim()) {
      this.errorMessage.set('Username is required.');
      return;
    }
    if (!form.password || form.password.length < 8) {
      this.errorMessage.set('Password is required and must be at least 8 characters.');
      return;
    }
    if (['OFFICER', 'INSPECTOR', 'APPROVER'].includes(form.role) && !form.lga) {
      this.errorMessage.set('Council / LGA is required for LGA staff roles.');
      return;
    }

    this.saving.set(true);
    this.clearMessages();

    const payload: CreateUserData = {
      username: form.username.trim(),
      email: form.email.trim(),
      first_name: form.first_name.trim(),
      last_name: form.last_name.trim(),
      phone_number: form.phone_number.trim(),
      role: form.role,
      lga: form.lga,
      password: form.password,
      is_active: form.is_active,
    };

    this.api.createUser(payload).subscribe({
      next: (newUser) => {
        this.saving.set(false);
        this.closeCreateModal();
        this.successMessage.set(`User ${newUser.username} (${ROLE_LABELS[newUser.role]}) created successfully.`);
        this.loadUsers();
      },
      error: (err) => {
        this.saving.set(false);
        const detail = err?.error?.detail ?? (err?.error ? Object.values(err.error).flat().join(' ') : null);
        this.errorMessage.set(detail ?? 'Failed to create user.');
      },
    });
  }

  // ── Edit User ────────────────────────────────────────────────────────────

  openEditModal(user: User): void {
    this.editingUser.set(user);
    this.editForm.set({
      first_name: user.first_name || '',
      last_name: user.last_name || '',
      email: user.email || '',
      phone_number: user.phone_number || '',
      role: user.role,
      lga: user.lga,
      is_active: user.is_active !== false,
    });
    this.clearMessages();
  }

  closeEditModal(): void {
    this.editingUser.set(null);
    this.editForm.set({});
  }

  submitEdit(): void {
    const user = this.editingUser();
    if (!user) return;
    const form = this.editForm();

    if (['OFFICER', 'INSPECTOR', 'APPROVER'].includes(form.role ?? user.role) && !form.lga) {
      this.errorMessage.set('Council / LGA is required for LGA staff roles.');
      return;
    }

    this.saving.set(true);
    this.clearMessages();

    this.api.updateUser(user.id, form).subscribe({
      next: (updated) => {
        this.saving.set(false);
        this.closeEditModal();
        this.successMessage.set(`User ${updated.username} updated successfully.`);
        this.loadUsers();
      },
      error: (err) => {
        this.saving.set(false);
        const detail = err?.error?.detail ?? (err?.error ? Object.values(err.error).flat().join(' ') : null);
        this.errorMessage.set(detail ?? 'Failed to update user.');
      },
    });
  }

  // ── Reset Password ───────────────────────────────────────────────────────

  openResetModal(user: User): void {
    this.resetUser.set(user);
    this.newPassword.set('');
    this.clearMessages();
  }

  closeResetModal(): void {
    this.resetUser.set(null);
    this.newPassword.set('');
  }

  submitResetPassword(): void {
    const user = this.resetUser();
    const pw = this.newPassword().trim();
    if (!user) return;
    if (!pw || pw.length < 8) {
      this.errorMessage.set('New password must be at least 8 characters.');
      return;
    }

    this.saving.set(true);
    this.clearMessages();

    this.api.resetUserPassword(user.id, pw).subscribe({
      next: (res) => {
        this.saving.set(false);
        this.closeResetModal();
        this.successMessage.set(res.detail ?? `Password updated for ${user.username}.`);
      },
      error: (err) => {
        this.saving.set(false);
        const detail = err?.error?.detail ?? (err?.error ? Object.values(err.error).flat().join(' ') : null);
        this.errorMessage.set(detail ?? 'Failed to reset password.');
      },
    });
  }

  // ── Toggle Active ────────────────────────────────────────────────────────

  toggleActive(user: User): void {
    if (this.actionInProgressId()) return;
    this.actionInProgressId.set(user.id);
    this.clearMessages();

    this.api.toggleUserActive(user.id).subscribe({
      next: (res) => {
        this.actionInProgressId.set(null);
        this.successMessage.set(res.detail);
        this.loadUsers();
      },
      error: (err) => {
        this.actionInProgressId.set(null);
        this.errorMessage.set(err?.error?.detail ?? 'Failed to toggle user status.');
      },
    });
  }

  // ── Delete User ──────────────────────────────────────────────────────────

  deleteUser(user: User): void {
    if (!confirm(`Are you sure you want to delete or deactivate user "${user.username}"?`)) {
      return;
    }

    if (this.actionInProgressId()) return;
    this.actionInProgressId.set(user.id);
    this.clearMessages();

    this.api.deleteUser(user.id).subscribe({
      next: (res) => {
        this.actionInProgressId.set(null);
        const msg = res?.detail ?? `User ${user.username} was deleted.`;
        this.successMessage.set(msg);
        this.loadUsers();
      },
      error: (err) => {
        this.actionInProgressId.set(null);
        this.errorMessage.set(err?.error?.detail ?? 'Failed to delete user.');
      },
    });
  }

  // ── Utilities ────────────────────────────────────────────────────────────

  protected clearMessages(): void {
    this.successMessage.set('');
    this.errorMessage.set('');
  }

  protected getRoleBadgeClass(role: UserRole): string {
    switch (role) {
      case 'ADMIN':
        return 'bg-purple-100 text-purple-800 border-purple-300 dark:bg-purple-950 dark:text-purple-300 dark:border-purple-800';
      case 'OFFICER':
        return 'bg-blue-100 text-blue-800 border-blue-300 dark:bg-blue-950 dark:text-blue-300 dark:border-blue-800';
      case 'INSPECTOR':
        return 'bg-amber-100 text-amber-800 border-amber-300 dark:bg-amber-950 dark:text-amber-300 dark:border-amber-800';
      case 'APPROVER':
        return 'bg-primary/20 text-success-deep border-primary/50';
      case 'APPLICANT':
        return 'bg-soft text-foreground border-hairline';
      default:
        return 'bg-soft text-muted border-hairline';
    }
  }
}
