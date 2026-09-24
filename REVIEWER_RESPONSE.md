# Response to Reviewers 2 & 3 — e-Leseni national-deployment readiness

Each point below is split into **[Implemented in the demo]** — verifiable in this repository —
and **[Production roadmap]** — what changes for national rollout. File paths refer to this codebase
so claims can be checked directly.

---

## Reviewer 2
e-leseni presents a timely, highly practical e-governance platform closing the digital gap between central government business registration and municipal licensing. To refine this system for national deployment, the design is structured so that every claim below is either **verified in this repository** or a **named production roadmap item** (with file path), so a reviewer can check the implementation directly rather than relying on documentation.

### eGA GovESB / Interoperability integration (BRELA, TRA, GePG)

#### [Implemented in the demo]

The platform already routes every outbound government call through a single **anti-corruption adapter layer** (`backend/integrations/adapters.py`) — the seam GovESB plugs into. Nothing in business logic touches an endpoint directly:

- **Typed service adapters** — one small surface per institution: `BRELAdapter.verify_registration()`, `TRAAdapter.verify_tin()`, `GePGAdapter.request_control_number()` / `reconcile_payment()`. Adding a new government service means writing one adapter + one mock, not touching the core flow.
- **Config-driven endpoints** — `INTEGRATIONS = {'BRELA_BASE_URL': …, 'TRA_BASE_URL': …, 'GEPG_BASE_URL': …}` in `backend/config/settings.py`. Zero hard-coded URLs; routing and credentials live in Django settings, so pointing at the GovESB gateway is a settings + credential change, not a rewrite.
- **Full audit trail** — every call persists to the `IntegrationLog` table (`backend/integrations/models.py`): system, direction, endpoint, request/response payloads, status code, error. Visible in Django admin under *Integrations*; this is the traceability backbone GovESB requires for governed message exchange.
- **Graceful degradation** — adapters return `AdapterResult(success, data, error)`; a failed BRELA/TRA check never blocks an informal-business application. It just flags it `unverified` for officer review, so the platform degrades in place instead of failing closed at the wrong layer.
- **GePG flow** — on `APPROVED → PAYMENT_PENDING` a signal (`backend/payments/signals.py`) creates the invoice idempotently and requests a **control number**; payment reconciliation drives `PAID → ISSUED` automatically. Idempotency on the GePG bill is what makes retries safe.
- **Mock parity** — each mock endpoint mirrors the real service contract (verify-tin, verify-registration, bill/reconcile), so the calling code is identical whether the endpoints are mock or production GovESB services.

#### [Production roadmap — conforming to eGA standards]

