# Production Env Fill Sheet (Section 2)

Use this sheet to close Configuration Readiness items in the production checklist.

Frontend and admin URLs already confirmed:
- Frontend: https://jamborafiki.vercel.app
- Admin UI path: https://jamborafiki.vercel.app/admin/login

## 1) Mandatory Runtime Variables

Fill all values before production startup.

| Variable | Required | Production Value | Status |
|---|---|---|---|
| DJANGO_ENV | Yes | production | [*] |
| DEBUG | Yes | False | [*] |
| ALLOWED_HOSTS | Yes | api.yourdomain.com | [*] |
| SECRET_KEY | Yes | <secure-random-secret> | [*] |
| DATABASE_URL | Yes | <postgresql://...> | [ ] |
| EMAIL_BACKEND | Yes | <provider-backend> | [*] |
| EMAIL_HOST | Yes | <smtp-host> | [ ] |
| EMAIL_PORT | Yes | <smtp-port> | [ ] |
| EMAIL_USE_TLS | Yes | True | [ ] |
| EMAIL_HOST_USER | Yes | <smtp-user> | [ ] |
| EMAIL_HOST_PASSWORD | Yes | <smtp-password> | [ ] |
| DEFAULT_FROM_EMAIL | Yes | infodirector@jamborafiki.org | [ ] |
| ADMIN_EMAIL | Yes | infodirector@jamborafiki.org | [ ] |

## 2) Frontend Origin Variables

These should match the deployed frontend.

| Variable | Required | Production Value | Status |
|---|---|---|---|
| FRONTEND_URL | Yes | https://jamborafiki.vercel.app | [*] |
| CORS_ALLOWED_ORIGINS | Yes | https://jamborafiki.vercel.app | [*] |
| CSRF_TRUSTED_ORIGINS | Yes | https://jamborafiki.vercel.app,https://api.yourdomain.com | [*] |

## 3) Media Storage Variables

Enable this set if production media should be durable and CDN-served.

| Variable | Required | Production Value | Status |
|---|---|---|---|
| USE_S3_MEDIA | Conditional | True | [ ] |
| AWS_STORAGE_BUCKET_NAME | If USE_S3_MEDIA=True | your-prod-media-bucket | [ ] |
| AWS_S3_REGION_NAME | If USE_S3_MEDIA=True | af-south-1 | [ ] |
| AWS_MEDIA_LOCATION | If USE_S3_MEDIA=True | media | [ ] |
| AWS_S3_CUSTOM_DOMAIN | Optional | cdn.yourdomain.com | [ ] |
| AWS_MEDIA_CACHE_CONTROL | Optional | max-age=86400 | [ ] |

## 4) Payment And Callback Secrets

| Variable | Required | Production Value | Status |
|---|---|---|---|
| MPESA_ENVIRONMENT | Yes | production | [ ] |
| MPESA_CONSUMER_KEY | Yes | <secret> | [ ] |
| MPESA_CONSUMER_SECRET | Yes | <secret> | [ ] |
| MPESA_SHORTCODE | Yes | <shortcode> | [ ] |
| MPESA_PASSKEY | Yes | <secret> | [ ] |
| MPESA_CALLBACK_URL | Yes | https://api.yourdomain.com/api/v1/donations/mpesa-callback/ | [ ] |
| MPESA_CALLBACK_TOKEN | Yes | <secret> | [ ] |
| MPESA_CALLBACK_SIGNATURE_SECRET | Recommended | <secret> | [ ] |
| MPESA_CALLBACK_SIGNATURE_HEADER | Recommended | X-MPESA-SIGNATURE | [ ] |
| STRIPE_PUBLIC_KEY | Yes (if Stripe enabled) | <publishable-key> | [ ] |
| STRIPE_SECRET_KEY | Yes (if Stripe enabled) | <secret-key> | [ ] |
| STRIPE_WEBHOOK_SECRET | Yes (if Stripe enabled) | <webhook-secret> | [ ] |

## 5) Security And Monitoring

| Variable | Required | Production Value | Status |
|---|---|---|---|
| SECURE_SSL_REDIRECT | Yes | True | [ ] |
| SESSION_COOKIE_SECURE | Yes | True | [ ] |
| CSRF_COOKIE_SECURE | Yes | True | [ ] |
| LOG_LEVEL | Yes | INFO | [ ] |
| SECURITY_LOG_LEVEL | Yes | WARNING | [ ] |
| SENTRY_DSN | Recommended | <dsn> | [ ] |
| SENTRY_TRACES_SAMPLE_RATE | Optional | 0.05 | [ ] |

## 6) Verification Commands

Run after filling production env values in staging or production-like shell.

1. Django check

```bash
./venv/bin/python manage.py check
```

2. Health checks

```bash
curl -fsS https://api.yourdomain.com/health/
curl -fsS https://api.yourdomain.com/ready/
```

3. CORS/CSRF smoke checks from frontend origin

Use browser network checks from https://jamborafiki.vercel.app and verify admin-auth CSRF/session flow.

## 7) Close Criteria For Section 2

Mark section 2 complete only when:

- all mandatory variables are filled and deployed
- manage.py check passes in production-like environment
- app boots with DJANGO_ENV=production and DEBUG=False
- frontend origin can authenticate and call admin APIs successfully