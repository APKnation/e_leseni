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

/* Status chips follow the NVIDIA badge-tag: uppercase bold caption on a
   soft/semantic surface, 2px radius, hairline border, no rounded-full. */
export const STATUS_STYLES: Record<ApplicationStatus, string> = {
  DRAFT: 'bg-soft text-muted border border-hairline',
  SUBMITTED: 'bg-soft text-foreground border border-hairline',
  UNDER_REVIEW: 'bg-soft text-foreground border border-hairline-strong',
  INSPECTION_SCHEDULED: 'bg-soft text-foreground border border-hairline-strong',
  INSPECTED: 'bg-soft text-foreground border border-hairline-strong',
  APPROVED: 'bg-primary/15 text-success-deep border border-primary/40',
  PAYMENT_PENDING: 'bg-warning/10 text-warning border border-warning/40',
  PAID: 'bg-primary/15 text-success-deep border border-primary/40',
  ISSUED: 'bg-primary text-black border border-primary',
  RETURNED_FOR_CORRECTION: 'bg-warning/10 text-warning border border-warning/40',
  REJECTED: 'bg-danger/10 text-danger border border-danger/40',
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

/** A council-controlled business activity (the "kind of business" taxonomy). */
export interface BusinessActivity {
  id: number;
  code: string;
  name: string;
  description: string;
  icon: string;
  order: number;
  is_active?: boolean;
  licence_type_count?: number;
}

/** Writable fields of a business activity (staff management UI). */
export interface BusinessActivityPayload {
  code: string;
  name: string;
  description?: string;
  icon?: string;
  order?: number;
  is_active?: boolean;
}

export interface LicenceType {
  id: number;
  name: string;
  code: string;
  category: LicenceCategory;
  activity: number | null;
  activity_name: string | null;
  description: string;
  fee: string;
  validity_months: number;
  requires_inspection: boolean;
  bylaw_reference?: string | null;
  lga: number;
  lga_name: string;
  requirements: Requirement[];
}

export interface BusinessDocument {
  id: number;
  business: number;
  kind: 'TIN_CERTIFICATE' | 'BRELA_CERTIFICATE' | 'STREET_ID_LETTER' | 'LEASE_AGREEMENT' | 'OTHER';
  kind_display: string;
  file: string;
  uploaded_at: string;
}

/** One TRA + BRELA verification run — rejections keep their reasons. */
export interface VerificationAttempt {
  id: number;
  verified: boolean;
  tra_valid: boolean | null;
  tra_reason: string;
  brela_registered: boolean | null;
  brela_reason: string;
  created_at: string;
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
  owner_nida: string;
  nida_number: string;
  tin_number: string;
  brela_registration_number: string;
  sector: string;
  activity: number | null;
  activity_name: string | null;
  is_verified: boolean;
  has_street_id_letter: boolean;
  /** Why TRA/BRELA rejected the last verification (null when none/passed). */
  verification_note?: string | null;
  verification_attempts?: VerificationAttempt[];
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
  applicant_has_nida: boolean;
  business: number;
  business_name: string;
  business_is_verified: boolean;
  licence_type: number;
  licence_type_name: string;
  activity?: number | null;
  activity_name?: string | null;
  lga_name: string;
  location: number;
  status: ApplicationStatus;
  priority: 'NORMAL' | 'URGENT';
  purpose_statement: string;
  rejection_reason: string;
  allowed_next_statuses: ApplicationStatus[];
  documents: ApplicationDocument[];
  history: StatusHistoryEntry[];
  /** Licence number once a licence has been issued (tracking). */
  licence_number?: string | null;
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
  activity: number | null;
  location: {
    lga: number;
    ward: string;
    street: string;
    plot_number: string;
  };
}

/** A document attached to a TRA TIN application. */
export interface TINApplicationDocument {
  id: number;
  tin_application: number;
  kind: 'NIDA_COPY' | 'PASSPORT_PHOTO' | 'OTHER';
  kind_display: string;
  file: string;
  uploaded_at: string;
}

/** A TIN application submitted to TRA (demo workflow, with NIDA + ID copy). */
export interface TINApplication {
  id: number;
  business_name: string;
  taxpayer_name: string;
  nida_number: string;
  tin_number: string;
  status: 'PENDING' | 'APPROVED' | 'REJECTED';
  documents: TINApplicationDocument[];
  created_at: string;
  processed_at: string | null;
}
