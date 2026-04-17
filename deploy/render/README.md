# Render Deploy Pack

This folder contains Render-first deployment assets for this Django backend.

## Files

- `render.yaml` (workspace root): Blueprint for web service, worker service, and PostgreSQL.
- `deploy/render/.env.render.example`: Environment variable template.
- `deploy/render/render-dashboard-step-by-step.md`: Manual click-by-click setup in Render dashboard.
- `deploy/render/launch-runbook.md`: Post-deploy checks, smoke tests, and rollback notes.
- `deploy/render/prod-env-fill-sheet.md`: Fill sheet to track required values.

## Quick Start (Blueprint)

1. Push this repository to GitHub.
2. In Render, choose **New +** -> **Blueprint**.
3. Select this repository and apply `render.yaml`.
4. Wait for database, web, and worker to provision.
5. Open service environment variables and fill all `sync: false` values.
6. Redeploy web and worker.
7. Run smoke tests in `deploy/render/launch-runbook.md`.

## Manual Setup (No Blueprint)

Follow `deploy/render/render-dashboard-step-by-step.md` to create:
- one PostgreSQL database,
- one web service,
- one worker service.

## Notes

- Keep web and worker on the same Git branch and deploy revision.
- Use Render's managed PostgreSQL unless you intentionally keep an external DB.
- Use Render environment variables for secrets; do not commit secrets.
