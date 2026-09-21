# e-Leseni Demo Walkthrough

The complete journey from **first-time registration** to **issued licence**, showing
what each role sees and does at every step.

---

## The big picture

```
 APPLICANT                OFFICER              INSPECTOR            APPROVER
 ─────────                ───────              ─────────            ────────
 1. Register account
 2. Register business ──► (TRA/BRELA auto-verify)
 3. Apply for licence
    + upload documents
    + submit ────────────► 4. Start review
                           5. Schedule
                              inspection ─────► 6. Conduct inspection,
                                                record pass/fail
                                                (or reject) ──────► 7. Approve
                                                                    8. Trigger invoice
                           System: GePG control number issued automatically
 APPLICANT pays via control number
                           System: licence issued automatically (QR-verifiable)
```

**Roles only touch their own step.** The backend enforces the matrix below —
a 403 is returned if a role tries to do someone else's job:

| Action | APPLICANT | OFFICER | INSPECTOR | APPROVER | ADMIN |
|---|---|---|---|---|---|
| Submit own draft/resubmit | ✅ | — | — | — | ✅ |
| Start review, return, reject | — | ✅ | — | — | ✅ |
| Schedule inspection | — | ✅ | ✅ (self) | — | ✅ |
| Record inspection result | — | — | ✅ | — | ✅ |
| Approve / trigger invoice | — | — | — | ✅ | ✅ |
| See other LGAs' applications | — | — | — | — | ✅ |

---

## Part 1 — First-time registration (Applicant)

### 1a. Create an account
- Go to **Get started** → fill in name, username, email, phone, password.
- Phone number matters: **every status change sends an SMS to this number.**

### 1b. Register the business (BRELA + TRA)
On the **Apply** page, step 3, choose *“+ Register a new business”*:

| Field | What happens |
|---|---|
| TRA TIN | Checked against the **TRA adapter** (mock in dev: 9–12 digits pass) |
| BRELA registration no. | Checked against the **BRELA adapter** (mock in dev: starts with `1` passes) |

- Provide **both numbers** → the system verifies them **automatically when the
  business is created** and marks the business **`verified ✓`**.
- Provide neither (informal business) → business is created **`unverified`** —
  you can still apply, but officers will see the “unverified” badge during review.
- The verification calls are logged in the `IntegrationLog` table
  (visible in Django admin under *Integrations*).

**Demo proof:** `POST /api/businesses/` with `tin_number: "123456789"`,
`brela_registration_number: "102345678"` → response contains `"is_verified": true`.

### 1c. Choose the location
- **Region → Council → Ward** cascade. Wards come from the
  `tanzaniageodata` dataset (2,900+ wards seeded into the DB), so you pick
  “Kariakoo” from a dropdown instead of typing it.

---

## Part 2 — Apply for the LGA licence (Applicant)

The apply form is a 5-step wizard:

1. **Where?** Region → Council (e.g. Dar es Salaam → Ilala).
2. **What licence?** Category (Business/Driving/Other) → licence card showing
   **fee, validity, and whether premises inspection is required**.
3. **Business details** — pick an existing business (verified ✓ badge shown)
   or register a new one (step 1b).
4. **Required documents** — the checklist is generated **from the licence
   type's requirements** in the DB. Example, Food Vendor Licence (Ilala):
   - 📎 *Food Handling Permit* — **\*required**
   - 📎 *Premises Inspection* — inspection-type (not a file upload)
   - Optional documents are marked *(optional)*.
   - File inputs accept PDF/JPG/PNG ≤ 10 MB; each upload is tied to its
     requirement via `POST /api/applications/{id}/upload_document/`.
5. **Purpose & submit** — the **Submit button stays disabled until every
   mandatory document is attached**. The backend re-checks this on the
   submit transition and answers `400 Missing required documents: …` if
   the frontend is bypassed.

**Demo proof:** submit a draft without documents →
`{"detail": "Missing required documents: Food Handling Permit. Upload them before submitting."}`

---

## Part 3 — What staff see (role by role)

Log in as each demo user (password `Demo@1234`) — **each lands on their own
workspace** and sees only their stage:

### officer1 — Review queue (`/staff/review`)
- Sees **SUBMITTED** applications in **their LGA only** (Ilala).
- Each card shows:
  - `verified ✓` / `unverified` **business badge** (from the TRA/BRELA check),
  - applicant, licence type, purpose statement,
  - **📎 chips for every attached document** — click to open the uploaded file,
    or “⚠ No documents attached” warning.
- Actions: **Start review** → applicant is auto-assigned to this officer,
  SMS sent. Officer can also **Return for correction** (with note) or **Reject**.
- On UNDER_REVIEW applications: **🗓 Schedule inspection** (date-time picker) —
  creates the Inspection record and moves the application to
  INSPECTION_SCHEDULED.

### inspector1 — Inspection queue (`/staff/inspections`)
- Sees **INSPECTION_SCHEDULED** applications for their LGA, with the scheduled
  date and inspector name.
- Actions: **Record result — passed** (→ INSPECTED) or **Failed — reject**.
- Cannot see review-stage applications, cannot approve (403).

### approver1 — Approval queue (`/staff/approvals`)
- Sees **INSPECTED** applications.
- Actions: **✓ Approve**, **Return for correction**, or **Reject**.
- On APPROVED applications: **→ Invoice** moves it to PAYMENT_PENDING, which
  fires the payments signal: an invoice is created and a **GePG control
  number** is requested automatically.

### admin — Administration (`/staff/admin`)
- Sees **everything, all LGAs**, grouped by stage tabs
  (Needs review / Inspections / Approvals / Payments).
- Can perform any transition.

---

## Part 4 — Payment & licence (back to the Applicant)

1. Applicant's dashboard shows the invoice with the **GePG control number**.
2. Click **Pay** (mock GePG reconciles instantly) → application → PAID →
   **licence issued automatically** with number `LIC-<TYPE>-<YEAR>-#####`.
3. The licence card shows the QR payload; scanning the QR hits the public
   `GET /api/licences/verify/{token}/` endpoint, which anyone can use to
   confirm the licence is genuine and current.

---

## Quick demo script (5 minutes)

```bash
# 1. Seed (creates LGAs, wards, licences, users, pipeline applications)
python manage.py seed_demo_data

# 2. Run backend + frontend
python manage.py runserver          # http://localhost:8000
npm start                           # http://localhost:4200

# 3. Walk the journey in the browser:
#    - register applicant1's flow: /apply → new business (TIN 123456789,
#      BRELA 102345678) → watch it come back verified ✓
#    - pick Ilala → Business → Food Vendor Licence → upload the permit → submit
#    - log out, log in as officer1  → land on /staff/review → Start review
#      → Schedule inspection
#    - log in as inspector1        → Record result — passed
#    - log in as approver1         → ✓ Approve → → Invoice
#    - log in as applicant1        → dashboard → Pay invoice → licence issued!
```
