import { Component, computed, inject, OnInit, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';

import { ApiService } from '../../core/api.service';
import { AuthService, ROLE_LABELS, UserRole } from '../../core/auth.service';
import { Application, ApplicationStatus, Inspection, STATUS_LABELS, STATUS_STYLES } from '../../core/models';

interface QueueFilter {
  label: string;
  statuses: ApplicationStatus[] | null;
}

/** Workspace config per staff role: which applications they see and why. */
interface RoleWorkspace {
  title: string;
  subtitle: string;
  badge: string;
  queueFilters: QueueFilter[];
}

const WORKSPACES: Record<UserRole, RoleWorkspace> = {
  // Applicants never reach this page (guarded), so reuse the admin view.
  APPLICANT: {
    title: 'Staff area',
    subtitle: 'Applications across the licensing flow.',
    badge: 'STAFF',
    queueFilters: [{ label: 'All', statuses: null }],
  },
  OFFICER: {
    title: 'Review queue',
    subtitle: 'Applications awaiting review in your LGA.',
    badge: 'LICENSING OFFICER',
    queueFilters: [
      { label: 'Needs review', statuses: ['SUBMITTED'] },
      { label: 'In progress', statuses: ['UNDER_REVIEW', 'INSPECTION_SCHEDULED'] },
      { label: 'All', statuses: null },
    ],
  },
  INSPECTOR: {
    title: 'Inspection queue',
    subtitle: 'Inspections to conduct in your LGA.',
    badge: 'INSPECTOR',
    queueFilters: [
      { label: 'To schedule', statuses: ['UNDER_REVIEW'] },
      { label: 'Scheduled', statuses: ['INSPECTION_SCHEDULED'] },
      { label: 'All', statuses: null },
    ],
  },
  APPROVER: {
    title: 'Approval queue',
    subtitle: 'Inspected applications awaiting your decision.',
    badge: 'APPROVER',
    queueFilters: [
      { label: 'Awaiting approval', statuses: ['INSPECTED'] },
      { label: 'Decided', statuses: ['APPROVED', 'REJECTED', 'PAYMENT_PENDING'] },
      { label: 'All', statuses: null },
    ],
  },
  ADMIN: {
    title: 'Administration',
    subtitle: 'Every application across all LGAs — full workflow control.',
    badge: 'SYSTEM ADMIN',
    queueFilters: [
      { label: 'Needs review', statuses: ['SUBMITTED'] },
      { label: 'Inspections', statuses: ['UNDER_REVIEW', 'INSPECTION_SCHEDULED'] },
      { label: 'Approvals', statuses: ['INSPECTED'] },
      { label: 'Payments', statuses: ['APPROVED', 'PAYMENT_PENDING'] },
      { label: 'All', statuses: null },
    ],
  },
};

@Component({
  imports: [FormsModule, RouterLink],
  selector: 'app-staff',
  templateUrl: './staff.html',
})
export class Staff implements OnInit {
  private readonly api = inject(ApiService);
  private readonly auth = inject(AuthService);

  protected readonly STATUS_LABELS = STATUS_LABELS;
  protected readonly STATUS_STYLES = STATUS_STYLES;

  protected readonly loading = signal(true);
  protected readonly errorMessage = signal('');
  protected readonly successMessage = signal('');
  protected readonly applications = signal<Application[]>([]);
  protected readonly inspections = signal<Inspection[]>([]);
  protected readonly processingId = signal<number | null>(null);

  /** Inspection scheduling form state (officers/inspectors). */
  protected readonly schedulingId = signal<number | null>(null);
  protected readonly scheduledFor = signal('');

  protected readonly role: UserRole = this.auth.role() ?? 'ADMIN';
  protected readonly workspace = WORKSPACES[this.role] ?? WORKSPACES.ADMIN;
  protected readonly roleLabel = ROLE_LABELS[this.role] ?? this.role;
  protected readonly isAdmin = this.role === 'ADMIN';
  protected readonly canReview = this.role === 'OFFICER' || this.isAdmin;
  protected readonly canInspect = this.role === 'INSPECTOR' || this.isAdmin;
  protected readonly canApprove = this.role === 'APPROVER' || this.isAdmin;

  protected readonly activeFilter = signal<QueueFilter>(this.workspace.queueFilters[0]);

  /** Latest open inspection per application id. */
  private readonly inspectionByApplication = computed(() => {
    const map = new Map<number, Inspection>();
    for (const inspection of this.inspections()) {
      if (!map.has(inspection.application)) {
        map.set(inspection.application, inspection);
      }
    }
    return map;
  });

  ngOnInit(): void {
    this.load();
  }

  protected load(): void {
    this.loading.set(true);
    this.errorMessage.set('');
    this.successMessage.set('');
    this.api.applications().subscribe({
      next: (page) => {
        this.applications.set(page.results);
        this.loading.set(false);
      },
      error: () => {
        this.errorMessage.set('Could not load the application queue.');
        this.loading.set(false);
      },
    });
    this.api.inspections().subscribe({
      next: (page) => this.inspections.set(page.results),
      error: () => this.inspections.set([]),
    });
  }

  protected get filteredApplications(): Application[] {
    const statuses = this.activeFilter().statuses;
    if (!statuses) return this.applications();
    return this.applications().filter((a) => statuses.includes(a.status));
  }

  protected countFor(filter: QueueFilter): number {
    if (!filter.statuses) return this.applications().length;
    return this.applications().filter((a) => filter.statuses!.includes(a.status)).length;
  }

  /** Advance an application along its allowed next statuses (staff action). */
  protected advance(app: Application, toStatus: string): void {
    if (this.processingId()) return;
    this.processingId.set(app.id);
    this.errorMessage.set('');
    this.successMessage.set('');
    this.api.transitionApplication(app.id, toStatus).subscribe({
      next: (updated) => {
        this.successMessage.set(
          `${updated.reference_number} → ${STATUS_LABELS[toStatus as ApplicationStatus] ?? toStatus}`,
        );
        this.load();
      },
      error: (err) => {
        const detail = err?.error?.detail ?? err?.error ? Object.values(err.error).flat()[0] : null;
        this.errorMessage.set(typeof detail === 'string' ? detail : 'Action not allowed.');
        this.processingId.set(null);
      },
    });
  }

  protected startReview(app: Application): void {
    this.advance(app, 'UNDER_REVIEW');
  }

  protected schedule(app: Application): void {
    this.schedulingId.set(app.id);
    this.scheduledFor.set(this.defaultScheduleDateTime());
  }

  protected cancelSchedule(): void {
    this.schedulingId.set(null);
  }

  protected confirmSchedule(app: Application): void {
    if (!this.scheduledFor()) return;
    this.processingId.set(app.id);
    this.api.scheduleInspection(app.id, new Date(this.scheduledFor()).toISOString()).subscribe({
      next: () => {
        this.advanceAfterSchedule(app);
        this.schedulingId.set(null);
      },
      error: (err) => {
        const detail = err?.error?.detail ?? 'Could not schedule the inspection.';
        this.errorMessage.set(typeof detail === 'string' ? detail : 'Could not schedule the inspection.');
        this.processingId.set(null);
        this.schedulingId.set(null);
      },
    });
  }

  private advanceAfterSchedule(app: Application): void {
    this.api.transitionApplication(app.id, 'INSPECTION_SCHEDULED').subscribe({
      next: (updated) => {
        this.successMessage.set(`Inspection scheduled for ${updated.reference_number}.`);
        this.load();
      },
      error: () => {
        this.errorMessage.set('Inspection saved, but the status could not be updated.');
        this.load();
      },
    });
  }

  private defaultScheduleDateTime(): string {
    const d = new Date();
    d.setDate(d.getDate() + 1);
    d.setHours(9, 0, 0, 0);
    // datetime-local input wants YYYY-MM-DDTHH:mm
    return d.toISOString().slice(0, 16);
  }

  protected scheduledDate(app: Application): string {
    const inspection = this.inspectionByApplication().get(app.id);
    if (!inspection) return '';
    return new Date(inspection.scheduled_for).toLocaleString();
  }

  protected inspectorName(app: Application): string {
    return this.inspectionByApplication().get(app.id)?.inspector_name ?? '';
  }
}
