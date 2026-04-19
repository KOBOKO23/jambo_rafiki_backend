# How to Compare and Fix Admin CMS API URLs

Your frontend CMS uses backend API endpoints defined in the codebase. If your backend URL has changed (e.g., new Render deployment or custom domain), you must update the frontend config to match.

## 1. Where API URLs Are Set
- The API base URL is set by the environment variable `VITE_API_BASE_URL` (see `.env`, `.env.local`, or deployment settings).
- Example: `VITE_API_BASE_URL=https://api.jamborafiki.org/api/v1`
- The code that loads this is in `/src/config/runtimeEnv.ts`.

## 2. Where Admin CMS Endpoints Are Used
- All admin/auth endpoints are defined in `/src/services/api.ts`:
  - `/admin/auth/login/`
  - `/admin/auth/logout/`
  - `/admin/auth/me/`
  - `/admin/auth/csrf/`
  - ...and more under `/admin/`
- The frontend builds full URLs by combining `VITE_API_BASE_URL` with these paths.

## 3. How to Check and Update
1. **Check your deployed backend URL** (e.g., `https://api.jamborafiki.org/api/v1`).
2. **Check your frontend environment variable** for `VITE_API_BASE_URL`:
   - In Vercel dashboard, or in your `.env` file.
3. **If the URLs do not match, update the frontend config** to use the correct backend URL.
   - Example: Set `VITE_API_BASE_URL=https://api.jamborafiki.org/api/v1`
4. **Redeploy your frontend** after making changes.

## 4. CORS, CSRF, and Credentials Checklist
- In your Django backend `.env` (on Render), set:
  ```
  ALLOWED_HOSTS=api.jamborafiki.org,www.jamborafiki.org
  CORS_ALLOWED_ORIGINS=https://www.jamborafiki.org
  CSRF_TRUSTED_ORIGINS=https://www.jamborafiki.org
  CORS_ALLOW_CREDENTIALS=True
  ```
- This configuration allows any call from your CMS/frontend (hosted at https://www.jamborafiki.org) to your backend API (https://api.jamborafiki.org/api/v1) as long as VITE_API_BASE_URL is set to that value in your frontend environment.
- In your frontend (Vercel), ensure all fetch/axios requests use:
  ```js
  credentials: 'include'
  ```
  This allows cookies (sessionid, csrftoken) to be sent with API requests.
- Make sure your Django backend uses session authentication or token authentication as required.

## 5. Troubleshooting 403 Errors
- If you get 403 errors, check:
  - You are using the correct backend URL.
  - CORS and authentication are set up correctly on the backend.
  - The frontend is sending credentials (cookies/tokens) if required.
  - CSRF tokens are included for POST/PUT/PATCH/DELETE requests.

## 6. Deployment Checklist
- [x] VITE_API_BASE_URL is set to `https://api.jamborafiki.org/api/v1` in Vercel.
- [x] Django backend `.env` on Render is updated for CORS/CSRF/credentials as above.
- [x] Both frontend and backend are redeployed after changes.
- [x] Test login and all admin CMS features from https://www.jamborafiki.org/admin/login.

## 7. Reference
- See `/src/config/runtimeEnv.ts` for how the API URL is loaded.
- See `/src/services/api.ts` for all API endpoint paths.
- See `FRONTEND_BACKEND_API_GUIDE.md` for integration details.

---

**Summary:**
- Make sure your frontend and backend are using the same API base URL.
- Use credentials: 'include' in all frontend API requests.
- Update CORS/CSRF/credentials settings in Django backend.
- Redeploy both frontend and backend after any change.
