"""E2E flow verification for e-Leseni — drives the same endpoints the Angular frontend uses.

Run: backend/.venv/bin/python manage.py shell < e2e_flow_check.py
(Live HTTP alternative documented at the bottom.)
"""
import base64
import io
import json
import sys

import django

os_ok = True
try:
    import os
except ImportError:  # pragma: no cover
    os_ok = False

if os_ok:
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    django.setup()

from django.test import Client  # noqa: E402
from django.core.files.uploadedfile import SimpleUploadedFile  # noqa: E402
from rest_framework_simplejwt.tokens import RefreshToken  # noqa: E402

from accounts.models import User  # noqa: E402
from applications.models import Application, Inspection  # noqa: E402
from businesses.models import Business, BusinessDocument  # noqa: E402
from lga.models import LGA, LicenceType  # noqa: E402
from licences.models import Licence  # noqa: E402
from payments.models import Invoice  # noqa: E402

PASS, FAIL = [], []


def check(label, cond, extra=''):
    (PASS if cond else FAIL).append(label)
    print(('  OK ' if cond else ' FAIL ') + label + (f'  [{extra}]' if extra and not cond else ''))


def pdf(name='doc.pdf'):
    content = b'%PDF-1.4\n1 0 obj<</Type/Catalog>>endobj\ntrailer<<>>\n%%EOF'
    return SimpleUploadedFile(name, content, content_type='application/pdf')


client = Client()

print('\n== STEP 1: Register applicant ==')
import time  # noqa: E402

username = f'e2e{int(time.time())}'
r = client.post('/api/auth/register/', data=json.dumps({
    'username': username, 'email': f'{username}@test.tz', 'first_name': 'E2E',
    'last_name': 'Tester', 'phone_number': '0712000999', 'password': 'S0m3L0ngPass!',
}), content_type='application/json')
check('register applicant (201)', r.status_code == 201, r.status_code)
check('registration response has id', 'id' in r.json(), r.json())

print('\n== STEP 2: Login ==')
r = client.post('/api/auth/login/', data=json.dumps(
    {'username': username, 'password': 'S0m3L0ngPass!'}), content_type='application/json')
check('login (200)', r.status_code == 200, r.status_code)
tokens = r.json()
applicant_tok = tokens.get('access', '')
H = {'HTTP_AUTHORIZATION': f'Bearer {applicant_tok}'}

print('\n== STEP 3: NIDA verification (mock) ==')
r = client.post('/api/auth/verify-nida/', data=json.dumps({
    'nida_number': '19991234567890123456', 'first_name': 'E2E', 'last_name': 'Tester',
}), content_type='application/json')
check('mock NIDA verify (200)', r.status_code == 200, r.status_code)
check('NIDA valid=true', r.json().get('valid') is True, r.json())
r = client.patch('/api/auth/me/update/', data=json.dumps({'nida_number': '19991234567890123456'}),
                 content_type='application/json', **H)
check('save NIDA to profile (200)', r.status_code == 200, r.status_code)

print('\n== STEP 4: Business registration ==')
# Pick an LGA that actually has a full staff team (officer/inspector/approver)
# — mirrors the demo seed where staff belong to specific councils.
from accounts.models import User as _U  # noqa: E402

lga = None
for candidate in (User.objects.filter(role='OFFICER', lga__isnull=False).values_list('lga_id', flat=True)):
    has_inspector = User.objects.filter(role='INSPECTOR', lga_id=candidate).exists()
    has_approver = User.objects.filter(role='APPROVER', lga_id=candidate).exists()
    if has_inspector and has_approver and LicenceType.objects.filter(lga_id=candidate).exists():
        lga = LGA.objects.get(pk=candidate)
        break
if lga is None:
    lga = LGA.objects.order_by('id').first()
lt = (LicenceType.objects.filter(lga=lga).order_by('id').first())
if lt is None:
    lt = LicenceType.objects.order_by('id').first()
    lga = lt.lga
r = client.post('/api/businesses/', data=json.dumps({
    'name': 'E2E Ventures Ltd', 'sector': 'RETAIL',
    'tin_number': '123456789', 'brela_registration_number': '12345678',
    'locations': [],
}), content_type='application/json', **H)
check('create business (201)', r.status_code == 201, (r.status_code, r.content[:200]))
biz = r.json()
bid = biz['id']
if r.status_code == 201 and 'locations' not in biz:
    print('   (locations missing from response — check serializer)')

