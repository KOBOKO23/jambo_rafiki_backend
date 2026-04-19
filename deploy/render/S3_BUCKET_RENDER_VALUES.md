# S3 Bucket Values for Render (Copy-Paste)

Use these in both Render services:
- jambo-rafiki-backend-web
- jambo-rafiki-backend-worker

---

## A) Fixed bucket values

USE_S3_MEDIA=True
AWS_STORAGE_BUCKET_NAME=jamborafiki-prod-media
AWS_S3_REGION_NAME=us-east-1
AWS_MEDIA_LOCATION=media
AWS_S3_CUSTOM_DOMAIN=
AWS_MEDIA_CACHE_CONTROL=max-age=86400

---

## B) Required AWS credentials (paste your own values)

AWS_ACCESS_KEY_ID=<your-iam-access-key-id>
AWS_SECRET_ACCESS_KEY=<your-iam-secret-access-key>

---

## C) Ready block for Render env (copy all)

USE_S3_MEDIA=True
AWS_STORAGE_BUCKET_NAME=jamborafiki-prod-media
AWS_S3_REGION_NAME=us-east-1
AWS_MEDIA_LOCATION=media
AWS_S3_CUSTOM_DOMAIN=
A_CACHE_CONTROL=max-age=86400
AWS_ACCESS_KEY_ID=<your-iam-access-key-id>
AWS_SECRET_ACCESS_KEY=<your-iam-secret-access-key>

---

## D) Quick check after deploy

1. Upload one image in admin.
2. Confirm image URL starts with:
https://jamborafiki-prod-media.s3.amazonaws.com/media/
WS_MEDIA