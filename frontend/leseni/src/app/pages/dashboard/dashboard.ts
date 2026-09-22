import { Component, DestroyRef, inject, signal } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { RouterLink } from '@angular/router';

import { ApiService } from '../../core/api.service';
import { AuthService, ROLE_LABELS } from '../../core/auth.service';
import { RealtimeService } from '../../core/realtime.service';
import {
  Application,
  ApplicationStatus,
  Business,
  Invoice,
  Licence,
  STATUS_LABELS,
  STATUS_STYLES,
  StatusHistoryEntry,
} from '../../core/models';

/** One row of the visible timeline: a main-line step or a system event. */
interface TimelineStep {
  status: ApplicationStatus;
  label: string;
  icon: string;
  /** 'done' | 'current' | 'upcoming' for main-line steps; 'event' for extras. */
  state: 'done' | 'current' | 'upcoming' | 'event';
  when: string | null;
  actor: string;
  note: string;
}

@Component({
  imports: [RouterLink],
  selector: 'app-dashboard',
  templateUrl: './dashboard.html',
})
export class Dashboard {
  private readonly api = inject(ApiService);
  private readonly realtime = inject(RealtimeService);
  protected readonly auth = inject(AuthService);

  protected readonly STATUS_LABELS = STATUS_LABELS;
  protected readonly STATUS_STYLES = STATUS_STYLES;

  protected readonly loading = signal(true);
  protected readonly errorMessage = signal('');

  protected readonly applications = signal<Application[]>([]);
  protected readonly licences = signal<Licence[]>([]);
  protected readonly invoices = signal<Invoice[]>([]);
  protected readonly businesses = signal<Business[]>([]);

  protected readonly payingInvoiceId = signal<number | null>(null);

  /** Per-application visibility of the expanded status timeline. */
  protected readonly expandedTimeline = signal<number | null>(null);

  protected toggleTimeline(appId: number): void {
    this.expandedTimeline.update((current) => (current === appId ? null : appId));
  }

  /** The main-line journey every application walks through. */
  private static readonly MAIN_LINE: { status: ApplicationStatus; label: string; icon: string }[] = [
    { status: 'DRAFT', label: 'Draft', icon: '📝' },
    { status: 'SUBMITTED', label: 'Submitted', icon: '📤' },
    { status: 'UNDER_REVIEW', label: 'Under review', icon: '👀' },
    { status: 'INSPECTED', label: 'Inspected', icon: '🔍' },
    { status: 'APPROVED', label: 'Approved', icon: '✅' },
    { status: 'PAID', label: 'Paid', icon: '💳' },
    { status: 'ISSUED', label: 'Issued', icon: '🎫' },
  ];

  /**
   * Build the visible timeline for an application: the main-line steps with
   * done/current/upcoming states, plus branch events (returned, rejected,
   * invoiced, scheduled) interleaved as extra rows with their timestamps.
   */
  protected timelineFor(app: Application): TimelineStep[] {
    const history = app.history ?? [];
    const whenOf = (status: ApplicationStatus): StatusHistoryEntry | undefined =>
      history.find((h) => h.to_status === status);

    const fmt = (iso: string | null): string =>
      iso ? new Date(iso).toLocaleString(undefined, { dateStyle: 'medium', timeStyle: 'short' }) : '';

    // Current position on the main line; terminal side-branches get special care.
    const currentIdx = Dashboard.MAIN_LINE.findIndex((s) => s.status === app.status);
    const reached = (status: ApplicationStatus): boolean =>
      history.some((h) => h.to_status === status) ||
      currentIdx >= Dashboard.MAIN_LINE.findIndex((s) => s.status === status);

    const steps: TimelineStep[] = Dashboard.MAIN_LINE.map((step, index) => {
      const entry = whenOf(step.status);
      const state: TimelineStep['state'] =
        app.status === step.status
          ? 'current'
          : reached(step.status) && index < (currentIdx === -1 ? Dashboard.MAIN_LINE.length : currentIdx)
            ? 'done'
            : 'upcoming';
      return {
        ...step,
        state,
        when: entry ? fmt(entry.changed_at) : null,
        actor: entry?.changed_by_name ?? '',
        note: entry?.note ?? '',
      };
    });

    // Interleave non-main-line events (returned, rejected, invoiced…) as event rows.
    const mainStatuses = new Set(Dashboard.MAIN_LINE.map((s) => s.status));
    const extraEvents: TimelineStep[] = history
      .filter((h) => mainStatuses.has(h.to_status) === false)
      .map((h) => ({
        status: h.to_status,
        label: STATUS_LABELS[h.to_status] ?? h.to_status,
        icon: h.to_status === 'REJECTED' ? '⛔' : h.to_status === 'RETURNED_FOR_CORRECTION' ? '↩️' : '🔔',
        state: 'event' as const,
        when: fmt(h.changed_at),
        actor: h.changed_by_name,
        note: h.note,
      }));

    // Merge: keep chronological order by timestamp where events have one.
    const merged = [...steps];
    for (const event of extraEvents) {
      const afterIndex = merged.findIndex(
        (s) => s.when && event.when && new Date(s.when) > new Date(event.when),
      );
      if (afterIndex === -1) {
        merged.push(event);
      } else {
        merged.splice(afterIndex, 0, event);
      }
    }
    return merged;
  }

