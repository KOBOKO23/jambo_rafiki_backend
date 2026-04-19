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

We have received your message and will respond as soon as possible.

Your message:
Subject: {subject}
{message}

---
Blessings,
Jambo Rafiki Team

P.O Box 311 - 40222, OYUGIS - KENYA
Email: hopenationsministries8@gmail.com
""",
    },
    'volunteer_confirmation': {
        'subject': 'Volunteer Application Received - Jambo Rafiki',
        'body': """
Dear {name},

Thank you for your interest in volunteering with Jambo Rafiki Children Orphanage and Church Centre!

We have received your application and will review it carefully. Our team will contact you within 5-7 business days.

Your Application Details:
- Skills: {skills_preview}
- Availability: {availability}
- Duration: {duration}

If you have any questions, please feel free to reach out to us.

Blessings,
Jambo Rafiki Team

P.O Box 311 - 40222, OYUGIS - KENYA
Email: hopenationsministries8@gmail.com
""",
    },
    'volunteer_admin_notification': {
        'subject': 'New Volunteer Application: {name}',
        'body': """
New volunteer application received:

Name: {name}
Email: {email}
Phone: {phone}
Location: {location}

Skills: {skills}

Availability: {availability}

Motivation:
{motivation}

Experience:
{experience}
Areas of Interest:
{areas_of_interest}
        'body': """

---
Submitted at: {submitted_at}

View in admin: {admin_url}
""",
    },
    'newsletter_welcome': {
        'subject': 'Welcome to Jambo Rafiki Newsletter',
        'body': """
Dear {name},

Thank you for subscribing to the Jambo Rafiki newsletter!
To unsubscribe at any time, reply to this email or visit our website.

---
Blessings,
Jambo Rafiki Team
P.O Box 311 - 40222, OYUGIS - KENYA
Email: hopenationsministries8@gmail.com
""",
    },
        'subject': 'New Testimonial Pending Review: {name}',
        'body': """
        'body': """
A new testimonial has been submitted and is waiting for your review.

From: {name}
Role: {role}
Email: {email}

Testimonial:
{text}

---
Submitted at: {submitted_at}

Approve or reject in the admin panel:
{admin_url}
    },
    'testimonial_submitter_confirmation': {
        'subject': 'Thank you for your testimonial - Jambo Rafiki',
        'body': """
Dear {name},
Thank you for taking the time to share your experience with Jambo Rafiki!

        'body': """
Your testimonial has been received and will appear on our website once it has been reviewed by our team.

We truly appreciate your support and kind words.

---
Blessings,
Jambo Rafiki Team
P.O Box 311 - 40222, OYUGIS - KENYA
Email: hopenationsministries8@gmail.com
""",
    },
    'testimonial_approved': {
        'subject': 'Your testimonial is now live on our website!',
        'body': """

Great news! Your testimonial has been approved and is now live on the Jambo Rafiki website.

Thank you again for sharing your story - it means a great deal to us and helps inspire others to support our mission.


---
        'body': """
Blessings,
Jambo Rafiki Team
P.O Box 311 - 40222, OYUGIS - KENYA
Email: hopenationsministries8@gmail.com
""",
    },
    'sponsorship_interest_admin': {
        'subject': 'New Sponsorship Interest',
        'body': """
Name: {name}
Email: {email}
Phone: {phone}
Preferred Level: {preferred_level}
""",
    'donation_receipt': {
        'subject': 'Donation Receipt - {receipt_number}',
        'body': """
Dear {donor_name},


Donation Details:
        'body': """
Receipt Number: {receipt_number}
Amount: {currency} {amount}
Date: {completed_at}
Purpose: {purpose}
Payment Method: {payment_method}

Your contribution helps us provide care, education, and hope to orphaned and vulnerable children in Kenya.

May God bless you abundantly for your generosity!

---
Jambo Rafiki Children Orphanage and Church Centre
P.O Box 311 - 40222, OYUGIS - KENYA
Email: hopenationsministries8@gmail.com
""",
    },
}


def render_email_template(template_name: str, context: dict) -> tuple[str, str]:
    """Return rendered (subject, body) for a known email template."""
        raise ValueError(f'Unknown email template: {template_name}')

    template = EMAIL_TEMPLATES[template_name]
    safe_context = defaultdict(str, context or {})
    body = template['body'].format_map(safe_context).strip()
    return subject, body
        'body': """
