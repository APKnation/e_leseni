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

export interface LGA {
  id: number;
  name: string;
  region: string;
  code: string;
}

export interface Requirement {
  id: number;
  name: string;
  kind: 'DOCUMENT' | 'INSPECTION' | 'CLEARANCE';
  kind_display: string;
  is_mandatory: boolean;
  order: number;
}

export interface LicenceType {
  id: number;
  name: string;
  code: string;
  description: string;
  fee: string;
  validity_months: number;
  requires_inspection: boolean;
  lga: number;
  lga_name: string;
  requirements: Requirement[];
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
  documents: unknown[];
}

export interface Application {
  id: number;
  reference_number: string;
  applicant: number;
  applicant_name: string;
  business: number;
  business_name: string;
  licence_type: number;
  licence_type_name: string;
  lga_name: string;
  location: number;
  status: ApplicationStatus;
  priority: 'NORMAL' | 'URGENT';
  purpose_statement: string;
  rejection_reason: string;
  allowed_next_statuses: ApplicationStatus[];
  documents: unknown[];
  created_at: string;
  submitted_at: string | null;
  decided_at: string | null;
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
