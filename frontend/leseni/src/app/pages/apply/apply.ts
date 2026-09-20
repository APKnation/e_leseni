import { Component, computed, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';

import { ApiService } from '../../core/api.service';
import { AuthService } from '../../core/auth.service';
import { Application, Business, LGA, LicenceCategory, LicenceType, RegionInfo } from '../../core/models';

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

@Component({
  imports: [FormsModule],
  selector: 'app-apply',
  templateUrl: './apply.html',
})
export class Apply {
  private readonly api = inject(ApiService);
  private readonly auth = inject(AuthService);
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
  protected readonly locationId = signal<number | null>(null);
  protected readonly creatingNewBusiness = signal(false);
  protected readonly newBusiness = signal<NewBusinessForm>({
    name: '', tin_number: '', brela_registration_number: '',
    sector: '', lga: null, ward: '', street: '', plot_number: '',
  });

  protected readonly purpose = signal('');

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
    if (lgaId) {
      this.api.licenceTypes({ lga: lgaId }).subscribe((page) => {
        const all = page.results;
        this.licenceTypes.set(all);
        const available = new Set<LicenceCategory>(all.map((t) => t.category));
        if (available.size === 1) {
          this.categoryId.set([...available][0]);
        }
      });
    }
  }

  // Step 3: category chosen -> filter licences
  protected onCategoryChange(category: LicenceCategory | null): void {
    this.categoryId.set(category);
    this.licenceTypeId.set(null);
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
      return !!nb.name && !!nb.lga && !!nb.ward && !!nb.street;
    }
    return !!this.businessId() && !!this.locationId();
  }

  protected selectBusiness(id: number | null): void {
    this.businessId.set(id);
    this.locationId.set(null);
  }

  protected toggleNewBusiness(): void {
    this.creatingNewBusiness.update((v) => !v);
    // Default the inline business LGA to the selected area.
    if (this.creatingNewBusiness() && this.lgaId()) {
      this.newBusiness.update((nb) => ({ ...nb, lga: this.lgaId() }));
    }
  }

  protected submit(): void {
    if (!this.canSubmit || this.submitting()) return;
    this.submitting.set(true);
    this.errorMessage.set('');

    const createAndSubmit = (businessId: number, locationId: number) => {
      this.api
        .createApplication({
          business: businessId,
          licence_type: this.licenceTypeId()!,
          location: locationId,
          purpose_statement: this.purpose(),
        })
        .subscribe({
          next: (application) => {
            this.api.transitionApplication(application.id, 'SUBMITTED').subscribe({
              next: (submitted) => {
                this.created.set(submitted);
                this.submitting.set(false);
              },
              error: () => {
                this.created.set(application);
                this.submitting.set(false);
              },
            });
          },
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
              next: (location) => createAndSubmit(business.id, (location as { id: number }).id),
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
  }

  protected goHome(): void {
    void this.router.navigate(['/dashboard']);
  }

  protected get userName(): string {
    return this.auth.currentUser()?.first_name || this.auth.currentUser()?.username || '';
  }
}
