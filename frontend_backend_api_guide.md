# Backend API Integration Guide for Frontend Developers

This document outlines all backend endpoints, data models, and integration details needed to connect the frontend to the Jambo Rafiki backend. Use this as a reference to ensure your frontend aligns with backend expectations.

---

## 1. API Base URL

- The API base URL is determined by the environment variable: `apiUrl` (see `/src/config/runtimeEnv.ts`).
- All endpoints are relative to: `https://<your-backend-domain>/api/v1/`

---

## 2. Authentication

- Admin authentication uses session cookies and CSRF tokens.
- Endpoints for login/logout:
  - `POST /admin/auth/login/` — `{ email, password }`
  - `POST /admin/auth/logout/`
  - `GET /admin/auth/me/` — returns current user profile
  - `GET /admin/auth/csrf/` — get CSRF token

---

## 3. Contact Form

- **Submit:** `POST /contacts/`
- **Payload:**
  ```json
  {
    "name": "string",
    "email": "string",
    "subject": "string",
    "message": "string"
  }
  ```
- **Response:** `{ message, data }`

---

## 4. Donations

- **M-Pesa:**
  - `POST /donations/mpesa/` — initiate donation
  - `POST /donations/mpesa-async/` — async donation
  - `POST /donations/mpesa-sync/` — sync donation
  - **Payload:**
    ```json
    {
      "donor_name": "string",
      "donor_email": "string",
      "donor_phone": "string",
      "amount": number,
      "currency": "KES|USD|EUR|GBP",
      "donation_type": "one_time|monthly|quarterly|annual",
      "purpose": "string",
      "message": "string",
      "is_anonymous": boolean
    }
    ```
- **Stripe:**
  - `POST /donations/stripe/`
  - **Payload:**
    ```json
    {
      "donor_name": "string",
      "donor_email": "string",
      "amount": number,
      "currency": "KES|USD|EUR|GBP",
      "donation_type": "one_time|monthly|quarterly|annual",
      "purpose": "string",
      "message": "string",
      "is_anonymous": boolean,
      "payment_method_id": "string"
    }
    ```

---

## 5. Volunteer Application

- **Submit:** `POST /volunteers/`
- **Payload:**
  ```json
  {
    "name": "string",
    "email": "string",
    "phone": "string",
    "location": "string",
    "skills": "string",
    "availability": "string",
    "duration": "string",
    "motivation": "string"
  }
  ```
- **Response:** `{ message, data }`

---

## 6. Newsletter

- **Subscribe:** `POST /newsletter/` — `{ email, name?, source? }`
- **Unsubscribe:** `POST /newsletter/unsubscribe/` — `{ email }`

---

## 7. Testimonials

- **Submit:** `POST /testimonials/`
- **Payload:**
  ```json
  {
    "name": "string",
    "email": "string",
    "role": "community_member|volunteer|donor|sponsor|partner|other",
    "role_custom": "string (if role is 'other')",
    "text": "string"
  }
  ```
- **List Approved:** `GET /testimonials/`
- **List Pending (admin):** `GET /testimonials/pending/`

---

## 8. Sponsorships

- **Express Interest:** `POST /sponsorships/interest/`
- **Payload:**
  ```json
  {
    "name": "string",
    "email": "string",
    "phone": "string",
    "preferred_level": "string|null"
  }
  ```

---

## 9. Gallery

- **List Categories:** `GET /gallery/categories/`
- **List Photos:** `GET /gallery/photos/`
- **Get Photo:** `GET /gallery/photos/{id}/`

---

## 10. Organization Info

- **Get:** `GET /organization/`
- Returns organization config, contact info, and bank account details.

---

## 11. Error Handling

- Errors are returned as `{ message: string }` or `{ error: string }`.
- HTTP status codes follow REST conventions (400, 403, 404, 500, etc).

---

## 12. Environment Variables (Frontend)

- `apiUrl` — Base URL for backend API (e.g., `https://api.jamborafiki.org`)
- Any additional config required for authentication/session/cookies.

---

## 13. Notes

- All requests and responses are JSON.
- For admin endpoints, session authentication and CSRF tokens are required.
- For public endpoints (contact, donations, testimonials, etc.), no authentication is required.

---

For any new endpoints or changes, coordinate with the backend team to update this document.
