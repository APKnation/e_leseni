import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

import { API_BASE_URL } from './api.config';
import {
  Application,
  Business,
  Invoice,
  Licence,
  LGA,
  LicenceType,
  NewBusinessPayload,
  Paginated,
  RegionInfo,
} from './models';

/** Small helper so list endpoints are easy to page/filter. */
export interface ListOptions {
  page?: number;
  pageSize?: number;
  filters?: Record<string, string | number | boolean | null | undefined>;
}

@Injectable({ providedIn: 'root' })
export class ApiService {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = API_BASE_URL;

  private list<T>(path: string, options: ListOptions = {}): Observable<Paginated<T>> {
    let params = new HttpParams();
    if (options.page) params = params.set('page', options.page);
    if (options.pageSize) params = params.set('page_size', options.pageSize);
    for (const [key, value] of Object.entries(options.filters ?? {})) {
      if (value !== null && value !== undefined && value !== '') {
        params = params.set(key, String(value));
      }
    }
    return this.http.get<Paginated<T>>(`${this.baseUrl}/${path}/`, { params });
  }

  // -- Catalog (public reference data) ------------------------------------

  regions(): Observable<RegionInfo[]> {
    return this.http.get<RegionInfo[]>(`${this.baseUrl}/regions/`);
  }

  lgas(filters?: ListOptions['filters']): Observable<Paginated<LGA>> {
    return this.list<LGA>('lgas', { filters, pageSize: 250 });
  }

  licenceTypes(filters?: ListOptions['filters']): Observable<Paginated<LicenceType>> {
    return this.list<LicenceType>('licence-types', { filters, pageSize: 250 });
  }

  // -- Businesses ----------------------------------------------------------

  businesses(): Observable<Paginated<Business>> {
    return this.list<Business>('businesses');
  }

  createBusiness(payload: NewBusinessPayload): Observable<Business> {
    return this.http.post<Business>(`${this.baseUrl}/businesses/`, payload);
  }

  createLocation(
    businessId: number,
    data: Omit<NewBusinessPayload['location'], 'lga'> & { lga: number; is_primary?: boolean },
  ) {
    return this.http.post(`${this.baseUrl}/business-locations/`, { business: businessId, ...data });
  }

  // -- Applications --------------------------------------------------------

  applications(filters?: ListOptions['filters']): Observable<Paginated<Application>> {
    return this.list<Application>('applications', { filters });
  }

  createApplication(payload: {
    business: number;
    licence_type: number;
    location: number;
    purpose_statement: string;
  }): Observable<Application> {
    return this.http.post<Application>(`${this.baseUrl}/applications/`, payload);
  }

  transitionApplication(id: number, toStatus: string, note = ''): Observable<Application> {
    return this.http.post<Application>(`${this.baseUrl}/applications/${id}/transition/`, {
      to_status: toStatus,
      note,
    });
  }

  // -- Invoices ------------------------------------------------------------

  invoices(filters?: ListOptions['filters']): Observable<Paginated<Invoice>> {
    return this.list<Invoice>('invoices', { filters });
  }

  requestControlNumber(invoiceId: number): Observable<Invoice> {
    return this.http.post<Invoice>(`${this.baseUrl}/invoices/${invoiceId}/control-number/`, {});
  }

  payInvoice(
    invoiceId: number,
    data: { amount: string; method: string; payer_name?: string; payer_phone?: string; reference?: string },
  ): Observable<{ invoice_settled: boolean; application_status: string; receipt_number: string }> {
    return this.http.post<{ invoice_settled: boolean; application_status: string; receipt_number: string }>(
      `${this.baseUrl}/invoices/${invoiceId}/pay/`,
      data,
    );
  }

  // -- Licences ------------------------------------------------------------

  licences(filters?: ListOptions['filters']): Observable<Paginated<Licence>> {
    return this.list<Licence>('licences', { filters });
  }
}
