from datetime import datetime, date
from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column
from .database import Base

class Institution(Base):
    __tablename__ = "institutions"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(30), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(180), index=True)
    address: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

class AcademicYear(Base):
    __tablename__ = "academic_years"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    institution_id: Mapped[int | None] = mapped_column(ForeignKey("institutions.id"), nullable=True, index=True)
    label: Mapped[str] = mapped_column(String(40))
    start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    is_current: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

class Course(Base):
    __tablename__ = "courses"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    institution_id: Mapped[int | None] = mapped_column(ForeignKey("institutions.id"), nullable=True, index=True)
    code: Mapped[str] = mapped_column(String(40))
    name: Mapped[str] = mapped_column(String(180))
    programme_type: Mapped[str | None] = mapped_column(String(80), nullable=True)
    duration_years: Mapped[int] = mapped_column(Integer, default=1)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

class Department(Base):
    __tablename__ = "departments"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    institution_id: Mapped[int | None] = mapped_column(ForeignKey("institutions.id"), nullable=True, index=True)
    code: Mapped[str] = mapped_column(String(40))
    name: Mapped[str] = mapped_column(String(180))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

class Batch(Base):
    __tablename__ = "batches"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    institution_id: Mapped[int | None] = mapped_column(ForeignKey("institutions.id"), nullable=True, index=True)
    course_id: Mapped[int | None] = mapped_column(ForeignKey("courses.id"), nullable=True)
    label: Mapped[str] = mapped_column(String(80))
    start_year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    end_year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

class Semester(Base):
    __tablename__ = "semesters"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    course_id: Mapped[int | None] = mapped_column(ForeignKey("courses.id"), nullable=True)
    label: Mapped[str] = mapped_column(String(60))
    sequence: Mapped[int] = mapped_column(Integer, default=1)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

class Role(Base):
    __tablename__ = "roles"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    key: Mapped[str] = mapped_column(String(60), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(120))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_system: Mapped[bool] = mapped_column(Boolean, default=False)

class Permission(Base):
    __tablename__ = "permissions"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    key: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(150))
    module: Mapped[str] = mapped_column(String(80))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

