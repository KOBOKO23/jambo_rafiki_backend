# Render Dashboard Step-by-Step

Use this if you do not want to use Blueprint import.

## 1) Create PostgreSQL

1. In Render dashboard, click **New +** -> **PostgreSQL**.
2. Name: `jambo-rafiki-postgres`.
3. Region: pick one close to users (for example Oregon).
4. Plan: Starter (or higher for production).
5. Click **Create Database**.
6. Copy the **Internal Database URL**.

## 2) Create Web Service

1. Click **New +** -> **Web Service**.
2. Connect this repository.
3. Name: `jambo-rafiki-backend-web`.
4. Runtime: Python.
5. Build command:
   `pip install -r requirements.txt && python manage.py collectstatic --noinput`
6. Pre-deploy command:
   `python manage.py migrate --noinput`
7. Start command:
   `gunicorn jambo_rafiki.wsgi:application --bind 0.0.0.0:$PORT --workers 3 --timeout 60`
8. Health check path: `/ready/`.

## 3) Create Worker Service

1. Click **New +** -> **Background Worker**.
2. Connect the same repository.
3. Name: `jambo-rafiki-backend-worker`.
4. Runtime: Python.
5. Build command:
   `pip install -r requirements.txt`
6. Start command:
   `python manage.py process_jobs`

## 4) Set Environment Variables (Both services)

Use values from `deploy/render/.env.render.example` and `deploy/render/prod-env-fill-sheet.md`.

Required minimum:
- `DJANGO_ENV=production`
- `DEBUG=False`
- `SECRET_KEY=<secure random value>`
- `DATABASE_URL=<render postgres internal url>`
- `ALLOWED_HOSTS=<web-service.onrender.com>`
- `FRONTEND_URL=https://jamborafiki.vercel.app`
- `CORS_ALLOWED_ORIGINS=https://jamborafiki.vercel.app`
- `CSRF_TRUSTED_ORIGINS=https://jamborafiki.vercel.app,https://<web-service.onrender.com>`
- SMTP values
- M-Pesa values

## 5) First Deploy Validation

1. Deploy web and worker.
2. Open `https://<web-service.onrender.com>/health/`.
3. Open `https://<web-service.onrender.com>/ready/`.
4. Confirm both return HTTP 200.
5. Run one M-Pesa sandbox payment test.

## 6) Custom Domain (Optional now)

1. Open web service -> **Settings** -> **Custom Domains**.
2. Add your API domain later when purchased.
3. Update `ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS`, and `MPESA_CALLBACK_URL` after domain cutover.
