"""Shared email templates used across notification workflows."""
from __future__ import annotations
from collections import defaultdict

EMAIL_TEMPLATES = {
    'contact_admin_notification': {
        'subject': 'New Contact Form: {subject}',
        'body': """
New contact form submission received:

From: {name}
Email: {email}
Subject: {subject}

Message:
{message}

---
Submitted at: {submitted_at}
View in admin: {admin_url}
""",
    },
    'contact_auto_reply': {
        'subject': 'Thank you for contacting Jambo Rafiki',
        'body': """
Dear {name},

Thank you for reaching out to Jambo Rafiki Children Orphanage and Church Centre.

Your message:
{message}

---
Blessings,
Jambo Rafiki Team
P.O Box 311 - 40222, OYUGIS - KENYA
""",
    },
    'volunteer_confirmation': {
        'subject': 'Volunteer Application Received - Jambo Rafiki',
        'body': """
Dear {name},

We have received your application and will review it carefully. Our team will contact you within 5-7 business days.

Your Application Details:
- Skills: {skills_preview}
- Availability: {availability}
- Duration: {duration}

---
Blessings,
Jambo Rafiki Team
P.O Box 311 - 40222, OYUGIS - KENYA
Email: hopenationsministries8@gmail.com
""",
    },
    'volunteer_admin_notification': {
        'subject': 'New Volunteer Application: {name}',
        'body': """
A new volunteer application has been submitted.

Name: {name}
Email: {email}
Phone: {phone}
Skills: {skills}

Areas of Interest:
{areas_of_interest}

Motivation:
{motivation}

Experience:
{experience}

---
Submitted at: {submitted_at}
View in admin: {admin_url}
""",
    },
    'newsletter_welcome': {
        'subject': 'Welcome to Jambo Rafiki Newsletter',
        'body': """
Thank you for subscribing to the Jambo Rafiki newsletter!

To unsubscribe at any time, reply to this email or visit our website.

---
Blessings,
Jambo Rafiki Team
P.O Box 311 - 40222, OYUGIS - KENYA
""",
    },
    'testimonial_admin_notification': {
        'subject': 'New Testimonial Pending Review: {name}',
        'body': """
A new testimonial has been submitted and is waiting for your review.

Testimonial:
{text}

---
Submitted at: {submitted_at}
Approve or reject in the admin panel: {admin_url}
""",
    },
    'testimonial_submitter_confirmation': {
        'subject': 'Thank you for your testimonial - Jambo Rafiki',
        'body': """
Thank you for taking the time to share your experience with Jambo Rafiki!

We truly appreciate your support and kind words.

---
Jambo Rafiki Team
P.O Box 311 - 40222, OYUGIS - KENYA
""",
    },
    'testimonial_approved': {
        'subject': 'Your testimonial is now live on our website!',
        'body': """
Thank you again for sharing your story - it means a great deal to us and helps inspire others to support our mission.

---
Jambo Rafiki Team
P.O Box 311 - 40222, OYUGIS - KENYA
""",
    },
    'sponsorship_interest_admin': {
        'subject': 'New Sponsorship Interest',
        'body': """
A new sponsorship inquiry has been received.

Name: {name}
Email: {email}
Phone: {phone}
Preferred Level: {preferred_level}
""",
    },
    'donation_receipt': {
        'subject': 'Donation Receipt - {receipt_number}',
        'body': """
Dear {donor_name},

Donation Details:
Receipt Number: {receipt_number}
Amount: {currency} {amount}
Date: {completed_at}
Purpose: {purpose}
Payment Method: {payment_method}

Your contribution helps us provide care, education, and hope to orphaned and vulnerable children in Kenya.

---
Jambo Rafiki Children Orphanage and Church Centre
P.O Box 311 - 40222, OYUGIS - KENYA
Email: hopenationsministries8@gmail.com
""",
    },
    'bank_transfer_details': {
        'subject': 'Bank Transfer Details - Jambo Rafiki',
        'body': """
Dear {donor_name},

Thank you for your intention to donate to Jambo Rafiki Children Orphanage.

Here are our bank transfer details for your donation of KES {amount} towards {purpose}:

BANK ACCOUNT DETAILS
--------------------
Account Name:   {account_name}
Account Number: {account_number}
Bank Code:      {bank_code}
Branch Code:    {branch_code}
SWIFT / BIC:    {swift_code}

IMPORTANT: Please use the following reference when making your transfer:
Reference: {reference}

This helps us match your transfer to your donation record.

Once you have made the transfer, please reply to this email or contact us at
info@jamborafiki.org with your transfer confirmation so we can acknowledge your donation.

Your generosity transforms lives. Thank you!

---
Jambo Rafiki Children Orphanage and Church Centre
P.O Box 311 - 40222, OYUGIS - KENYA
Email: info@jamborafiki.org
""",
    },
}


def render_email_template(template_name: str, context: dict) -> tuple[str, str]:
    """Return rendered (subject, body) for a known email template."""
    template = EMAIL_TEMPLATES[template_name]
    safe_context = defaultdict(str, context or {})
    subject = template['subject'].format_map(safe_context)
    body = template['body'].format_map(safe_context).strip()
    return subject, body