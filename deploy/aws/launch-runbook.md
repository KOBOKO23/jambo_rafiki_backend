# AWS Launch Runbook

## 1. Pre-Launch Validation

1. Confirm RDS PostgreSQL is provisioned and reachable from ECS private subnets.
2. Confirm S3 media bucket exists and task role has read/write permissions.
3. Confirm Secrets Manager entries are present for all required secret keys.
4. Confirm ALB, target group, ACM certificate, Route53 records are configured.
5. Confirm ECS cluster, task definitions, and services (web + worker) are deployed.

## 2. One-Time Setup Commands

Run in a one-off ECS task using the same image and env/secrets as web:

1. python manage.py check
2. python manage.py migrate --noinput
3. python manage.py collectstatic --noinput
4. python manage.py createsuperuser (if needed)

## 3. Health and Readiness Checks

1. GET /health/ should return 200.
2. GET /ready/ should return 200.
3. ALB target group health check path must be /ready/.

## 4. Functional Smoke Tests

1. Public forms:
   - Contacts submission
   - Volunteers submission
   - Newsletter subscribe/unsubscribe
2. Donations:
   - mpesa (queue-backed)
   - stripe intent creation
3. Gallery upload path:
   - Create/upload image in admin
   - Confirm returned image URL is S3/CloudFront URL
4. Worker verification:
   - enqueue a test notification job
   - confirm worker logs show successful processing

## 5. Canary Rollout Steps

1. Deploy new revision to staging and validate all checks.
2. In production, shift 10% traffic to new task revision.
3. Observe 30 to 60 minutes:
   - ALB 5xx
   - ECS task restarts
   - queue processing errors
   - payment callback errors
4. Shift to 50%, observe.
5. Shift to 100% and monitor for at least one business cycle.

## 6. Rollback Procedure

1. Revert ECS service to previous stable task definition revision.
2. Confirm target group health recovers.
3. If DB migration is incompatible, execute prepared rollback/restore plan.
4. Keep incident notes with timestamps and root cause.

## 7. Post-Launch Monitoring

Set CloudWatch alarms for:
1. ALB 5xx error rate
2. ECS service running task count below desired
3. ECS task memory and CPU high utilization
4. RDS connection saturation and storage threshold
5. Application log pattern alarms for payment callback failures

Set Sentry alerts for:
1. New unhandled exception types
2. Spike in donation/payment errors
3. Worker processing failures
