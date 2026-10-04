import { Component, computed, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';

import { ApiService } from '../../core/api.service';
import { AuthService } from '../../core/auth.service';

/** One line of the phone-screen transcript. */
interface LogEntry {
  from: 'you' | 'ussd' | 'system';
  text: string;
}

/** One gateway round-trip, shown in the protocol log. */
interface GatewayLogEntry {
  at: string;
  sessionId: string;
  phone: string;
  text: string;
  prefix: 'CON' | 'END' | 'ERROR';
  body: string;
  ms: number;
}

/**
 * USSD demo — because a real telco gateway (Africa's Talking etc.) costs
 * money, this page replays exactly what the phone would do: dial a service
 * code, then POST every menu reply to the same /ussd/gateway/ endpoint a
 * live gateway would call. The backend is the real USSD engine (CON/END).
 */
@Component({
  imports: [CommonModule, FormsModule, RouterLink, ProfileLink],
  selector: 'app-ussd-demo',
  templateUrl: './ussd-demo.html',
})
export class UssdDemo {
  private readonly api = inject(ApiService);
  protected readonly auth = inject(AuthService);

  /** The demo service code advertised in the user guide. */
  protected static readonly SERVICE_CODE = '*152*00#';

  protected readonly dial = signal(UssdDemo.SERVICE_CODE);
  protected readonly phone = signal(this.auth.currentUser()?.phone_number || '0712000111');

  protected readonly busy = signal(false);
  protected readonly errorMessage = signal('');

  /** Current USSD screen text (CON) — null while no session is open. */
  protected readonly screen = signal<string | null>(null);
  protected readonly sessionEnded = signal(false);
  protected readonly transcript = signal<LogEntry[]>([]);
  protected readonly reply = signal('');
  protected readonly sessionId = signal('');

  /** Raw gateway request/response pairs for the protocol log. */
  protected readonly gatewayLog = signal<GatewayLogEntry[]>([]);

  private accumulatedText = '';

  /** Dial the service code: starts a fresh USSD session at the main menu. */
  protected dialNow(): void {
    if (this.busy()) return;
    const code = this.dial().trim();
    if (!/^\*[\d*]+#$/.test(code)) {
      this.errorMessage.set('Enter a service code like *152*00# (starts with *, ends with #).');
      return;
    }
    if (!/^0?\d{9,12}$/.test(this.phone().replace(/\s/g, ''))) {
      this.errorMessage.set('Enter a phone number, e.g. 0712000111.');
      return;
    }
    this.errorMessage.set('');
    this.sessionId.set(`ATUid_${Date.now()}_${Math.floor(Math.random() * 10_000)}`);
    this.accumulatedText = '';
    this.transcript.set([
      { from: 'system', text: `Dialing ${code} from ${this.phone()}…` },
    ]);
    this.gatewayLog.set([]);
    this.sessionEnded.set(false);
    this.reply.set('');
    void this.gatewayCall(''); // first gateway call: empty text = main menu
  }

  /** Send one menu reply — the gateway appends it with * separators. */
  protected sendReply(): void {
    if (this.busy() || this.sessionEnded()) return;
    const value = this.reply().trim();
    if (!value) return;
    this.reply.set('');
    this.accumulatedText = this.accumulatedText
      ? `${this.accumulatedText}*${value}`
      : value;
    void this.gatewayCall(this.accumulatedText);
  }

  /** Drop the session (like the phone closing the dialogue). */
  protected endSession(): void {
    this.sessionEnded.set(true);
    this.screen.set(null);
    this.transcript.update((log) => [...log, { from: 'system', text: 'Session closed.' }]);
  }

  private gatewayCall(text: string): void {
    this.busy.set(true);
    const startedAt = Date.now();
    this.api.ussdGateway(this.sessionId(), this.phone(), text).subscribe({
      next: (raw) => {
        this.busy.set(false);
        const isEnd = raw.startsWith('END');
        const body = raw.replace(/^(CON|END)\s*/, '').trim();
        this.logRequest({
          at: new Date().toLocaleTimeString(),
          sessionId: this.sessionId(),
          phone: this.phone(),
          text,
          prefix: isEnd ? 'END' : 'CON',
          body,
          ms: Date.now() - startedAt,
        });
        if (text === '') {
          this.transcript.update((log) => [...log, { from: 'you', text: this.dial().trim() }]);
        } else {
          const last = text.split('*').at(-1) ?? '';
          this.transcript.update((log) => [...log, { from: 'you', text: last }]);
        }
        this.transcript.update((log) => [...log, { from: 'ussd', text: body }]);
        this.screen.set(body);
        if (isEnd) {
          this.sessionEnded.set(true);
          this.transcript.update((log) => [
            ...log,
            { from: 'system', text: '— session ended —' },
          ]);
        }
      },
      error: () => {
        this.busy.set(false);
        this.logRequest({
          at: new Date().toLocaleTimeString(),
          sessionId: this.sessionId(),
          phone: this.phone(),
          text,
          prefix: 'ERROR',
          body: 'Could not reach /ussd/gateway/ — is the backend running?',
          ms: Date.now() - startedAt,
        });
        this.errorMessage.set('Could not reach the USSD gateway. Is the backend running?');
      },
    });
  }

  private logRequest(entry: GatewayLogEntry): void {
    this.gatewayLog.update((log) => [...log, entry].slice(-50));
  }

  protected readonly serviceCode = UssdDemo.SERVICE_CODE;

  // -- Clickable keypad -------------------------------------------------------

  /** Classic 3x4 feature-phone layout. */
  protected readonly keys = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '*', '0', '#'];

  /** With a session open the keypad types the reply; otherwise it dials. */
  protected readonly keypadEditsDial = computed(() => !this.screen() || this.sessionEnded());

  protected pressKey(key: string): void {
    if (this.busy()) return;
    if (this.keypadEditsDial()) {
      this.dial.update((v) => v + key);
    } else {
      this.reply.update((v) => v + key);
    }
  }

  protected backspace(): void {
    if (this.busy()) return;
    if (this.keypadEditsDial()) {
      this.dial.update((v) => v.slice(0, -1));
    } else {
      this.reply.update((v) => v.slice(0, -1));
    }
  }
}
