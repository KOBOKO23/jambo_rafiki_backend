# Backend Exposed APIs (Frontend Handoff)

This file documents the currently exposed backend APIs from the Django/DRF server.

## Base URL and Versioning

- Preferred prefix: `/api/v1/`
- Backward-compatible prefix: `/api/`
- Frontend should target `/api/v1/` for all new work.

Examples:
- `/api/v1/donations/mpesa/`
- `/api/v1/gallery/photos/random/`

## Auth, CSRF, and Throttling

- Default auth for protected routes: `SessionAuthentication`
- Public routes are explicitly marked `AllowAny`.
- Admin routes require staff/admin user (`IsAdminUser`).
- For session-authenticated mutating admin calls (`POST/PATCH/PUT/DELETE`), include CSRF token.
- Public high-risk endpoints are throttled:
  - `public_forms`
  - `donation_initiation`
  - `payment_callbacks`

## Response Patterns

### Paginated list format (typical DRF)

```json
{
  "count": 123,
  "next": "http://.../page=2",
  "previous": null,
  "results": []
}
```

### Validation error format

```json
{
  "field_name": ["Error message"]
}
```

## Operational Endpoints

### GET /api/v1/organization/
- Access: Public
- Purpose: Frontend bootstrap endpoint for organization website/contact/bank transfer details
- Response 200:
```json
{
  "website": {
    "domain": "www.jamborafiki.org",
    "url": "https://www.jamborafiki.org"
  },
  "contact": {
    "email": "infodirector@jamborafiki.org",
    "call_redirect_number": "+254799616542",
    "call_redirect_url": "tel:+254799616542"
  },
  "bank_account": {
    "bank_code": "07",
    "branch_code": "123",
    "swift_code": "CBAFKENX",
    "account_name": "Benjamin Oyoo Ondoro",
    "account_number": "1002622088"
  },
  "timestamp": "2026-04-16T12:00:00Z"
}
```

### GET /health/
- Access: Public
- Purpose: Liveness probe
- Response 200:
```json
{
  "status": "ok",
  "service": "jambo-rafiki-backend",
  "timestamp": "2026-04-15T12:00:00Z"
}
```

### GET /ready/
- Access: Public
- Purpose: Readiness probe (checks DB connectivity)
- Response 200 when ready:
```json
{
  "status": "ready",
  "checks": {"database": "ok"},
  "timestamp": "2026-04-15T12:00:00Z"
}
```
- Response 503 when not ready:
```json
{
  "status": "not_ready",
  "checks": {"database": "error"},
  "errors": {"database": "..."},
  "timestamp": "2026-04-15T12:00:00Z"
}
```

---

## Contacts API

Base: `/api/v1/contacts/`

### POST /
- Access: Public
- Purpose: Submit contact form
- Request body:
```json
{
  "name": "John Omondi",
  "email": "john@example.com",
  "subject": "Inquiry",
  "message": "I would like to know more..."
}
```
- Response 201:
```json
{
  "message": "Thank you for your message! We will get back to you soon.",
  "data": {
    "id": 1,
    "name": "John Omondi",
    "email": "john@example.com",
    "subject": "Inquiry",
    "message": "I would like to know more...",
    "created_at": "...",
    "is_read": false
  }
}
```

### GET /
- Access: Admin only
- Purpose: List contact submissions (paginated)

### GET /{id}/
- Access: Admin only
- Purpose: Retrieve submission detail

### PATCH /{id}/mark_read/
- Access: Admin only
- Purpose: Mark submission as read

---

## Donations API

Base: `/api/v1/donations/`

### POST /mpesa/
- Access: Public
- Purpose: Queue-backed M-Pesa initiation (default path)
- Request body:
```json
{
  "donor_name": "Jane Wanjiku",
  "donor_email": "jane@example.com",
  "donor_phone": "0712345678",
  "amount": "500.00",
  "currency": "KES",
  "donation_type": "one_time",
  "purpose": "Education support",
  "message": "Keep it up",
  "is_anonymous": false
}
```
- Response 202:
```json
{
  "message": "Donation accepted and queued for M-Pesa initiation.",
  "donation_id": 101,
  "job_id": 501,
  "status": "pending"
}
```

### POST /mpesa-async/
- Access: Public
- Purpose: Explicit async alias for queue-backed M-Pesa initiation
- Contract: same as `/mpesa/`

