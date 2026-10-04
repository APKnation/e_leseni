# e-Leseni (e-Licensing Platform for Tanzania LGAs)

[![Django](https://img.shields.io/badge/Django-5.0+-green.svg)](https://www.djangoproject.com/)
[![Angular](https://img.shields.io/badge/Angular-18-red.svg)](https://angular.dev/)
[![Tailwind CSS](https://img.shields.io/badge/Tailwind_CSS-v4-blue.svg)](https://tailwindcss.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15+-blue.svg)](https://www.postgresql.org/)

**e-Leseni** is an end-to-end digital licensing and revenue administration platform designed for Local Government Authorities (LGAs / Halmashauri) in Tanzania. It digitises the complete licensing journey: from inter-agency verification (BRELA, TRA, NIDA) to field inspections with GPS, council approvals, GePG electronic payments, and cryptographically verified digital licences with QR codes.

---

## 📖 Documentation Index

- **[Complete Project Flow & Architecture](docs/PROJECT_FLOW.md)**: Full technical breakdown of system architecture, state machines, actors, and workflows.
- **[Business Owner User Guide](docs/USER_GUIDE.md)**: Citizen walkthrough from account registration to licence issuance.

---

## 🏛️ The Complete System Flow

```
1. Register & NIDA Verification
   └── Citizen creates account with NIDA & phone number

2. Business Registration Wizard
   └── TRA TIN + BRELA Registration + Street ID Letter + Premises Location

3. Inter-Agency Verification
   └── Auto-verification with TRA, BRELA, and NIDA

4. Licence Application
   └── Select Council & Licence Type → Upload mandatory documents (PDF)

5. Council Workflow (Staff Area)
   ├── Licensing Officer: Reviews dossier, returns for correction, or schedules inspection
   ├── Field Inspector: Verifies physical premises via device GPS & records pass/fail findings
   └── Approver: Final statutory review & approval

6. Invoicing & GePG Payment
   └── Auto-invoice generation → GePG control number sent via SMS → Mobile Money / Bank settlement

7. Licence Issuance & QR Verification
   └── Digital licence issued → Public QR code verification portal (/verify) → PDF Certificate
```

---

## 👥 System Roles & Workspaces

| Role | Interface Route | Key Capabilities |
|------|-----------------|------------------|
| **Applicant** | `/dashboard`, `/businesses`, `/apply` | Register businesses, apply for licences, pay invoices, download licences. |
| **Licensing Officer** | `/staff/review` | Review queue, return for correction with instructions, schedule inspections, manage council licence catalog & activities. |
| **Field Inspector** | `/staff/inspections` | Inspection queue, capture device GPS location, submit pass/fail findings. |
| **Licensing Approver** | `/staff/approvals` | Review inspected applications, approve licences, initiate invoicing. |
| **System Admin** | `/staff/admin`, `/staff/users` | Full CRUD user management (create, edit, reset passwords, activate/deactivate staff per LGA), cross-council oversight. |

---

## 🔑 Demo Login Credentials

The database includes pre-seeded accounts for every role:

| Role | Username | Password | Council / Scope | Primary Workspace |
|------|----------|----------|-----------------|-------------------|
| **System Admin** | `admin` | `Demo@1234` | All LGAs (National) | `/staff/users` (User CRUD) & `/staff/admin` |
| **Licensing Officer** | `officer1` | `Demo@1234` | Ilala Municipal | `/staff/review` |
| **Field Inspector** | `inspector1` | `Demo@1234` | Ilala Municipal | `/staff/inspections` |
| **Licensing Approver** | `approver1` | `Demo@1234` | Ilala Municipal | `/staff/approvals` |
| **Applicant (Citizen 1)** | `applicant1` | `Demo@1234` | Citizen Owner | `/dashboard` & `/businesses` ("Mama Neema Foods") |
| **Applicant (Citizen 2)** | `applicant2` | `Demo@1234` | Citizen Owner | `/dashboard` & `/apply` ("Komba Hardware") |
| **Mufindi Officer** | `officer_mufindi` | `Demo@1234` | Mufindi DC (Iringa) | `/staff/review` |
| **Mufindi Inspector** | `inspector_mufindi` | `Demo@1234` | Mufindi DC (Iringa) | `/staff/inspections` |
| **Mufindi Approver** | `approver_mufindi` | `Demo@1234` | Mufindi DC (Iringa) | `/staff/approvals` |
| **Mufindi Applicant** | `applicant_mufindi` | `Demo@1234` | Mufindi Citizen | `/dashboard` ("Mufindi Highland Tea & Timber") |

---

## 🚀 Getting Started

### Prerequisites
- Python 3.12+
- Node.js 22+ & npm
- PostgreSQL

### 1. Backend Setup (Django + DRF)

```bash
cd backend

# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Run tests
python manage.py test

# Start backend server
python manage.py runserver
```

Backend API will be accessible at: `http://localhost:8000/api/`  
OpenAPI Documentation at: `http://localhost:8000/api/docs/`

### 2. Frontend Setup (Angular 18)

```bash
cd frontend/leseni

# Install dependencies
npm install

# Start development server
ng serve
```

Frontend application will be accessible at: `http://localhost:4200/`

---

## 📲 Omnichannel Access

- **Web Portal**: Full-featured responsive web application for desktop, tablet, and mobile.
- **USSD Gateway (`*152*00#`)**: Lightweight text-based interface allowing informal sector traders and citizens with basic feature phones to apply, check status, and request GePG payment control numbers.
- **SMS Notifications**: Automated SMS dispatch to applicants at every lifecycle milestone (receipt, review updates, inspection, approval, control number, payment confirmation, licence issuance).

---

## 🛡️ Security & Compliance

- **Cryptographic Licence Verification**: QR code payloads signed with SHA-256 HMAC tokens.
- **eGA Standards Compliance**: Aligned with Tanzania e-Government Authority (eGA) interoperability guidelines and GovESB standards.
- **Audit Trails**: Every state change recorded with timestamps, user credentials, and operational notes.
