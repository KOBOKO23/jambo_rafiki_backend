#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
AWS_DIR="$ROOT_DIR/deploy/aws"
WEB_TEMPLATE="$AWS_DIR/ecs-task-web.json"
WORKER_TEMPLATE="$AWS_DIR/ecs-task-worker.json"

if [[ $# -lt 1 ]]; then
  echo "Usage: $0 deploy/aws/.env.deploy"
  exit 1
fi

ENV_FILE="$1"
if [[ ! -f "$ENV_FILE" ]]; then
  echo "Env file not found: $ENV_FILE"
  exit 1
fi

# shellcheck disable=SC1090
source "$ENV_FILE"

require_cmd() {
  command -v "$1" >/dev/null 2>&1 || { echo "Missing command: $1"; exit 1; }
}

require_var() {
  local name="$1"
  if [[ -z "${!name:-}" ]]; then
    echo "Missing required variable: $name"
    exit 1
  fi
}

require_cmd aws
require_cmd jq
require_cmd docker
require_cmd sed

require_var AWS_REGION
require_var ECR_REPOSITORY
require_var IMAGE_TAG
require_var ECS_CLUSTER
require_var ECS_WEB_SERVICE
require_var ECS_WORKER_SERVICE
require_var API_DOMAIN
require_var FRONTEND_URL
require_var CORS_ALLOWED_ORIGINS
require_var CSRF_TRUSTED_ORIGINS
require_var USE_S3_MEDIA
require_var AWS_STORAGE_BUCKET_NAME
require_var AWS_MEDIA_LOCATION
require_var AWS_MEDIA_CACHE_CONTROL

AWS_ARGS=(--region "$AWS_REGION")
if [[ -n "${AWS_PROFILE:-}" ]]; then
  AWS_ARGS+=(--profile "$AWS_PROFILE")
fi

if [[ -z "${AWS_ACCOUNT_ID:-}" ]]; then
  AWS_ACCOUNT_ID="$(aws "${AWS_ARGS[@]}" sts get-caller-identity --query Account --output text)"
fi

ECR_IMAGE="$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPOSITORY:$IMAGE_TAG"

echo "[1/8] Ensuring ECR repository exists"
if ! aws "${AWS_ARGS[@]}" ecr describe-repositories --repository-names "$ECR_REPOSITORY" >/dev/null 2>&1; then
  aws "${AWS_ARGS[@]}" ecr create-repository --repository-name "$ECR_REPOSITORY" >/dev/null
fi

echo "[2/8] Logging in to ECR"
aws "${AWS_ARGS[@]}" ecr get-login-password | docker login --username AWS --password-stdin "$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com"

echo "[3/8] Building and pushing image: $ECR_IMAGE"
docker build -t "$ECR_IMAGE" "$ROOT_DIR"
docker push "$ECR_IMAGE"

TMP_DIR="$(mktemp -d)"
cleanup() { rm -rf "$TMP_DIR"; }
trap cleanup EXIT

render_task_def() {
  local in_file="$1"
  local out_file="$2"
  local is_web="$3"

  sed -e "s|<ACCOUNT_ID>|$AWS_ACCOUNT_ID|g" \
      -e "s|<REGION>|$AWS_REGION|g" \
      -e "s|<IMAGE_TAG>|$IMAGE_TAG|g" \
      "$in_file" > "$out_file"

  jq \
    --arg image "$ECR_IMAGE" \
    --arg api_domain "$API_DOMAIN" \
    --arg frontend "$FRONTEND_URL" \
    --arg cors "$CORS_ALLOWED_ORIGINS" \
    --arg csrf "$CSRF_TRUSTED_ORIGINS" \
    --arg use_s3 "$USE_S3_MEDIA" \
    --arg bucket "$AWS_STORAGE_BUCKET_NAME" \
    --arg media_loc "$AWS_MEDIA_LOCATION" \
    --arg custom_domain "${AWS_S3_CUSTOM_DOMAIN:-}" \
    --arg media_cache "$AWS_MEDIA_CACHE_CONTROL" \
    --arg log_level "${LOG_LEVEL:-INFO}" \
    --arg sec_level "${SECURITY_LOG_LEVEL:-WARNING}" \
    --arg traces "${SENTRY_TRACES_SAMPLE_RATE:-0.05}" \
    '
    .containerDefinitions[0].image = $image |
    .containerDefinitions[0].environment |= map(
      if .name == "ALLOWED_HOSTS" then .value = $api_domain
      elif .name == "FRONTEND_URL" then .value = $frontend
      elif .name == "CORS_ALLOWED_ORIGINS" then .value = $cors
      elif .name == "CSRF_TRUSTED_ORIGINS" then .value = $csrf
      elif .name == "USE_S3_MEDIA" then .value = $use_s3
      elif .name == "AWS_STORAGE_BUCKET_NAME" then .value = $bucket
      elif .name == "AWS_MEDIA_LOCATION" then .value = $media_loc
      elif .name == "AWS_S3_CUSTOM_DOMAIN" then .value = $custom_domain
      elif .name == "AWS_MEDIA_CACHE_CONTROL" then .value = $media_cache
      elif .name == "LOG_LEVEL" then .value = $log_level
      elif .name == "SECURITY_LOG_LEVEL" then .value = $sec_level
      elif .name == "SENTRY_TRACES_SAMPLE_RATE" then .value = $traces
      else . end
    )
    ' "$out_file" > "$out_file.tmp"

  mv "$out_file.tmp" "$out_file"

  if [[ "$is_web" != "true" ]]; then
    jq 'del(.containerDefinitions[0].environment[] | select(.name == "ALLOWED_HOSTS" or .name == "FRONTEND_URL" or .name == "CORS_ALLOWED_ORIGINS" or .name == "CSRF_TRUSTED_ORIGINS" or .name == "SENTRY_TRACES_SAMPLE_RATE"))' "$out_file" > "$out_file.tmp"
    mv "$out_file.tmp" "$out_file"
  fi
}

WEB_RENDERED="$TMP_DIR/web-task.json"
WORKER_RENDERED="$TMP_DIR/worker-task.json"

echo "[4/8] Rendering task definitions"
render_task_def "$WEB_TEMPLATE" "$WEB_RENDERED" true
render_task_def "$WORKER_TEMPLATE" "$WORKER_RENDERED" false

register_task() {
  local file="$1"
  aws "${AWS_ARGS[@]}" ecs register-task-definition --cli-input-json "file://$file" --query 'taskDefinition.taskDefinitionArn' --output text
}

echo "[5/8] Registering ECS task definitions"
WEB_TASK_ARN="$(register_task "$WEB_RENDERED")"
WORKER_TASK_ARN="$(register_task "$WORKER_RENDERED")"
echo "Web task: $WEB_TASK_ARN"
echo "Worker task: $WORKER_TASK_ARN"

run_migrations() {
  require_var ECS_SUBNET_IDS
  require_var ECS_SECURITY_GROUP_IDS

  IFS=',' read -r -a subnets <<< "$ECS_SUBNET_IDS"
  IFS=',' read -r -a sec_groups <<< "$ECS_SECURITY_GROUP_IDS"

  subnet_json="$(printf '"%s",' "${subnets[@]}" | sed 's/,$//')"
  secgroup_json="$(printf '"%s",' "${sec_groups[@]}" | sed 's/,$//')"

  echo "[6/8] Running one-off migrations task"
  task_arn="$(aws "${AWS_ARGS[@]}" ecs run-task \
    --cluster "$ECS_CLUSTER" \
    --launch-type FARGATE \
    --task-definition "$WEB_TASK_ARN" \
    --count 1 \
    --network-configuration "awsvpcConfiguration={subnets=[$subnet_json],securityGroups=[$secgroup_json],assignPublicIp=DISABLED}" \
    --overrides '{"containerOverrides":[{"name":"web","command":["python","manage.py","migrate","--noinput"]}]}' \
    --query 'tasks[0].taskArn' --output text)"

  aws "${AWS_ARGS[@]}" ecs wait tasks-stopped --cluster "$ECS_CLUSTER" --tasks "$task_arn"

  exit_code="$(aws "${AWS_ARGS[@]}" ecs describe-tasks --cluster "$ECS_CLUSTER" --tasks "$task_arn" --query 'tasks[0].containers[0].exitCode' --output text)"
  if [[ "$exit_code" != "0" ]]; then
    echo "Migration task failed with exit code $exit_code"
    exit 1
  fi
}

if [[ "${RUN_MIGRATIONS:-false}" == "true" ]]; then
  run_migrations
else
  echo "[6/8] Skipping migrations (RUN_MIGRATIONS=${RUN_MIGRATIONS:-false})"
fi

echo "[7/8] Updating ECS services"
aws "${AWS_ARGS[@]}" ecs update-service --cluster "$ECS_CLUSTER" --service "$ECS_WEB_SERVICE" --task-definition "$WEB_TASK_ARN" >/dev/null
aws "${AWS_ARGS[@]}" ecs update-service --cluster "$ECS_CLUSTER" --service "$ECS_WORKER_SERVICE" --task-definition "$WORKER_TASK_ARN" >/dev/null

if [[ "${WAIT_FOR_STABLE:-true}" == "true" ]]; then
  echo "[8/8] Waiting for ECS services to stabilize"
  aws "${AWS_ARGS[@]}" ecs wait services-stable --cluster "$ECS_CLUSTER" --services "$ECS_WEB_SERVICE" "$ECS_WORKER_SERVICE"
else
  echo "[8/8] Skipping wait-for-stable"
fi

echo "Deployment complete."