### POST /mpesa-sync/
- Access: Public
- Purpose: Immediate M-Pesa initiation
- Request body: same as `/mpesa/`
- Success response 200:
```json
{
  "message": "Please check your phone for M-Pesa prompt",
  "donation_id": 101,
  "checkout_request_id": "ws_CO_...",
  "merchant_request_id": "..."
}
```
- Failure responses:
  - 400 for provider/business validation failure
  - 500 for unexpected server exception

### POST /stripe/
- Access: Public
- Purpose: Create Stripe PaymentIntent; completion is webhook-driven
- Request body:
```json
{
  "donor_name": "Jane Wanjiku",
  "donor_email": "jane@example.com",
  "amount": "50.00",
  "currency": "USD",
  "donation_type": "one_time",
  "purpose": "General",
  "message": "",
  "is_anonymous": false,
  "payment_method_id": "pm_optional"
}
```
- Response 202:
```json
{
  "message": "Payment initiated. Complete the payment in the frontend and wait for webhook confirmation.",
  "donation_id": 102,
  "payment_intent_id": "pi_...",
  "client_secret": "...",
  "status": "requires_payment_method"
}
```

### GET /
- Access: Admin only
- Purpose: List donations (paginated)

### GET /{id}/
- Access: Admin only
- Purpose: Donation detail

### GET /reconciliation/
- Access: Admin only
- Purpose: Payment operations summary
- Response 200 shape:
```json
{
  "generated_at": "...",
  "donation_status_counts": {"pending": 10, "completed": 20},
  "stale_processing_count": 1,
  "stale_processing": [
    {
      "id": 12,
      "payment_method": "stripe",
      "status": "processing",
      "created_at": "...",
      "updated_at": "...",
      "transaction_id": "STRIPE-..."
    }
  ],
  "callbacks_last_24h": {
    "total": 15,
    "unprocessed": 2,
    "orphans": 1
  }
}
```

### POST /mpesa-callback/
- Access: Public (provider callback endpoint)
- Notes:
  - Optional HMAC signature check if configured
  - Optional callback token query param check if configured
  - Replay-safe idempotent callback persistence
- Success response: HTTP 200 with `ResultCode`

### POST /stripe-webhook/
- Access: Public (provider callback endpoint)
- Notes:
  - Stripe signature required
  - Replay-safe idempotent callback persistence
- Success response:
```json
{"received": true}
```

### Donation enums (frontend typing)
- `payment_method`: `mpesa | stripe | paypal | bank | cash | other`
- `status`: `pending | processing | completed | failed | refunded | cancelled`
- `donation_type`: `one_time | monthly | quarterly | annual`
- `currency`: `KES | USD | EUR | GBP`

---

## Volunteers API

Base: `/api/v1/volunteers/`

### POST /
- Access: Public
- Purpose: Submit volunteer application
- Request body:
```json
{
  "name": "David Mwangi",
  "email": "david@example.com",
  "phone": "0712345678",
  "location": "Nairobi, Kenya",
  "skills": "Teaching and mentoring",
  "availability": "Weekends",
  "duration": "3 months",
  "motivation": "I want to support children in education...",
  "experience": "Optional",
  "areas_of_interest": "Optional"
}
```
- Response 201:
```json
{
  "message": "Thank you for your application! We will contact you soon.",
  "data": {"id": 1, "status": "pending", "...": "..."}
}
```

### GET /
- Access: Admin only
- Purpose: List applications

### GET /{id}/
- Access: Admin only
- Purpose: Application detail

### PATCH /{id}/update_status/
- Access: Admin only
- Request body:
```json
{"status": "approved"}
```
- Valid status values:
  - `pending`
  - `reviewing`
  - `approved`
  - `rejected`
  - `contacted`
  - `scheduled`

---

## Newsletter API

Base: `/api/v1/newsletter/`

### POST /
- Access: Public
- Purpose: Subscribe email
- Request body:
```json
{
  "email": "person@example.com",
  "name": "Optional name",
  "source": "homepage_footer"
}
```
- Responses:
  - 201: new subscription
  - 200: already subscribed or re-subscribed

### POST /unsubscribe/
- Access: Public
- Purpose: Unsubscribe email
- Request body:
```json
{"email": "person@example.com"}
```
- Responses:
  - 200: unsubscribed or already not present
  - 400: missing email

### GET /
- Access: Admin only
- Purpose: List subscribers

### GET /{id}/
- Access: Admin only
- Purpose: Subscriber detail

