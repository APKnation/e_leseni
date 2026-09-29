import { Component, DestroyRef, inject, signal } from '@angular/core';
import { takeUntilDestroyed, toSignal } from '@angular/core/rxjs-interop';
import { NavigationEnd, Router, RouterLink, RouterLinkActive, RouterOutlet } from '@angular/router';
import { filter, map, startWith } from 'rxjs';

import { ApplicationStatusEvent, RealtimeService } from './core/realtime.service';
import { AuthService, ROLE_LABELS } from './core/auth.service';

@Component({
  imports: [RouterOutlet, RouterLink, RouterLinkActive],
  selector: 'app-root',
  styleUrl: './app.css',
  templateUrl: './app.html',
})
export class App {
  protected readonly auth = inject(AuthService);
  protected readonly realtime = inject(RealtimeService);
  protected readonly roleLabel = ROLE_LABELS;
  protected readonly year = new Date().getFullYear();
  private readonly router = inject(Router);

  /** The marketing footer is hidden on the auth pages (login / register). */
  protected readonly hideFooter = toSignal(
    this.router.events.pipe(
      filter((e): e is NavigationEnd => e instanceof NavigationEnd),
      startWith(null),
      map(() => this.router.url.startsWith('/login') || this.router.url.startsWith('/register')),
    ),
    { initialValue: this.router.url.startsWith('/login') || this.router.url.startsWith('/register') },
  );

  /** Mobile navigation drawer state. */
  protected readonly menuOpen = signal(false);

  /** Transient toast showing a live status update as it arrives. */
  protected readonly toast = signal<ApplicationStatusEvent | null>(null);
  private toastTimer: ReturnType<typeof setTimeout> | null = null;

  private readonly destroyRef = inject(DestroyRef);

  constructor() {
    // Live toast: every status change pops a small notification (3 s).
    this.realtime.events$
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe((event) => {
        if (event.type !== 'application.status' || event.payload.snapshot) return;
        this.toast.set(event.payload);
        if (this.toastTimer) clearTimeout(this.toastTimer);
        this.toastTimer = setTimeout(() => this.toast.set(null), 4000);
      });
    this.destroyRef.onDestroy(() => this.realtime.disconnect());
  }

  protected dismissToast(): void {
    if (this.toastTimer) clearTimeout(this.toastTimer);
    this.toast.set(null);
  }

  protected goToApplication(): void {
    this.dismissToast();
    void this.router.navigate(['/dashboard']);
  }

  protected toggleMenu(): void {
    this.menuOpen.update((open) => !open);
  }

  protected closeMenu(): void {
    this.menuOpen.set(false);
  }

  protected logout(): void {
    this.auth.logout();
    this.closeMenu();
    void this.router.navigate(['/']);
  }
}