  protected timelineNoteFor(app: Application): string {
    if (app.status === 'RETURNED_FOR_CORRECTION' && app.rejection_reason) return app.rejection_reason;
    const last = (app.history ?? []).at(-1);
    return last?.note ?? '';
  }

  constructor() {
    this.loadAll();

    // Live progress: refetch whenever a status/inspection event arrives.
    // Snapshot events (on connect) also reconcile anything missed while away.
    this.realtime.events$
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe(() => this.loadAll());
  }

  private readonly destroyRef = inject(DestroyRef);

  protected loadAll(): void {
    this.loading.set(true);
    this.errorMessage.set('');

    let pending = 4;
    const done = () => {
      if (--pending === 0) this.loading.set(false);
    };

    this.api.applications().subscribe({
      next: (page) => {
        this.applications.set(page.results);
        done();
      },
      error: () => {
        this.errorMessage.set('Could not load your data. Is the backend running?');
        this.loading.set(false);
      },
    });

    this.api.businesses().subscribe({
      next: (page) => {
        this.businesses.set(page.results);
        done();
      },
      error: () => done(),
    });

    this.api.invoices().subscribe({
      next: (page) => {
        this.invoices.set(page.results);
        done();
      },
      error: () => done(),
    });

    this.api.licences().subscribe({
      next: (page) => {
        this.licences.set(page.results);
        done();
      },
      error: () => done(),
    });
  }

  /** Applicant onboarding checklist: BRELA -> TRA -> business -> licence. */
  protected get onboardingSteps(): { label: string; done: boolean; link: string | null; cta: string }[] {
    if (this.isStaff()) return [];
    const businesses = this.businesses();
    const verified = businesses.some((b) => b.is_verified);
    const hasBusiness = businesses.length > 0;
    const hasApplication = this.applications().length > 0;
    const hasLicence = this.licences().length > 0;
    return [
      {
        label: 'Register your business with BRELA',
        done: hasBusiness,
        link: '/businesses',
        cta: 'Start registration',
      },
      {
        label: 'Get your TIN from TRA',
        done: businesses.some((b) => !!b.tin_number),
        link: '/businesses',
        cta: 'Apply for TIN',
      },
      {
        label: 'Get verified (TRA + BRELA check)',
        done: verified,
        link: '/businesses',
        cta: 'Verify business',
      },
      {
        label: 'Apply for your first LGA licence',
        done: hasApplication,
        link: '/apply',
        cta: 'Apply now',
      },
      {
        label: 'Receive your licence',
        done: hasLicence,
        link: null,
        cta: '',
      },
    ];
  }

  protected get stats() {
    const active = this.applications().filter(
      (a) => !['ISSUED', 'REJECTED'].includes(a.status),
    ).length;
    const awaitingPayment = this.invoices().filter(
      (i) => i.status === 'WAITING_PAYMENT' || i.status === 'PENDING',
    ).length;
    const activeLicences = this.licences().filter(
      (l) => l.status === 'ACTIVE' && !l.is_expired,
    ).length;
    return [
      { label: 'Active applications', value: active, highlight: true },
      { label: 'Awaiting payment', value: awaitingPayment, highlight: false },
      { label: 'Active licences', value: activeLicences, highlight: false },
    ];
  }

  /** SIMULATED payment (mock GePG): pay the full amount from the dashboard. */
  protected payInvoice(invoice: Invoice): void {
    if (this.payingInvoiceId()) return;
    this.payingInvoiceId.set(invoice.id);

    this.api
      .payInvoice(invoice.id, {
        amount: invoice.amount,
        method: 'MOBILE_MONEY',
        payer_name: this.auth.currentUser()?.username ?? '',
        payer_phone: '0712000111',
        reference: 'WEB-DEMO',
      })
      .subscribe({
        next: () => this.loadAll(),
        error: () => this.payingInvoiceId.set(null),
      });
  }

  protected user = () => this.auth.currentUser();

  /** Staff see admin actions instead of the applicant CTA. */
  protected readonly isStaff = this.auth.isStaff;
  protected readonly roleLabel = ROLE_LABELS;
}