class RolePermission(Base):
    __tablename__ = "role_permissions"
    __table_args__ = (UniqueConstraint("role_id", "permission_id", name="uq_role_permission"),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    role_id: Mapped[int] = mapped_column(ForeignKey("roles.id", ondelete="CASCADE"), index=True)
    permission_id: Mapped[int] = mapped_column(ForeignKey("permissions.id", ondelete="CASCADE"), index=True)
    is_granted: Mapped[bool] = mapped_column(Boolean, default=True)

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(180))
    email: Mapped[str] = mapped_column(String(180), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(300))
    institution_id: Mapped[int | None] = mapped_column(ForeignKey("institutions.id"), nullable=True, index=True)
    role_id: Mapped[int | None] = mapped_column(ForeignKey("roles.id"), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_login: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

class PortalAccess(Base):
    __tablename__ = "portal_access"
    __table_args__ = (UniqueConstraint("user_id", "portal_key", name="uq_user_portal_access"),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    portal_key: Mapped[str] = mapped_column(String(80))
    can_view: Mapped[bool] = mapped_column(Boolean, default=True)
    can_create: Mapped[bool] = mapped_column(Boolean, default=False)
    can_update: Mapped[bool] = mapped_column(Boolean, default=False)
    can_delete: Mapped[bool] = mapped_column(Boolean, default=False)

class ApprovalWorkflow(Base):
    __tablename__ = "approval_workflows"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    institution_id: Mapped[int | None] = mapped_column(ForeignKey("institutions.id"), nullable=True, index=True)
    name: Mapped[str] = mapped_column(String(150))
    module: Mapped[str] = mapped_column(String(80))
    level1_role: Mapped[str] = mapped_column(String(100))
    level2_role: Mapped[str] = mapped_column(String(100))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

class NotificationConfig(Base):
    __tablename__ = "notification_configs"
    __table_args__ = (UniqueConstraint("institution_id", "event_key", name="uq_institution_notification_event"),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    institution_id: Mapped[int | None] = mapped_column(ForeignKey("institutions.id"), nullable=True, index=True)
    event_key: Mapped[str] = mapped_column(String(100))
    channel_email: Mapped[bool] = mapped_column(Boolean, default=True)
    channel_in_app: Mapped[bool] = mapped_column(Boolean, default=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)

class AuditLog(Base):
    __tablename__ = "audit_logs"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    actor_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    actor_name: Mapped[str] = mapped_column(String(120))
    action: Mapped[str] = mapped_column(String(80), index=True)
    entity: Mapped[str] = mapped_column(String(100), index=True)
    entity_id: Mapped[str | None] = mapped_column(String(80), nullable=True)
    details: Mapped[str | None] = mapped_column(Text, nullable=True)
    institution_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), index=True)

# These records are owned by the Admin and HR portals respectively. The Main Admin
# receives an institution-wide read-only view for oversight.
class Student(Base):
    __tablename__ = "students"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    institution_id: Mapped[int | None] = mapped_column(ForeignKey("institutions.id"), nullable=True, index=True)
    student_no: Mapped[str] = mapped_column(String(60), index=True)
    full_name: Mapped[str] = mapped_column(String(180))
    course: Mapped[str | None] = mapped_column(String(140), nullable=True)
    batch: Mapped[str | None] = mapped_column(String(80), nullable=True)
    status: Mapped[str] = mapped_column(String(40), default="Active")

class Employee(Base):
    __tablename__ = "employees"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    institution_id: Mapped[int | None] = mapped_column(ForeignKey("institutions.id"), nullable=True, index=True)
    employee_no: Mapped[str] = mapped_column(String(60), index=True)
    full_name: Mapped[str] = mapped_column(String(180))
    department: Mapped[str | None] = mapped_column(String(140), nullable=True)
    designation: Mapped[str | None] = mapped_column(String(140), nullable=True)
    status: Mapped[str] = mapped_column(String(40), default="Active")

class FeeAssignment(Base):
    __tablename__ = "fee_assignments"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    student_id: Mapped[int | None] = mapped_column(ForeignKey("students.id"), nullable=True, index=True)
    institution_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    amount: Mapped[float] = mapped_column(Float, default=0)
    status: Mapped[str] = mapped_column(String(40), default="Unpaid")
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True)

class Payment(Base):
    __tablename__ = "payments"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    student_id: Mapped[int | None] = mapped_column(ForeignKey("students.id"), nullable=True, index=True)
    institution_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    amount: Mapped[float] = mapped_column(Float, default=0)
    status: Mapped[str] = mapped_column(String(40), default="Success")
    paid_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

class AttendanceRecord(Base):
    __tablename__ = "attendance_records"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    employee_id: Mapped[int | None] = mapped_column(ForeignKey("employees.id"), nullable=True, index=True)
    institution_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    attendance_date: Mapped[date] = mapped_column(Date, default=date.today)
    status: Mapped[str] = mapped_column(String(40), default="Present")

class LeaveApplication(Base):
    __tablename__ = "leave_applications"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    employee_id: Mapped[int | None] = mapped_column(ForeignKey("employees.id"), nullable=True, index=True)
    institution_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    status: Mapped[str] = mapped_column(String(40), default="Pending")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

# Finance module entities from the KMCT FinHR functional specification.
class FeeCategory(Base):
    __tablename__ = "fee_categories"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    institution_id: Mapped[int | None] = mapped_column(ForeignKey("institutions.id"), nullable=True, index=True)
    name: Mapped[str] = mapped_column(String(120))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

