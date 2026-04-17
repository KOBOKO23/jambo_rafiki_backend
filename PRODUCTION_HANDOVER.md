# Production Handover

This file is the operational handover for deploying and running the backend in production.

## 1) Current readiness state

Code-level production guardrails are implemented:
- Production must use `DEBUG=False`.
- `ALLOWED_HOSTS` is mandatory in production.
- `SECRET_KEY` is mandatory in production.
- `DATABASE_URL` must be provided and must not be SQLite in production.
- SMTP config is validated for SMTP backends.
- Admin notification recipients are centralized through `ADMIN_NOTIFICATION_EMAILS`.

Open items are runtime/deployment-only and tracked in:
- [production_readiness_checklist.md](production_readiness_checklist.md)
- [production_remaining_implementation_guide.md](production_remaining_implementation_guide.md)

## 2) Deployment docs map

Start here:
- [deploy/render/render-dashboard-step-by-step.md](deploy/render/render-dashboard-step-by-step.md)

Deployment pack:
- [deploy/render/README.md](deploy/render/README.md)
- [deploy/render/launch-runbook.md](deploy/render/launch-runbook.md)
- [deploy/render/prod-env-fill-sheet.md](deploy/render/prod-env-fill-sheet.md)
- [deploy/render/.env.render.example](deploy/render/.env.render.example)
- [render.yaml](render.yaml)

## 3) Required credentials and values

Infrastructure values:
- Render service names and region
- API domain
- Render PostgreSQL connection string
- S3 bucket name and optional CDN domain

Application secrets:
- Django `SECRET_KEY`
- `DATABASE_URL`
- SMTP credentials
- M-Pesa production credentials and callback secrets
- Stripe production keys/webhook secret
- Optional Sentry DSN

## 4) Deploy order

1. Create Render PostgreSQL, web, and worker services (or use Blueprint with `render.yaml`).
2. Fill Render environment variables using `deploy/render/prod-env-fill-sheet.md`.
3. Deploy web service (with pre-deploy migrations).
4. Deploy worker service.
5. Validate health/readiness and smoke tests.
6. Observe logs and error tracking, then promote.

## 5) Operational ownership

At go-live, ensure named owners exist for:
- app deployment and rollback
- payments monitoring
- queue/worker monitoring
- incident response communications

## 6) Final gate

Do not mark production ready until all pending checkbox items are closed in [production_readiness_checklist.md](production_readiness_checklist.md).
