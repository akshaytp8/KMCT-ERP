import os
from sqlalchemy import select
from .models import Institution, Role, Permission, RolePermission, User
from .security import hash_password

DEFAULT_ROLES = [
    ("SUPERADMIN", "Super Admin", "Central administration across institutions"),
    ("FINANCE_ADMIN", "Finance Admin", "Fee configuration and financial operations"),
    ("HR_ADMIN", "HR Admin", "Employee and HR operations"),
    ("ADMIN", "Admin", "Student administration and academic operations"),
    ("FACULTY", "Faculty", "Teaching and classroom activities"),
    ("HOD", "HOD", "Department-level review and approvals"),
    ("PRINCIPAL", "Principal", "Institution-level approvals"),
    ("STUDENT", "Student", "Student self-service portal"),
]

DEFAULT_PERMISSIONS = [
    ("dashboard.view", "View dashboard", "Dashboard"),
    ("institutions.manage", "Manage institutions", "Institution Setup"),
    ("masters.manage", "Manage academic masters", "Institution Setup"),
    ("users.manage", "Manage users", "Access Control"),
    ("roles.manage", "Manage roles", "Access Control"),
    ("permissions.manage", "Manage permissions", "Access Control"),
    ("workflows.manage", "Manage approval workflows", "Workflow"),
    ("notifications.manage", "Manage notifications", "Communication"),
    ("audit.view", "View audit logs", "Monitoring"),
    ("reports.view", "View institution reports", "Reports"),
    ("finance.dashboard.view", "View finance dashboard", "Finance"),
    ("finance.fees.manage", "Manage fee structures and heads", "Finance"),
    ("finance.ledger.manage", "Manage student fee mapping and ledger", "Finance"),
    ("finance.payments.view", "View payment collections", "Finance"),
    ("finance.reports.view", "View finance reports", "Finance"),
]

def seed_database(db):
    ncp = db.scalar(select(Institution).where(Institution.code == "NCP"))
    if not ncp:
        ncp = Institution(code="NCP", name="National College of Pharmacy", address="KMCT", is_active=True)
        db.add(ncp)
        db.flush()
    for key, name, description in DEFAULT_ROLES:
        if not db.scalar(select(Role).where(Role.key == key)):
            db.add(Role(key=key, name=name, description=description, is_system=True))
    for key, name, module in DEFAULT_PERMISSIONS:
        if not db.scalar(select(Permission).where(Permission.key == key)):
            db.add(Permission(key=key, name=name, module=module))
    db.flush()
    # Grant the seeded Super Admin every starter permission in the configuration matrix.
    super_role = db.scalar(select(Role).where(Role.key == "SUPERADMIN"))
    if super_role:
        for permission in db.scalars(select(Permission)).all():
            exists = db.scalar(select(RolePermission).where(
                RolePermission.role_id == super_role.id,
                RolePermission.permission_id == permission.id,
            ))
            if not exists:
                db.add(RolePermission(role_id=super_role.id, permission_id=permission.id, is_granted=True))
    finance_role = db.scalar(select(Role).where(Role.key == "FINANCE_ADMIN"))
    if finance_role:
        for permission in db.scalars(select(Permission).where(Permission.module == "Finance")).all():
            exists = db.scalar(select(RolePermission).where(RolePermission.role_id == finance_role.id, RolePermission.permission_id == permission.id))
            if not exists:
                db.add(RolePermission(role_id=finance_role.id, permission_id=permission.id, is_granted=True))
    username = os.getenv("SUPERADMIN_USERNAME", "admin")
    email = os.getenv("SUPERADMIN_EMAIL", "admin@kmct.local")
    user = db.scalar(select(User).where(User.username == username))
    if not user:
        role = db.scalar(select(Role).where(Role.key == "SUPERADMIN"))
        password = os.getenv("SUPERADMIN_PASSWORD", "ChangeMe123!")
        user = User(username=username, full_name="KMCT Super Admin", email=email,
                    password_hash=hash_password(password), institution_id=None,
                    role_id=role.id if role else None, is_active=True)
        db.add(user)
    finance_username = os.getenv("FINANCE_USERNAME", "finance")
    finance_user = db.scalar(select(User).where(User.username == finance_username))
    if not finance_user:
        finance_role = db.scalar(select(Role).where(Role.key == "FINANCE_ADMIN"))
        finance_user = User(username=finance_username, full_name="Joseph Mathew", email=os.getenv("FINANCE_EMAIL", "finance@kmct.local"),
                            password_hash=hash_password(os.getenv("FINANCE_PASSWORD", "Finance123!")),
                            institution_id=ncp.id, role_id=finance_role.id if finance_role else None, is_active=True)
        db.add(finance_user)
    db.commit()
