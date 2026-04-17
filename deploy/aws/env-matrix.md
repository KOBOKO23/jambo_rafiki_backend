# Environment Matrix (AWS)

## Core Runtime

| Variable | Staging | Production | Notes |
|---|---|---|---|
| DJANGO_ENV | staging | production | Must be production in live env |
| DEBUG | False | False | Never True in hosted env |
| ALLOWED_HOSTS | api-staging.yourdomain.com | api.yourdomain.com | Comma-separated allowed |
| FRONTEND_URL | https://staging.yourdomain.com | https://jamborafiki.vercel.app | Used in emails and links |
| CORS_ALLOWED_ORIGINS | https://staging.yourdomain.com | https://jamborafiki.vercel.app | Comma-separated |
| CSRF_TRUSTED_ORIGINS | https://staging.yourdomain.com,https://api-staging.yourdomain.com | https://jamborafiki.vercel.app,https://api.yourdomain.com | Include https scheme |

## Media Storage (S3)

| Variable | Staging | Production | Notes |
|---|---|---|---|
| USE_S3_MEDIA | True | True | Enables django-storages S3 backend |
| AWS_STORAGE_BUCKET_NAME | your-staging-media-bucket | your-prod-media-bucket | Bucket per env recommended |
| AWS_S3_REGION_NAME | af-south-1 | af-south-1 | Match bucket region |
| AWS_MEDIA_LOCATION | media | media | Prefix path in bucket |
| AWS_S3_CUSTOM_DOMAIN | cdn-staging.yourdomain.com | cdn.yourdomain.com | Optional CloudFront/custom domain |
| AWS_MEDIA_CACHE_CONTROL | max-age=3600 | max-age=86400 | CDN/object cache hint |

## Security and Observability

| Variable | Staging | Production | Notes |
|---|---|---|---|
| SECURE_SSL_REDIRECT | True | True | Enforce HTTPS |
| SESSION_COOKIE_SECURE | True | True | Secure cookie flag |
| CSRF_COOKIE_SECURE | True | True | Secure cookie flag |
| LOG_LEVEL | INFO | INFO | App logs |
| SECURITY_LOG_LEVEL | WARNING | WARNING | Security event logger |
| SENTRY_TRACES_SAMPLE_RATE | 0.05 | 0.05 | Tune by traffic |

## Secret Values (Secrets Manager)

Store each secret under a path like:
- prod/backend/<name>
- staging/backend/<name>

Required secret keys:
- SECRET_KEY
- DATABASE_URL
- EMAIL_BACKEND
- EMAIL_HOST
- EMAIL_PORT
- EMAIL_USE_TLS
- EMAIL_HOST_USER
- EMAIL_HOST_PASSWORD
- DEFAULT_FROM_EMAIL
- ADMIN_EMAIL
- MPESA_CALLBACK_TOKEN
- MPESA_CALLBACK_SIGNATURE_SECRET
- MPESA_CALLBACK_SIGNATURE_HEADER
- STRIPE_SECRET_KEY
- STRIPE_WEBHOOK_SECRET
- SENTRY_DSN
