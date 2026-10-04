import { HttpClient } from '@angular/common/http';
import { Injectable, computed, inject, signal } from '@angular/core';
import { Observable, tap } from 'rxjs';

import { API_BASE_URL } from './api.config';

export type UserRole = 'APPLICANT' | 'OFFICER' | 'INSPECTOR' | 'APPROVER' | 'ADMIN';

export interface User {
  id: number;
  username: string;
  first_name: string;
  last_name: string;
  email: string;
  role: UserRole;
  phone_number: string;
  nida_number: string;
  has_nida: boolean;
  lga: number | null;
  lga_name: string | null;
  is_lga_staff: boolean;
  is_active?: boolean;
  date_joined?: string;
}

export interface CreateUserData {
  username: string;
  email?: string;
  first_name?: string;
  last_name?: string;
  phone_number?: string;
  nida_number?: string;
  role: UserRole;
  lga?: number | null;
  password?: string;
  is_active?: boolean;
}

/** Home route for each role — staff land on their own workspace. */
export const ROLE_HOME: Record<UserRole, string> = {
  APPLICANT: '/dashboard',
  OFFICER: '/staff/review',
  INSPECTOR: '/staff/inspections',
  APPROVER: '/staff/approvals',
  ADMIN: '/staff/admin',
};

export const ROLE_LABELS: Record<UserRole, string> = {
  APPLICANT: 'Applicant',
  OFFICER: 'Licensing Officer',
  INSPECTOR: 'Inspector',
  APPROVER: 'Approver',
  ADMIN: 'System Admin',
};

export interface AuthResponse {
  access: string;
  refresh: string;
  user: User;
}

const TOKEN_KEY = 'leseni.access';
const REFRESH_KEY = 'leseni.refresh';
const USER_KEY = 'leseni.user';

@Injectable({ providedIn: 'root' })
export class AuthService {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = API_BASE_URL;

  private readonly currentUserSignal = signal<User | null>(this.readStoredUser());

  /** Reactive current user (null when logged out). */
  readonly currentUser = this.currentUserSignal.asReadonly();
  readonly isLoggedIn = computed(() => this.currentUserSignal() !== null);
  readonly isStaff = computed(() => this.currentUserSignal()?.is_lga_staff ?? false);
  /** Reactive role of the current user (null when logged out). */
  readonly role = computed<UserRole | null>(() => this.currentUserSignal()?.role ?? null);

  /** Route this user should land on after login. */
  homeRoute(): string {
    const role = this.role();
    return role ? ROLE_HOME[role] : '/dashboard';
  }

  hasRole(...roles: UserRole[]): boolean {
    const role = this.role();
    return role !== null && roles.includes(role);
  }

  register(data: {
    username: string;
    email: string;
    first_name: string;
    last_name: string;
    phone_number: string;
    password: string;
  }): Observable<User> {
    return this.http.post<User>(`${this.baseUrl}/auth/register/`, data);
  }

  login(username: string, password: string): Observable<AuthResponse> {
    return this.http
      .post<AuthResponse>(`${this.baseUrl}/auth/login/`, { username, password })
      .pipe(tap((res) => this.storeSession(res)));
  }

  passwordResetRequest(username: string, phone_number: string): Observable<{ token: string; detail: string }> {
    return this.http.post<{ token: string; detail: string }>(
      `${this.baseUrl}/auth/password-reset/`,
      { username, phone_number },
    );
  }

  passwordResetConfirm(token: string, new_password: string): Observable<{ detail: string }> {
    return this.http.post<{ detail: string }>(
      `${this.baseUrl}/auth/password-reset/confirm/`,
      { token, new_password },
    );
  }

  /** POST /auth/refresh/ — the backend rotates tokens, so a new refresh may come back. */
  refresh(): Observable<{ access: string; refresh?: string }> {
    return this.http.post<{ access: string; refresh?: string }>(
      `${this.baseUrl}/auth/refresh/`,
      { refresh: this.refreshToken ?? '' },
    );
  }

  me(): Observable<User> {
    return this.http.get<User>(`${this.baseUrl}/auth/me/`);
  }

  logout(): void {
    sessionStorage.removeItem(TOKEN_KEY);
    sessionStorage.removeItem(REFRESH_KEY);
    sessionStorage.removeItem(USER_KEY);
    this.currentUserSignal.set(null);
  }

  get accessToken(): string | null {
    try {
      return sessionStorage.getItem(TOKEN_KEY);
    } catch {
      return null; // server-side render: no storage
    }
  }

  get refreshToken(): string | null {
    try {
      return sessionStorage.getItem(REFRESH_KEY);
    } catch {
      return null; // server-side render: no storage
    }
  }

  /** Persist rotated tokens from a silent refresh (access always, refresh when rotated). */
  setTokens(access: string, refresh?: string): void {
    try {
      sessionStorage.setItem(TOKEN_KEY, access);
      if (refresh) sessionStorage.setItem(REFRESH_KEY, refresh);
    } catch {
      // server-side render: no storage
    }
  }

  private storeSession(res: AuthResponse): void {
    sessionStorage.setItem(TOKEN_KEY, res.access);
    sessionStorage.setItem(REFRESH_KEY, res.refresh);
    sessionStorage.setItem(USER_KEY, JSON.stringify(res.user));
    this.currentUserSignal.set(res.user);
  }

  updateUserSession(user: Partial<User>): void {
    const current = this.currentUserSignal();
    const merged = current ? ({ ...current, ...user } as User) : (user as User);
    sessionStorage.setItem(USER_KEY, JSON.stringify(merged));
    this.currentUserSignal.set(merged);
  }

  private readStoredUser(): User | null {
    try {
      const raw = sessionStorage.getItem(USER_KEY);
      return raw ? (JSON.parse(raw) as User) : null;
    } catch {
      return null;
    }
  }
}
