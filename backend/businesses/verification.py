"""TRA + BRELA verification with human-readable outcomes.

Used by both Business.ensure_verified() (auto-verify after save) and the
`POST /api/businesses/<id>/verify/` action, so rejection reasons are derived
in exactly one place and can be persisted on a VerificationAttempt.
"""


def run_verification(business):
    """Ask TRA (TIN) and BRELA (registration) about this business.

    Returns a dict with:
        verified         — both agencies accepted the business
        tra_valid        — TRA accepted the TIN (False when rejected/unreachable)
        tra_reason       — '' when TRA passed, else why it refused
        brela_registered — BRELA accepted the registration number
        brela_reason     — '' when BRELA passed, else why it refused

    The mock endpoints (dev) reject a TIN that is not 9-12 digits and a
    registration number that does not start with '1'; the real TRA ITAX /
    BRELA ORS APIs return their own reasons which flow through here too.
    """
    from integrations.adapters import BRELAdapter, TRAAdapter

    tin_result = TRAAdapter().verify_tin(business.tin_number, business.name)
    brela_result = BRELAdapter().verify_registration(
        business.brela_registration_number, business.name
    )

    tra_reachable = tin_result.success
    brela_reachable = brela_result.success
    tra_valid = bool(tra_reachable and tin_result.data.get('valid') is True)
    brela_registered = bool(
        brela_reachable and brela_result.data.get('registered') is True
    )

    if not tra_reachable:
        tra_reason = 'TRA service unreachable — try again later.'
    elif not tra_valid:
        tra_reason = (
            f'TRA rejected TIN {business.tin_number}: not found or it does not '
            'match the taxpayer name.'
        )
    else:
        tra_reason = ''

    if not brela_reachable:
        brela_reason = 'BRELA service unreachable — try again later.'
    elif not brela_registered:
        brela_reason = (
            f'BRELA rejected {business.brela_registration_number}: registration '
            'not found or the entity is not active.'
        )
    else:
        brela_reason = ''

    return {
        'verified': tra_valid and brela_registered,
        'tra_valid': tra_valid,
        'tra_reason': tra_reason,
        'brela_registered': brela_registered,
        'brela_reason': brela_reason,
    }
