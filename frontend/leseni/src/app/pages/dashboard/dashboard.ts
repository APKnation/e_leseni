import { Component, inject, OnInit, signal } from '@angular/core';
import { RouterLink } from '@angular/router';
import { finalize } from 'rxjs';

import { ApiService } from '../../core/api.service';
import { AuthService } from '../../core/auth.service';
import {
  Application,
  Invoice,
  Licence,
  STATUS_LABELS,
  STATUS_STYLES,
} from '../../core/models';


@Component({
  imports: [RouterLink],
  selector: 'app-dashboard',
  templateUrl: './dashboard.html',
  styles: ``,
})
export class Dashboard {
  private readonly api = inject(ApiService);
  protected readonly auth = inject(AuthService);

  protected readonly STATUS_LABELS = STATUS_LABELS;

  protected readonly loading = signal(true);
  protected readonly errorMessage = signal('');

  protected readonly applications = signal<Application[]>([]);
  protected readonly licences = signal<Licence[]>([]);
  protected readonly invoices = signal<Invoice[]>([]);

  protected readonly payingInvoiceId = signal<number | null>(null);

  constructor() {
    this.loadAll();
  }

  protected loadAll(): void {
    this.loading.set(true);
    this.errorMessage.set('');

    this.api.applications().subscribe({
      next: (page) => {
        this.applications.set(page.results);
        this.loadInvoicesAndLicences();
      },
      error: () => {
        this.errorMessage.set('Could not load your data. Is the backend running?');
        this.loading.set(false);
      },
    });
  }

  private loadInvoicesAndLicences(): void {
    let pending = 2;
    const done = () => {
      if (--pending === 0) this.loading.set(false);
    };

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
        complete: () => finalize(() => this.payingInvoiceId.set(null)),
      });
  }

  protected user = () => this.auth.currentUser();
}
