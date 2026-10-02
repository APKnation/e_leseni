import { Component, DestroyRef, computed, inject, OnInit, signal } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { FormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';

import { ApiService } from '../../core/api.service';
import { AuthService, ROLE_LABELS, UserRole } from '../../core/auth.service';
import { RealtimeService } from '../../core/realtime.service';
import { Application, ApplicationStatus, BusinessActivity, Inspection, LGA, LicenceType, STATUS_LABELS, STATUS_STYLES } from '../../core/models';

interface QueueFilter {
  label: string;
  statuses: ApplicationStatus[] | null;
}

/** Editable form state for the business-activity manager (officers/admins). */
interface ActivityForm {
  code: string;
  name: string;
  description: string;
  icon: string;
  order: number;
  is_active: boolean;
}

const BLANK_ACTIVITY: ActivityForm = {
  code: '',
  name: '',
  description: '',
  icon: '',
  order: 0,
  is_active: true,
};

/** Editable form state for the council-catalogue licence editor. */
interface LicenceForm {
  name: string;
  code: string;
  category: 'BUSINESS' | 'DRIVING' | 'GENERAL';
  fee: string;
  validity_months: number;
  requires_inspection: boolean;
  description: string;
  bylaw_reference: string;
  activity_id: number | null;
}

const BLANK_LICENCE: LicenceForm = {
  name: '',
  code: '',
  category: 'BUSINESS',
  fee: '0',
  validity_months: 12,
  requires_inspection: true,
  description: '',
  bylaw_reference: '',
  activity_id: null,
};

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
  private readonly realtime = inject(RealtimeService);
  private readonly destroyRef = inject(DestroyRef);

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

  /** Inspection result form state (inspectors). */
  protected readonly recordingId = signal<number | null>(null);
  protected readonly resultFindings = signal('');

  /** Rejection form state — a reason is mandatory for every rejection. */
  protected readonly rejectingId = signal<number | null>(null);
  protected readonly rejectReason = signal('');
  /** Captured GPS per application id (nulled when capture fails). */
  protected readonly capturedLocation = signal<Map<number, { lat: number; lng: number; accuracy: number } | null>>(new Map());

  protected readonly role: UserRole = this.auth.role() ?? 'ADMIN';
  protected readonly workspace = WORKSPACES[this.role] ?? WORKSPACES.ADMIN;
  protected readonly roleLabel = ROLE_LABELS[this.role] ?? this.role;
  protected readonly isAdmin = this.role === 'ADMIN';
  protected readonly canReview = this.role === 'OFFICER' || this.isAdmin;
  protected readonly canInspect = this.role === 'INSPECTOR' || this.isAdmin;
  protected readonly canApprove = this.role === 'APPROVER' || this.isAdmin;
  /** Officers run the licensing taxonomy; admins oversee it. */
  protected readonly canManageActivities = this.role === 'OFFICER' || this.isAdmin;

  protected readonly activeFilter = signal<QueueFilter>(this.workspace.queueFilters[0]);

  /** Activity taxonomy — drives the queue filter and the manager panel. */
  protected readonly activities = signal<BusinessActivity[]>([]);
  /** Server-side activity filter for the queue (null = all activities). */
  protected readonly activeActivityId = signal<number | null>(null);

  /** Business-activity manager panel state (role-gated). */
  protected readonly showActivities = signal(false);
  protected readonly editingActivityId = signal<number | 'new' | null>(null);
  protected readonly savingActivity = signal(false);
  protected readonly activityForm = signal<ActivityForm>({ ...BLANK_ACTIVITY });

  /** Council-catalogue editor state (officers manage their own council only). */
  protected readonly showCatalog = signal(false);
  protected readonly officerLgaId = signal<number | null>(this.auth.currentUser()?.lga ?? null);
  protected readonly allLgas = signal<LGA[]>([]);
  protected readonly catalogue = signal<LicenceType[]>([]);
  protected readonly loadingCatalog = signal(false);
  protected readonly editingLicenceId = signal<number | 'new' | null>(null);
  protected readonly savingLicence = signal(false);
  protected readonly licenceForm = signal<LicenceForm>({ ...BLANK_LICENCE });
  protected readonly expandedRequirementsFor = signal<number | null>(null);
  protected readonly reqName = signal('');
  protected readonly reqKind = signal<'DOCUMENT' | 'INSPECTION' | 'CLEARANCE'>('DOCUMENT');
  protected readonly reqMandatory = signal(true);

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
    this.loadActivities();

    // Live queue: refresh when any application/inspection event arrives
    // (e.g. an applicant submits while the officer has the page open).
    this.realtime.events$
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe(() => this.load());
  }

  protected load(): void {
    this.loading.set(true);
    this.errorMessage.set('');
    this.successMessage.set('');
    this.api.applications(this.activityFilterParams()).subscribe({
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

  // -- Activity taxonomy: queue filter + management (officers/admins) ------

  /** Load the taxonomy; staff also see disabled activities. */
  private loadActivities(): void {
    this.api.businessActivities({ include_inactive: '1' }).subscribe({
      next: (list) => this.activities.set(list),
      error: () => this.activities.set([]),
    });
  }

  private activityFilterParams(): Record<string, number> {
    const activity = this.activeActivityId();
    return activity === null ? {} : { activity };
  }

  /** Queue filter select changed — refetch applications for the activity. */
  protected onActivityFilterChange(value: string): void {
    this.activeActivityId.set(value === '' ? null : Number(value));
    this.load();
  }

  protected toggleActivities(): void {
    this.showActivities.update((visible) => !visible);
    if (!this.showActivities()) this.cancelActivityEdit();
  }

  protected startNewActivity(): void {
    this.editingActivityId.set('new');
    this.activityForm.set({
      ...BLANK_ACTIVITY,
      order: Math.max(0, ...this.activities().map((activity) => activity.order ?? 0)) + 1,
    });
  }

  protected editActivity(activity: BusinessActivity): void {
    this.editingActivityId.set(activity.id);
    this.activityForm.set({
      code: activity.code,
      name: activity.name,
      description: activity.description ?? '',
      icon: activity.icon ?? '',
      order: activity.order ?? 0,
      is_active: activity.is_active !== false,
    });
  }

  protected cancelActivityEdit(): void {
    this.editingActivityId.set(null);
    this.activityForm.set({ ...BLANK_ACTIVITY });
  }

  protected updateActivityForm(patch: Partial<ActivityForm>): void {
    this.activityForm.update((form) => ({ ...form, ...patch }));
  }

  /** number inputs emit strings — coerce before storing. */
  protected setActivityOrder(value: string | number): void {
    const order = typeof value === 'number' ? value : Number(value);
    this.updateActivityForm({ order: Number.isFinite(order) ? order : 0 });
  }

  protected isActivityActive(activity: BusinessActivity): boolean {
    return activity.is_active !== false;
  }

  protected saveActivity(): void {
    const form = this.activityForm();
    const code = form.code.trim().toUpperCase();
    const name = form.name.trim();
    if (!code || !name) {
      this.errorMessage.set('An activity needs both a code and a name.');
      return;
    }
    if (this.savingActivity()) return;
    this.savingActivity.set(true);
    this.errorMessage.set('');

    const payload = {
      code,
      name,
      description: form.description.trim(),
      icon: form.icon.trim(),
      order: form.order,
      is_active: form.is_active,
    };
    const editingId = this.editingActivityId();
    const request$ =
      editingId === 'new'
        ? this.api.createBusinessActivity(payload)
        : this.api.updateBusinessActivity(editingId as number, payload);

    request$.subscribe({
      next: (activity) => {
        this.savingActivity.set(false);
        this.cancelActivityEdit();
        this.loadActivities();
        this.successMessage.set(`Activity “${activity.name}” saved.`);
      },
      error: (err) => {
        this.savingActivity.set(false);
        this.errorMessage.set(this.firstError(err, 'Could not save the activity.'));
      },
    });
  }

  protected deleteActivity(activity: BusinessActivity): void {
    if (
      !window.confirm(
        `Delete “${activity.name}”? Licence types linked to it stay, but lose their activity.`,
      )
    ) {
      return;
    }
    this.errorMessage.set('');
    this.api.deleteBusinessActivity(activity.id).subscribe({
      next: () => {
        // If the queue was filtered by the deleted activity, reset it.
        if (this.activeActivityId() === activity.id) {
          this.activeActivityId.set(null);
          this.load();
        }
        this.loadActivities();
        this.successMessage.set(`Activity “${activity.name}” deleted.`);
      },
      error: (err) => this.errorMessage.set(this.firstError(err, 'Could not delete the activity.')),
    });
  }

  private firstError(err: unknown, fallback: string): string {
    const error = (err as { error?: unknown } | null)?.error;
    if (typeof error === 'string') return error;
    if (error && typeof error === 'object') {
      const first = Object.values(error as Record<string, unknown>)
        .flat()
        .find((value) => typeof value === 'string');
      if (typeof first === 'string') return first;
    }
    return fallback;
  }

  // -- Council catalogue: per-LGA licence types, fees and requirements ------

  protected toggleCatalog(): void {
    this.showCatalog.update((visible) => !visible);
    if (this.showCatalog()) {
      if (this.allLgas().length === 0) {
        this.api.lgas().subscribe({
          next: (page) => this.allLgas.set(page.results),
          error: () => {},
        });
      }
      this.loadCatalog();
    } else {
      this.cancelLicenceEdit();
    }
  }

  /** Admins may browse any council; officers are pinned to their own. */
  protected onCatalogCouncilChange(value: string): void {
    this.officerLgaId.set(value === '' ? null : Number(value));
    this.loadCatalog();
  }

  private loadCatalog(): void {
    const lgaId = this.officerLgaId();
    if (!lgaId) {
      this.catalogue.set([]);
      return;
    }
    this.loadingCatalog.set(true);
    this.api.licenceTypes({ lga: lgaId }).subscribe({
      next: (page) => {
        this.catalogue.set(page.results);
        this.loadingCatalog.set(false);
      },
      error: () => {
        this.catalogue.set([]);
        this.loadingCatalog.set(false);
      },
    });
  }

  protected startNewLicence(): void {
    this.editingLicenceId.set('new');
    this.licenceForm.set({ ...BLANK_LICENCE });
    this.expandedRequirementsFor.set(null);
  }

  protected startEditLicence(licenceType: LicenceType): void {
    this.editingLicenceId.set(licenceType.id);
    this.licenceForm.set({
      name: licenceType.name,
      code: licenceType.code,
      category: licenceType.category,
      fee: String(licenceType.fee ?? '0'),
      validity_months: licenceType.validity_months,
      requires_inspection: licenceType.requires_inspection,
      description: licenceType.description ?? '',
      bylaw_reference: licenceType.bylaw_reference ?? '',
      activity_id: licenceType.activity ?? null,
    });
    this.expandedRequirementsFor.set(null);
  }

  protected cancelLicenceEdit(): void {
    this.editingLicenceId.set(null);
    this.licenceForm.set({ ...BLANK_LICENCE });
  }

  protected updateLicenceForm(patch: Partial<LicenceForm>): void {
    this.licenceForm.update((form) => ({ ...form, ...patch }));
  }

  protected setLicenceMonths(value: string | number): void {
    const months = typeof value === 'number' ? value : Number(value);
    this.updateLicenceForm({ validity_months: Number.isFinite(months) ? months : 12 });
  }

  protected setLicenceActivity(value: string): void {
    this.updateLicenceForm({ activity_id: value === '' ? null : Number(value) });
  }

  protected saveLicence(): void {
    const form = this.licenceForm();
    const name = form.name.trim();
    const code = form.code.trim().toUpperCase();
    if (!name || !code) {
      this.errorMessage.set('A licence type needs both a name and a code.');
      return;
    }
    if (!this.officerLgaId()) {
      this.errorMessage.set('Choose a council first.');
      return;
    }
    if (this.savingLicence()) return;
    this.savingLicence.set(true);
    this.errorMessage.set('');

    const payload = {
      name,
      code,
      category: form.category,
      activity: form.activity_id,
      description: form.description.trim(),
      fee: form.fee || '0',
      validity_months: form.validity_months,
      requires_inspection: form.requires_inspection,
      bylaw_reference: form.bylaw_reference.trim(),
      lga: this.officerLgaId()!,
    };
    const editingId = this.editingLicenceId();
    const request$ =
      editingId === 'new'
        ? this.api.createLicenceType(payload)
        : this.api.updateLicenceType(editingId as number, payload);

    request$.subscribe({
      next: (licenceType) => {
        this.savingLicence.set(false);
        this.cancelLicenceEdit();
        this.loadCatalog();
        this.successMessage.set(`Licence type “${licenceType.name}” saved.`);
      },
      error: (err) => {
        this.savingLicence.set(false);
        this.errorMessage.set(this.firstError(err, 'Could not save the licence type.'));
      },
    });
  }

  protected toggleRequirements(licenceType: LicenceType): void {
    this.expandedRequirementsFor.update((current) =>
      current === licenceType.id ? null : licenceType.id,
    );
  }

  protected addRequirement(licenceType: LicenceType): void {
    const name = this.reqName().trim();
    if (!name) return;
    this.api
      .createRequirement({
        licence_type: licenceType.id,
        name,
        kind: this.reqKind(),
        is_mandatory: this.reqMandatory(),
        order: licenceType.requirements.length + 1,
      })
      .subscribe({
        next: () => {
          this.reqName.set('');
          this.loadCatalog();
        },
        error: (err) => this.errorMessage.set(this.firstError(err, 'Could not add the requirement.')),
      });
  }

  protected removeRequirement(licenceType: LicenceType, requirementId: number): void {
    this.errorMessage.set('');
    this.api.deleteRequirement(requirementId).subscribe({
      next: () => this.loadCatalog(),
      error: () => this.errorMessage.set('Could not remove the requirement.'),
    });
  }

  /**
   * Capture the inspector's GPS position for an application. Stored on the
   * component so `recordResult` submits it with the inspection outcome.
   */
  protected captureLocation(app: Application): void {
    if (!navigator.geolocation) {
      this.errorMessage.set('Geolocation is not supported by this browser.');
      return;
    }
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        const next = new Map(this.capturedLocation());
        next.set(app.id, {
          lat: pos.coords.latitude,
          lng: pos.coords.longitude,
          accuracy: pos.coords.accuracy,
        });
        this.capturedLocation.set(next);
        this.successMessage.set(
          `Location captured for ${app.reference_number} (±${Math.round(pos.coords.accuracy)} m). Record the result to submit it.`,
        );
        setTimeout(() => this.successMessage.set(''), 4000);
      },
      (err) => {
        // Permission denied / unavailable — allow recording without GPS.
        const next = new Map(this.capturedLocation());
        next.set(app.id, null);
        this.capturedLocation.set(next);
        this.errorMessage.set(`Could not capture location: ${err.message}. You can still record the result.`);
      },
    );
  }

  protected hasCapturedLocation(app: Application): boolean {
    return !!this.capturedLocation().get(app.id);
  }

  /** Open the findings form for an inspection. */
  protected openResultForm(app: Application): void {
    this.recordingId.set(app.id);
    this.resultFindings.set('');
  }

  protected cancelResult(): void {
    this.recordingId.set(null);
    this.resultFindings.set('');
  }

  /**
   * Record the inspection outcome on the LATEST open inspection, then move
   * the application along the state machine (INSPECTED or REJECTED). A
   * failed inspection rejects with the findings as the mandatory reason.
   */
  protected recordResult(app: Application, passed: boolean): void {
    const inspection = this.inspectionByApplication().get(app.id);
    if (!inspection) {
      this.errorMessage.set('No scheduled inspection found for this application.');
      return;
    }
    if (this.processingId()) return;
    this.processingId.set(app.id);
    this.errorMessage.set('');
    this.successMessage.set('');

    const location = this.capturedLocation().get(app.id) ?? null;
    this.api
      .updateInspection(inspection.id, {
        passed,
        findings: this.resultFindings().trim() || (passed ? 'Premises inspected — no issues found.' : 'Inspection failed.'),
        conducted_at: new Date().toISOString(),
        ...(location ? { latitude: location.lat, longitude: location.lng, location_accuracy: location.accuracy } : {}),
      })
      .subscribe({
        next: () => {
          // Outcome saved — now advance the workflow status. A failed
          // inspection carries the findings as the rejection reason.
          const toStatus = passed ? 'INSPECTED' : 'REJECTED';
          const note = passed ? '' : this.resultFindings().trim() || 'Inspection failed.';
          this.api.transitionApplication(app.id, toStatus, note).subscribe({
            next: (updated) => {
              this.successMessage.set(
                `${updated.reference_number}: inspection ${passed ? 'PASSED' : 'FAILED'} recorded → ${STATUS_LABELS[toStatus as ApplicationStatus] ?? toStatus}`,
              );
              this.recordingId.set(null);
              this.resultFindings.set('');
              this.load();
            },
            error: (err) => {
              const detail = err?.error?.detail ?? 'Outcome saved, but the status could not be updated.';
              this.errorMessage.set(typeof detail === 'string' ? detail : 'Status update failed.');
              this.processingId.set(null);
              this.load();
            },
          });
        },
        error: (err) => {
          const detail = err?.error?.detail ?? 'Could not record the inspection result.';
          this.errorMessage.set(typeof detail === 'string' ? detail : 'Could not record the result.');
          this.processingId.set(null);
        },
      });
  }

  protected countFor(filter: QueueFilter): number {
    if (!filter.statuses) return this.applications().length;
    return this.applications().filter((a) => filter.statuses!.includes(a.status)).length;
  }

  // -- Rejection (mandatory reason) -----------------------------------------

  /** Open the reason form instead of rejecting silently. */
  protected openRejectForm(app: Application): void {
    this.rejectingId.set(app.id);
    this.rejectReason.set('');
  }

  protected cancelReject(): void {
    this.rejectingId.set(null);
    this.rejectReason.set('');
  }

  protected confirmReject(app: Application): void {
    const reason = this.rejectReason().trim();
    if (!reason) {
      this.errorMessage.set('A rejection reason is required.');
      return;
    }
    if (this.processingId()) return;
    this.processingId.set(app.id);
    this.errorMessage.set('');
    this.successMessage.set('');
    this.api.transitionApplication(app.id, 'REJECTED', reason).subscribe({
      next: (updated) => {
        this.successMessage.set(
          `${updated.reference_number} → ${STATUS_LABELS.REJECTED} (reason sent to the applicant)`,
        );
        this.processingId.set(null);
        this.cancelReject();
        this.load();
      },
      error: (err) => {
        const detail =
          err?.error?.detail ??
          (err?.error?.note ? String(err.error.note) : null) ??
          'Could not reject the application.';
        this.errorMessage.set(typeof detail === 'string' ? detail : 'Could not reject the application.');
        this.processingId.set(null);
      },
    });
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
        this.processingId.set(null);
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
