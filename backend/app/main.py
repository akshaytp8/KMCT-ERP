import json
from datetime import date, datetime
from typing import Any

import jwt
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from sqlalchemy.sql.sqltypes import Date as SQLDate, DateTime as SQLDateTime

from .database import Base, engine, get_db, SessionLocal
from . import models
from .seed import seed_database
from .security import create_access_token, decode_access_token, verify_password, hash_password

app = FastAPI(title="KMCT ERP – Super Admin API", version="1.0.0",
              description="Central administration APIs for the KMCT multi-institution ERP.")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True, allow_methods=["*"], allow_headers=["*"],
)

bearer = HTTPBearer(auto_error=False)

RESOURCES = {
    "institutions": (models.Institution, ["code", "name", "address", "is_active"]),
    "academic-years": (models.AcademicYear, ["institution_id", "label", "start_date", "end_date", "is_current", "is_active"]),
    "courses": (models.Course, ["institution_id", "code", "name", "programme_type", "duration_years", "is_active"]),
    "departments": (models.Department, ["institution_id", "code", "name", "is_active"]),
    "batches": (models.Batch, ["institution_id", "course_id", "label", "start_year", "end_year", "is_active"]),
    "semesters": (models.Semester, ["course_id", "label", "sequence", "is_active"]),
    "users": (models.User, ["username", "full_name", "email", "password", "institution_id", "role_id", "is_active"]),
    "roles": (models.Role, ["key", "name", "description", "is_system"]),
    "permissions": (models.Permission, ["key", "name", "module", "description"]),
    "role-permissions": (models.RolePermission, ["role_id", "permission_id", "is_granted"]),
    "portal-access": (models.PortalAccess, ["user_id", "portal_key", "can_view", "can_create", "can_update", "can_delete"]),
    "approval-workflows": (models.ApprovalWorkflow, ["institution_id", "name", "module", "level1_role", "level2_role", "is_active"]),
    "notification-configs": (models.NotificationConfig, ["institution_id", "event_key", "channel_email", "channel_in_app", "enabled"]),
}
READ_ONLY = {
    "students": models.Student,
    "employees": models.Employee,
}


def serialize(obj: Any) -> dict:
    data = {}
    for column in obj.__table__.columns:
        if column.name == "password_hash":
            continue
        value = getattr(obj, column.name)
        if isinstance(value, (datetime, date)):
            value = value.isoformat()
        data[column.name] = value
    if isinstance(obj, models.User):
        role = getattr(obj, "_role_name", None)
        data["role_name"] = role
    if isinstance(obj, models.AuditLog):
        try:
            data["details"] = json.loads(data["details"]) if data.get("details") else {}
        except (ValueError, TypeError):
            pass
    return data


