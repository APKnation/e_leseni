"""Role-based workflow rules for the application status flow.

Standard workflow split (enforced in the API layer AND used to filter the
`allowed_next_statuses` the frontend shows as buttons):

    OFFICER   - review stage: start review, return for correction, reject,
                schedule an inspection
    INSPECTOR - record inspection results (mark inspected, reject on findings)
    APPROVER  - approve after inspection, return for correction, reject
    ADMIN     - every staff action, plus visibility of all LGAs
    APPLICANT - submit their own drafts / resubmit returned applications

System-triggered transitions (APPROVED -> PAYMENT_PENDING -> PAID -> ISSUED)
are driven by payment/licensing signals with `by=None`, so they bypass the
per-role check but remain valid state-machine transitions.
"""
from .models import Application

Status = Application.Status

# Transitions each staff role may perform manually. APPLICANT is handled
# separately below. APPLIES TO ALL LGAs regardless of the user's own LGA:
# the LGA scoping of *which* applications they see is done in get_queryset().
ROLE_TRANSITIONS = {
    'OFFICER': {
        Status.UNDER_REVIEW,            # start review (from SUBMITTED)
        Status.INSPECTION_SCHEDULED,    # schedule an inspection
        Status.RETURNED_FOR_CORRECTION,
        Status.REJECTED,
    },
    'INSPECTOR': {
        Status.INSPECTED,               # record inspection outcome
        Status.REJECTED,                # failed inspection
    },
    'APPROVER': {
        Status.APPROVED,                # final approval (from INSPECTED)
        Status.PAYMENT_PENDING,         # approve & invoice in one step
        Status.REJECTED,
        Status.RETURNED_FOR_CORRECTION,
    },
    'ADMIN': {
        Status.SUBMITTED,
        Status.UNDER_REVIEW,
        Status.INSPECTION_SCHEDULED,
        Status.INSPECTED,
        Status.APPROVED,
        Status.PAYMENT_PENDING,
        Status.PAID,
        Status.RETURNED_FOR_CORRECTION,
        Status.REJECTED,
    },
}

# Applicant-allowed transitions (own applications only).
APPLICANT_TRANSITIONS = {
    Status.SUBMITTED,                   # submit a draft / resubmit a returned app
}


def allowed_statuses_for(user, application):
    """The set of transition targets `user` may perform on `application`."""
    next_statuses = application.allowed_next_statuses
    if not user.is_authenticated:
        return set()

    if user.is_superuser or user.role == 'ADMIN':
        return next_statuses

    role_map = {
        'OFFICER': ROLE_TRANSITIONS['OFFICER'],
        'INSPECTOR': ROLE_TRANSITIONS['INSPECTOR'],
        'APPROVER': ROLE_TRANSITIONS['APPROVER'],
    }
    role_statuses = role_map.get(user.role, set())
    if user.role == 'APPLICANT':
        role_statuses = APPLICANT_TRANSITIONS

    return next_statuses & role_statuses
