"""End-to-end smoke test: role enforcement against the live API."""
import json
import urllib.request

BASE = 'http://localhost:8000/api'


def req(method, path, token=None, data=None):
    body = json.dumps(data).encode() if data is not None else None
    r = urllib.request.Request(BASE + path, data=body, method=method)
    r.add_header('Content-Type', 'application/json')
    if token:
        r.add_header('Authorization', f'Bearer {token}')
    try:
        with urllib.request.urlopen(r) as resp:
            return resp.status, json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read().decode())
        except Exception:
            return e.code, {}


def login(username):
    status, data = req('POST', '/auth/login/', data={'username': username, 'password': 'Demo@1234'})
    assert status == 200, f'login {username} failed: {status}'
    return data['access']


def find_application(token, **filters):
    qs = '&'.join(f'status={v}' for v in filters.values())
    status, data = req('GET', f'/applications/?{qs}&page_size=100', token=token)
    return data['results']


def transition(token, app_id, to_status):
    return req('POST', f'/applications/{app_id}/transition/', token=token, data={'to_status': to_status})


checks = []


def check(label, ok, extra=''):
    checks.append(ok)
    print(f'  {"PASS" if ok else "FAIL"}  {label} {extra}')


# --- setup: login all roles -------------------------------------------------
applicant = login('applicant1')
officer = login('officer1')
inspector = login('inspector1')
approver = login('approver1')
admin = login('admin')

# --- find the seed pipeline application (SUBMITTED) --------------------------
submitted = find_application(applicant, status='SUBMITTED')
assert submitted, 'no SUBMITTED application found'
app = submitted[0]
app_id = app['id']
print(f'Testing with application {app["reference_number"]}\n')

# --- 1. applicant cannot review ----------------------------------------------
s, d = transition(applicant, app_id, 'UNDER_REVIEW')
check('applicant cannot start review (403)', s == 403, f'(got {s})')

# --- 2. inspector cannot review ----------------------------------------------
s, d = transition(inspector, app_id, 'UNDER_REVIEW')
check('inspector cannot start review (403)', s == 403, f'(got {s})')

# --- 3. approver cannot review -----------------------------------------------
s, d = transition(approver, app_id, 'UNDER_REVIEW')
check('approver cannot start review (403)', s == 403, f'(got {s})')

# --- 4. officer CAN review ----------------------------------------------------
s, d = transition(officer, app_id, 'UNDER_REVIEW')
check('officer starts review (200)', s == 200, f'(got {s})')
check('officer auto-assigned', d.get('assigned_officer') is not None)

# --- 5. officer cannot approve ------------------------------------------------
s, d = transition(officer, app_id, 'APPROVED')
check('officer cannot approve (403)', s == 403, f'(got {s})')

# --- 6. officer schedules inspection ------------------------------------------
s, d = req('POST', '/inspections/', token=officer, data={'application': app_id, 'scheduled_for': '2026-10-01T09:00:00Z'})
check('officer schedules inspection (201)', s == 201, f'(got {s})')
s, d = transition(officer, app_id, 'INSPECTION_SCHEDULED')
check('officer marks inspection scheduled (200)', s == 200, f'(got {s})')

# --- 7. inspector cannot approve ----------------------------------------------
s, d = transition(inspector, app_id, 'APPROVED')
check('inspector cannot approve (403)', s == 403, f'(got {s})')

# --- 8. officer cannot record inspection result -------------------------------
s, d = transition(officer, app_id, 'INSPECTED')
check('officer cannot record inspection result (403)', s == 403, f'(got {s})')

# --- 9. inspector records result ----------------------------------------------
s, d = transition(inspector, app_id, 'INSPECTED')
check('inspector records inspection result (200)', s == 200, f'(got {s})')

# --- 10. admin does everything -------------------------------------------------
s, d = transition(admin, app_id, 'RETURNED_FOR_CORRECTION')
check('admin returns for correction (200)', s == 200, f'(got {s})')
s, d = transition(admin, app_id, 'DRAFT')
check('admin moves back to draft (200)', s == 200, f'(got {s})')
s, d = transition(admin, app_id, 'SUBMITTED')
check('admin resubmits (200)', s == 200, f'(got {s})')
s, d = transition(admin, app_id, 'UNDER_REVIEW')
check('admin starts review (200)', s == 200, f'(got {s})')
s, d = transition(admin, app_id, 'INSPECTION_SCHEDULED')
check('admin schedules inspection (200)', s == 200, f'(got {s})')
s, d = transition(admin, app_id, 'INSPECTED')
check('admin records inspection (200)', s == 200, f'(got {s})')
s, d = transition(admin, app_id, 'APPROVED')
check('admin approves (200)', s == 200, f'(got {s})')

print()
passed = sum(checks)
print(f'{passed}/{len(checks)} checks passed')
raise SystemExit(0 if passed == len(checks) else 1)
