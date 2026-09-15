import os
from typing import Any, Optional

import httpx


def send_booking_payment_email(
    email: str,
    booking_reference: str,
    payment_link: str,
    amount: str,
    currency: str,
    from_email: Optional[str] = None,
) -> dict[str, Any]:
    api_key = os.getenv("RESEND_API_KEY")
    from_email = from_email or os.getenv("RESEND_FROM_EMAIL")

    if not api_key or not from_email:
        return {
            "sent": False,
            "message_id": None,
            "error": "Email service is not configured (RESEND_API_KEY or RESEND_FROM_EMAIL missing)",
        }

    payload = {
        "from": from_email,
        "to": [email],
        "subject": f"Complete payment for booking {booking_reference}",
        "html": f"""
            <h2>Complete your payment</h2>
            <p>Your booking reference is <strong>{booking_reference}</strong>.</p>
            <p>Amount due: <strong>{amount} {currency}</strong></p>
            <p><a href="{payment_link}">Pay now</a></p>
        """,
    }

    try:
        with httpx.Client(timeout=20) as client:
            response = client.post(
                "https://api.resend.com/emails",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )
        if response.is_success:
            return {"sent": True, "message_id": response.json().get("id"), "error": None}
        return {"sent": False, "message_id": None, "error": response.text[:500]}
    except Exception as exc:
        return {"sent": False, "message_id": None, "error": str(exc)}


def send_welcome_email(
    email: str,
    first_name: str,
    last_name: str,
    from_email: Optional[str] = None,
) -> dict[str, Any]:
    api_key = os.getenv("RESEND_API_KEY")
    from_email = from_email or os.getenv("RESEND_FROM_EMAIL")

    if not api_key or not from_email:
        return {
            "sent": False,
            "message_id": None,
            "error": "Email service is not configured (RESEND_API_KEY or RESEND_FROM_EMAIL missing)",
        }

    payload = {
        "from": from_email,
        "to": [email],
        "subject": "Welcome to Supa Records Hotel Management",
        "html": f"""
            <h2>Welcome {first_name} {last_name}!</h2>
            <p>Your account has been created successfully.</p>
            <p>You can now sign in to Supa Records Hotel Management.</p>
        """,
    }

    try:
        with httpx.Client(timeout=20) as client:
            response = client.post(
                "https://api.resend.com/emails",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )
        if response.is_success:
            return {"sent": True, "message_id": response.json().get("id"), "error": None}
        return {"sent": False, "message_id": None, "error": response.text[:500]}
    except Exception as exc:
        return {"sent": False, "message_id": None, "error": str(exc)}
