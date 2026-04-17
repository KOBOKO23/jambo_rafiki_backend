# Production Remaining Implementation Guide

This guide covers the checklist items that still require deployment-side work, real secrets, or live verification. It is the execution companion to the production readiness checklist and the Render deploy pack.

## Already enforced in code

The backend now fails fast when production configuration is incomplete:
- `DEBUG` must be `False` in production.
- `ALLOWED_HOSTS` must be present and non-empty.
- `SECRET_KEY` must be present.
- `DATABASE_URL` must point to a non-SQLite production database.
- `EMAIL_BACKEND` must be set.
- SMTP backends require `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_HOST_USER`, and `EMAIL_HOST_PASSWORD`.
- Admin notification emails use the shared recipient list.

## Execution Order

1. Fill production secrets and env vars.
2. Deploy to staging.
3. Run migrations and collectstatic in a one-off task.
4. Run health, readiness, and smoke tests.
5. Enable canary rollout.
6. Observe metrics and logs.
7. Promote to full production.
8. Rehearse rollback.

## 3) Security Readiness

What to implement:
- Rotate all webhook, payment, and admin secrets before go-live.
- Keep `SECURE_SSL_REDIRECT=True`, `SESSION_COOKIE_SECURE=True`, and `CSRF_COOKIE_SECURE=True` in production.
- Confirm HSTS and security headers are present through the Render edge and app responses.
- Make sure logs never capture passwords, tokens, or callback payloads.

How to implement:
- Store new secrets in Render environment variables using [deploy/render/prod-env-fill-sheet.md](deploy/render/prod-env-fill-sheet.md).
- Redeploy the web service after secret rotation.
- Verify the live response headers through the Render web service URL.

Verification:
- `curl -I https://api.yourdomain.com/health/`
- `curl -I https://api.yourdomain.com/ready/`
- Check Render logs or your log sink for sensitive payload leakage.

## 4) Database And Migration Safety

What to implement:
- Use PostgreSQL in production through `DATABASE_URL`.
- Create a backup or snapshot before each production deployment.
- Keep a tested restore path for the last known good database state.

How to implement:
- Create a PostgreSQL backup before the release window.
- Run `python manage.py migrate --noinput` through Render pre-deploy command before cutting traffic.
- Keep the previous backup and schema version noted in the release log.

Verification:
- Restore the snapshot into a staging clone once before go-live.
- Boot the app against that restore and confirm readiness succeeds.

## 5) Media And Image Pipeline

What to implement:
- Set `USE_S3_MEDIA=True` if you want durable image hosting.
- Fill `AWS_STORAGE_BUCKET_NAME`, `AWS_S3_REGION_NAME`, and optionally `AWS_S3_CUSTOM_DOMAIN`.
- Validate admin uploads, page-section images, gallery images, and branding assets.

How to implement:
- Create the S3 bucket and grant the Render service IAM/user access with least privilege.
- If using CloudFront or a custom domain, set `AWS_S3_CUSTOM_DOMAIN` and verify MEDIA_URL generation.
- Keep `AWS_MEDIA_LOCATION=media` unless you have a strong reason to change it.

Verification:
- Upload a test image through the admin placement endpoint.
- Confirm the public placement feed returns reachable URLs.
- Confirm favicon/logo updates appear in the frontend after deploy.

## 6) Payments And External Integrations

What to implement:
- Configure live M-Pesa credentials and callback URL.
- Configure live Stripe keys and webhook secret if Stripe is enabled.
- Ensure callback validation is enabled in production.

How to implement:
- Store live payment secrets in Render environment variables.
- Set the callback URL to the production API hostname.
- Confirm the Render web service and backend allow inbound callbacks from the payment providers.

Verification:
- Run a low-value payment smoke test.
- Replay the callback and confirm the state transition remains idempotent.

## 7) Background Jobs And Reliability

What to implement:
- Run the worker as a separate always-on Render background worker.
- Add backlog and failure alerting.
- Verify retry behavior on failed jobs.

How to implement:
- Use the worker deployment in [render.yaml](render.yaml) or manual setup in [deploy/render/render-dashboard-step-by-step.md](deploy/render/render-dashboard-step-by-step.md).
- Scale the worker service independently from the web service.
- Add Render alerts and external monitoring for repeated failures and queue lag.

Verification:
- Enqueue a known failing job and observe retries and final failure.
- Confirm the worker drains a normal queue backlog.

## 8) Observability And Operations

What to implement:
- Expose `/health/` and `/ready/` through the Render web service.
- Stream web and worker logs to a centralized log destination.
- Add alerts for application exceptions, queue failures, and payment issues.

How to implement:
- Configure the Render health check path to `/ready/`.
- Create dashboard views for Render web and worker logs.
- Wire Sentry or your error tracker using `SENTRY_DSN`.

Verification:
- `curl https://api.yourdomain.com/health/`
- `curl https://api.yourdomain.com/ready/`
- Confirm alert delivery to the operational owner group.

## 9) Performance Verification

What to implement:
- Test list endpoints under realistic traffic.
- Review query plans for the most expensive reads.
- Confirm pagination keeps response sizes bounded.

How to implement:
- Run a small load test from a controlled environment.
- Inspect the endpoints that sort or filter heavily.
- Watch DB CPU, query latency, and app response times during the test.

Verification:
- Capture p95 latency for the major public endpoints.
- Confirm memory and CPU remain within the service envelope.

## 10) Deployment Process And Rollback

What to implement:
- Build a reproducible production image.
- Deploy to staging before production.
- Perform a canary release before full rollout.
- Rehearse rollback once.

How to implement:
- Follow [deploy/render/render-dashboard-step-by-step.md](deploy/render/render-dashboard-step-by-step.md).
- Follow [deploy/render/launch-runbook.md](deploy/render/launch-runbook.md) for launch sequence and smoke tests.
- Keep the previous successful Render deploy ready for rollback.

Verification:
- Confirm staging and production use the same git revision/deploy configuration.
- Confirm you can revert Render services without data loss.

## 11) Frontend Contract Validation

What to implement:
- Validate the deployed frontend against `/api/v1/`.
- Confirm media rendering works for all supported image sources.
- Confirm no frontend screen depends on removed legacy fields.

How to implement:
- Use the deployed frontend at `https://jamborafiki.vercel.app`.
- Walk through admin image upload, public render, contact, volunteer, newsletter, and donation flows.
- Check CORS and CSRF from browser network traces.

Verification:
- Admin upload succeeds and public image URLs render correctly.
- No frontend console errors for API field mismatches.

## 12) Final Go-Live Gate

Do not promote to full production until:
- all production secrets are deployed,
- the staging smoke test pack passes,
- one canary deployment is stable,
- rollback has been rehearsed,
- product, engineering, and operations sign off.

## Primary references

- [Production readiness checklist](production_readiness_checklist.md)
- [Section 2 env fill sheet](deploy/render/prod-env-fill-sheet.md)
- [Render dashboard step-by-step](deploy/render/render-dashboard-step-by-step.md)
- [Render launch runbook](deploy/render/launch-runbook.md)
- [Render deploy pack](deploy/render/README.md)
