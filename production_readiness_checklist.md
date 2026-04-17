# Production Readiness Checklist (10/10 Plan)

This checklist is the execution plan to move from current state to a full production-ready backend.

Status legend:
- [x] completed
- [ ] pending
- [*] implemented in code but must be validated in production environment

## 0) Current Baseline

- [x] Full local test suite passes.
- [x] Django system check passes.
- [x] Fresh-database migration run succeeds.
- [ ] Release branch is clean (no uncommitted/untracked changes).

Verification note:
- Full suite: `./venv/bin/python manage.py test -v 0` -> OK (171 tests).
- Django checks: `./venv/bin/python manage.py check` -> OK.
- Fresh DB migrate: `DATABASE_URL=sqlite:////tmp/<fresh>.sqlite3 ./venv/bin/python manage.py migrate --noinput` -> OK.

## 1) Code And Release Hygiene

Goal: produce a deployable, auditable release branch.

- [ ] Decide which current modified files are intended for release.
- [ ] Commit intended changes in focused commits.
- [ ] Remove or ignore non-release files.
- [ ] Ensure git status is clean.
- [ ] Tag release candidate (for example v1.0.0-rc1).

Definition of done:
- [ ] Release branch is clean and tagged.

## 2) Configuration Readiness

Goal: ensure production settings are safe and complete.

- [ ] DEBUG is false in production.
- [ ] ALLOWED_HOSTS contains only valid production hosts.
- [ ] SECRET_KEY is injected from secure environment.
- [ ] CSRF_TRUSTED_ORIGINS is configured correctly.
- [ ] DATABASE_URL points to production database.
- [ ] EMAIL_BACKEND and SMTP/provider credentials are configured.
- [ ] USE_S3_MEDIA is enabled if durable media hosting is required.
- [ ] S3 bucket/domain settings are configured correctly.
- [ ] SENTRY_DSN (or equivalent) is configured.

Definition of done:
- [ ] Production environment starts cleanly with all required env vars.

## 3) Security Readiness

Goal: reduce exploit and misconfiguration risk.

- [x] Admin API requires authenticated staff access.
- [x] CSRF protection is enforced for session-based admin mutations.
- [x] High-risk public endpoints are throttled.
- [ ] Rotate and verify all production webhook/payment secrets.
- [ ] Verify HTTPS and secure cookie behavior in production.
- [ ] Verify HSTS/security headers in live responses.
- [ ] Verify logs contain no secrets or sensitive payload leakage.

Definition of done:
- [ ] Security checks pass in staging and production smoke tests.

## 4) Database And Migration Safety

Goal: eliminate migration and data-loss risk.

- [x] Migrations apply on a fresh database.
- [ ] Verify migration path from current production snapshot.
- [ ] Confirm no destructive migration without rollback strategy.
- [ ] Confirm automated backups exist.
- [ ] Rehearse restore procedure.

Definition of done:
- [ ] Backup and restore verified, migrations validated for prod upgrade path.

## 5) Media And Image Pipeline

Goal: make all media flows durable and frontend-safe.

- [x] Gallery APIs provide image_url.
- [x] Media asset APIs provide file_url.
- [x] Admin destination-aware image placement upload is implemented.
- [x] Public image placement feed is implemented.
- [ ] Validate upload and render flows end-to-end in staging frontend.
- [ ] Validate logo and favicon updates propagate correctly.
- [ ] Validate S3/CDN URL behavior in production.

Definition of done:
- [ ] Admin upload and public render pass for all supported destinations.

## 6) Payments And External Integrations

Goal: ensure money movement and callbacks are safe and observable.

- [x] Donation callback handling is idempotent.
- [x] Reconciliation telemetry exists.
- [ ] Verify live M-Pesa credentials and callback endpoint.
- [ ] Verify live Stripe credentials and webhook endpoint.
- [ ] Execute controlled end-to-end payment smoke tests.
- [ ] Confirm callback replay does not duplicate state transitions.

Definition of done:
- [ ] Payment flows pass monitored smoke tests with expected statuses.

## 7) Background Jobs And Reliability

Goal: ensure async work is reliably processed.

- [x] Durable job queue is present.
- [x] Worker command exists.
- [ ] Deploy worker as always-on production service.
- [ ] Validate retry behavior on failed jobs.
- [ ] Add alerting for queue backlog and repeated failures.

Definition of done:
- [ ] Queue remains healthy under expected load and failure simulations.

## 8) Observability And Operations

Goal: make failures visible and actionable.

- [x] Health and readiness endpoints exist.
- [ ] Verify /health and /ready through production load balancer.
- [ ] Ensure centralized logs are queryable.
- [ ] Ensure error alerts route to owners.
- [ ] Add dashboard panels for jobs, payment failures, and callback errors.

Definition of done:
- [ ] On-call can detect and triage incidents without SSHing into hosts.

## 9) Performance Verification

Goal: confirm behavior under realistic traffic.

- [ ] Run load tests for public high-traffic endpoints.
- [ ] Run query-plan checks for critical DB queries.
- [ ] Validate cache hit behavior and invalidation.
- [ ] Validate pagination and response size on large datasets.

Definition of done:
- [ ] P95/P99 latency and DB load are within accepted targets.

## 10) Deployment Process And Rollback

Goal: ship safely and recover quickly.

- [x] Deployment assets exist (Docker and AWS deploy pack).
- [ ] Build production image reproducibly.
- [ ] Deploy to staging and run full smoke test pack.
- [ ] Perform canary rollout.
- [ ] Validate rollback runbook with one rehearsal.

Definition of done:
- [ ] Team can deploy and rollback within agreed time window.

## 11) Frontend Contract Validation

Goal: ensure backend and finished frontend align fully.

- [ ] Validate frontend against deployed /api/v1 base.
- [ ] Validate media rendering for all image sources.
- [ ] Validate image placement endpoints from admin and public UIs.
- [ ] Confirm no frontend dependence on removed/legacy fields.

Definition of done:
- [ ] No integration regressions in staging sign-off.

## 12) Final Go-Live Gate

Only go live when all pending items in sections 1 to 11 are closed.

- [ ] Product sign-off
- [ ] Engineering sign-off
- [ ] Operations sign-off

Go-live sequence:
1. Deploy to staging.
2. Run smoke tests.
3. Run canary.
4. Monitor for stability window.
5. Promote to full production.