class FeeHead(Base):
    __tablename__ = "fee_heads"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    institution_id: Mapped[int | None] = mapped_column(ForeignKey("institutions.id"), nullable=True, index=True)
    category_id: Mapped[int | None] = mapped_column(ForeignKey("fee_categories.id"), nullable=True)
    name: Mapped[str] = mapped_column(String(120))
    fee_type: Mapped[str] = mapped_column(String(60), default="Regular")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

class FeeStructure(Base):
    __tablename__ = "fee_structures"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    institution_id: Mapped[int | None] = mapped_column(ForeignKey("institutions.id"), nullable=True, index=True)
    course_id: Mapped[int | None] = mapped_column(ForeignKey("courses.id"), nullable=True, index=True)
    fee_head_id: Mapped[int | None] = mapped_column(ForeignKey("fee_heads.id"), nullable=True)
    amount: Mapped[float] = mapped_column(Float, default=0)
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    academic_year: Mapped[str | None] = mapped_column(String(40), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

class FeeInstallment(Base):
    __tablename__ = "fee_installments"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    fee_structure_id: Mapped[int] = mapped_column(ForeignKey("fee_structures.id", ondelete="CASCADE"), index=True)
    label: Mapped[str] = mapped_column(String(100))
    amount: Mapped[float] = mapped_column(Float, default=0)
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True)

class StudentLedger(Base):
    __tablename__ = "student_ledger"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    institution_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id"), index=True)
    entry_type: Mapped[str] = mapped_column(String(40))
    reference: Mapped[str | None] = mapped_column(String(100), nullable=True)
    debit: Mapped[float] = mapped_column(Float, default=0)
    credit: Mapped[float] = mapped_column(Float, default=0)
    narration: Mapped[str | None] = mapped_column(Text, nullable=True)
    entry_date: Mapped[date] = mapped_column(Date, default=date.today)

class ScholarshipScheme(Base):
    __tablename__ = "scholarship_schemes"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    institution_id: Mapped[int | None] = mapped_column(ForeignKey("institutions.id"), nullable=True, index=True)
    name: Mapped[str] = mapped_column(String(150))
    category: Mapped[str] = mapped_column(String(100))
    amount: Mapped[float] = mapped_column(Float, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

class PaymentTransaction(Base):
    __tablename__ = "payment_transactions"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    institution_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    student_id: Mapped[int | None] = mapped_column(ForeignKey("students.id"), nullable=True, index=True)
    transaction_ref: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    payment_mode: Mapped[str] = mapped_column(String(50), default="Online")
    amount: Mapped[float] = mapped_column(Float, default=0)
    status: Mapped[str] = mapped_column(String(40), default="Pending")
    gateway_ref: Mapped[str | None] = mapped_column(String(120), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

class ReceiptSeries(Base):
    __tablename__ = "receipt_series"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    institution_id: Mapped[int | None] = mapped_column(ForeignKey("institutions.id"), nullable=True, index=True)
    prefix: Mapped[str] = mapped_column(String(30))
    next_number: Mapped[int] = mapped_column(Integer, default=1)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

class ChartOfAccount(Base):
    __tablename__ = "chart_of_accounts"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    institution_id: Mapped[int | None] = mapped_column(ForeignKey("institutions.id"), nullable=True, index=True)
    code: Mapped[str] = mapped_column(String(40), unique=True)
    name: Mapped[str] = mapped_column(String(140))
    account_type: Mapped[str] = mapped_column(String(50))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

class PaymentGatewayConfig(Base):
    __tablename__ = "payment_gateway_configs"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    institution_id: Mapped[int | None] = mapped_column(ForeignKey("institutions.id"), nullable=True, index=True)
    gateway_name: Mapped[str] = mapped_column(String(100))
    merchant_id: Mapped[str | None] = mapped_column(String(120), nullable=True)
    payment_mode: Mapped[str] = mapped_column(String(40), default="Online")
    is_sandbox: Mapped[bool] = mapped_column(Boolean, default=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=False)
