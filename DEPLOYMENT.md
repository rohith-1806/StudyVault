# StudyVault — Production Deployment Guide

This document outlines the step-by-step guide to deploy the **StudyVault** student digital library platform to production hosting services (Render/Railway for Flask Backend API and Vercel/Netlify for React Frontend).

---

## 📌 Architecture & Deployment Overview

```
┌──────────────────────────────────────────────┐
│  Frontend (Vercel / Netlify)                 │
│  React SPA + Glassmorphism UI                │
│  URL: https://studyvault-frontend.vercel.app │
└──────────────────────┬───────────────────────┘
                       │ HTTPS REST API / JWT
                       ▼
┌──────────────────────────────────────────────┐
│  Backend (Render / Railway / VPS)            │
│  Python 3.13 + Flask + Gunicorn WSGI Server  │
│  URL: https://studyvault-api.onrender.com    │
└──────────────┬───────────────────────┬───────┘
               │                       │
               ▼                       ▼
┌─────────────────────────────┐   ┌──────────────────────────────┐
│ Supabase PostgreSQL DB      │   │ Supabase Storage             │
│ (Metadata & Profiles)       │   │ Private PDF Document Vault   │
└─────────────────────────────┘   └──────────────────────────────┘
```

---

## 1. Backend Deployment (Render / Railway / VPS)

### Deployment Configuration
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `gunicorn --config gunicorn.conf.py "app:create_app()"`
- **Root Directory**: `backend`

### Environment Variables (Backend)
Configure the following environment variables in your hosting provider's dashboard:

| Variable Name | Example Value / Description |
|---|---|
| `PORT` | `5000` (Assigned dynamically by Render/Railway) |
| `FRONTEND_URL` | `https://your-frontend-domain.vercel.app` |
| `SUPABASE_URL` | `https://your-project.supabase.co` |
| `SUPABASE_ANON_KEY` | `your-supabase-anon-key` |
| `SUPABASE_SERVICE_ROLE_KEY` | `your-supabase-service-role-key` |
| `SECRET_KEY` | `your-production-jwt-secret-key-string` |
| `ADMIN_EMAIL` | `admin@studyvault.edu` |
| `ADMIN_PASSWORD_HASH` | `scrypt:32768:8:1$...` (Hashed admin password) |
| `MAX_UPLOAD_SIZE` | `26214400` (25MB) |
| `AUTO_APPROVE` | `true` |
| `REWARD_DURATION_HOURS` | `24` |
| `STORAGE_BUCKET` | `documents` |
| `BREVO_API_KEY` | `xkeysib-...` (Your verified Brevo API key) |
| `BREVO_SENDER_EMAIL` | `noreply@studyvault.edu` (Verified sender email in Brevo) |
| `BREVO_SENDER_NAME` | `StudyVault` (Branded sender name) |
| `ENABLE_IN_APP_SCHEDULER` | `false` in multi-worker production (`true` for local dev) |
| `REMINDER_CHECK_INTERVAL_SECONDS` | `60` (Polling frequency in seconds) |

### Health Check Endpoint
Verify your deployed backend with:
```http
GET https://your-backend-api.onrender.com/api/health
```
Expected response:
```json
{
  "status": "ok",
  "app": "StudyVault Student Digital Library API",
  "version": "1.0.0"
}
```

---

## 2. Background Reminder Worker Setup

When deploying to production, do not run the background scheduler inside multi-worker Gunicorn web processes, as multiple workers would duplicate scheduling cycles. StudyVault provides an independent, persistent database-polling worker:

### Running on Render / Railway as a Worker Process
- In Render, create a **Background Worker** linked to the same repository.
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `python worker.py`
- **Environment Variables**: Add identical database and Brevo environment variables.
- Or use the included `Procfile`:
  ```procfile
  web: gunicorn --config gunicorn.conf.py "app:create_app()"
  worker: python worker.py
  ```

### Running as a Scheduled Cron Job (Alternative)
If your platform supports Cron Jobs (e.g. Render Cron, Railway Cron, GitHub Actions, AWS EventBridge):
- Run the single-shot command every 5 to 15 minutes:
  ```bash
  python worker.py --once
  ```
