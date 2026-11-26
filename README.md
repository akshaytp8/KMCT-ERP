# KMCT ERP – Super Admin Portal

A standalone implementation of the **Main Admin / Super Admin portal** described in `FinHR Final.docx`, using the supplied Super Admin screenshot as the visual reference.

## Included functionality

- Super Admin sign-in with JWT authentication.
- Institution-wide dashboard: student count, billed fees, collected fees, outstanding fees, employee count, present-today count, pending leave requests and audit-entry count.
- Monthly fee collection chart based on successful payment records.
- Institution Master.
- Academic Year, Course / Programme, Department, Batch and Semester / Year masters.
- User Management and Role Management.
- Permission Master and Role–Permission mapping.
- Portal Access configuration (view/create/update/delete flags per user and portal).
- Approval Workflow configuration (Level 1 and Level 2 approver roles).
- Notification configuration (email and in-app channels).
- Institution-wide, read-only Student and Employee views. These records remain owned by the Admin and HR portals as specified in the project plan.
- Audit trail for logins and create/update/delete operations performed through the Super Admin API.
- Institution-wise operational and financial reports with CSV export.
- PostgreSQL, SQLAlchemy, FastAPI, Alembic scaffold and Docker Compose setup.

## Run with Docker Compose

1. Install Docker Desktop and start it.
2. Copy `.env.example` to `.env`.
3. Change `JWT_SECRET` and `SUPERADMIN_PASSWORD` in `.env` before using the portal beyond a local demo.
4. From this folder, run:

   ```bash
   docker compose up --build
   ```

5. Open the frontend at `http://localhost:5173`.
6. API documentation is available at `http://localhost:8000/docs`.

Default first-run development account (change it in `.env` before launch):

- Username: `admin`
- Password: `ChangeMe123!`

On first startup, the backend creates the database tables, seeds the National College of Pharmacy institution, seeds the eight roles and starter permissions, and creates the Super Admin account. The dashboard starts with live zero values until student, employee, finance, HR and attendance records are created by the relevant modules.

## Run without Docker

### Backend

Requires Python 3.11+ and a running PostgreSQL database.

```bash
cd backend
python -m venv .venv
# Windows PowerShell: .venv\Scripts\Activate.ps1
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
```

Set environment variables before starting the API. Example PowerShell values:

```powershell
$env:DATABASE_URL="postgresql+psycopg://postgres:postgres@localhost:5432/kmct_erp"
$env:JWT_SECRET="replace-with-a-long-random-secret"
$env:SUPERADMIN_PASSWORD="ChangeMe123!"
uvicorn app.main:app --reload --port 8000
```

### Frontend

In another terminal:

```bash
cd frontend
npm install
npm run dev
```

The frontend uses `http://localhost:8000` by default. Override it with `VITE_API_BASE_URL` if your API runs elsewhere.

## Database and migration notes

- The application uses one PostgreSQL database. Institution-specific operational records carry an `institution_id` where appropriate.
- The API currently runs `Base.metadata.create_all()` at startup so a fresh local Docker environment can be started immediately.
- Alembic configuration and an initial metadata migration scaffold are included. For a managed deployment, switch to an explicit migration workflow and do not rely on `create_all()` for production schema changes.
- Never expose gateway credentials, database credentials or JWT secrets in the frontend.

## Important implementation boundaries

This package implements the Super Admin / Main Admin area, not the entire multi-portal ERP. The Finance, HR, Student, Admin and Faculty modules must write their operational records into the same database for the Super Admin aggregates and read-only oversight views to show live information.

The project plan describes role/permission and portal-access configuration; this starter includes the management screens and stores those configuration records. Enforcement of the full permission matrix across all other portal APIs must be integrated when those portals are implemented. Only the Super Admin API is currently protected and available to the seeded Super Admin account.

Payment gateway verification, biometric device integration, scholarship processing, refund posting, employee appraisal and production-grade notification delivery are not implemented here; they belong to the related Finance/HR and integration workstreams in the project plan.

## API overview

- `POST /api/auth/login`
- `GET /api/auth/me`
- `GET /api/admin/dashboard`
- `GET /api/admin/audit-logs`
- `GET /api/admin/institution-reports`
- `GET /api/admin/{resource}`
- `POST /api/admin/{resource}`
- `PATCH /api/admin/{resource}/{id}`
- `DELETE /api/admin/{resource}/{id}`

Resource keys include `institutions`, `academic-years`, `courses`, `departments`, `batches`, `semesters`, `users`, `roles`, `permissions`, `role-permissions`, `portal-access`, `approval-workflows` and `notification-configs`. `students` and `employees` are read-only resources in this portal.


## Finance Admin portal

The application now includes a Finance Admin workspace based on the Finance sections of `FinHR Final.docx`. Sign in with the seeded Finance Admin account to open the Finance portal automatically.

- Username: `finance`
- Password: `Finance123!` (change this before deployment)

Finance navigation includes Dashboard, Academic Masters (read-only reference data), Fee Structure, Students & Ledger, Scholarships, Fee Heads, Fee Categories, Installments, Collection Report, Payment Gateway configuration, Receipt Series, Chart of Accounts and Audit Logs. Fee structures can be assigned to students in the configured course. Direct student fee assignments create a ledger entry.

The Finance Admin account is scoped to the seeded National College of Pharmacy institution. Super Admin access remains separate and retains the central administration routes. Finance records are persisted in PostgreSQL using the same database as the Super Admin portal.

Payment gateway credentials and live payment verification are not implemented by this UI; gateway configuration is metadata only. Do not store secret keys in these fields. Live payment integration, refund approval processing, bank reconciliation, scholarship applications/approvals, and production receipt generation require the actual KMCT gateway/accounting requirements and should be completed before production use.