---

## Sponsorships API

Base: `/api/v1/sponsorships/`

### Children (public)

#### GET /children/
- Access: Public
- Purpose: List children needing sponsorship (`needs_sponsor=true`)

#### GET /children/{id}/
- Access: Public
- Purpose: Child detail

Child fields:
- `id`, `first_name`, `last_name`, `age`, `gender`, `bio`, `interests`, `photo`, `photo_url`, `is_sponsored`, `needs_sponsor`

### Sponsors (admin)

#### GET /sponsors/
#### POST /sponsors/
#### GET /sponsors/{id}/
#### PUT/PATCH /sponsors/{id}/
#### DELETE /sponsors/{id}/
- Access: Admin only

### Sponsorship records (admin)

#### GET /sponsorships/
#### POST /sponsorships/
#### GET /sponsorships/{id}/
#### PUT/PATCH /sponsorships/{id}/
#### DELETE /sponsorships/{id}/
- Access: Admin only
- Notes:
  - Query optimized with `select_related(child, sponsor)`
  - `child + sponsor` pair must be unique

### Public interest form

#### POST /interest/
- Access: Public
- Request body:
```json
{
  "name": "Jane Wanjiku",
  "email": "jane@example.com",
  "phone": "0712345678",
  "preferred_level": "Basic"
}
```
- `preferred_level` values: `Basic | Premium | Full`
- Response 201:
```json
{"message": "Interest registered successfully!"}
```

---

## Gallery API

Base: `/api/v1/gallery/`

### Categories (public)

#### GET /categories/
- Access: Public
- Purpose: Active categories with annotated `count`
- Response item fields:
  - `id`, `name`, `slug`, `description`, `icon`, `color`, `count`

#### GET /categories/{slug}/
- Access: Public
- Purpose: Category detail with nested active photos
- Detail fields include `photos`

### Photos (public)

#### GET /photos/
- Access: Public
- Pagination: custom page size default 12, `page_size` max 100
- Filters:
  - `category`
  - `is_featured`
  - `date_taken`
- Search:
  - `search` across `title`, `description`
- Ordering:
  - `ordering=date_taken|created_at` (prefix with `-` for desc)

#### GET /photos/featured/
- Access: Public
- Purpose: Top featured photos (max 8)

#### GET /photos/random/?count=30
- Access: Public
- Purpose: Randomized bounded-ID sample for performant random feed
- `count` min 1, max 100

Photo fields:
- `id`, `title`, `description`, `image`, `image_url`, `category`, `category_name`, `date_taken`, `is_featured`, `created_at`

---

## Testimonials API

Base: `/api/v1/testimonials/`

### GET /
- Access: Public
- Purpose: List approved testimonials only (paginated)
- Public response fields per item:
  - `id`, `name`, `display_role`, `text`, `approved_at`

### POST /
- Access: Public
- Purpose: Submit testimonial (created as pending)
- Request body:
```json
{
  "name": "Grace Atieno",
  "email": "grace@example.com",
  "role": "volunteer",
  "role_custom": "Optional custom role",
  "text": "At least 20 characters..."
}
```
- `role` values:
  - `community_member`
  - `volunteer`
  - `donor`
  - `sponsor`
  - `partner`
  - `other`
- Response 201:
```json
{
  "message": "Thank you for sharing your story! Your testimonial will appear on the site once reviewed."
}
```

### GET /pending/
- Access: Admin only
- Purpose: List pending testimonials

### PATCH /{id}/approve/
- Access: Admin only
- Purpose: Approve testimonial

### PATCH /{id}/reject/
- Access: Admin only
- Purpose: Reject testimonial
- Request body supports:
```json
{"notes": "Reason"}
```

### GET /{id}/
- Access: Admin only
- Purpose: Full testimonial detail

---

## Frontend Alignment Notes

- Use `/api/v1/` paths in all frontend API clients.
- Treat webhook endpoints as backend-only (not called by browser UI).
- Distinguish public submit endpoints from admin management endpoints.
- Build TypeScript enums/types from the enum sections above.
- Handle both 200 and 201 success for newsletter subscribe flows.
- Handle 202 for async payment initiation (`/donations/mpesa/`, `/donations/stripe/`).
- Implement global handling for 400, 403, 429, and 500 responses.

## Backend Implementation Addendum (15 April 2026)

This section reflects the current frontend implementation and should be treated as mandatory backend alignment for donations and card processing.

