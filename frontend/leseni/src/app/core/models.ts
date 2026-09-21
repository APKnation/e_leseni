/** Shared API types mirroring the Django backend models. */

export type ApplicationStatus =
  | 'DRAFT'
  | 'SUBMITTED'
  | 'UNDER_REVIEW'
  | 'INSPECTION_SCHEDULED'
  | 'INSPECTED'
  | 'APPROVED'
  | 'PAYMENT_PENDING'
  | 'PAID'
  | 'ISSUED'
  | 'RETURNED_FOR_CORRECTION'
  | 'REJECTED';

export const STATUS_STYLES: Record<ApplicationStatus, string> = {
  DRAFT: 'bg-brand-lime/10 text-brand-lime border border-brand-lime/30',
  SUBMITTED: 'bg-brand-lime/10 text-brand-lime border border-brand-lime/30',
  UNDER_REVIEW: 'bg-blue-500/15 text-blue-300 border border-blue-400/40',
  INSPECTION_SCHEDULED: 'bg-blue-500/15 text-blue-300 border border-blue-400/40',
  INSPECTED: 'bg-blue-500/15 text-blue-300 border border-blue-400/40',
  APPROVED: 'bg-emerald-500/15 text-emerald-300 border border-emerald-400/40',
  PAYMENT_PENDING: 'bg-amber-500/15 text-amber-300 border border-amber-400/40',
  PAID: 'bg-emerald-500/15 text-emerald-300 border border-emerald-400/40',
  ISSUED: 'bg-brand-lime text-brand-purple border border-brand-lime',
  RETURNED_FOR_CORRECTION: 'bg-orange-500/15 text-orange-300 border border-orange-400/40',
  REJECTED: 'bg-red-500/15 text-red-300 border border-red-400/40',
};

export const STATUS_LABELS: Record<ApplicationStatus, string> = {
  DRAFT: 'Draft',
  SUBMITTED: 'Submitted',
  UNDER_REVIEW: 'Under review',
  INSPECTION_SCHEDULED: 'Inspection scheduled',
  INSPECTED: 'Inspected',
  APPROVED: 'Approved',
  PAYMENT_PENDING: 'Payment pending',
  PAID: 'Paid',
  ISSUED: 'Issued',
  RETURNED_FOR_CORRECTION: 'Returned for correction',
  REJECTED: 'Rejected',
};

export interface Paginated<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

export interface RegionInfo {
  region: string;
  lga_count: number;
}

export interface LGA {
  id: number;
  name: string;
  region: string;
  code: string;
  licence_type_count: number;
}

export interface Requirement {
  id: number;
  name: string;
  kind: 'DOCUMENT' | 'INSPECTION' | 'CLEARANCE';
  kind_display: string;
  is_mandatory: boolean;
  order: number;
}

export type LicenceCategory = 'BUSINESS' | 'DRIVING' | 'GENERAL';

export interface LicenceType {
  id: number;
  name: string;
  code: string;
  category: LicenceCategory;
  description: string;
  fee: string;
  validity_months: number;
  requires_inspection: boolean;
  lga: number;
  lga_name: string;
  requirements: Requirement[];
}

export interface BusinessDocument {
  id: number;
  business: number;
  kind: 'TIN_CERTIFICATE' | 'BRELA_CERTIFICATE' | 'LEASE_AGREEMENT' | 'OTHER';
  kind_display: string;
  file: string;
  uploaded_at: string;
}

export interface BusinessLocation {
  id: number;
  business: number;
  lga: number;
  lga_name: string;
  ward: string;
  street: string;
  plot_number: string;
  is_primary: boolean;
}

export interface Business {
  id: number;
  name: string;
  owner: number;
  owner_name: string;
  tin_number: string;
  brela_registration_number: string;
  sector: string;
  is_verified: boolean;
  locations: BusinessLocation[];
  documents: BusinessDocument[];
}

export interface ApplicationDocument {
  id: number;
  application: number;
  requirement: number | null;
  requirement_name: string | null;
  file: string;
  uploaded_at: string;
  verified: boolean;
}

/** One entry of the application's audit trail (status timeline). */
export interface StatusHistoryEntry {
  from_status: ApplicationStatus;
  to_status: ApplicationStatus;
  changed_by_name: string;
  note: string;
  changed_at: string;
}

export interface Application {
  id: number;
  reference_number: string;
  applicant: number;
  applicant_name: string;
  business: number;
  business_name: string;
  business_is_verified: boolean;
  licence_type: number;
  licence_type_name: string;
  lga_name: string;
  location: number;
  status: ApplicationStatus;
  priority: 'NORMAL' | 'URGENT';
  purpose_statement: string;
  rejection_reason: string;
  allowed_next_statuses: ApplicationStatus[];
  documents: ApplicationDocument[];
  history: StatusHistoryEntry[];
  created_at: string;
  submitted_at: string | null;
  decided_at: string | null;
}

export interface Inspection {
  id: number;
  application: number;
  application_reference: string;
  inspector: number;
  inspector_name: string;
  scheduled_for: string;
  conducted_at: string | null;
  findings: string;
  passed: boolean | null;
}

export interface Invoice {
  id: number;
  application: number;
  application_reference: string;
  licence_type_name: string;
  business_name: string;
  control_number: string;
  amount: string;
  currency: string;
  status: 'PENDING' | 'WAITING_PAYMENT' | 'PAID' | 'CANCELLED' | 'EXPIRED';
  amount_paid: string;
  is_fully_paid: boolean;
  payments: unknown[];
}

export interface Licence {
  id: number;
  licence_number: string;
  application: number;
  application_reference: string;
  business_name: string;
  licence_type: number;
  licence_type_name: string;
  lga: number;
  lga_name: string;
  status: 'ACTIVE' | 'EXPIRED' | 'RENEWAL_PENDING' | 'REVOKED';
  issued_at: string;
  valid_from: string;
  valid_until: string;
  days_until_expiry: number;
  is_expired: boolean;
  qr_payload: string;
}

export interface NewBusinessPayload {
  name: string;
  tin_number: string;
  brela_registration_number: string;
  sector: string;
  location: {
    lga: number;
    ward: string;
    street: string;
    plot_number: string;
  };
}