- The worker executes an atomic database check for any users whose 24-hour access has approximately 10 hours remaining, dispatches any due reminders idempotently, and exits cleanly with exit code 0.

---

## 3. Brevo (Sendinblue) Setup & Domain Authentication

### Step 1: Create Brevo Account & API Key
1. Go to [https://app.brevo.com](https://app.brevo.com) and log in.
2. In the top-right profile dropdown, click **SMTP & API Keys**.
3. Under the **API Keys** tab, click **Generate a new API key**.
4. Name it `StudyVault-Production` and copy the secret key (format: `xkeysib-...`).
5. Add this to your hosting platform's environment variables as `BREVO_API_KEY`.

### Step 2: Add and Verify Sender Email / Domain
1. In Brevo, go to **Senders, Domains & Dedicated IPs** &rarr; **Senders**.
2. Click **Add a Sender**.
3. Enter `StudyVault` as Sender Name and your email (e.g., `contact@yourdomain.edu` or your email).
4. Brevo will send a verification link to that email address. Click the link to verify.
5. Set `BREVO_SENDER_EMAIL` to this verified email address.
6. *(Recommended for production deliverability)*: Under the **Domains** tab, add your domain and configure the SPF, DKIM, and DMARC DNS records provided by Brevo.

### Step 3: Safe Testing Without Real User Dispatches
- To test the API without sending messages to external students, set `BREVO_SENDER_EMAIL` and test recipient emails to addresses you control (e.g., your personal test mailbox).
- In automated test runs (`pytest`), StudyVault automatically runs in mock mode where Brevo HTTP network calls are intercepted, preventing API quota usage or accidental emails.

---

## 4. Frontend Deployment (Vercel / Netlify)

### Deployment Configuration
- **Framework Preset**: `Vite`
- **Root Directory**: `frontend`
- **Build Command**: `npm run build`
- **Output Directory**: `dist`

### Environment Variables (Frontend)
Configure in Vercel / Netlify project settings:

| Variable Name | Value |
|---|---|
| `VITE_API_BASE_URL` | `https://your-backend-api.onrender.com/api` |

> **Security Note**: Never expose the `BREVO_API_KEY` or Supabase service role keys in frontend environment variables. All email operations are handled securely on the backend.

### SPA Routing Fallback
For Single Page Application client-side routing on Vercel, create a `vercel.json` in `frontend/`:
```json
{
  "rewrites": [
    { "source": "/(.*)", "destination": "/index.html" }
  ]
}
```

---

## 5. Post-Deployment Verification Checklist

Once both frontend, backend, and Brevo are configured:

1. **Health Check**: Open `https://your-backend-api.onrender.com/api/health` and verify `{"status": "ok"}`.
2. **Student Registration & Welcome Email**:
   - Register a new account with a verified email address.
   - Verify that registration succeeds immediately.
   - Check mailbox for the branded StudyVault Welcome Email: *"Welcome to StudyVault — Unlock a World of Knowledge"*.
3. **PDF Upload & 24-Hour Access Confirmation Email**:
   - Log in and upload a valid PDF study resource.
   - Confirm upload succeeds and unlocks 24 hours of download access.
   - Check mailbox for the confirmation email: *"Resource Uploaded Successfully — 24 Hours Unlimited Access Unlocked!"*.
4. **Duplicate Prevention & Zero Duplicate Emails**:
   - Try uploading the same PDF again. Verify rejection banner and confirm NO duplicate email is sent.
5. **10-Hour Expiration Reminder**:
   - Run `python worker.py --once`.
   - Verify that users approaching the 10-hour remaining window receive the reminder email: *"Reminder: 10 Hours of Unlimited Access Remaining — StudyVault"*.
   - Verify that running the worker again does not produce duplicate reminder emails.
6. **Admin Moderation & Unrelated Features**:
   - Log in to `/admin/login` and verify search, categories, and moderation continue operating smoothly.
