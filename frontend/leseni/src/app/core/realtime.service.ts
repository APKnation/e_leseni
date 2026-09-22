import { HttpClient } from '@angular/common/http';
import { Injectable, NgZone, effect, inject, signal } from '@angular/core';
import { Observable, Subject } from 'rxjs';

import { API_BASE_URL } from './api.config';
import { AuthService } from './auth.service';

/** Payload of an application.status SSE event. */
export interface ApplicationStatusEvent {
  application_id: number;
  reference_number: string;
  business_name: string;
  licence_type_name: string;
  from_status: string | null;
  to_status: string;
  to_status_label: string;
  changed_by: string;
  at: string;
  snapshot?: boolean;
}

/** Payload of an inspection.update SSE event. */
export interface InspectionEvent {
  application_id: number;
  reference_number: string;
  inspection_id: number;
  action: 'scheduled' | 'conducted' | 'updated';
  scheduled_for: string;
  passed: boolean | null;
  at: string;
}

export type RealtimeEvent =
  | { type: 'application.status'; payload: ApplicationStatusEvent }
  | { type: 'inspection.update'; payload: InspectionEvent };

/**
 * Server-Sent Events connection for live application progress.
 *
 * - Connects when the user logs in, closes on logout.
 * - Auto-reconnects with backoff; the backend replays a snapshot on connect.
 * - Exposes `live()` for a connection indicator and `events$` for consumers.
 */
@Injectable({ providedIn: 'root' })
export class RealtimeService {
  private readonly auth = inject(AuthService);
  private readonly zone = inject(NgZone);
  private readonly http = inject(HttpClient);

  private readonly eventSubject = new Subject<RealtimeEvent>();
  /** All realtime events, in order. */
  readonly events$ = this.eventSubject.asObservable();

  private readonly liveSignal = signal(false);
  /** True while the SSE connection is open. */
  readonly live = this.liveSignal.asReadonly();

  private source: EventSource | null = null;
  private retryTimer: ReturnType<typeof setTimeout> | null = null;
  private retryAttempt = 0;

  constructor() {
    // Open/close the stream with the session (computed -> effect bridge).
    effect(() => {
      if (this.auth.isLoggedIn()) {
        this.connect();
      } else {
        this.disconnect();
      }
    });
  }

  /** Manually (re)connect — also used after a token refresh. */
  connect(): void {
    if (!this.auth.isLoggedIn()) return;

    const token = this.auth.accessToken;
    if (!token) return;

    this.disconnect();

    this.zone.runOutsideAngular(() => {
      const source = new EventSource(`${API_BASE_URL}/events/?token=${encodeURIComponent(token)}`);
      this.source = source;

      source.onopen = () => {
        this.retryAttempt = 0;
        this.zone.run(() => this.liveSignal.set(true));
      };

      source.addEventListener('application.status', (e) => this.dispatch('application.status', e));
      source.addEventListener('inspection.update', (e) => this.dispatch('inspection.update', e));

      source.onerror = () => {
        // EventSource retries on its own, but the token may have expired —
        // close and reconnect with the fresh token after a backoff.
        source.close();
        this.source = null;
        this.zone.run(() => this.liveSignal.set(false));
        if (!this.auth.isLoggedIn()) return;
        const delay = Math.min(1000 * 2 ** this.retryAttempt++, 15000);
        this.retryTimer = setTimeout(() => this.connect(), delay);
      };
    });
  }

  disconnect(): void {
    if (this.retryTimer) {
      clearTimeout(this.retryTimer);
      this.retryTimer = null;
    }
    if (this.source) {
      this.source.close();
      this.source = null;
    }
    this.liveSignal.set(false);
  }

  private dispatch(type: 'application.status' | 'inspection.update', event: MessageEvent): void {
    try {
      const payload = JSON.parse((event as MessageEvent<string>).data);
      this.zone.run(() => this.eventSubject.next({ type, payload }));
    } catch {
      // ignore malformed frames
    }
  }

  /** Refresh the JWT-bound stream (call after refreshing the access token). */
  refreshToken(): void {
    if (this.auth.isLoggedIn()) this.connect();
  }
}
