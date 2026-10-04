import { DatePipe } from '@angular/common';
import { Component, computed, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';

import { ApiService } from '../../core/api.service';
import { AuthService } from '../../core/auth.service';
import { TanzaniaGeoService } from '../../core/tanzania-geo.service';
import { ProfileLink } from '../../shared/profile-link';
import {
  Business,
  BusinessActivity,
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
  imports: [FormsModule, RouterLink, DatePipe, ProfileLink],
  selector: 'app-businesses',
  templateUrl: './businesses.html',
})
export class Businesses {
  private readonly api = inject(ApiService);
  private readonly geo = inject(TanzaniaGeoService);
  private readonly auth = inject(AuthService);

  // Data
  protected readonly businesses = signal<Business[]>([]);
  protected readonly tinApps = signal<TINApplication[]>([]);
  protected readonly regions = signal<RegionInfo[]>([]);
  protected readonly lgas = signal<LGA[]>([]);
  protected readonly wards = signal<string[]>([]);

  protected readonly loading = signal(true);
  protected readonly errorMessage = signal('');
  protected readonly successMessage = signal('');

  // Wizard state
  protected readonly wizardOpen = signal(false);
  protected readonly step = signal(1); // 1 = details, 2 = BRELA, 3 = TRA TIN, 4 = NIDA, 5 = location
  protected readonly working = signal(false);

  // Wizard form fields
  protected readonly name = signal('');
  protected readonly sector = signal('');
  protected readonly activityId = signal<number | null>(null);
  protected readonly allActivities = signal<BusinessActivity[]>([]);
  protected readonly taxpayerName = signal('');
  protected readonly nidaNumber = signal('');
  protected readonly regionName = signal<string | null>(null);
  protected readonly lgaId = signal<number | null>(null);
  protected readonly ward = signal('');
  protected readonly street = signal('');
  protected readonly plotNumber = signal('');
  protected readonly stepLabels = ['Details', 'BRELA', 'NIDA', 'Location', 'Submit'];
  protected readonly uploadKind = signal('BRELA_CERTIFICATE');
  protected readonly uploadForBusinessId = signal<number | null>(null);
  protected readonly uploadingDoc = signal(false);
  protected readonly pendingDocFile = signal<File | null>(null);
  protected readonly pendingDocBusinessId = signal<number | null>(null);


  // Street identification letter (from the mtaa/street chairman) — PDF only.
  protected readonly streetLetterFile = signal<File | null>(null);
  protected readonly streetLetterName = signal('');

  // NIDA copy for the TRA TIN application — PDF only.
  protected readonly nidaCopyFile = signal<File | null>(null);
  protected readonly nidaCopyName = signal('');

  // Results from the demo government systems
  // Field-level validation messages (per step).
  protected readonly fieldErrors = signal<Record<string, string>>({});

  protected readonly brelaNumber = signal('');
  protected readonly tinNumber = signal('');
  protected readonly brelaReceipt = signal<StepReceipt | null>(null);
  protected readonly tinReceipt = signal<StepReceipt | null>(null);
  protected readonly nidaReceipt = signal<StepReceipt | null>(null);

  // Verification + save
  protected readonly verificationMessage = signal('');
  protected readonly createdBusiness = signal<Business | null>(null);

  // Add-premises form — register the same business in another council/region.
  protected readonly premisesForBusinessId = signal<number | null>(null);
  protected readonly premisesRegion = signal<string | null>(null);
  protected readonly premisesLgaId = signal<number | null>(null);
  protected readonly premisesLgas = signal<LGA[]>([]);
  protected readonly premisesWards = signal<string[]>([]);
  protected readonly premisesWard = signal('');
  protected readonly premisesStreet = signal('');
  protected readonly premisesPlot = signal('');
  protected readonly savingPremises = signal(false);

  /** Get a field-level error message for a step. */
  protected fieldError(step: string): string {
    return this.fieldErrors()[step] ?? '';
  }

  /** Set a field-level error message for a step. */
  protected setFieldError(step: string, message: string): void {
    this.fieldErrors.update((e) => ({ ...e, [step]: message }));
  }

  /** Clear all field errors for a step. */
  protected clearFieldErrors(step: string): void {
    this.fieldErrors.update((e) => {
      const next = { ...e };
      delete next[step];
      return next;
    });
  }

  // ---- Construction / layout ----------------------------------------------------

