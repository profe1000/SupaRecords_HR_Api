import os
from html import escape
from typing import Any, Optional

import httpx


def _send(payload: dict[str, Any], from_email: Optional[str] = None) -> dict[str, Any]:
    api_key = os.getenv("RESEND_API_KEY")
    from_email = from_email or os.getenv("RESEND_FROM_EMAIL")

    if not api_key or not from_email:
        return {
            "sent": False,
            "message_id": None,
            "error": "Email service is not configured (RESEND_API_KEY or RESEND_FROM_EMAIL missing)",
        }

    try:
        with httpx.Client(timeout=20) as client:
            response = client.post(
                "https://api.resend.com/emails",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={"from": from_email, **payload},
            )
        if response.is_success:
            return {"sent": True, "message_id": response.json().get("id"), "error": None}
        return {"sent": False, "message_id": None, "error": response.text[:500]}
    except Exception as exc:
        return {"sent": False, "message_id": None, "error": str(exc)}


def _sign_in_line() -> str:
    """Link to the staff portal when FRONTEND_URL is configured."""
    url = os.getenv("FRONTEND_URL", "").rstrip("/")
    if not url:
        return "<p>You can now sign in to the staff portal with this email address.</p>"
    return (
        f'<p>You can now sign in to the staff portal with this email address: '
        f'<a href="{escape(url)}/auth/signin">{escape(url)}/auth/signin</a></p>'
    )


def send_booking_payment_email(
    email: str,
    booking_reference: str,
    payment_link: str,
    amount: str,
    currency: str,
    from_email: Optional[str] = None,
) -> dict[str, Any]:
    return _send(
        {
            "to": [email],
            "subject": f"Complete payment for booking {booking_reference}",
            "html": f"""
                <h2>Complete your payment</h2>
                <p>Your booking reference is <strong>{booking_reference}</strong>.</p>
                <p>Amount due: <strong>{amount} {currency}</strong></p>
                <p><a href="{payment_link}">Pay now</a></p>
            """,
        },
        from_email,
    )


def send_welcome_email(
    email: str,
    first_name: str,
    last_name: str,
    business_name: str,
    branch_name: Optional[str] = None,
    from_email: Optional[str] = None,
) -> dict[str, Any]:
    business = escape(business_name)
    branch = f" ({escape(branch_name)})" if branch_name else ""
    return _send(
        {
            "to": [email],
            "subject": f"Welcome to {business_name}",
            "html": f"""
                <h2>Welcome to {business}, {escape(first_name)} {escape(last_name)}!</h2>
                <p>Your staff account at <strong>{business}</strong>{branch} has been created.</p>
                {_sign_in_line()}
                <p>Your administrator will give you your password. Please change it after you first sign in
                (Settings &rarr; Change Password).</p>
            """,
        },
        from_email,
    )


def send_password_reset_email(
    email: str,
    first_name: str,
    business_name: str,
    new_password: str,
    from_email: Optional[str] = None,
) -> dict[str, Any]:
    business = escape(business_name)
    return _send(
        {
            "to": [email],
            "subject": f"Your {business_name} password has been reset",
            "html": f"""
                <h2>Hello {escape(first_name)},</h2>
                <p>An administrator at <strong>{business}</strong> has reset your staff portal password.</p>
                <p>Your new temporary password is: <strong>{escape(new_password)}</strong></p>
                {_sign_in_line()}
                <p>Please sign in and change it straight away (Settings &rarr; Change Password).
                If you did not expect this, contact your administrator.</p>
            """,
        },
        from_email,
    )
