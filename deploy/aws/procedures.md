# Deployment Procedures (Script-Driven)

## 1) Install Prerequisites

1. AWS CLI v2
2. Docker
3. jq
4. IAM permissions for:
   - ECR push/pull
   - ECS register task/update service/run task
   - Secrets Manager read
   - CloudWatch logs write

## 2) Prepare AWS Resources

1. Create ECS cluster and services:
   - web service (behind ALB)
   - worker service (no ALB)
2. Create ECR repository (optional: script auto-creates).
3. Create RDS PostgreSQL and set `DATABASE_URL` secret.
4. Create S3 media bucket and apply task role policy from `iam-task-role-policy.json`.
5. Create Secrets Manager entries listed in `env-matrix.md`.
6. Configure ALB health check path to `/ready/`.

## 3) Configure Deploy File

1. Copy config template:
   - `cp deploy/aws/.env.deploy.example deploy/aws/.env.deploy`
2. Fill real values in `deploy/aws/.env.deploy`.
3. Ensure `RUN_MIGRATIONS=true` for release deploys.

## 4) Run Deployment Script

1. Make script executable:
   - `chmod +x deploy/aws/scripts/deploy.sh`
2. Execute deployment:
   - `deploy/aws/scripts/deploy.sh deploy/aws/.env.deploy`

What the script does:
1. Ensures ECR repository exists.
2. Logs into ECR.
3. Builds and pushes Docker image.
4. Renders web/worker ECS task definitions.
5. Registers ECS task definitions.
6. Runs one-off migration task (if enabled).
7. Updates web + worker ECS services.
8. Waits for service stability (if enabled).

## 5) Post-Deploy Validation

1. Check:
   - `GET /health/` returns 200
   - `GET /ready/` returns 200
2. Smoke test:
   - contacts, volunteers, newsletter flows
   - donations mpesa + stripe initiation
3. Validate media upload:
   - upload image in admin
   - ensure URL is S3/CloudFront URL
4. Check CloudWatch logs for web + worker errors.

## 6) Rollback Procedure

1. Find previous task definition revisions in ECS.
2. Update services back to previous revisions.
3. Verify services stabilize and health checks pass.
4. If migration is incompatible, run your DB restore/rollback plan.