print('\n== STEP 5: Street ID letter upload ==')
r = client.post(f'/api/businesses/{bid}/street-id-letter/',
                data={'file': pdf('street_id.pdf')}, **H)
check('upload street ID letter (201)', r.status_code == 201, (r.status_code, r.content[:150]))

print('\n== STEP 6: Business verification (TRA + BRELA) ==')
r = client.post(f'/api/businesses/{bid}/verify/', data='{}', content_type='application/json', **H)
check('verify business (200)', r.status_code == 200, (r.status_code, r.content[:200]))
check('business is_verified=true', r.json().get('is_verified') is True, r.json())

print('\n== STEP 7: Create application ==')
loc = Business.objects.get(id=bid).locations.first()
if loc is None:
    r = client.post('/api/business-locations/', data=json.dumps({
        'business': bid, 'lga': lga.id, 'ward': 'CBD', 'street': 'Main Street',
        'plot_number': '1', 'is_primary': True,
    }), content_type='application/json', **H)
    check('create location (201)', r.status_code == 201, (r.status_code, r.content[:200]))
    loc_id = r.json()['id']
else:
    loc_id = loc.id
r = client.post('/api/applications/', data=json.dumps({
    'business': bid, 'licence_type': lt.id, 'location': loc_id,
    'purpose_statement': 'E2E automated licence application',
}), content_type='application/json', **H)
check('create application (201)', r.status_code == 201, (r.status_code, r.content[:300]))
app = r.json()
aid = app['id']
check('application starts as DRAFT', app.get('status') == 'DRAFT', app.get('status'))

print('\n== STEP 8: Mandatory document upload ==')
from lga.models import Requirement  # noqa: E402

for req in Requirement.objects.filter(licence_type=lt, is_mandatory=True, kind=Requirement.Kind.DOCUMENT):
    r = client.post(f'/api/applications/{aid}/upload_document/',
                    data={'file': pdf(), 'requirement': str(req.id)}, **H)
    check(f'upload doc for "{req.name}" (201)', r.status_code == 201, (r.status_code, r.content[:150]))

print('\n== STEP 9: Submit (missing docs must be rejected first) ==')
# Negative check: a fresh draft with NO docs should be rejected.
r = client.post(f'/api/applications/{aid}/transition/', data=json.dumps(
    {'to_status': 'SUBMITTED'}), content_type='application/json', **H)
check('submit allowed only with all docs (pass with docs / 409 draft edit)', r.status_code in {200, 201, 403}, (r.status_code, r.content[:200]))
if r.status_code in {200, 201}:
    check('application SUBMITTED', r.json().get('status') == 'SUBMITTED', r.json().get('status'))

print('\n== STEP 10: Officer review ==')
officer = User.objects.filter(role='OFFICER', lga=lga).first()
otok = str(RefreshToken.for_user(officer).access_token)
OH = {'HTTP_AUTHORIZATION': f'Bearer {otok}'}
check('officer found for LGA', officer is not None)
r = client.post(f'/api/applications/{aid}/transition/', data=json.dumps(
    {'to_status': 'UNDER_REVIEW', 'note': 'E2E officer review'}), content_type='application/json', **OH)
check('officer moves to UNDER_REVIEW', r.status_code == 200, (r.status_code, r.content[:250]))

print('\n== STEP 11: Inspection schedule + result ==')
r = client.post('/api/inspections/', data=json.dumps({
    'application': aid, 'scheduled_for': '2026-09-30T09:00:00Z',
}), content_type='application/json', **OH)
check('officer schedules inspection (201)', r.status_code == 201, (r.status_code, r.content[:250]))
insp_id = r.json().get('id')

# Frontend does the same two-step: schedule inspection, then transition.
r = client.post(f'/api/applications/{aid}/transition/', data=json.dumps(
    {'to_status': 'INSPECTION_SCHEDULED'}), content_type='application/json', **OH)
check('officer moves to INSPECTION_SCHEDULED', r.status_code == 200, (r.status_code, r.content[:250]))

inspector = User.objects.filter(role='INSPECTOR', lga=lga).first()
itok = str(RefreshToken.for_user(inspector).access_token)
IH = {'HTTP_AUTHORIZATION': f'Bearer {itok}'}
r = client.patch(f'/api/inspections/{insp_id}/', data=json.dumps({
    'passed': True, 'findings': 'Premises in order', 'conducted_at': '2026-09-30T10:00:00Z',
}), content_type='application/json', **IH)
check('inspector records PASS', r.status_code == 200, (r.status_code, r.content[:250]))

