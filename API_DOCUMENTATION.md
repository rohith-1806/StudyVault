# StudyVault REST API Documentation

Base URL: `http://localhost:5000/api`

---

## 1. Authentication APIs

### `POST /api/auth/register`
Register a new student account.
- **Request Body**:
  ```json
  {
    "full_name": "Rahul Sharma",
    "email": "rahul@university.edu",
    "password": "Password123!",
    "confirm_password": "Password123!"
  }
  ```
- **Response** (201 Created):
  ```json
  {
    "message": "Registration successful.",
    "token": "eyJhbGciOi...",
    "user": {
      "id": "uuid",
      "full_name": "Rahul Sharma",
      "email": "rahul@university.edu",
      "role": "student"
    }
  }
  ```

### `POST /api/auth/login`
Authenticate student account.
- **Request Body**: `{"email": "...", "password": "..."}`
- **Response** (200 OK): `{"token": "...", "user": {...}}`

### `GET /api/auth/me`
Fetch current authenticated user profile & 24h download access remaining time.
- **Headers**: `Authorization: Bearer <token>`
- **Response** (200 OK):
  ```json
  {
    "user": {
      "id": "uuid",
      "full_name": "Rahul Sharma",
      "access_active": true,
      "remaining_seconds": 67320,
      "access_expires_at": "2026-09-11T10:30:00Z"
    }
  }
  ```

---

## 2. Document & Library APIs

### `GET /api/documents`
List approved library resources with search, category filter, course filter, and sorting.
- **Query Parameters**:
  - `category`: Category ID or slug (e.g. `cat_1`, `btech`)
  - `search`: Search query term
  - `course`: Course name (e.g. `CSE`)
  - `sort_by`: `latest` | `popular` | `downloads`
  - `page`: Page index (default: 1)
  - `limit`: Items per page (default: 20)

### `GET /api/documents/:id`
Get single document metadata and trigger view increment.

### `POST /api/documents/upload`
Upload a new educational PDF resource.
- **Headers**: `Authorization: Bearer <token>`
- **Content-Type**: `multipart/form-data`
- **Form Fields**:
  - `file`: PDF binary file
  - `title`: Document Title
  - `description`: Summary
  - `category_id`: Category ID (e.g. `cat_4`)
  - `course`: Course name
  - `subject`: Subject name
  - `semester`: Semester
  - `tags`: Comma-separated tags
  - `copyright_confirmed`: `true`
- **Response** (201 Created):
  ```json
  {
    "message": "Contribution added successfully!",
    "document": { ... },
    "reward_granted": true,
    "reward_info": {
      "access_active": true,
      "expires_at": "2026-09-11T10:30:00Z",
      "duration_hours": 24
    }
  }
  ```

### `GET /api/documents/:id/download`
Download resource PDF.
- **Headers**: `Authorization: Bearer <token>`
- **Behavior**: Checks 24-hour active contribution status OR document ownership. Returns signed temporary download URL or streams file directly. If expired, returns 403 Forbidden.

### `GET /api/documents/:id/stream`
Stream PDF file for in-browser canvas viewer.

### `DELETE /api/documents/:id`
Delete uploaded contribution.

---

## 3. Report & Admin APIs

### `POST /api/documents/:id/report`
Submit a violation or copyright report.
- **Request Body**: `{"reason": "copyright_issue", "description": "..."}`

### `POST /api/admin/login`
Authenticate administrator credentials.
- **Request Body**: `{"email": "admin@studyvault.edu", "password": "..."}`

### `GET /api/admin/dashboard`
Get system-wide metrics and category distribution.

### `GET /api/admin/documents/pending`
Fetch moderation queue of documents pending review.

### `PATCH /api/admin/documents/:id/approve`
Approve pending document and grant 24-hour access reward to uploader.

### `PATCH /api/admin/documents/:id/reject`
Reject pending document with reason.

### `GET /api/admin/users`
List registered users and upload counts.

### `PATCH /api/admin/users/:id/status`
Toggle user active status (`is_active`: `true` / `false`).
