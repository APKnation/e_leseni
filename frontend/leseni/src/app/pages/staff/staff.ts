import { Component, inject, OnInit, signal } from '@angular/core';

import { ApiService } from '../../core/api.service';
import { Application, ApplicationStatus, STATUS_LABELS, STATUS_STYLES } from '../../core/models';

interface QueueFilter {
  label: string;
  statuses: ApplicationStatus[] | null;
}

@Component({
  selector: 'app-staff',
  templateUrl: './staff.html',
})
export class Staff implements OnInit {
  private readonly api = inject(ApiService);

  protected readonly STATUS_LABELS = STATUS_LABELS;
  protected readonly STATUS_STYLES = STATUS_STYLES;

  protected readonly loading = signal(true);
  protected readonly errorMessage = signal('');
  protected readonly applications = signal<Application[]>([]);
  protected readonly processingId = signal<number | null>(null);

  protected readonly queueFilters: QueueFilter[] = [
    { label: 'Needs review', statuses: ['SUBMITTED'] },
    { label: 'Ready for inspection', statuses: ['INSPECTION_SCHEDULED', 'INSPECTED'] },
    { label: 'Payment pending', statuses: ['PAYMENT_PENDING'] },
    { label: 'All', statuses: null },
  ];
  protected readonly activeFilter = signal<QueueFilter>(this.queueFilters[3]);

  ngOnInit(): void {
    this.load();
  }

  protected load(): void {
    this.loading.set(true);
    this.errorMessage.set('');
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
    this.api.transitionApplication(app.id, toStatus).subscribe({
      next: () => this.load(),
      error: () => this.processingId.set(null),
    });
  }

  protected startReview(app: Application): void {
    this.advance(app, 'UNDER_REVIEW');
  }
}
