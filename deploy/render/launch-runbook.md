# Render Launch Runbook

## Pre-Deploy

1. Confirm all required environment variables are set on both web and worker.
2. Confirm PostgreSQL is reachable from the web service.
4. Confirm M-Pesa callback URL points to your Render web hostname.

## Deploy

1. Deploy web service.
2. Ensure pre-deploy migration command succeeds.
3. Deploy worker service.

## Smoke Tests

1. `GET /health/` returns 200.
2. `GET /ready/` returns 200.
3. Admin login and one admin write action succeed.
4. Contact form create succeeds.
5. Newsletter subscribe succeeds.
6. M-Pesa sandbox donation path returns initiation success and callback updates donation status.

## Post-Deploy Monitoring

1. Watch web logs for startup/migration errors.
2. Watch worker logs for queue processing and failures.
3. Verify no sensitive payloads are logged.

## Rollback

1. In Render web service, open **Deploys** and rollback to previous successful deploy.
2. Do the same for worker service.
3. Re-run `/health/` and `/ready/` checks.
4. If a migration is not backward-compatible, restore DB backup before routing traffic.
