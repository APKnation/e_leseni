"""Message templates for application lifecycle SMS."""
from .models import SMSLog


def _app_label(application):
    return application.reference_number


def application_submitted(application, phone):
    return send_application_sms(
        application, phone,
        purpose=SMSLog.Purpose.SUBMISSION,
        body=f'e-Leseni: Application {application.reference_number} received. '
             f'Status: {application.get_status_display()}. Keep this reference for follow-up.',
    )


def returned_for_correction(application, phone, note=''):
    reason = f' Reason: {note}' if note else ''
    return send_application_sms(
        application, phone,
        purpose=SMSLog.Purpose.CORRECTION,
        body=f'e-Leseni: Application {application.reference_number} was returned for correction.{reason} '
             f'Resubmit on e-Leseni or by dialling the USSD code.',
    )


def application_approved(application, phone):
    return send_application_sms(
        application, phone,
        purpose=SMSLog.Purpose.APPROVAL,
        body=f'e-Leseni: Application {application.reference_number} APPROVED. '
             f'An invoice with a control number will follow shortly.',
    )


def control_number_issued(application, phone, control_number, amount, currency='TZS'):
    return send_application_sms(
        application, phone,
        purpose=SMSLog.Purpose.CONTROL_NUMBER,
        body=f'e-Leseni: Pay {amount} {currency} for {application.reference_number} '
             f'using control number {control_number} at any agent, bank or mobile money.',
    )


def payment_confirmed(application, phone, amount, currency='TZS', receipt=''):
    receipt_bit = f' Receipt: {receipt}.' if receipt else ''
    return send_application_sms(
        application, phone,
        purpose=SMSLog.Purpose.PAYMENT_CONFIRMED,
        body=f'e-Leseni: Payment of {amount} {currency} for {application.reference_number} confirmed.{receipt_bit}',
    )


def licence_issued(application, phone, licence_number, valid_until):
    return send_application_sms(
        application, phone,
        purpose=SMSLog.Purpose.ISSUANCE,
        body=f'e-Leseni: Licence {licence_number} issued for {application.reference_number}. '
             f'Valid until {valid_until.isoformat()}. Print it from your e-Leseni account.',
    )


def application_rejected(application, phone, reason=''):
    reason_bit = f' Reason: {reason}' if reason else ''
    return send_application_sms(
        application, phone,
        purpose=SMSLog.Purpose.REJECTION,
        body=f'e-Leseni: Application {application.reference_number} was rejected.{reason_bit}',
    )


def renewal_update(renewal, phone):
    return send_application_sms(
        renewal.licence.application, phone,
        purpose=SMSLog.Purpose.RENEWAL,
        body=f'e-Leseni: Renewal for licence {renewal.licence.licence_number} '
             f'is now {renewal.get_status_display()}.',
    )


def send_application_sms(application, phone, *, purpose, body):
    """Create + send, binding the log entry to the application and its owner."""
    from .backends import send_sms

    return send_sms(
        recipient=phone,
        body=body,
        purpose=purpose,
        user=application.applicant,
        application=application,
    )
