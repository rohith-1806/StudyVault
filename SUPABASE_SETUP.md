# StudyVault - Supabase Database & Storage Setup Guide

This document provides step-by-step instructions to configure **Supabase PostgreSQL** and **Supabase Private Storage** for the **StudyVault** platform.

---

## 1. Supabase Project Creation

1. Go to [https://supabase.com](https://supabase.com) and sign in.
2. Click **New Project**, select your organization, and name your project (e.g. `studyvault`).
3. Set a secure database password and choose your region.
4. Copy the following credentials from **Project Settings > API**:
   - `Project URL` (`SUPABASE_URL`)
   - `anon public` key (`SUPABASE_ANON_KEY`)
   - `service_role secret` key (`SUPABASE_SERVICE_ROLE_KEY`)

---

## 2. Execute SQL Database Schema

1. In your Supabase Dashboard, click **SQL Editor** in the left navigation sidebar.
2. Click **New Query**.
3. Copy the entire contents of [`schema.sql`](file:///c:/Users/rohit/OneDrive/Desktop/digital_library/schema.sql) from the project repository.
4. Paste the SQL code into the query editor and click **Run**.
5. Verify that the following 7 tables are created:
   - `profiles`
   - `categories` (pre-seeded with 15 educational categories)
   - `documents`
   - `downloads`
   - `document_views`
   - `reports`
   - `access_grants`

---

## 3. Create Private Storage Bucket

1. In your Supabase Dashboard, click **Storage** in the left navigation sidebar.
2. Click **New Bucket**.
3. Bucket Details:
   - **Name**: `documents`
   - **Public Bucket**: `OFF` (Keep as **Private** so files cannot be downloaded without short-lived signed backend URLs)
   - **Allowed MIME types**: `application/pdf`
   - **Max file size**: `26214400` bytes (25 MB)
4. Click **Save Bucket**.

---

## 4. Environment Variables Configuration

Copy your Supabase credentials into `backend/.env`:

```env
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_ANON_KEY=your-supabase-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-supabase-service-role-key

SECRET_KEY=super-secret-jwt-signing-key
ADMIN_EMAIL=admin@studyvault.edu
ADMIN_PASSWORD_HASH=scrypt:32768:8:1$xH2g8l9B4v2k0L5m$95096b79753065a78248bc3bebb0ef3878b273b4b0e50efb0ef7645bfbc094208a0d0d82dd2604ca75a5cb33a6f1947b19818b76db01b1df40003b573510e140

MAX_UPLOAD_SIZE=26214400
AUTO_APPROVE=true
REWARD_DURATION_HOURS=24
STORAGE_BUCKET=documents
```

> **Note**: For local development without Supabase credentials, StudyVault automatically falls back to an embedded SQLite database (`database.db`) and local folder file storage (`storage_data/`).
