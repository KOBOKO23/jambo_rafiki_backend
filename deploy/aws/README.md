# AWS Deploy Pack

This folder contains deploy-ready templates for ECS/Fargate deployment.

## Files

- ecs-task-web.json
- ecs-task-worker.json
- iam-task-role-policy.json
- env-matrix.md
- launch-runbook.md
- .env.deploy.example
- procedures.md
- scripts/deploy.sh

## Quick Start (Script-Driven)

1. Copy environment template:
	- cp deploy/aws/.env.deploy.example deploy/aws/.env.deploy
2. Fill real values in deploy/aws/.env.deploy.
3. Make deploy script executable:
	- chmod +x deploy/aws/scripts/deploy.sh
4. Run deployment:
	- deploy/aws/scripts/deploy.sh deploy/aws/.env.deploy
5. Follow post-deploy checks in launch-runbook.md.

## Manual Apply Order (If Not Using Script)

1. Create/update IAM task role policy using iam-task-role-policy.json.
2. Create Secrets Manager values listed in env-matrix.md.
3. Replace placeholders in ecs-task-web.json and ecs-task-worker.json.
4. Register ECS task definitions.
5. Update ECS services to new task definitions.
6. Verify ALB health checks point to /ready/.
7. Execute launch-runbook.md (pre-launch checks, smoke tests, canary, rollback readiness).

## Placeholder Checklist

- ACCOUNT_ID
- REGION
- IMAGE_TAG
- yourdomain.com values
- bucket and CDN values

## Notes

- Keep USE_S3_MEDIA=True for durable image URLs consumed by frontend.
- Use task role IAM permissions for S3 and Secrets Manager (avoid static AWS keys).
