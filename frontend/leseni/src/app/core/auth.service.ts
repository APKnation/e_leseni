import { HttpClient } from '@angular/common/http';
import { Injectable, computed, inject, signal } from '@angular/core';
import { Observable, tap } from 'rxjs';

import { API_BASE_URL } from './api.config';

export interface User {
  id: number;
  username: string;
  first_name: string;
  last_name: string;
  email: string;
  role: 'APPLICANT' | 'OFFICER' | 'INSPECTOR' | 'APPROVER' | 'ADMIN';
  phone_number: string;
  lga: number | null;
  lga_name: string | null;
  is_lga_staff: boolean;
}

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

  refresh(): Observable<{ access: string }> {
    const refresh = sessionStorage.getItem(REFRESH_KEY) ?? '';
    return this.http.post<{ access: string }>(`${this.baseUrl}/auth/refresh/`, { refresh });
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
    return sessionStorage.getItem(TOKEN_KEY);
  }

  private storeSession(res: AuthResponse): void {
    sessionStorage.setItem(TOKEN_KEY, res.access);
    sessionStorage.setItem(REFRESH_KEY, res.refresh);
    sessionStorage.setItem(USER_KEY, JSON.stringify(res.user));
    this.currentUserSignal.set(res.user);
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