1. **Transport & routing.** Point `*_BASE_URL` at the eGA GovESB gateway (per eGA's *Criteria for Data Sharing and Exchange through GovESB*). Because mediation is centralised in `BaseAdapter._post()`, this is a settings + credential change, not a rewrite.
2. **Authentication.** Mutual TLS (mTLS) with eGA-issued client certificates at the gateway, plus per-institution service credentials stored in the platform secret store. Certificate rotation follows the existing settings pipeline.
3. **Message standards.** Adopt the e-Government Interoperability Framework (eGIF) schemas per service contract. The request/response field mapping lives in exactly one place per adapter, so each mapping is auditable in a single file. GovESB message IDs are correlated into `IntegrationLog` for end-to-end traceability.
4. **Resilience.** Celery (already in `requirements.txt`) queues asynchronous government calls with retry, dead-letter, and circuit-breaker semantics. GePG bill submission is idempotent per application so control numbers can never be duplicated across retries.
5. **Data protection.** NIDA/TIN data minimisation is enforced at the adapter boundary (the only place personal identifiers cross the platform), TLS in transit, encryption at rest, and retention rules aligned with the Personal Data Protection Act, 2022.
6. **Governance & monitoring.** `IntegrationLog` becomes the audit record for eGA compliance reviews; a health-check endpoint reports adapter status, last call times, and circuit states so the operations team can observe the bus before incidents.

### Configurable LGA bylaw engine (City vs Municipal vs District councils)

#### [Implemented in the demo]

Licensing content is **fully data-driven per council, zero hard-coded rules**:

- `LGA` → `LicenceType` is one-to-many (`backend/lga/models.py`): each council owns its own catalogue rows with its own **fee**, **validity_months**, and **requires_inspection** flag. Ilala's *Food Vendor Licence* and Temeke's are independent records (unique `(lga, code)`), so the same national template can diverge per council.
- `Requirement` rows per licence type define the **document checklist** with `kind = DOCUMENT | INSPECTION | CLEARANCE`, `is_mandatory`, and ordering. The applicant wizard renders it, and the backend **re-validates on submit** server-side (`400 Missing required documents: …`) — the frontend can never bypass the checklist.
- `OfficerAssignment` maps council staff to licence types with `can_review / can_inspect / can_approve`, so a small district council runs one person per stage while a city council runs dedicated teams.
- **Role scoping** is enforced server-side (403, not UI-only): officers see **only their LGA's** applications; admins see all (matrix in `DEMO_WALKTHROUGH.md`).
- `Ward` lookup feeds the region → council → ward cascade from the same `tanzaniageodata` dataset used to seed LGAs, so every council's geography is driven by one source of truth.

#### [Production roadmap — council-tier configurability]

1. **Council tiers.** Add a `tier` attribute (`CITY / MUNICIPAL / TOWN / DISTRICT`) to `LGA`, then a **template + override** model: nationally standard licence templates (e.g. Food Vendor) publish default fees and checklists per tier; each council overrides under its own bylaws. Today every row is independent — correct for autonomy, but 180+ councils need bulk seeding.
2. **Versioned fee schedules.** Effective-dated licence types (fiscal-year fees) with an immutable change log, so applications are always billed under the schedule in force at submission — a council cannot retroactively raise a fee on an approved application.
3. **Per-licence-type inspection checklists.** Replace free-text findings with configurable `InspectionChecklistItem` rows per licence type: a city council's food inspection carries different items than a rural district's, while the workflow engine stays uniform.
4. **Bylaw references.** Each licence type links to its enabling bylaw document, shown to applicants and officers alongside the requirement list.
5. **Council-specific officer permissions** — a single `OfficerAssignment` row per officer × licence type, so a rural district council can staff one person per stage while a city council runs dedicated teams; the `can_review / can_inspect / can_approve` flags make the staffing model configurable without code changes.

### Digital certificate verification (dynamic QR for field enforcement)

#### [Implemented in the demo]

- Every issued licence gets a **cryptographically random token** (`secrets.token_urlsafe(32)`, `backend/licences/models.py`) and QR payload resolving to the **public, unauthenticated** endpoint `GET /api/licences/verify/{token}/` (`backend/licences/views.py`).
- The endpoint returns a verdict any officer can act on: `valid`, `licence_number`, business, licence type, issuing LGA, status (`ACTIVE / EXPIRED / REVOKED / RENEWAL_PENDING`), validity dates, and `checked_at`. `is_expired` is computed server-side and is **never trusted from the card** — the badge is self-checking.
- Covered by tests: valid licence, expired licence, and unknown-token forgery attempts (`backend/licences/tests.py`).
- No holder PII is exposed on the public endpoint — only business-level data — so verification stays safe to surface in the field.

#### [Production roadmap — verifiable security features]

1. **Signed claims (offline verification).** Embed licence claims in a JWS signed by the issuer's private key inside the QR. Field officers in poor connectivity verify the signature against a cached public key, then reconcile with the server when back online.
2. **Dynamic anti-photocopy QR.** The printed deep-link token stays static for citizens, while a companion **rotating QR** (HMAC over time slices, refreshed every few minutes on the licence page / printed certificate) proves a live artefact — a photocopy fails the freshness check even though it scans.
3. **Officer verification app flow.** Scan → licence card + premises photo + issuing LGA → one-tap **Report mismatch**, which flags the licence for the revocation workflow (`REVOKED` + `revoked_reason` already exist on the model).
4. **Privacy & abuse controls.** Rate limiting on the public verification endpoint plus verification analytics on the enforcement dashboard, so it cannot be scanned at scale to harvest business data.
5. **Certificate lifecycle.** `REVOKED` + `revoked_reason` already exist on the licence model and are returned by the verification endpoint, so a revoked licence fails instantly at the field level.

## Reviewer 3
Outline security measures (such as geotagged inspection signatures or time-stamped photo proofs) to ensure field inspections are conducted transparently.

#### [Implemented in the demo]

- Inspections are first-class records (`backend/applications/models.py`): inspector identity, `scheduled_for`, server-stamped `conducted_at`, findings, pass/fail.
- Every status transition writes an immutable **`StatusHistory`** audit row with actor and note — the full timeline is visible to the applicant and staff.
- The server enforces the role matrix (an inspector cannot approve; officers cannot see other LGAs' work) — 403, not UI-only.

#### [Production roadmap — field-proof capture]

1. **Geotagged result submission.** Record GPS latitude / longitude + accuracy at the moment the inspector records the result; compare against the geocoded registered premises (`BusinessLocation`) and **flag** large discrepancies for supervisor review. This is a soft-flag, not a hard block — rural GPS can be poor — so it surfaces anomalies for human review rather than denying inspectors the ability to work.
2. **Time-stamped photo evidence.** `InspectionPhoto` records the required photo set per checklist, the client capture time **plus the server receipt time**, a SHA-256 content hash, and EXIF extraction. Photos are hash-chained per inspection so evidence cannot be swapped after the fact.
3. **Inspector e-signature.** Result submission requires the inspector's PIN/biometric; store the signature hash with a device fingerprint. `conducted_at` is set server-side, so a manipulated device clock cannot forge timing.
4. **Anti-collusion design.** Random assignment among eligible inspectors (`can_inspect` in `OfficerAssignment`), a rotation policy, and a conflict-of-interest declaration before conducting an inspection.
5. **Offline-first capture.** Inspections queue on-device in the field and sync later with monotonic sequence numbers and server-side dedupe — critical for district councils with poor connectivity.
6. **Immutable audit.** All of the above lands in the same append-only audit pattern as `StatusHistory` / `IntegrationLog`, reviewable by council leadership and audit bodies. No field record can be silently edited after submission.

---

### [Implemented in the demo]

All outbound government calls already funnel through a single **anti-corruption adapter layer**
(`backend/integrations/adapters.py`), which is the seam GovESB plugs into:

| Concern | Where it lives today |
|---|---|
| Typed service adapters | `BRELAdapter.verify_registration()`, `TRAAdapter.verify_tin()`, `GePGAdapter.request_control_number()` / `reconcile_payment()` — one small surface per institution |
| Config-driven endpoints | `INTEGRATIONS = {'BRELA_BASE_URL': …, 'TRA_BASE_URL': …, 'GEPG_BASE_URL': …}` in `backend/config/settings.py`. No endpoint is hard-coded in business logic |
| Full audit trail | Every call is persisted to the `IntegrationLog` table (`backend/integrations/models.py`): system, direction, endpoint, request/response payloads, status code, error — visible in Django admin under *Integrations* |
| Graceful degradation | Adapter calls return `AdapterResult(success, data, error)`; a failed BRELA/TRA check never blocks an informal-business application, it just flags it `unverified` for officer review |
| GePG flow | On `APPROVED → PAYMENT_PENDING` a signal (`backend/payments/signals.py`) creates the invoice idempotently and requests a **control number**; payment reconciliation drives `PAID → ISSUED` automatically |
| Mock parity | Each mock endpoint mirrors the real service contract (verify-tin, verify-registration, bill/reconcile), so swapping base URLs does not change calling code |

### [Production roadmap — conforming to eGA standards]

1. **Transport & routing.** Point `*_BASE_URL` at the GovESB gateway (per eGA's *Criteria for
   Data Sharing and Exchange through GovESB*). Because mediation is centralised in `BaseAdapter._post()`,
   this is a settings + credential change, not a rewrite.
2. **Authentication.** Mutual TLS with eGA-issued client certificates at the gateway, plus
   per-institution service credentials stored in the platform secret store; certificates rotated
   via the existing settings pipeline.
3. **Message standards.** Adopt the e-Government Interoperability Framework schemas per service
   contract (request/response field mapping lives in exactly one place per adapter); correlate
   GovESB message IDs into `IntegrationLog` for end-to-end traceability.
4. **Resilience.** Celery (already in `requirements.txt`) queues asynchronous calls with retry,
   dead-letter, and circuit-breaker semantics; GePG bill submission is made idempotent per
   application so control numbers can never be duplicated across retries.
5. **Data protection.** NIDA/TIN data minimisation, TLS in transit, encryption at rest, and
   retention rules aligned with the Personal Data Protection Act, 2022 — enforced at the
   adapter boundary where all personal identifiers cross the platform.

## Configurable LGA bylaw engine (City vs Municipal vs District councils)

#### [Implemented in the demo]

Licensing content is **fully data-driven per council, zero hard-coded rules**:

- `LGA` → `LicenceType` is one-to-many (`backend/lga/models.py`): each council owns its own
  catalogue rows with its own **fee**, **validity_months**, and **requires_inspection** flag.
  Ilala's *Food Vendor Licence* and Temeke's are independent records (unique `(lga, code)`).
- `Requirement` rows per licence type define the **document checklist** with
  `kind = DOCUMENT | INSPECTION | CLEARANCE`, `is_mandatory`, and ordering. The applicant wizard
  renders it, and the backend **re-validates on submit** server-side
  (`400 Missing required documents: …`) so the frontend can never be bypassed.
- `OfficerAssignment` maps council staff to licence types with `can_review / can_inspect / can_approve`,
  so a small district council can staff one person per stage while a city council runs dedicated teams.
- Role scoping ensures officers see **only their LGA's** applications; admins see all (403 matrix in `DEMO_WALKTHROUGH.md`).

#### [Production roadmap — council-tier configurability]

1. **Council tiers.** Add a `tier` attribute (CITY / MUNICIPAL / TOWN / DISTRICT) to `LGA`, then a
   **template + override** model: nationally standard licence templates (e.g. Food Vendor) publish
   default fees/checklists per tier, which each council may override under its own bylaws.
   Today every row is independent — correct for autonomy, but 180+ councils need bulk seeding.
2. **Versioned fee schedules.** Effective-dated licence types (fiscal-year fees) with an immutable
   change log, so applications are always billed under the schedule in force at submission.
3. **Per-licence-type inspection checklists.** Replace free-text findings with configurable
   `InspectionChecklistItem` rows per licence type — a city council's food inspection carries
   different items than a rural district's, while the workflow engine stays uniform.
4. **Bylaw references.** Each licence type links to its enabling bylaw document, shown to
   applicants and officers alongside the requirement list.

## Digital certificate verification (dynamic QR for field enforcement)

### [Implemented in the demo]

- Every issued licence gets a cryptographically random token (`secrets.token_urlsafe(32)`,
  `backend/licences/models.py`) and QR payload resolving to the **public, unauthenticated**
  endpoint `GET /api/licences/verify/{token}/` (`backend/licences/views.py`).
- The endpoint returns a verdict any officer can act on: `valid`, `licence_number`, business,
  licence type, issuing LGA, status (ACTIVE / EXPIRED / **REVOKED** / RENEWAL_PENDING), validity
  dates, and `checked_at` — plus `is_expired` computed server-side, never trusted from the card.
- Covered by tests: valid licence, expired licence, and unknown-token forgery attempts
  (`backend/licences/tests.py`).

### [Production roadmap — verifiable security features]

1. **Signed claims (offline verification).** Embed licence claims in a JWS signed by the issuer's
   private key inside the QR; field officers with poor connectivity verify the signature against a
   cached public key, then reconcile with the server when back online.
2. **Dynamic anti-photocopy QR.** The printed deep-link token stays static for citizens, while a
   companion **rotating QR** (HMAC over time slices, refreshed every few minutes on the licence
   page/printed certificate) proves a *live* artefact — a photocopy fails the freshness check even
   though it scans.
3. **Officer verification app flow.** Scan → licence card + premises photo + issuing LGA → one-tap
   **Report mismatch**, which flags the licence for the revocation workflow (`REVOKED` +
   `revoked_reason` already exist on the model).
4. **Privacy & abuse controls.** The public endpoint exposes business-level data only (no holder
   PII), with rate limiting and verification analytics for enforcement dashboards.

---

## R3 — Transparency & integrity of field inspections

### [Implemented in the demo]

- Inspections are first-class records (`backend/applications/models.py`): inspector identity,
  `scheduled_for`, server-stamped `conducted_at`, findings, pass/fail.
- Every status transition writes an immutable **`StatusHistory`** audit row with actor and note —
  the full timeline is visible to the applicant and staff.
- The server enforces the role matrix (an inspector cannot approve; officers cannot see other
  LGAs' work) — 403, not UI-only.

### [Production roadmap — field-proof capture]

1. **Geotagged result submission.** Record GPS lat/long + accuracy at the moment the inspector
   records the result; compare against the geocoded registered premises (`BusinessLocation`) and
   **flag** large discrepancies for supervisor review (soft-flag, not hard-block — rural GPS can be poor).
2. **Time-stamped photo evidence.** `InspectionPhoto` records: required photo set per checklist,
   client capture time **plus server receipt time**, SHA-256 content hash, and EXIF extraction;
   photos are hash-chained per inspection so evidence cannot be swapped after the fact.
3. **Inspector e-signature.** Result submission requires the inspector's PIN/biometric; store the
   signature hash with a device fingerprint. `conducted_at` is set server-side, so a manipulated
   device clock cannot forge timing.
4. **Anti-collusion design.** Random assignment among eligible inspectors (`can_inspect` in
   `OfficerAssignment`), rotation policy, and a conflict-of-interest declaration before conducting
   an inspection.
5. **Offline-first capture.** Inspections queue on-device in the field and sync later with
   monotonic sequence numbers and server-side dedupe — critical for district councils.
6. **Immutable audit.** All of the above lands in the same append-only audit pattern as
   `StatusHistory`/`IntegrationLog`, reviewable by council leadership and audit bodies.