  protected readonly journeySteps = [
    { title: 'Register with BRELA', hint: 'We submit your business to BRELA and get your registration number.' },
    { title: 'Get a TIN from TRA', hint: 'We apply for your TIN with your NIDA number and a PDF copy of your ID.' },
    { title: 'Street ID letter', hint: 'The mtaa/street chairman letter confirms where you operate.' },
    { title: 'Apply for a licence', hint: 'Take your verified business to the council and apply online.' },
  ];

  protected readonly docKinds = [
    { value: 'TIN_CERTIFICATE', label: 'TIN certificate (TRA)' },
    { value: 'BRELA_CERTIFICATE', label: 'BRELA registration certificate' },
    { value: 'STREET_ID_LETTER', label: 'Street identification letter' },
    { value: 'LEASE_AGREEMENT', label: 'Lease agreement' },
    { value: 'OTHER', label: 'Other document' },
  ];

  protected readonly canFinish = computed(() => {
    const lga = this.lgaId();
    return !!(
      this.brelaNumber() &&
      this.tinNumber() &&
      this.nidaReceipt() &&
      this.streetLetterFile() &&
      lga &&
      this.ward() &&
      this.street()
    );
  });

  constructor() {
    this.loadAll();
    this.api.regions().subscribe((regions) => this.regions.set(regions));
    this.api.businessActivities().subscribe({
      next: (list) => this.allActivities.set(list),
      error: () => this.allActivities.set([]),
    });
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
    this.step.set(1);
    this.wizardOpen.set(true);
  }

  protected closeWizard(): void {
    this.wizardOpen.set(false);
  }

  private resetWizard(): void {
    this.step.set(1);
    this.name.set('');
    this.sector.set('');
    this.activityId.set(null);
    this.taxpayerName.set('');
    this.nidaNumber.set(this.auth.currentUser()?.nida_number ?? '');
    this.regionName.set(null);
    this.lgaId.set(null);
    this.ward.set('');
    this.street.set('');
    this.plotNumber.set('');
    this.brelaNumber.set('');
    this.tinNumber.set('');
    this.brelaReceipt.set(null);
    this.tinReceipt.set(null);
    this.nidaReceipt.set(null);
    this.streetLetterFile.set(null);
    this.streetLetterName.set('');
    this.nidaCopyFile.set(null);
    this.nidaCopyName.set('');
    this.verificationMessage.set('');
    this.createdBusiness.set(null);
    this.errorMessage.set('');
  }

  protected goToStep(n: number): void {
    this.step.set(n);
  }

  /** Keep the free-text sector in sync with the chosen activity. */
  protected onActivitySelect(value: number | null): void {
    const id = value === null || value === undefined || (value as unknown) === '' ? null : Number(value);
    this.activityId.set(id);
    const activity = this.allActivities().find((a) => a.id === id);
    this.sector.set(activity?.name ?? '');
  }

  /** Validate the business details from step 1. */
  protected get detailsValid(): boolean {
    return this.validateDetails();
  }

  /** Validate the business details from step 1. */
  protected validateDetails(): boolean {
    const name = this.name().trim();
    const sector = this.sector().trim();
    const taxpayer = this.taxpayerName().trim();

    if (name.length < 3) {
      this.setFieldError('step1', 'Business name must be at least 3 characters.');
      return false;
    }
    if (taxpayer.length < 3) {
      this.setFieldError('step1', 'Taxpayer name must be at least 3 characters.');
      return false;
    }
    // Sector is optional
    this.clearFieldErrors('step1');
    return true;
  }



  protected get hasNidaOnProfile(): boolean {
    return this.auth.currentUser()?.has_nida ?? false;
  }

  protected continueToLocation(): void {
    if (!this.streetLetterFile()) {
      this.setFieldError('step4', 'The street identification letter (PDF) is required before continuing.');
      return;
    }
    this.clearFieldErrors('step4');
    this.errorMessage.set('');
    this.goToStep(5);
  }

  protected onLetterSelected(event: Event): void {
    const file = this.readPdfFile(event);
    if (!file) return;
    this.streetLetterFile.set(file);
    this.streetLetterName.set(file.name);
    this.errorMessage.set('');
  }

  /** Validate NIDA — must be exactly 20 digits. Show a field-level error if invalid. */
  protected validateNida(): boolean {
    const nida = this.nidaNumber().trim();
    if (!nida) {
      this.setFieldError('step3', 'NIDA number is required.');
      return false;
    }
    if (nida.length !== 20 || !/^\d+$/.test(nida)) {
      this.setFieldError('step3', 'NIDA number must be exactly 20 digits (e.g. 1999 1234 5678 9012 3456).');
      return false;
    }
    this.clearFieldErrors('step3');
    return true;
  }