### Donation UX assumptions now live in frontend

- The "Your Donation at Work" cards are clickable and prefill donation amounts in the form:
  - Education Transforms: `KES 1000`
  - Learning Empowers: `KES 5000`
  - Health Matters: `KES 10000`
- Bank transfer is removed from the donation UI.
- Active payment methods in UI are now:
  - `mpesa`
  - `card` (Stripe)

### Stripe flow currently implemented in frontend

Frontend card flow is:

1. Frontend calls `POST /api/v1/donations/stripe/` with donation metadata.
2. Backend returns `client_secret` for the created PaymentIntent.
3. Frontend confirms the payment with Stripe SDK using `confirmCardPayment(client_secret, ...)`.
4. Backend final source of truth remains webhook processing.

Backend must therefore:

- Always return these fields on successful Stripe initiation:
  - `message`
  - `donation_id`
  - `payment_intent_id`
  - `client_secret`
  - `status`
- Keep response code `202` for initiation success.
- Keep webhook endpoint authoritative for final donation status transitions.

### Stripe request body requirements

`POST /api/v1/donations/stripe/` request body from frontend:

```json
{
  "donor_name": "Jane Wanjiku",
  "donor_email": "jane@example.com",
  "amount": "50.00",
  "currency": "USD",
  "donation_type": "one_time",
  "purpose": "General",
  "message": "",
  "is_anonymous": false
}
```

Notes:

- `payment_method_id` may be omitted by frontend and backend must support this.
- Backend should still accept `payment_method_id` if provided for compatibility.

### Stripe backend configuration requirements

Required backend environment variables:

- `STRIPE_SECRET_KEY`
- `STRIPE_WEBHOOK_SECRET`

Required webhook endpoint:

- `POST /api/v1/donations/stripe-webhook/`

Recommended minimum subscribed Stripe events:

- `payment_intent.succeeded`
- `payment_intent.payment_failed`
- `payment_intent.processing`
- `charge.refunded` (if refunds are supported)

Webhook rules:

- Verify Stripe signature with `STRIPE_WEBHOOK_SECRET`.
- Persist callbacks idempotently (replay-safe).
- Update donation status consistently (`pending|processing|completed|failed|refunded|cancelled`).

### M-Pesa backend expectations reaffirmed

- `POST /api/v1/donations/mpesa/` remains queue-backed and returns `202`.
- Response should include:
  - `message`
  - `donation_id`
  - `job_id`
  - `status`

### Validation and error payload expectations (required)

Frontend now depends on consistent JSON error payloads for:

- `400` field validation errors (serializer field arrays preferred)
- `403` permission errors
- `429` throttling errors
- `500+` generic server failures

### Suggested optional analytics fields

If feasible, backend can add optional donation fields:

- `donation_source` (e.g. `impact_card`, `custom_amount`, `donation_page`)
- `campaign_hint` (e.g. `education_transforms`, `learning_empowers`, `health_matters`)

These are not currently sent by frontend but can be added quickly once supported.

### Backend implementation prompt (copy/paste)

Use this exact prompt in backend workspace:

```text
Use apis.md as source of truth and fully implement backend support for current frontend donation and Stripe flow.

Requirements:
1) Keep API base under /api/v1/.
2) Ensure POST /donations/mpesa/ returns 202 and includes message, donation_id, job_id, status.
3) Ensure POST /donations/stripe/ returns 202 and includes message, donation_id, payment_intent_id, client_secret, status.
4) Accept Stripe initiation payload with or without payment_method_id.
5) Configure Stripe webhook endpoint at /donations/stripe-webhook/ with signature verification and idempotent processing.
6) Update donation status based on webhook events (succeeded, processing, failed, refunded).
7) Return clean JSON errors for 400, 403, 429, 500.
8) Preserve existing donation enums and serializer contracts in apis.md.
9) Add tests for mpesa initiation, stripe initiation, webhook success/failure/idempotency.

Constraints:
- Do not break existing public endpoints.
- Keep webhook replay-safe.
- Keep admin protections and throttling behavior.
```

## Prompt To Use In Frontend Workspace

Use the prompt below in your frontend project after pasting this file:

