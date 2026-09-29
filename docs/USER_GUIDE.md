# e-Leseni User Guide — Business Owner

**From first visit to a verified business, step by step.**

This guide walks a business owner through everything they need to do on the
e-Leseni platform — from opening the website for the first time until their
business shows the **Verified** status (TRA TIN ✓ + BRELA registration ✓ +
NIDA ✓).

> 💡 You do **not** need to visit any government office. e-Leseni submits your
> details to BRELA and TRA for you, and the street letter is uploaded as a PDF
> scan. Everything happens online — including from a basic phone via USSD.

---

## What you need before you start

Have these ready to make the process smooth:

| # | Requirement | Where to get it |
|---|-------------|-----------------|
| 1 | **National ID (NIDA) number** — 20 digits | Your NIDA card |
| 2 | **A PDF scan of your national ID** | Scan or photograph the card, save as PDF |
| 3 | **Phone number** (for SMS updates) | Your phone |
| 4 | **Street identification letter** (PDF) | From your mtaa/street chairman |
| 5 | Business details — name, sector, ward, street | Your own records |

> 📄 All uploads must be **PDF files** (up to ~10 MB). Images and other
> formats are rejected, exactly like at a real council counter.

---

## Step 1 — Visit the website

1. Open your browser and go to the e-Leseni site (for local development:
   `http://localhost:4200`).
2. On the landing page you will see:
   - **Get Started** — creates a new account (use this if you are new).
   - **Log in** — for people who already have an account.

---

## Step 2 — Create your account

1. Click **Get Started** (or go directly to `/register`).
2. Fill in the registration form:
   - First name and last name
   - Username (your login name)
   - Email address
   - Phone number — *you will receive SMS status updates on this number*
   - **NIDA number** — 20 digits from your national ID
   - Password, then confirm the password
3. Submit the form.
4. Your account is created with the role **Applicant** and you land on your
   **Dashboard**.

> ⚠️ The NIDA number matters. Without it you cannot register a business, and
> no licence can be approved for you. If you skipped it, add it later under
> **Profile**.

---

## Step 3 — Your dashboard

After logging in you land on the dashboard, which shows:

- An **onboarding checklist** — your personal to-do list:
  1. ☐ Register your business with BRELA
  2. ☐ Get your TIN from TRA
  3. ☐ Get verified (TRA + BRELA check)
  4. ☐ Apply for your first LGA licence
  5. ☐ Receive your licence
- **Stats** — active applications, invoices awaiting payment, active licences.
- A **+ New application** shortcut for when you are ready to apply for a licence.

Each checklist item has a button that takes you to the right page. The next
section covers the first three items — the business registration wizard.

---

## Step 4 — Register your business (the 5-step wizard)

Open **My businesses** from the navigation (or click *Start registration* on
the checklist), then click **+ Register a business**.

The wizard guides you through 5 screens: **Details → BRELA → NIDA → Location
→ Submit**.

### 4.1 — Business details (step 1)
- Enter the **business name**, **sector**, and other basic details.
- Click **Continue to BRELA →**.
- e-Leseni tells you what happens next: it registers this name with **BRELA**
  (step 2) and applies for a **TIN at TRA** (step 3) — you do not need to
  visit either office.

### 4.2 — BRELA registration (step 2)
- Read the explainer: **BRELA — Business Registrations and Licensing Agency**.
- Click **Register with BRELA →**.
- When it succeeds you see **"BRELA — Registration confirmed"** with your
  **registration number** (starts with `1`), saved on your business
  automatically. This replaces the BRELA ORES form.

### 4.3 — TRA TIN + NIDA (step 3)
- Read the explainer: **TRA — Tanzania Revenue Authority**. TRA issues TINs
  against a national ID, exactly like the real ITAX form.
- Provide:
  - Your **NIDA number** (20 digits)
  - A **PDF copy of your national ID** — click *Choose PDF file* to attach it
- Click **Apply for TIN →**.
- When approved you see **"TRA — TIN approved"** with your new **TIN number**.
  The NIDA is also recorded on your profile automatically
  ("NIDA — Identity recorded").

### 4.4 — Street identification letter (step 4)
- Attach the **street identification letter** — the letter from your
  mtaa/street chairman that confirms where the business operates and carries
  your NIDA number (**PDF only**).
