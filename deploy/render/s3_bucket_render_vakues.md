# S3 Bucket Render Vakues

Use this guide to get AWS access keys and configure S3 media for Render.

## 1) Create IAM user for Render

1. Open AWS Console.
2. Go to IAM.
3. Go to Users.
4. Click Create user.
5. Username: jambo-rafiki-render-media
6. Do not enable console password.
7. Create user.

## 2) Add S3 permissions (inline policy)

Open user -> Permissions -> Add permissions -> Create inline policy -> JSON, then paste:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "ListBucket",
      "Effect": "Allow",
      "Action": ["s3:ListBucket"],
      "Resource": "arn:aws:s3:::jamborafiki-prod-media"
    },
    {
      "Sid": "ObjectRW",
      "Effect": "Allow",
      "Action": ["s3:GetObject", "s3:PutObject", "s3:DeleteObject"],
      "Resource": "arn:aws:s3:::jamborafiki-prod-media/*"
    }
  ]
}
```

## 3) Create access key

1. Open user -> Security credentials.
2. Access keys -> Create access key.
3. Use case: Application running outside AWS.
4. Create access key.
5. Copy:
   - AWS_ACCESS_KEY_ID
   - AWS_SECRET_ACCESS_KEY

Important: You only see the secret key once.

## 4) Render env values (copy-paste)

Set these in both services:
- jambo-rafiki-backend-web
- jambo-rafiki-backend-worker

```env
USE_S3_MEDIA=True
AWS_STORAGE_BUCKET_NAME=jamborafiki-prod-media
AWS_S3_REGION_NAME=us-east-1
AWS_MEDIA_LOCATION=media
AWS_S3_CUSTOM_DOMAIN=
AWS_MEDIA_CACHE_CONTROL=max-age=86400
AWS_ACCESS_KEY_ID=<your-iam-access-key-id>
AWS_SECRET_ACCESS_KEY=<your-iam-secret-access-key>
```

## 5) Verify

1. Redeploy web and worker.
2. Upload one image from admin.
3. Confirm URL starts with:
   https://jamborafiki-prod-media.s3.amazonaws.com/media/
