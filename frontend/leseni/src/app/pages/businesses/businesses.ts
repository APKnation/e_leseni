import { DatePipe } from '@angular/common';
import { Component, computed, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';

import { ApiService } from '../../core/api.service';
import { TanzaniaGeoService } from '../../core/tanzania-geo.service';
import {
  Business,
  LGA,
  RegionInfo,
  TINApplication,
} from '../../core/models';

/** Result of one demo-government step, shown as a receipt. */
interface StepReceipt {
  title: string;
  lines: { label: string; value: string }[];
}

@Component({
  imports: [FormsModule, RouterLink, DatePipe],
  selector: 'app-businesses',
  templateUrl: './businesses.html',
})
export class Businesses {
  private readonly api = inject(ApiService);
  private readonly geo = inject(TanzaniaGeoService);

  // Data
  protected readonly businesses = signal<Business[]>([]);
  protected readonly tinApps = signal<TINApplication[]>([]);
  protected readonly regions = signal<RegionInfo[]>([]);
  protected readonly lgas = signal<LGA[]>([]);
  protected readonly wards = signal<string[]>([]);

  protected readonly loading = signal(true);
  protected readonly errorMessage = signal('');

  // Wizard state
  protected readonly wizardOpen = signal(false);
  protected readonly step = signal(1); // 1 = details, 2 = BRELA, 3 = TRA TIN, 4 = location
  protected readonly working = signal(false);

  // Wizard form fields
  protected readonly name = signal('');
  protected readonly sector = signal('');
  protected readonly taxpayerName = signal('');
  protected readonly regionName = signal<string | null>(null);
  protected readonly lgaId = signal<number | null>(null);
  protected readonly ward = signal('');
  protected readonly street = signal('');
  protected readonly plotNumber = signal('');

  // Results from the demo government systems
  protected readonly brelaNumber = signal('');
  protected readonly tinNumber = signal('');
  protected readonly brelaReceipt = signal<StepReceipt | null>(null);
  protected readonly tinReceipt = signal<StepReceipt | null>(null);

  // Verification + save
  protected readonly verificationMessage = signal('');
  protected readonly createdBusiness = signal<Business | null>(null);

  protected readonly canFinish = computed(() => {
    const lga = this.lgaId();
    return !!(this.brelaNumber() && this.tinNumber() && lga && this.ward() && this.street());
  });

  constructor() {
    this.loadAll();
    this.api.regions().subscribe((regions) => this.regions.set(regions));
  }

  protected loadAll(): void {
    this.loading.set(true);
    let pending = 2;
    const done = () => {
      if (--pending === 0) this.loading.set(false);
    };
    this.api.businesses().subscribe({
      next: (page) => {
        this.businesses.set(page.results);
        done();
      },
      error: () => {
        this.errorMessage.set('Could not load your businesses. Is the backend running?');
        this.loading.set(false);
      },
    });
    this.api.tinApplications().subscribe({
      next: (list) => {
        this.tinApps.set(list);
        done();
      },
      error: () => done(),
    });
  }

  // ---- Wizard navigation -------------------------------------------------

  protected openWizard(): void {
    this.resetWizard();
    this.wizardOpen.set(true);
  }

  protected closeWizard(): void {
    this.wizardOpen.set(false);
  }

  private resetWizard(): void {
    this.step.set(1);
    this.name.set('');
    this.sector.set('');
    this.taxpayerName.set('');
    this.regionName.set(null);
    this.lgaId.set(null);
    this.ward.set('');
    this.street.set('');
    this.plotNumber.set('');
    this.brelaNumber.set('');
    this.tinNumber.set('');
    this.brelaReceipt.set(null);
    this.tinReceipt.set(null);
    this.verificationMessage.set('');
    this.createdBusiness.set(null);
    this.errorMessage.set('');
  }

  protected goToStep(n: number): void {
    this.step.set(n);
  }

  protected get stepLabels(): string[] {
    return ['Business details', 'BRELA registration', 'TRA TIN', 'Location & finish'];
  }

  protected readonly journeySteps = [
    { title: 'Register with BRELA', hint: 'We submit your business to BRELA and get your registration number.' },
    { title: 'Get a TIN from TRA', hint: 'We apply for your Taxpayer Identification Number at TRA.' },
    { title: 'Verified automatically', hint: 'Your numbers are checked with both agencies — no paperwork.' },
    { title: 'Apply for a licence', hint: 'Take your verified business to the council and apply online.' },
  ];

  // ---- Step 2: BRELA ------------------------------------------------------

  protected get detailsValid(): boolean {
    return this.name().trim().length >= 3 && this.taxpayerName().trim().length >= 3;
  }

  protected registerWithBrela(): void {
    if (!this.detailsValid || this.working()) return;
    this.working.set(true);
    this.errorMessage.set('');
    this.api.brelaRegister(this.name().trim()).subscribe({
      next: (res) => {
        this.brelaNumber.set(res.registration_number);
        this.brelaReceipt.set({
          title: 'BRELA — Registration confirmed',
          lines: [
            { label: 'Registration no.', value: res.registration_number },
            { label: 'Entity name', value: res.entity_name },
            { label: 'Status', value: res.status },
            { label: 'Issued by', value: res.source },
          ],
        });
        this.working.set(false);
        this.goToStep(3);
      },
      error: () => {
        this.errorMessage.set('BRELA registration failed. Please try again.');
        this.working.set(false);
      },
    });
  }

  // ---- Step 3: TRA TIN ----------------------------------------------------

  protected applyForTin(): void {
    if (!this.detailsValid || this.working()) return;
    this.working.set(true);
    this.errorMessage.set('');
    this.api.applyForTin(this.name().trim(), this.taxpayerName().trim()).subscribe({
      next: (app) => {
        this.tinNumber.set(app.tin_number);
        this.tinReceipt.set({
          title: 'TRA — TIN approved',
          lines: [
            { label: 'TIN', value: app.tin_number },
            { label: 'Taxpayer', value: app.taxpayer_name },
            { label: 'Business', value: app.business_name },
            { label: 'Status', value: app.status },
          ],
        });
        this.working.set(false);
        this.goToStep(4);
      },
      error: () => {
        this.errorMessage.set('TIN application failed. Please try again.');
        this.working.set(false);
      },
    });
  }

  // ---- Step 4: location + save -------------------------------------------

  protected onRegionChange(region: string | null): void {
    this.regionName.set(region);
    this.lgaId.set(null);
    this.ward.set('');
    if (region) {
      this.api.lgas({ region }).subscribe((page) => this.lgas.set(page.results));
    } else {
      this.lgas.set([]);
    }
  }

  protected onLgaChange(lgaId: number | null): void {
    this.lgaId.set(lgaId);
    this.ward.set('');
    if (lgaId) {
      this.api.wards(lgaId).subscribe({
        next: (list) => this.wards.set(list.map((w) => w.name)),
        error: () => this.wards.set([]),
      });
    } else {
      this.wards.set([]);
    }
  }

  protected saveBusiness(): void {
    if (!this.canFinish || this.working()) return;
    this.working.set(true);
    this.errorMessage.set('');

    const lga = this.lgaId()!;
    this.api
      .createBusiness({
        name: this.name().trim(),
        tin_number: this.tinNumber(),
        brela_registration_number: this.brelaNumber(),
        sector: this.sector().trim(),
        location: {
          lga,
          ward: this.ward(),
          street: this.street().trim(),
          plot_number: this.plotNumber().trim(),
        },
      })
      .subscribe({
        next: (business) => {
          // The backend auto-verifies when both numbers are present; make sure.
          if (business.is_verified) {
            this.finishCreate(business);
            return;
          }
          this.api.verifyBusiness(business.id).subscribe({
            next: (v) => {
              this.verificationMessage.set(
                v.is_verified
                  ? 'Verified with TRA and BRELA — your business is trusted.'
                  : 'Verification did not pass — officers will see this business as unverified.',
              );
              this.finishCreate({ ...business, is_verified: v.is_verified });
            },
            error: () => this.finishCreate(business),
          });
        },
        error: (err) => {
          const detail = err?.error ? Object.values(err.error).flat()[0] : null;
          this.errorMessage.set(
            typeof detail === 'string' ? detail : 'Could not save the business.',
          );
          this.working.set(false);
        },
      });
  }

  private finishCreate(business: Business): void {
    this.createdBusiness.set(business);
    this.working.set(false);
    this.loadAll();
  }

  protected wizardDone(): void {
    this.wizardOpen.set(false);
    this.loadAll();
  }

  // ---- Existing businesses ------------------------------------------------

  protected verifyNow(business: Business): void {
    this.api.verifyBusiness(business.id).subscribe({
      next: () => this.loadAll(),
      error: () => this.errorMessage.set('Verification failed. Please try again.'),
    });
  }
}