- This letter is **mandatory**: the council requires it before any licence
  can be approved, and business verification cannot run without it.
- Click **Continue to location →**.

### 4.5 — Location & submit (step 5)
- Choose the **region**, **council (LGA)**, **ward**, and **street** where the
  business operates, plus the plot number if you have one.
- The summary shows your BRELA number, TIN, and "NIDA verified".
- Click the final submit button. e-Leseni then:
  1. Creates the business record,
  2. Uploads your street ID letter,
  3. **Runs verification with TRA, BRELA and NIDA automatically**.
- You will see **"Business registered"** and a verification message:
  - ✅ *"Verified with TRA, BRELA and NIDA — your business is trusted."*
  - ⚠️ or *"Verification did not pass — officers will see this business as
    unverified."* (see Step 6 to fix it)

---

## Step 5 — Check the business is Verified

On the **My businesses** page each business card shows:

- **Verified** badge (when TRA + BRELA + NIDA all passed)
- TIN and BRELA numbers
- Its location (ward, street, council)

If the business is **not** verified yet, click **Verify with TRA & BRELA** on
its card to run the checks again.

### Verification checklist — all four must be true

| Check | Why |
|-------|-----|
| NIDA number on your profile | Proves who owns the business |
| TIN from TRA | Proves you are tax-registered |
| BRELA registration number | Proves the business legally exists |
| Street ID letter uploaded | Proves where the business operates |

> ❌ **Verification failed or blocked?** Common causes and fixes:
> - *No street identification letter* → use **Upload document** on the
>   business card and pick the kind *Street identification letter*.
> - *Missing TIN or BRELA number* → finish the wizard first (steps 2–3).
> - *No NIDA on your profile* → add it under **Profile**.
> - Any extra supporting documents (lease agreement, TIN certificate, etc.)
>   can be attached with **Upload document** as well.

---

## Step 6 — What "Verified" unlocks

Once your business shows the verified badge you can:

- **Apply for an LGA licence** — go to **Apply** (the *Apply now* checklist
  button takes you there):
  1. Choose your **council** and the **licence type** you need.
  2. Choose your **business** and **premises (location)**.
  3. Upload every **mandatory document** listed for that licence type (PDF).
  4. **Submit** the application — you get an SMS with a reference number.
- Track the application as the council processes it:
  **Submitted → Under review → Inspection scheduled → Inspected → Approved →
  Payment pending → Paid → Issued**. You receive an SMS at every change.
- Pay the invoice using the **GePG control number** sent to you by SMS
  (mobile money, bank, or any authorised agent).
- Download your **QR-verifiable licence certificate** (PDF) from the
  dashboard.

> 🔎 Anyone can scan the QR code on your licence — it opens a public
> verification page showing whether the licence is genuine and current. No
> account needed.

---

## Quick reference — the full journey

```
Visit site → Create account (with NIDA)
    → My businesses → + Register a business (wizard)
        → Step 1: Business details
        → Step 2: BRELA registration        → BRELA number ✓
        → Step 3: TRA TIN (+ NIDA + ID copy PDF) → TIN ✓
        → Step 4: Street ID letter (PDF)
        → Step 5: Location + Submit
                                   → auto-verification runs
    → BUSINESS VERIFIED ✓ (badge on My businesses)
    → Apply for a licence → upload documents → submit
    → Officer review → Inspection → Approval
    → Invoice + GePG control number (by SMS) → Pay
    → Licence issued → download PDF certificate with QR
```

---

## Troubleshooting & FAQ

**I did not receive any SMS.**
Check that the phone number on your **Profile** is correct. SMS updates are
sent at every status change.

**My upload is rejected.**
Only **PDF** files are accepted, up to about 10 MB. Convert photos to PDF
before uploading.

**Can I use e-Leseni without a smartphone?**
Yes. Dial **\*152*00#** (USSD) to apply and check your application status
from any phone.

**My business is missing / belongs to another account.**
Businesses belong to the account that created them. Log in with the account
you used during registration, or contact your council administrator.

**Where do I see my TIN applications?**
**My businesses** page → **TRA TIN applications** section shows every TIN
application with its status and result.

**Do I have to verify manually every time?**
No. Verification runs automatically at the end of the wizard. The
**Verify with TRA & BRELA** button is only for re-running the check if
something was missing the first time.
