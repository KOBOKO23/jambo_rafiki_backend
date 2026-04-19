# Render Environment Values (Copy-Paste)

Use this for both:
- web service: jambo-rafiki-backend-web
- worker service: jambo-rafiki-backend-worker

Replace only placeholder parts like `<your-render-web-url>` and `<your-secret>`.

---

## 0) Email Provider Choice (Important)

Render does not provide SMTP mail credentials by default.

Pick one option:

- Option A (recommended): Use an SMTP provider like Brevo, SendGrid, Mailgun, or Postmark.
- Option B (temporary): Use console backend so app boots while emails are printed in logs.

---

## 1) Values for jambo-rafiki-backend-web

ALLOWED_HOSTS=<your-render-web-url-without-https>
CSRF_TRUSTED_ORIGINS=https://jamborafiki.vercel.app,https://<your-render-web-url-without-https>

EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.sendgrid.net
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=apikey
EMAIL_HOST_PASSWORD=<your-sendgrid-api-key>
DEFAULT_FROM_EMAIL=infodirector@jamborafiki.org
ADMIN_EMAIL=infodirector@jamborafiki.org
ADMIN_NOTIFICATION_EMAILS=benjaminoyoo182@gmail.com,infodirector@jamborafiki.org,inforinternationaldirector@jamborafiki.org,email@jamborafiki.org

MPESA_CONSUMER_KEY=<your-mpesa-consumer-key>
MPESA_CONSUMER_SECRET=<your-mpesa-consumer-secret>
MPESA_PASSKEY=<your-mpesa-passkey>
MPESA_CALLBACK_TOKEN=<your-generated-callback-token>
MPESA_CALLBACK_SIGNATURE_SECRET=<your-generated-signature-secret>

SENTRY_DSN=

---

## 2) Values for jambo-rafiki-backend-worker

ALLOWED_HOSTS=<your-render-web-url-without-https>
CSRF_TRUSTED_ORIGINS=https://jamborafiki.vercel.app,https://<your-render-web-url-without-https>

EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.sendgrid.net
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=apikey
EMAIL_HOST_PASSWORD=<your-sendgrid-api-key>
DEFAULT_FROM_EMAIL=infodirector@jamborafiki.org
ADMIN_EMAIL=infodirector@jamborafiki.org
ADMIN_NOTIFICATION_EMAILS=benjaminoyoo182@gmail.com,infodirector@jamborafiki.org,inforinternationaldirector@jamborafiki.org,email@jamborafiki.org

MPESA_CONSUMER_KEY=<your-mpesa-consumer-key>
MPESA_CONSUMER_SECRET=<your-mpesa-consumer-secret>
MPESA_PASSKEY=<your-mpesa-passkey>
MPESA_CALLBACK_TOKEN=<your-generated-callback-token>
MPESA_CALLBACK_SIGNATURE_SECRET=<your-generated-signature-secret>

SENTRY_DSN=

---

## 3) Example for URL fields

If Render gives you:
https://jambo-rafiki-backend-web.onrender.com

Then use:
ALLOWED_HOSTS=jambo-rafiki-backend-web.onrender.com
CSRF_TRUSTED_ORIGINS=https://jamborafiki.vercel.app,https://jambo-rafiki-backend-web.onrender.com

---

## 4) SMTP Host Examples

- Brevo: EMAIL_HOST=smtp-relay.brevo.com
- SendGrid: EMAIL_HOST=smtp.sendgrid.net
- Mailgun: EMAIL_HOST=smtp.mailgun.org
- Postmark: EMAIL_HOST=smtp.postmarkapp.com

SendGrid auth reminder:
- EMAIL_HOST_USER must be exactly: apikey
- EMAIL_HOST_PASSWORD is your SendGrid API key

---

## 5) Temporary Option (No SMTP Provider Yet)

If you want to deploy first and configure real email later, set this in both services:

EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend

When this is enabled, email is logged to service logs and not sent to real inboxes.

# ---
# Full Copy-Paste Block (Recommended for Render)
# ---

DJANGO_ENV=production
DEBUG=False
SECRET_KEY=<your-secret-key>
DATABASE_URL=<your-render-postgres-url>

FRONTEND_URL=https://jamborafiki.vercel.app
ALLOWED_HOSTS=jambo-rafiki-backend-web.onrender.com
CORS_ALLOWED_ORIGINS=https://jamborafiki.vercel.app
CSRF_TRUSTED_ORIGINS=https://jamborafiki.vercel.app,https://jambo-rafiki-backend-web.onrender.com

EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=email-smtp.us-east-1.amazonaws.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=<your-smtp-user>
EMAIL_HOST_PASSWORD=<your-smtp-password>
DEFAULT_FROM_EMAIL=infodirector@jamborafiki.org
ADMIN_EMAIL=infodirector@jamborafiki.org
ADMIN_NOTIFICATION_EMAILS=benjaminoyoo182@gmail.com,infodirector@jamborafiki.org,inforinternationaldirector@jamborafiki.org,email@jamborafiki.org

USE_S3_MEDIA=False

MPESA_ENVIRONMENT=sandbox
MPESA_CONSUMER_KEY=<your-mpesa-key>
MPESA_CONSUMER_SECRET=<your-mpesa-secret>
MPESA_SHORTCODE=174379
MPESA_PASSKEY=<your-mpesa-passkey>
MPESA_CALLBACK_URL=https://jambo-rafiki-backend-web.onrender.com/api/v1/donations/mpesa-callback/
MPESA_CALLBACK_TOKEN=<your-mpesa-callback-token>
MPESA_CALLBACK_SIGNATURE_SECRET=<your-mpesa-signature-secret>
MPESA_CALLBACK_SIGNATURE_HEADER=X-MPESA-SIGNATURE

LOG_LEVEL=INFO
SECURITY_LOG_LEVEL=WARNING
SENTRY_DSN=
SENTRY_TRACES_SAMPLE_RATE=0.05

# Replace all <...> with your actual values.
# Keep values in sync for both web and worker services.
