# Render Production Env Fill Sheet

Fill this before setting Render environment variables.

## Core

| Variable | Required | Value |
|---|---|---|
| DJANGO_ENV | Yes | production |
| DEBUG | Yes | False |
| SECRET_KEY | Yes | |
| DATABASE_URL | Yes | |

## Domains and Security

| Variable | Required | Value |
|---|---|---|
| FRONTEND_URL | Yes | https://jamborafiki.vercel.app |
| ALLOWED_HOSTS | Yes | |
| CORS_ALLOWED_ORIGINS | Yes | https://jamborafiki.vercel.app |
| CSRF_TRUSTED_ORIGINS | Yes | |

## SMTP

| Variable | Required | Value |
|---|---|---|
| EMAIL_BACKEND | Yes | django.core.mail.backends.smtp.EmailBackend |
| EMAIL_HOST | Yes | email-smtp.us-east-1.amazonaws.com |
| EMAIL_PORT | Yes | 587 |
| EMAIL_USE_TLS | Yes | True |
| EMAIL_HOST_USER | Yes | |
| EMAIL_HOST_PASSWORD | Yes | |
| DEFAULT_FROM_EMAIL | Yes | |
| ADMIN_EMAIL | Yes | |
| ADMIN_NOTIFICATION_EMAILS | Yes | benjaminoyoo182@gmail.com,infodirector@jamborafiki.org,inforinternationaldirector@jamborafiki.org,email@jamborafiki.org |

## Media

| Variable | Required | Value |
|---|---|---|
| USE_S3_MEDIA | Yes | False |

## Payments

| Variable | Required | Value |
|---|---|---|
| MPESA_ENVIRONMENT | Yes | sandbox (switch to production later) |
| MPESA_CONSUMER_KEY | Yes | |
| MPESA_CONSUMER_SECRET | Yes | |
| MPESA_SHORTCODE | Yes | 174379 |
| MPESA_PASSKEY | Yes | |
| MPESA_CALLBACK_URL | Yes | |
| MPESA_CALLBACK_TOKEN | Yes | |
| MPESA_CALLBACK_SIGNATURE_SECRET | Recommended | |
| MPESA_CALLBACK_SIGNATURE_HEADER | Recommended | X-MPESA-SIGNATURE |
| STRIPE_PUBLIC_KEY | Optional | |
| STRIPE_SECRET_KEY | Optional | |
| STRIPE_WEBHOOK_SECRET | Optional | |

## Observability

| Variable | Required | Value |
|---|---|---|
| LOG_LEVEL | Recommended | INFO |
| SECURITY_LOG_LEVEL | Recommended | WARNING |
| SENTRY_DSN | Optional | |
| SENTRY_TRACES_SAMPLE_RATE | Optional | 0.05 |