```text
Align this frontend codebase to the backend API contract in apis.md.

Goals:
1) Find every API call in the frontend and map it to the endpoint list in apis.md.
2) Replace unversioned paths (/api/...) with /api/v1/... unless explicitly backward-compat required.
3) Ensure each request body matches backend serializer fields exactly.
4) Ensure response handling matches backend status codes and payload shapes, especially:
  - donations mpesa/stripe async flows (202)
  - newsletter subscribe variations (200/201)
  - admin-only endpoints (403 handling)
  - throttling (429 handling)
5) Add or update frontend types/interfaces/enums to match apis.md enums and object fields.
6) Identify any backend endpoints in apis.md that are not yet consumed by frontend and list them as integration opportunities.
7) Produce a concise diff-style summary by feature area (donations, gallery, testimonials, contacts, volunteers, newsletter, sponsorships, health/readiness).

Constraints:
- Do not invent fields not present in apis.md.
- Keep UI behavior unchanged unless needed for API correctness.
- Prefer minimal, safe refactors.

Deliverables:
- Updated frontend API client/service files.
- Updated types/models.
- Updated screens/forms where payload or response handling changed.
- A final checklist confirming each endpoint group is aligned.
```

## Admin CMS Endpoints

Base: `/api/v1/admin/` (also available under `/api/admin/` for backward compatibility)

Access: Admin only (`IsAdminUser`)

### Overview and operations

- `GET /overview/` dashboard counts for operations and CMS objects
- `GET /audit-events/` audit event feed
- `GET /background-jobs/` background job list
- `GET /background-jobs/{id}/` background job detail
- `POST /background-jobs/{id}/retry/` retry failed job

### Site settings (singleton)

- `GET /site-settings/`
- `PUT /site-settings/`
- `PATCH /site-settings/`

### Image placements

- `GET /image-placements/` destination options for the admin upload form
- `POST /image-placements/` multipart upload that routes to page sections, gallery photos, media assets, or site branding

### Pages

- `GET /pages/`
- `POST /pages/`
- `GET /pages/{id}/`
- `PUT /pages/{id}/`
- `PATCH /pages/{id}/`
- `DELETE /pages/{id}/`
- `POST /pages/{id}/publish/`
- `POST /pages/{id}/archive/`
- `POST /pages/{id}/schedule/` with body `{ "scheduled_for": "<ISO datetime>" }`
- `GET /pages/{id}/preview/`

### Page sections

- `GET /page-sections/`
- `POST /page-sections/`
- `GET /page-sections/{id}/`
- `PUT /page-sections/{id}/`
- `PATCH /page-sections/{id}/`
- `DELETE /page-sections/{id}/`

### Navigation

- `GET /navigation-menus/`
- `POST /navigation-menus/`
- `GET /navigation-menus/{id}/`
- `PUT /navigation-menus/{id}/`
- `PATCH /navigation-menus/{id}/`
- `DELETE /navigation-menus/{id}/`

- `GET /navigation-items/`
- `POST /navigation-items/`
- `GET /navigation-items/{id}/`
- `PUT /navigation-items/{id}/`
- `PATCH /navigation-items/{id}/`
- `DELETE /navigation-items/{id}/`

### Marketing and redirects

- `GET /banners/`
- `POST /banners/`
- `GET /banners/{id}/`
- `PUT /banners/{id}/`
- `PATCH /banners/{id}/`
- `DELETE /banners/{id}/`

- `GET /redirect-rules/`
- `POST /redirect-rules/`
- `GET /redirect-rules/{id}/`
- `PUT /redirect-rules/{id}/`
- `PATCH /redirect-rules/{id}/`
- `DELETE /redirect-rules/{id}/`

### Media assets

- `GET /media-assets/`
- `POST /media-assets/` (multipart)
- `GET /media-assets/{id}/`
- `PUT /media-assets/{id}/`
- `PATCH /media-assets/{id}/`
- `DELETE /media-assets/{id}/`

### Content revisions

- `GET /content-revisions/`
- `GET /content-revisions/{id}/`

### Existing gallery admin endpoints

- `GET /gallery/categories/`
- `POST /gallery/categories/`
- `GET /gallery/categories/{id}/`
- `PUT /gallery/categories/{id}/`
- `PATCH /gallery/categories/{id}/`
- `DELETE /gallery/categories/{id}/`

- `GET /gallery/photos/`
- `POST /gallery/photos/` (multipart)
- `GET /gallery/photos/{id}/`
- `PUT /gallery/photos/{id}/`
- `PATCH /gallery/photos/{id}/`
- `DELETE /gallery/photos/{id}/`