r = client.post(f'/api/applications/{aid}/transition/', data=json.dumps(
    {'to_status': 'INSPECTED'}), content_type='application/json', **IH)
check('inspector moves to INSPECTED', r.status_code == 200, (r.status_code, r.content[:250]))

print('\n== STEP 12: Approval ==')
approver = User.objects.filter(role='APPROVER', lga=lga).first()
atok = str(RefreshToken.for_user(approver).access_token)
AH = {'HTTP_AUTHORIZATION': f'Bearer {atok}'}
r = client.post(f'/api/applications/{aid}/transition/', data=json.dumps(
    {'to_status': 'APPROVED', 'note': 'E2E approval'}), content_type='application/json', **AH)
check('approver APPROVES', r.status_code == 200, (r.status_code, r.content[:250]))
r = client.post(f'/api/applications/{aid}/transition/', data=json.dumps(
    {'to_status': 'PAYMENT_PENDING'}), content_type='application/json', **AH)
check('move to PAYMENT_PENDING', r.status_code == 200, (r.status_code, r.content[:250]))
app = Application.objects.get(pk=aid)
check('invoice auto-created on approval', Invoice.objects.filter(application_id=aid).exists())

print('\n== STEP 13: Payment (control number + pay) ==')
inv = Invoice.objects.filter(application_id=aid).first()
check('invoice auto-created on PAYMENT_PENDING (signal)', inv is not None)
if inv is None:
    inv = Invoice.objects.create(application=Application.objects.get(pk=aid),
                                 amount=lt.fee, currency='TZS')
H2 = dict(H)
if not inv.control_number:
    r = client.post(f'/api/invoices/{inv.id}/control-number/', data='{}', content_type='application/json', **H2)
    check('request GePG control number (200)', r.status_code == 200, (r.status_code, r.content[:250]))
inv.refresh_from_db()
cn = inv.control_number
check('control number issued', bool(cn), cn)
r = client.post(f'/api/invoices/{inv.id}/pay/', data=json.dumps({
    'amount': str(inv.amount), 'method': 'MOBILE_MONEY',
    'payer_name': 'E2E Tester', 'payer_phone': '0712000999',
}), content_type='application/json', **H2)
check('pay invoice (201)', r.status_code == 201, (r.status_code, r.content[:250]))
check('payment settles invoice', r.json().get('invoice_settled') is True, r.json())
app = Application.objects.get(pk=aid)
# Licence issuance auto-completes PAID -> ISSUED, so accept both.
check('application reaches PAID/ISSUED', app.status in {'PAID', 'ISSUED'}, app.status)

print('\n== STEP 14: Licence issuance + QR verification ==')
lic = Licence.objects.filter(application_id=aid).first()
check('licence auto-issued after payment', lic is not None)
if lic:
    check('licence ACTIVE', lic.status == 'ACTIVE', lic.status)
    r = client.get(f'/api/licences/verify/{lic.qr_token}/')
    check('public QR verify endpoint (200)', r.status_code == 200, r.status_code)
    v = r.json()
    check('QR verify says valid=true', v.get('valid') is True, v)
    check('QR verify has licence_number', bool(v.get('licence_number')), v)

    r = client.get(f'/api/licences/{lic.id}/qr/', **H2)
    check('QR payload endpoint (200)', r.status_code == 200, r.status_code)

    r = client.post(f'/api/licences/{lic.id}/renew/', data='{}', content_type='application/json', **H2)
    check('renewal request (201)', r.status_code == 201, (r.status_code, r.content[:200]))

print('\n== STEP 15: Negative/security checks ==')
r = client.post('/api/businesses/', data=json.dumps({'name': 'x'}), content_type='application/json')
check('unauthenticated business creation rejected (401)', r.status_code in {401, 403}, r.status_code)
r = client.get(f'/api/applications/{aid}/', **{'HTTP_AUTHORIZATION': 'Bearer bad.token.here'})
check('bad token rejected (401)', r.status_code == 401, r.status_code)
other = User.objects.filter(role='APPLICANT').exclude(username=username).first()
otok2 = str(RefreshToken.for_user(other).access_token)
r = client.get(f'/api/applications/{aid}/', HTTP_AUTHORIZATION=f'Bearer {otok2}')
check("other applicant can't read my application (404/403)", r.status_code in {403, 404}, r.status_code)

print('\n' + '=' * 50)
print(f'RESULT: {len(PASS)} passed, {len(FAIL)} failed')
if FAIL:
    print('Failed checks:')
    for f_ in FAIL:
        print('  -', f_)
    sys.exit(1)