def get_current_user(credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
                     db: Session = Depends(get_db)):
    if not credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    try:
        payload = decode_access_token(credentials.credentials)
        user_id = int(payload.get("sub", ""))
    except (jwt.InvalidTokenError, ValueError, TypeError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")
    user = db.get(models.User, user_id)
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User is inactive or unavailable")
    role = db.get(models.Role, user.role_id) if user.role_id else None
    if not role or role.key not in {"SUPERADMIN", "FINANCE_ADMIN"}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Authorised portal access required")
    return user


def require_superadmin(user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    role = db.get(models.Role, user.role_id) if user.role_id else None
    if not role or role.key != "SUPERADMIN":
        raise HTTPException(status_code=403, detail="Super Admin access required")
    return user


def write_audit(db: Session, actor: models.User, action: str, entity: str,
                entity_id: int | None, details: dict | None = None, institution_id: int | None = None):
    db.add(models.AuditLog(
        actor_id=actor.id, actor_name=actor.full_name, action=action,
        entity=entity, entity_id=str(entity_id) if entity_id is not None else None,
        details=json.dumps(details or {}, default=str), institution_id=institution_id,
    ))


def parse_value(model, key: str, value: Any):
    if value is None:
        return None
    column = model.__table__.columns.get(key)
    if column is None:
        return value
    python_type = column.type.python_type
    if value == "" and column.nullable:
        return None
    if python_type is date and isinstance(value, str):
        return date.fromisoformat(value)
    if python_type is datetime and isinstance(value, str):
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    if python_type is bool:
        if isinstance(value, str):
            return value.lower() in ("true", "1", "yes", "on")
        return bool(value)
    if python_type is int and value != "":
        return int(value)
    if python_type is float and value != "":
        return float(value)
    return value



FINANCE_RESOURCES = {
    "fee-categories": (models.FeeCategory, ["institution_id", "name", "description", "is_active"]),
    "fee-heads": (models.FeeHead, ["institution_id", "category_id", "name", "fee_type", "is_active"]),
    "fee-structures": (models.FeeStructure, ["institution_id", "course_id", "fee_head_id", "amount", "due_date", "academic_year", "is_active"]),
    "installments": (models.FeeInstallment, ["fee_structure_id", "label", "amount", "due_date"]),
    "scholarships": (models.ScholarshipScheme, ["institution_id", "name", "category", "amount", "is_active"]),
    "receipt-series": (models.ReceiptSeries, ["institution_id", "prefix", "next_number", "is_active"]),
    "chart-of-accounts": (models.ChartOfAccount, ["institution_id", "code", "name", "account_type", "is_active"]),
    "payment-gateways": (models.PaymentGatewayConfig, ["institution_id", "gateway_name", "merchant_id", "payment_mode", "is_sandbox", "is_active"]),
}


def finance_actor(user: models.User, db: Session):
    role = db.get(models.Role, user.role_id) if user.role_id else None
    if not role or role.key not in {"FINANCE_ADMIN", "SUPERADMIN"}:
        raise HTTPException(status_code=403, detail="Finance Admin access required")
    return role


@app.get("/api/finance/dashboard")
def finance_dashboard(user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    finance_actor(user, db)
    inst_filter = user.institution_id
    billed_stmt = select(func.coalesce(func.sum(models.FeeAssignment.amount), 0))
    collected_stmt = select(func.coalesce(func.sum(models.Payment.amount), 0)).where(models.Payment.status == "Success")
    students_stmt = select(func.count(models.Student.id))
    structures_stmt = select(func.count(models.FeeStructure.id))
    payments_stmt = select(func.count(models.Payment.id))
    if inst_filter:
        billed_stmt = billed_stmt.where(models.FeeAssignment.institution_id == inst_filter)
        collected_stmt = collected_stmt.where(models.Payment.institution_id == inst_filter)
        students_stmt = students_stmt.where(models.Student.institution_id == inst_filter)
        structures_stmt = structures_stmt.where(models.FeeStructure.institution_id == inst_filter)
        payments_stmt = payments_stmt.where(models.Payment.institution_id == inst_filter)
    billed = float(db.scalar(billed_stmt) or 0); collected = float(db.scalar(collected_stmt) or 0)
    monthly=[]; today=date.today()
    for offset in range(5,-1,-1):
        idx=today.year*12+today.month-1-offset; y,m=divmod(idx,12); m+=1
        start=date(y,m,1); end=date(y+1,1,1) if m==12 else date(y,m+1,1)
        stmt=select(func.coalesce(func.sum(models.Payment.amount),0)).where(
            models.Payment.status=="Success", models.Payment.paid_at>=datetime.combine(start,datetime.min.time()),
            models.Payment.paid_at<datetime.combine(end,datetime.min.time()))
        if inst_filter: stmt=stmt.where(models.Payment.institution_id==inst_filter)
        monthly.append({"month":f"{y}-{m:02d}","label":start.strftime("%Y-%m"),"amount":float(db.scalar(stmt) or 0)})
    return {"students":db.scalar(students_stmt) or 0,"billed":billed,"collected":collected,
            "outstanding":max(billed-collected,0),"monthly_collection":monthly,
            "fee_structures":db.scalar(structures_stmt) or 0,"payments_count":db.scalar(payments_stmt) or 0}


@app.get("/api/finance/courses")
def finance_courses(user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    finance_actor(user, db); stmt=select(models.Course)
    if user.institution_id: stmt=stmt.where(models.Course.institution_id==user.institution_id)
    return [serialize(x) for x in db.scalars(stmt.order_by(models.Course.name)).all()]


@app.get("/api/finance/academic-masters")
def finance_academic_masters(user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    finance_actor(user, db)
    result={}
    for key, model in [("institutions",models.Institution),("academic_years",models.AcademicYear),("courses",models.Course),("batches",models.Batch),("semesters",models.Semester)]:
        stmt=select(model)
        if user.institution_id and hasattr(model,"institution_id"): stmt=stmt.where(model.institution_id==user.institution_id)
        result[key]=[serialize(x) for x in db.scalars(stmt.order_by(model.id)).all()]
    return result


@app.post("/api/finance/fee-assignments")
def finance_create_assignment(payload: dict, user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    finance_actor(user, db)
    student_id=int(payload.get("student_id") or 0); amount=float(payload.get("amount") or 0)
    student=db.get(models.Student,student_id)
    if not student or (user.institution_id and student.institution_id!=user.institution_id): raise HTTPException(404,"Student not found")
    if amount<=0: raise HTTPException(422,"Amount must be greater than zero")
    due_date=parse_value(models.FeeAssignment,"due_date",payload.get("due_date"))
    assignment=models.FeeAssignment(student_id=student.id,institution_id=student.institution_id,amount=amount,status="Unpaid",due_date=due_date)
    db.add(assignment); db.flush()
    db.add(models.StudentLedger(institution_id=student.institution_id,student_id=student.id,entry_type="FEE_ASSIGNED",
        reference=f"FEE-{assignment.id}",debit=amount,credit=0,narration=payload.get("narration") or "Fee assigned",entry_date=date.today()))
    write_audit(db,user,"FEE_ASSIGN","STUDENT",student.id,{"amount":amount,"assignment_id":assignment.id},student.institution_id)
    db.commit(); db.refresh(assignment); return serialize(assignment)


@app.get("/api/finance/students")
def finance_students(user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    finance_actor(user, db); stmt=select(models.Student)
    if user.institution_id: stmt=stmt.where(models.Student.institution_id==user.institution_id)
    return [serialize(x) for x in db.scalars(stmt.order_by(models.Student.full_name)).all()]


@app.post("/api/finance/fee-structures/{structure_id}/assign")
def assign_fee_structure(structure_id: int, user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    finance_actor(user, db)
    structure=db.get(models.FeeStructure,structure_id)
    if not structure or (user.institution_id and structure.institution_id != user.institution_id):
        raise HTTPException(404,"Fee structure not found")
    course=db.get(models.Course,structure.course_id) if structure.course_id else None
    stmt=select(models.Student).where(models.Student.institution_id==structure.institution_id)
    if course: stmt=stmt.where(models.Student.course==course.name)
    students=db.scalars(stmt).all()
    created=0
    for student in students:
        exists=db.scalar(select(models.FeeAssignment).where(models.FeeAssignment.student_id==student.id,
            models.FeeAssignment.institution_id==structure.institution_id,
            models.FeeAssignment.amount==structure.amount, models.FeeAssignment.due_date==structure.due_date))
        if not exists:
            db.add(models.FeeAssignment(student_id=student.id,institution_id=structure.institution_id,
                amount=structure.amount,status="Unpaid",due_date=structure.due_date))
            created+=1
    write_audit(db,user,"FEE_ASSIGN","FEE_STRUCTURE",structure.id,{"assigned_count":created},structure.institution_id)
    db.commit()
    return {"assigned_count":created,"message":f"Fee assigned to {created} student(s)."}


@app.get("/api/finance/ledger")
def finance_ledger(user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    finance_actor(user, db)
    stmt=select(models.FeeAssignment, models.Student).join(models.Student, models.Student.id==models.FeeAssignment.student_id, isouter=True)
    if user.institution_id: stmt=stmt.where(models.FeeAssignment.institution_id==user.institution_id)
    return [{"id":a.id,"student_id":a.student_id,"student_no":st.student_no if st else "—",
             "student_name":st.full_name if st else "Unmapped student","amount":a.amount,"status":a.status,
             "due_date":a.due_date.isoformat() if a.due_date else None}
            for a,st in db.execute(stmt.order_by(models.FeeAssignment.id.desc())).all()]


@app.get("/api/finance/collection-report")
def finance_collection_report(user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    finance_actor(user, db); stmt=select(models.Payment, models.Student).join(models.Student, models.Student.id==models.Payment.student_id, isouter=True)
    if user.institution_id: stmt=stmt.where(models.Payment.institution_id==user.institution_id)
    return [{"id":p.id,"student_no":st.student_no if st else "—","student_name":st.full_name if st else "—",
             "amount":p.amount,"status":p.status,"paid_at":p.paid_at.isoformat() if p.paid_at else None}
            for p,st in db.execute(stmt.order_by(models.Payment.paid_at.desc())).all()]


@app.get("/api/finance/audit-logs")
def finance_audit_logs(limit: int = 200, user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    finance_actor(user, db); stmt=select(models.AuditLog)
    if user.institution_id: stmt=stmt.where(models.AuditLog.institution_id==user.institution_id)
    return [serialize(x) for x in db.scalars(stmt.order_by(models.AuditLog.created_at.desc()).limit(min(limit,500))).all()]


@app.get("/api/finance/{resource}")
def finance_list(resource: str, user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    finance_actor(user, db)
    if resource not in FINANCE_RESOURCES: raise HTTPException(404, "Unknown finance resource")
    model, fields=FINANCE_RESOURCES[resource]; stmt=select(model)
    if user.institution_id and "institution_id" in fields: stmt=stmt.where(model.institution_id==user.institution_id)
    return [serialize(x) for x in db.scalars(stmt.order_by(model.id.desc())).all()]


@app.post("/api/finance/{resource}")
def finance_create(resource: str, payload: dict, user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    finance_actor(user, db)
    if resource not in FINANCE_RESOURCES: raise HTTPException(404, "Unknown finance resource")
    model, fields=FINANCE_RESOURCES[resource]; data={k:parse_value(model,k,v) for k,v in payload.items() if k in fields}
    if user.institution_id and "institution_id" in fields: data["institution_id"]=user.institution_id
    obj=model(**data); db.add(obj)
    try:
        db.flush(); write_audit(db,user,"CREATE",resource.upper(),obj.id,data,user.institution_id); db.commit(); db.refresh(obj)
    except IntegrityError:
        db.rollback(); raise HTTPException(409,"Record conflicts with existing data or a required relationship is missing")
    return serialize(obj)


@app.patch("/api/finance/{resource}/{record_id}")
def finance_update(resource: str, record_id: int, payload: dict, user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    finance_actor(user, db)
    if resource not in FINANCE_RESOURCES: raise HTTPException(404, "Unknown finance resource")
    model, fields=FINANCE_RESOURCES[resource]; obj=db.get(model,record_id)
    if not obj or (user.institution_id and getattr(obj,"institution_id",user.institution_id)!=user.institution_id): raise HTTPException(404,"Record not found")
    changes={k:parse_value(model,k,v) for k,v in payload.items() if k in fields}
    for k,v in changes.items(): setattr(obj,k,v)
    write_audit(db,user,"UPDATE",resource.upper(),obj.id,changes,user.institution_id)
    try: db.commit(); db.refresh(obj)
    except IntegrityError: db.rollback(); raise HTTPException(409,"Unable to update record")
    return serialize(obj)


@app.delete("/api/finance/{resource}/{record_id}")
def finance_delete(resource: str, record_id: int, user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    finance_actor(user, db)
    if resource not in FINANCE_RESOURCES: raise HTTPException(404, "Unknown finance resource")
    model, fields=FINANCE_RESOURCES[resource]; obj=db.get(model,record_id)
    if not obj or (user.institution_id and getattr(obj,"institution_id",user.institution_id)!=user.institution_id): raise HTTPException(404,"Record not found")
    write_audit(db,user,"DELETE",resource.upper(),obj.id,{"record":serialize(obj)},user.institution_id)
    db.delete(obj); db.commit(); return {"ok":True}


@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_database(db)
    finally:
        db.close()


@app.get("/api/health")
def health():
    return {"status": "ok", "service": "kmct-super-admin-api"}


@app.post("/api/auth/login")
def login(payload: dict, db: Session = Depends(get_db)):
    username = str(payload.get("username", "")).strip()
    password = str(payload.get("password", ""))
    user = db.scalar(select(models.User).where(models.User.username == username))
    if not user or not user.is_active or not verify_password(password, user.password_hash):
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    role = db.get(models.Role, user.role_id) if user.role_id else None
    if not role or role.key not in {"SUPERADMIN", "FINANCE_ADMIN"}:
        raise HTTPException(status_code=403, detail="This account does not have access to an available portal")
    user.last_login = datetime.utcnow()
    write_audit(db, user, "LOGIN", "USER", user.id, {"username": user.username})
    db.commit()
    return {"access_token": create_access_token(user.id, user.username, role.key), "token_type": "bearer",
            "user": {"id": user.id, "username": user.username, "full_name": user.full_name,
                     "email": user.email, "role": role.key}}


@app.get("/api/auth/me")
def me(user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    role = db.get(models.Role, user.role_id) if user.role_id else None
    return {"id": user.id, "username": user.username, "full_name": user.full_name,
            "email": user.email, "role": role.key if role else None}


@app.get("/api/admin/dashboard")
def dashboard(user: models.User = Depends(require_superadmin), db: Session = Depends(get_db)):
    students = db.scalar(select(func.count(models.Student.id))) or 0
    employees = db.scalar(select(func.count(models.Employee.id))) or 0
    billed = db.scalar(select(func.coalesce(func.sum(models.FeeAssignment.amount), 0))) or 0
    collected = db.scalar(select(func.coalesce(func.sum(models.Payment.amount), 0)).where(models.Payment.status == "Success")) or 0
    outstanding = max(float(billed) - float(collected), 0)
    today = date.today()
    present = db.scalar(select(func.count(models.AttendanceRecord.id)).where(
        models.AttendanceRecord.attendance_date == today,
        func.lower(models.AttendanceRecord.status) == "present")) or 0
    pending_leaves = db.scalar(select(func.count(models.LeaveApplication.id)).where(
        func.lower(models.LeaveApplication.status) == "pending")) or 0
    audit_count = db.scalar(select(func.count(models.AuditLog.id))) or 0
    monthly = []
    year, month = today.year, today.month
    for offset in range(5, -1, -1):
        month_index = year * 12 + month - 1 - offset
        y, m = divmod(month_index, 12)
        m += 1
        start = date(y, m, 1)
        if m == 12:
            end = date(y + 1, 1, 1)
        else:
            end = date(y, m + 1, 1)
        amount = db.scalar(select(func.coalesce(func.sum(models.Payment.amount), 0)).where(
            models.Payment.status == "Success",
            models.Payment.paid_at >= datetime.combine(start, datetime.min.time()),
            models.Payment.paid_at < datetime.combine(end, datetime.min.time()))) or 0
        monthly.append({"month": start.strftime("%Y-%m"), "label": start.strftime("%b %Y"), "amount": float(amount)})
    recent_audit = db.scalars(select(models.AuditLog).order_by(models.AuditLog.created_at.desc()).limit(8)).all()
    return {"students": students, "employees": employees, "billed": float(billed),
            "collected": float(collected), "outstanding": outstanding,
            "present_today": present, "pending_leaves": pending_leaves,
            "audit_entries": audit_count, "monthly_collection": monthly,
            "recent_audit": [serialize(x) for x in recent_audit]}


@app.get("/api/admin/audit-logs")
def audit_logs(limit: int = 100, entity: str | None = None,
               user: models.User = Depends(require_superadmin), db: Session = Depends(get_db)):
    stmt = select(models.AuditLog).order_by(models.AuditLog.created_at.desc()).limit(min(max(limit, 1), 500))
    if entity:
        stmt = stmt.where(models.AuditLog.entity == entity.upper())
    return [serialize(x) for x in db.scalars(stmt).all()]


@app.get("/api/admin/institution-reports")
def institution_reports(user: models.User = Depends(require_superadmin), db: Session = Depends(get_db)):
    institutions = db.scalars(select(models.Institution).order_by(models.Institution.name)).all()
    output = []
    for institution in institutions:
        students = db.scalar(select(func.count(models.Student.id)).where(models.Student.institution_id == institution.id)) or 0
        employees = db.scalar(select(func.count(models.Employee.id)).where(models.Employee.institution_id == institution.id)) or 0
        billed = db.scalar(select(func.coalesce(func.sum(models.FeeAssignment.amount), 0)).where(models.FeeAssignment.institution_id == institution.id)) or 0
        collected = db.scalar(select(func.coalesce(func.sum(models.Payment.amount), 0)).where(
            models.Payment.institution_id == institution.id, models.Payment.status == "Success")) or 0
        output.append({"institution_id": institution.id, "institution": institution.name,
                       "code": institution.code, "students": students, "employees": employees,
                       "billed": float(billed), "collected": float(collected),
                       "outstanding": max(float(billed) - float(collected), 0)})
    return output


@app.get("/api/admin/{resource}")
def list_resource(resource: str, user: models.User = Depends(require_superadmin), db: Session = Depends(get_db)):
    if resource in READ_ONLY:
        model = READ_ONLY[resource]
        return [serialize(x) for x in db.scalars(select(model).order_by(model.id.desc()).limit(500)).all()]
    if resource not in RESOURCES:
        raise HTTPException(status_code=404, detail="Unknown resource")
    model, _ = RESOURCES[resource]
    records = db.scalars(select(model).order_by(model.id.desc()).limit(500)).all()
    output = []
    for record in records:
        item = serialize(record)
        if isinstance(record, models.User):
            role = db.get(models.Role, record.role_id) if record.role_id else None
            item["role_name"] = role.name if role else "Unassigned"
        if isinstance(record, models.PortalAccess):
            target = db.get(models.User, record.user_id)
            item["username"] = target.username if target else "Unknown"
        if isinstance(record, models.RolePermission):
            role = db.get(models.Role, record.role_id)
            permission = db.get(models.Permission, record.permission_id)
            item["role_name"] = role.name if role else "Unknown"
            item["permission_name"] = permission.name if permission else "Unknown"
        output.append(item)
    return output


@app.post("/api/admin/{resource}")
def create_resource(resource: str, payload: dict, user: models.User = Depends(require_superadmin), db: Session = Depends(get_db)):
    if resource not in RESOURCES:
        raise HTTPException(status_code=404, detail="Unknown or read-only resource")
    model, allowed = RESOURCES[resource]
    data = {k: parse_value(model, k, v) for k, v in payload.items()
            if k in allowed and k != "password"
            and (v != "" or model.__table__.columns.get(k).nullable)}
    if resource == "users":
        password = payload.get("password")
        if not password:
            raise HTTPException(status_code=422, detail="A temporary password is required when creating a user")
        data["password_hash"] = hash_password(str(password))
    try:
        record = model(**data)
        db.add(record)
        db.flush()
        institution_id = getattr(record, "institution_id", None)
        audit_data = {k: v for k, v in data.items() if k != "password_hash"}
        write_audit(db, user, "CREATE", resource.upper(), record.id, audit_data, institution_id)
        db.commit()
        db.refresh(record)
        result = serialize(record)
        if isinstance(record, models.User):
            role = db.get(models.Role, record.role_id) if record.role_id else None
            result["role_name"] = role.name if role else "Unassigned"
        return result
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="A unique value or related record conflicts with existing data") from exc
    except (ValueError, TypeError) as exc:
        db.rollback()
        raise HTTPException(status_code=422, detail=f"Invalid field value: {exc}") from exc


@app.patch("/api/admin/{resource}/{record_id}")
def update_resource(resource: str, record_id: int, payload: dict,
                    user: models.User = Depends(require_superadmin), db: Session = Depends(get_db)):
    if resource not in RESOURCES:
        raise HTTPException(status_code=404, detail="Unknown or read-only resource")
    model, allowed = RESOURCES[resource]
    record = db.get(model, record_id)
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
    data = {k: parse_value(model, k, v) for k, v in payload.items()
            if k in allowed and k != "password"
            and (v != "" or model.__table__.columns.get(k).nullable)}
    if resource == "users" and payload.get("password"):
        record.password_hash = hash_password(str(payload["password"]))
    try:
        for key, value in data.items():
            setattr(record, key, value)
        db.flush()
        write_audit(db, user, "UPDATE", resource.upper(), record.id, data,
                    getattr(record, "institution_id", None))
        db.commit()
        db.refresh(record)
        result = serialize(record)
        if isinstance(record, models.User):
            role = db.get(models.Role, record.role_id) if record.role_id else None
            result["role_name"] = role.name if role else "Unassigned"
        return result
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="A unique value or related record conflicts with existing data") from exc
    except (ValueError, TypeError) as exc:
        db.rollback()
        raise HTTPException(status_code=422, detail=f"Invalid field value: {exc}") from exc


@app.delete("/api/admin/{resource}/{record_id}")
def delete_resource(resource: str, record_id: int,
                    user: models.User = Depends(require_superadmin), db: Session = Depends(get_db)):
    if resource not in RESOURCES:
        raise HTTPException(status_code=404, detail="Unknown or read-only resource")
    model, _ = RESOURCES[resource]
    record = db.get(model, record_id)
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
    if isinstance(record, models.Role) and record.is_system:
        raise HTTPException(status_code=403, detail="System roles cannot be deleted")
    if isinstance(record, models.User) and record.id == user.id:
        raise HTTPException(status_code=403, detail="You cannot delete your own account")
    snapshot = serialize(record)
    db.delete(record)
    write_audit(db, user, "DELETE", resource.upper(), record_id, snapshot,
                snapshot.get("institution_id"))
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="This record is still referenced by other records") from exc
    return {"deleted": True, "id": record_id}
