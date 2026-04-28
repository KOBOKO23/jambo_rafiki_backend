# Backend Alignment Guide for Jambo Rafiki CMS

This document summarizes the frontend authentication and media upload requirements, and provides backend alignment recommendations for seamless integration.

---

## 1. Authentication & Session Management

- **Session-based authentication is required.**
- The frontend expects the following endpoints:
  - `POST /api/v1/admin/auth/login/` (with email, password, CSRF)
  - `POST /api/v1/admin/auth/logout/` (with CSRF)
  - `GET /api/v1/admin/auth/me/` (returns current user profile)
  - `GET /api/v1/admin/auth/csrf/` (returns CSRF token)
- The frontend expects a `csrf_token` in the response body from `/csrf/` and sends it as the `X-CSRFToken` header for all mutating requests.
- The backend must set `sessionid` and `csrftoken` cookies with `SameSite=Lax` or `SameSite=None; Secure` for cross-origin support.
- Only users with `is_staff: true` are allowed to access admin routes.

## 2. Media Uploads

- Endpoint: `POST /api/v1/admin/media-assets/`
- Requires authentication (valid session) and CSRF token in `X-CSRFToken` header.
- Accepts `multipart/form-data` with fields:
  - `title` (string)
  - `file` (image file)
  - `alt_text` (optional)
  - `caption` (optional)
  - `category` (string, e.g., 'CMS media')
  - `tags` (array or comma-separated string)
- Returns 201 with asset metadata on success.
- Returns 403 if not authenticated or not staff.

## 3. CSRF & CORS

- Backend must:
  - Allow the exact Vercel frontend origin.
  - Allow credentials (cookies) in CORS.
  - Trust the frontend domain for CSRF.
  - Set secure cookie policy for cross-origin session flow.
- All mutating requests (POST, PATCH, DELETE) require `X-CSRFToken` header.

## 4. Error Handling

- Return clear error codes:
  - 400: Invalid request
  - 403: Permission denied
  - 429: Too many requests
  - 500+: Server error
- Do not expose raw backend errors to the frontend.

## 5. Permissions

- Only users with `is_staff: true` (and optionally `is_superuser: true`) can access admin endpoints.
- Return 403 for insufficient permissions.

## 6. Endpoints Reference

- `/api/v1/admin/auth/csrf/` (GET)
- `/api/v1/admin/auth/login/` (POST)
- `/api/v1/admin/auth/logout/` (POST)
- `/api/v1/admin/auth/me/` (GET)
- `/api/v1/admin/media-assets/` (GET, POST)

## 7. Type Safety

- Use the following fields for user objects:
  - `id`, `email`, `username`, `first_name`, `last_name`, `is_staff`, `is_superuser`, `is_active`, `role`, `permissions`
- Media asset fields:
  - `id`, `title`, `file_url`, `alt_text`, `caption`, `category`, `tags`, `created_at`, `updated_at`

---

**Backend implementers:**
- Ensure all endpoints and behaviors above are present and match the contract.
- Test with the frontend to verify session and CSRF flow.
- See `/Docs/04-API-Contract-Integration.md` and `/Docs/09-AWS-Backend-Handover.md` for more details.
