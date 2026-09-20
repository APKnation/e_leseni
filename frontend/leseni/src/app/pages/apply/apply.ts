import { Component, inject, OnInit, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { finalize } from 'rxjs';

import { ApiService } from '../../core/api.service';
import { AuthService } from '../../core/auth.service';
import { Application, Business, LGA, LicenceType } from '../../core/models';

@Component({
  imports: [FormsModule, RouterLink],
  selector: 'app-apply',
  templateUrl: './apply.html',
})
export class Apply implements OnInit {
  private readonly api = inject(ApiService);
  private readonly auth = inject(AuthService);
  private readonly router = inject(Router);

  protected readonly submitting = signal(false);
  protected readonly errorMessage = signal('');
  protected readonly created = signal<Application | null>(null);

  // Reference data
  protected readonly lgas = signal<LGA[]>([]);
  protected readonly businesses = signal<Business[]>([]);
  protected readonly licenceTypes = signal<LicenceType[]>([]);

  // Form state
  protected readonly businessId = signal<number | null>(null);
  protected readonly locationId = signal<number | null>(null);
  protected readonly licenceTypeId = signal<number | null>(null);
  protected readonly purpose = signal('');

  // Inline "new business" flow
  protected readonly creatingNewBusiness = signal(false);
  protected readonly newBusiness = signal({
    name: '',
    tin_number: '',
    brela_registration_number: '',
    sector: '',
    lga: null as number | null,
    ward: '',
    street: '',
    plot_number: '',
  });

  protected ngOnInit(): void {
    this.api.lgas().subscribe((page) => this.lgas.set(page.results));
    this.api.licenceTypes().subscribe((page) => this.licenceTypes.set(page.results));
    this.api.businesses().subscribe((page) => {
      this.businesses.set(page.results);
      if (page.results.length === 0) this.creatingNewBusiness.set(true);
    });
  }

  protected get selectedLicenceType(): LicenceType | null {
    return this.licenceTypes().find((t) => t.id === this.licenceTypeId()) ?? null;
  }

  protected get selectedBusiness(): Business | null {
    return this.businesses().find((b) => b.id === this.businessId()) ?? null;
  }

  protected get selectedLocationId(): number | null {
    if (this.creatingNewBusiness()) return null;
    return this.locationId();
  }

  protected get canSubmit(): boolean {
    if (this.creatingNewBusiness()) {
      const nb = this.newBusiness();
      return (
        !!nb.name && !!nb.lga && !!nb.ward && !!nb.street && !!this.licenceTypeId()
      );
    }
    return !!this.businessId() && !!this.locationId() && !!this.licenceTypeId();
  }

  protected selectBusiness(id: number | null): void {
    this.businessId.set(id);
    this.locationId.set(null);
  }

  protected toggleNewBusiness(): void {
    this.creatingNewBusiness.update((v) => !v);
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
            // Auto-submit: DRAFT -> SUBMITTED
            this.api.transitionApplication(application.id, 'SUBMITTED').subscribe({
              next: (submitted) => {
                this.created.set(submitted);
                this.submitting.set(false);
              },
              error: () => {
                // Draft was created but auto-submit failed; still show it.
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
          location: {
            lga: nb.lga!,
            ward: nb.ward,
            street: nb.street,
            plot_number: nb.plot_number,
          },
        })
        .subscribe({
          next: (business) => {
            const locationPayload = {
              lga: nb.lga!,
              ward: nb.ward,
              street: nb.street,
              plot_number: nb.plot_number,
              is_primary: true,
            };
            // The backend serialiser currently ignores nested locations, so
            // create the location explicitly and use its id.
            this.api.createLocation(business.id, locationPayload).subscribe({
              next: (location: unknown) => {
                const loc = location as { id: number };
                createAndSubmit(business.id, loc.id);
              },
              error: () => createAndSubmit(business.id, 0), // will fail; surfaced as error
            });
          },
          error: (err) => {
            const detail = err?.error ? Object.values(err.error).flat()[0] : null;
            this.errorMessage.set(
              typeof detail === 'string' ? detail : 'Could not create the business.',
            );
            this.submitting.set(false);
          },
        });
    } else {
      createAndSubmit(this.businessId()!, this.locationId()!);
    }
  }

  protected goHome(): void {
    void this.router.navigate(['/dashboard']);
  }

  protected get userName(): string {
    return this.auth.currentUser()?.first_name || this.auth.currentUser()?.username || '';
  }
}
