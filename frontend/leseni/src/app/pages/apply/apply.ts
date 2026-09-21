import { Component, computed, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';

import { ApiService } from '../../core/api.service';
import { AuthService } from '../../core/auth.service';
import { TanzaniaGeoService } from '../../core/tanzania-geo.service';
import {
  Application,
  Business,
  BusinessLocation,
  LGA,
  LicenceCategory,
  LicenceType,
  RegionInfo,
  Requirement,
} from '../../core/models';

interface NewBusinessForm {
  name: string;
  tin_number: string;
  brela_registration_number: string;
  sector: string;
  lga: number | null;
  ward: string;
  street: string;
  plot_number: string;
}

/** One row of the document checklist. */
interface UploadRow {
  requirement: Requirement | null; // null = extra/other document
  label: string;
  mandatory: boolean;
  uploaded: boolean;
  uploading: boolean;
  fileName: string;
  /** File staged in memory before the draft application exists. */
  pendingFile?: File;
  /** True once the file has been persisted to the backend. */
  persisted?: boolean;
}

@Component({
  imports: [FormsModule, RouterLink],
  selector: 'app-apply',
  templateUrl: './apply.html',
})
export class Apply {
  private readonly api = inject(ApiService);
  private readonly auth = inject(AuthService);
  private readonly geo = inject(TanzaniaGeoService);
  private readonly router = inject(Router);

  protected readonly submitting = signal(false);
  protected readonly errorMessage = signal('');
  protected readonly created = signal<Application | null>(null);

  // Reference data
  protected readonly regions = signal<RegionInfo[]>([]);
  protected readonly lgas = signal<LGA[]>([]);
  protected readonly licenceTypes = signal<LicenceType[]>([]);

  // Cascade selections
  protected readonly regionName = signal<string | null>(null);
  protected readonly lgaId = signal<number | null>(null);
  protected readonly categoryId = signal<LicenceCategory | null>(null);
  protected readonly licenceTypeId = signal<number | null>(null);

  // Business selection
  protected readonly businesses = signal<Business[]>([]);
  protected readonly businessId = signal<number | null>(null);
  protected readonly locations = signal<BusinessLocation[]>([]);
  protected readonly locationId = signal<number | null>(null);
  protected readonly creatingNewBusiness = signal(false);
  protected readonly verifying = signal(false);
  protected readonly newBusiness = signal<NewBusinessForm>({
    name: '', tin_number: '', brela_registration_number: '',
    sector: '', lga: null, ward: '', street: '', plot_number: '',
  });

  protected readonly purpose = signal('');

  /** Wards of the selected council, from the tanzaniageodata dataset. */
  protected readonly wards = signal<string[]>([]);

  // Document checklist (built after the licence type is chosen)
  protected readonly uploadRows = signal<UploadRow[]>([]);
  protected readonly draftApplication = signal<Application | null>(null);

  protected readonly categories: { value: LicenceCategory; label: string; icon: string; hint: string }[] = [
    { value: 'BUSINESS', label: 'Business', icon: '🏪', hint: 'Shops, food vendors, services' },
    { value: 'DRIVING', label: 'Driving', icon: '🚗', hint: 'New licences & renewals' },
    { value: 'GENERAL', label: 'Other', icon: '📋', hint: 'Anything else' },
  ];

  constructor() {
    this.api.regions().subscribe((regions) => this.regions.set(regions));
    this.api.businesses().subscribe((page) => {
      this.businesses.set(page.results);
      if (page.results.length === 0) this.creatingNewBusiness.set(true);
    });
  }

  // Step 1: region chosen -> load its LGAs
  protected onRegionChange(region: string | null): void {
    this.regionName.set(region);
    this.lgaId.set(null);
    this.categoryId.set(null);
    this.licenceTypeId.set(null);
    this.licenceTypes.set([]);
    if (region) {
      this.api.lgas({ region }).subscribe((page) => this.lgas.set(page.results));
    } else {
      this.lgas.set([]);
    }
  }

  // Step 2: LGA chosen -> load its licences and derive available categories
  protected onLgaChange(lgaId: number | null): void {
    this.lgaId.set(lgaId);
    this.categoryId.set(null);
    this.licenceTypeId.set(null);
    this.licenceTypes.set([]);
    this.wards.set([]);
    this.newBusiness.update((nb) => ({ ...nb, ward: '' }));
    if (lgaId) {
      this.api.licenceTypes({ lga: lgaId }).subscribe((page) => {
        const all = page.results;
        this.licenceTypes.set(all);
        const available = new Set<LicenceCategory>(all.map((t) => t.category));
        if (available.size === 1) {
          this.categoryId.set([...available][0]);
        }
      });
      // Wards come from the backend DB (seeded from tanzaniageodata);
      // fall back to the bundled geo dataset if the API has none yet.
      const lga = this.lgas().find((l) => l.id === lgaId);
      this.api.wards(lgaId).subscribe({
        next: (list) => {
          if (list.length > 0) {
            this.wards.set(list.map((w) => w.name));
          } else if (lga) {
            this.wards.set(this.wardsFromDataset(lga.name));
          }
        },
        error: () => {
          if (lga) this.wards.set(this.wardsFromDataset(lga.name));
        },
      });
    }
  }

  /** Fallback: match an LGA name to the bundled tanzaniageodata dataset. */
  private wardsFromDataset(lgaName: string): string[] {
    for (const region of this.geo.regions()) {
      for (const district of this.geo.districts(region)) {
        if (
          district.fullName === lgaName ||
          district.name === lgaName ||
          district.fullName.startsWith(lgaName + ' ') ||
          lgaName.startsWith(district.name + ' ')
        ) {
          return this.geo.wards(district.fullName);
        }
      }
    }
    return [];
  }

  // Step 3: category chosen -> filter licences; licence chosen -> build checklist
  protected onCategoryChange(category: LicenceCategory | null): void {
    this.categoryId.set(category);
    this.selectLicence(null);
  }

  protected selectLicence(id: number | null): void {
    this.licenceTypeId.set(id);
    this.uploadRows.set([]);
    this.draftApplication.set(null);
    const licence = this.selectedLicenceType;
    if (licence) {
      const rows: UploadRow[] = licence.requirements
        .filter((r) => r.kind === 'DOCUMENT')
        .map((r) => ({
          requirement: r,
          label: r.name,
          mandatory: r.is_mandatory,
          uploaded: false,
          uploading: false,
          fileName: '',
        }));
      this.uploadRows.set(rows);
    }
  }

  protected get licencesForCategory(): LicenceType[] {
    const category = this.categoryId();
    if (!category) return [];
    return this.licenceTypes().filter((t) => t.category === category);
  }

  protected get selectedLicenceType(): LicenceType | null {
    return this.licenceTypes().find((t) => t.id === this.licenceTypeId()) ?? null;
  }

  protected get selectedLga(): LGA | null {
    return this.lgas().find((l) => l.id === this.lgaId()) ?? null;
  }

  protected get canSubmit(): boolean {
    if (!this.licenceTypeId()) return false;
    if (this.creatingNewBusiness()) {
      const nb = this.newBusiness();
      if (!nb.name || !nb.lga || !nb.ward || !nb.street) return false;
    } else if (!this.businessId() || !this.locationId()) {
      return false;
    }
    // All mandatory documents must be uploaded (or be on an existing draft).
    const draft = this.draftApplication();
    if (draft) {
      return this.uploadRows().every((row) => !row.mandatory || row.uploaded);
    }
    return this.uploadRows().every((row) => !row.mandatory || row.uploaded);
  }

  protected get uploadedCount(): number {
    return this.uploadRows().filter((r) => r.uploaded).length;
  }

  protected selectBusiness(id: number | null): void {
    this.businessId.set(id);
    const business = this.businesses().find((b) => b.id === id);
    const locs = business?.locations ?? [];
    this.locations.set(locs);
    // Auto-select the primary (or first) location; clear if none exist.
    const primary = locs.find((l) => l.is_primary) ?? locs[0] ?? null;
    this.locationId.set(primary?.id ?? null);
  }

  protected toggleNewBusiness(): void {
    this.creatingNewBusiness.update((v) => !v);
    // Default the inline business LGA to the selected area.
    if (this.creatingNewBusiness() && this.lgaId()) {
      this.newBusiness.update((nb) => ({ ...nb, lga: this.lgaId() }));
    }
  }

  protected get businessVerificationHint(): string {
    const nb = this.newBusiness();
    if (nb.tin_number && nb.brela_registration_number) {
      return 'We will verify your TIN with TRA and your registration with BRELA automatically when you continue.';
    }
    if (!nb.tin_number && !nb.brela_registration_number) {
      return 'TRA TIN and BRELA registration are optional here — businesses without them stay marked “unverified”.';
    }
    return 'Provide both TRA TIN and BRELA registration number to get your business verified automatically.';
  }

  protected onFileSelected(row: UploadRow, event: Event): void {
    const input = event.target as HTMLInputElement;
    const file = input.files?.[0];
    if (!file) return;

    const draft = this.draftApplication();
    if (!draft) {
      // No draft yet: stage the file; it is uploaded right after submission creates the application.
      row.fileName = file.name;
      row.uploaded = true; // staged
      row.persisted = false;
      row.pendingFile = file;
      return;
    }

    row.uploading = true;
    this.api.uploadDocument(draft.id, file, row.requirement?.id).subscribe({
      next: () => {
        row.uploaded = true;
        row.fileName = file.name;
        row.uploading = false;
      },
      error: () => {
        row.uploading = false;
        this.errorMessage.set(`Could not upload ${file.name}.`);
      },
    });
  }

  /** Create the draft application now so documents can be attached. */
  protected createDraft(businessId: number, locationId: number): void {
    this.api
      .createApplication({
        business: businessId,
        licence_type: this.licenceTypeId()!,
        location: locationId,
        purpose_statement: this.purpose(),
      })
      .subscribe({
        next: (application) => {
          this.draftApplication.set(application);
          this.submitting.set(false);
        },
        error: (err) => {
          const detail = err?.error ? Object.values(err.error).flat()[0] : null;
          this.errorMessage.set(typeof detail === 'string' ? detail : 'Could not create the application draft.');
          this.submitting.set(false);
        },
      });
  }

  protected submit(): void {
    if (!this.canSubmit || this.submitting()) return;
    this.submitting.set(true);
    this.errorMessage.set('');

    const submitDraft = (application: Application) => {
      // Upload any staged files first, then submit the application.
      const staged = this.uploadRows().filter((row) => row.uploaded && !row.persisted);
      let pending = staged.length;
      const afterUploads = () => {
        this.api.transitionApplication(application.id, 'SUBMITTED').subscribe({
          next: (submitted) => {
            this.created.set(submitted);
            this.submitting.set(false);
          },
          error: (err) => {
            const detail = err?.error?.detail ?? null;
            this.errorMessage.set(
              typeof detail === 'string' ? detail : 'Could not submit the application.',
            );
            this.submitting.set(false);
          },
        });
      };
      if (pending === 0) {
        afterUploads();
        return;
      }
      for (const row of staged) {
        this.api.uploadDocument(application.id, row.pendingFile!, row.requirement?.id ?? undefined).subscribe({
          next: () => {
            row.persisted = true;
            if (--pending === 0) afterUploads();
          },
          error: () => {
            row.uploaded = false;
            if (--pending === 0) afterUploads();
          },
        });
      }
    };

    const existingDraft = this.draftApplication();
    if (existingDraft) {
      submitDraft(existingDraft);
      return;
    }

    const createAndSubmit = (businessId: number, locationId: number) => {
      this.api
        .createApplication({
          business: businessId,
          licence_type: this.licenceTypeId()!,
          location: locationId,
          purpose_statement: this.purpose(),
        })
        .subscribe({
          next: (application) => submitDraft(application),
          error: (err) => {
            const detail = err?.error ? Object.values(err.error).flat()[0] : null;
            this.errorMessage.set(typeof detail === 'string' ? detail : 'Could not create the application.');
            this.submitting.set(false);
          },
        });
    };

    if (this.creatingNewBusiness()) {
      const nb = this.newBusiness();
      this.api
        .createBusiness({
          name: nb.name,
          tin_number: nb.tin_number,
          brela_registration_number: nb.brela_registration_number,
          sector: nb.sector,
          location: { lga: nb.lga!, ward: nb.ward, street: nb.street, plot_number: nb.plot_number },
        })
        .subscribe({
          next: (business) => {
            this.api.createLocation(business.id, {
              lga: nb.lga!, ward: nb.ward, street: nb.street,
              plot_number: nb.plot_number, is_primary: true,
            }).subscribe({
              next: (location) => {
                createAndSubmit(business.id, (location as { id: number }).id);
              },
              error: () => {
                this.errorMessage.set('Business created but the location could not be saved.');
                this.submitting.set(false);
              },
            });
          },
          error: (err) => {
            const detail = err?.error ? Object.values(err.error).flat()[0] : null;
            this.errorMessage.set(typeof detail === 'string' ? detail : 'Could not create the business.');
            this.submitting.set(false);
          },
        });
    } else {
      createAndSubmit(this.businessId()!, this.locationId()!);
    }
  }

  protected reset(): void {
    this.created.set(null);
    this.errorMessage.set('');
    this.draftApplication.set(null);
    this.uploadRows.set([]);
    // Reload businesses: a just-registered business should appear for the next application.
    this.api.businesses().subscribe((page) => {
      this.businesses.set(page.results);
      this.creatingNewBusiness.set(page.results.length === 0);
    });
  }

  protected goHome(): void {
    void this.router.navigate(['/dashboard']);
  }

  protected get userName(): string {
    return this.auth.currentUser()?.first_name || this.auth.currentUser()?.username || '';
  }
}