  protected onNidaCopySelected(event: Event): void {
    const file = this.readPdfFile(event);
    if (!file) return;
    this.nidaCopyFile.set(file);
    this.nidaCopyName.set(file.name);
    this.errorMessage.set('');
  }

  /** Validate a picked file is a PDF within the size limit; show an error otherwise. */
  private readPdfFile(event: Event): File | null {
    const input = event.target as HTMLInputElement;
    const file = input.files?.[0] ?? null;
    input.value = ''; // allow re-picking the same file after a failure
    if (!file) return null;
    const isPdf = file.type === 'application/pdf' || file.name.toLowerCase().endsWith('.pdf');
    if (!isPdf) {
      this.errorMessage.set(`${file.name} is not a PDF — only PDF documents are accepted.`);
      return null;
    }
    if (file.size > 10 * 1024 * 1024) {
      this.errorMessage.set(
        `${file.name} is too large (${(file.size / 1024 / 1024).toFixed(1)} MB). Max is 10 MB.`,
      );
      return null;
    }
    return file;
  }

  // ---- Step 2: BRELA ------------------------------------------------------
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
    if (this.working()) return;
    if (!this.validateNida()) return;
    if (!this.nidaCopyFile()) {
      this.setFieldError('step3', 'Attach a PDF copy of your national ID — TRA requires it with every TIN application.');
      return;
    }
    this.working.set(true);
    this.errorMessage.set('');
    const nida = this.nidaNumber().trim();
    this.api
      .applyForTin(
        this.name().trim(),
        this.taxpayerName().trim(),
        nida,
        this.nidaCopyFile()!,
      )
      .subscribe({
        next: (app) => {
          this.tinNumber.set(app.tin_number);
          this.tinReceipt.set({
            title: 'TRA — TIN approved',
            lines: [
              { label: 'TIN', value: app.tin_number },
              { label: 'Taxpayer', value: app.taxpayer_name },
              { label: 'Business', value: app.business_name },
              { label: 'NIDA no.', value: nida },
              { label: 'ID copy', value: 'Attached' },
              { label: 'Status', value: app.status },
            ],
          });
          // Persist the NIDA on the profile — approvals and BRELA checks rely on it.
          this.api.updateProfile({ nida_number: nida }).subscribe({
            next: () => {
              this.nidaReceipt.set({
                title: 'NIDA — Identity recorded',
                lines: [
                  { label: 'NIDA no.', value: nida },
                  { label: 'ID copy', value: 'Attached' },
                  { label: 'Verified with', value: 'TRA (with TIN application)' },
                ],
              });
              this.working.set(false);
              this.goToStep(4);
            },
            error: () => {
              this.errorMessage.set('TIN approved but saving the NIDA failed — please retry.');
              this.working.set(false);
            },
          });
        },
        error: () => {
          this.errorMessage.set('TIN application failed. Please try again.');
          this.working.set(false);
        },
      });
  }



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
    const selectedActivity = this.allActivities().find((a) => a.id === this.activityId());
    this.api
      .createBusiness({
        name: this.name().trim(),
        tin_number: this.tinNumber(),
        brela_registration_number: this.brelaNumber(),
        sector: selectedActivity?.name ?? this.sector().trim(),
        activity: this.activityId(),
        location: {
          lga,
          ward: this.ward(),
          street: this.street().trim(),
          plot_number: this.plotNumber().trim(),
        },
      })
      .subscribe({
        next: (business) => {
          const letter = this.streetLetterFile();
          if (!letter) {
            this.finishCreate(business);
            return;
          }
          // Upload the street letter, then verify (verification requires it).
          this.api.uploadStreetIdLetter(business.id, letter).subscribe({
            next: () => {
              this.api.verifyBusiness(business.id).subscribe({
                next: (v) => {
                  this.verificationMessage.set(
                    v.is_verified
                      ? 'Verified with TRA, BRELA and NIDA — your business is trusted.'
                      : 'Verification did not pass — officers will see this business as unverified.',
                  );
                  this.finishCreate({ ...business, is_verified: v.is_verified, has_street_id_letter: true });
                },
                error: () => this.finishCreate(business),
              });
            },
            error: () => {
              this.errorMessage.set(
                'Business saved but the street letter upload failed — you can upload it from the business card.',
              );
              this.finishCreate(business);
            },
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
    this.errorMessage.set('');
    this.successMessage.set('');
    this.api.verifyBusiness(business.id).subscribe({
      next: (res: any) => {
        this.successMessage.set(
          res?.is_verified
            ? `${business.name} verified with TRA & BRELA.`
            : 'Verification did not pass — check the TIN and BRELA numbers.',
        );
        this.loadAll();
      },
      error: (err) => {
        // Surface the backend's real reason (missing street letter, no NIDA, etc.)
        const detail = err?.error?.detail ?? err?.error?.non_field_errors?.[0];
        this.errorMessage.set(
          typeof detail === 'string' && detail
            ? detail
            : 'Verification failed. Please try again.',
        );
      },
    });
  }

  // ---- Add premises (possibly in another region) ----------------------------

  protected togglePremises(business: Business): void {
    const opening = this.premisesForBusinessId() !== business.id;
    this.premisesForBusinessId.set(opening ? business.id : null);
    this.premisesRegion.set(null);
    this.premisesLgaId.set(null);
    this.premisesLgas.set([]);
    this.premisesWards.set([]);
    this.premisesWard.set('');
    this.premisesStreet.set('');
    this.premisesPlot.set('');
    this.errorMessage.set('');
  }

  protected onPremisesRegion(region: string | null): void {
    this.premisesRegion.set(region);
    this.premisesLgaId.set(null);
    this.premisesWards.set([]);
    this.premisesWard.set('');
    if (region) {
      this.api.lgas({ region }).subscribe((page) => this.premisesLgas.set(page.results));
    } else {
      this.premisesLgas.set([]);
    }
  }

  protected onPremisesLga(lgaId: number | null): void {
    this.premisesLgaId.set(lgaId);
    this.premisesWards.set([]);
    this.premisesWard.set('');
    if (lgaId) {
      this.api.wards(lgaId).subscribe({
        next: (list) => this.premisesWards.set(list.map((w) => w.name)),
        error: () => this.premisesWards.set([]),
      });
    }
  }

  protected savePremises(business: Business): void {
    const lga = this.premisesLgaId();
    const ward = this.premisesWard().trim();
    const street = this.premisesStreet().trim();
    if (!lga || !ward || !street || this.savingPremises()) return;
    this.savingPremises.set(true);
    this.errorMessage.set('');
    this.api
      .createLocation(business.id, {
        lga,
        ward,
        street,
        plot_number: this.premisesPlot().trim(),
        is_primary: business.locations.length === 0,
      })
      .subscribe({
        next: () => {
          this.savingPremises.set(false);
          this.togglePremises(business);
          this.successMessage.set(
            `Premises added to ${business.name} — you can now apply for that council's licence.`,
          );
          this.loadAll();
        },
        error: () => {
          this.savingPremises.set(false);
          this.errorMessage.set('Could not save the premises. Please try again.');
        },
      });
  }

  // ---- Supporting documents on existing businesses ------------------------

  protected toggleDocUpload(businessId: number): void {
    this.errorMessage.set('');
    this.pendingDocFile.set(null);
    this.uploadForBusinessId.update((current) => (current === businessId ? null : businessId));
  }

  protected onBusinessDocSelected(businessId: number, event: Event): void {
    const input = event.target as HTMLInputElement;
    const file = input.files?.[0] ?? null;
    input.value = ''; // allow re-picking the same file after a failure
    if (!file) return;
    const isPdf = file.type === 'application/pdf' || file.name.toLowerCase().endsWith('.pdf');
    if (!isPdf) {
      this.errorMessage.set(`${file.name} is not a PDF — only PDF documents are accepted.`);
      return;
    }
    if (file.size > 10 * 1024 * 1024) {
      this.errorMessage.set(`${file.name} is too large (max 10 MB).`);
      return;
    }
    this.errorMessage.set('');
    this.pendingDocFile.set(file);
    this.pendingDocBusinessId.set(businessId);
  }

  protected submitBusinessDoc(businessId: number): void {
    const file = this.pendingDocFile();
    if (!file || this.pendingDocBusinessId() !== businessId) return;

    this.errorMessage.set('');
    this.uploadingDoc.set(true);
    const kind = this.uploadKind();
    this.api.uploadBusinessDocument(businessId, file, kind).subscribe({
      next: () => {
        this.uploadingDoc.set(false);
        this.pendingDocFile.set(null);
        this.loadAll();
      },
      error: () => {
        this.uploadingDoc.set(false);
        this.errorMessage.set('Upload failed — make sure the file is a PDF under 10 MB and try again.');
      },
    });
  }
}
