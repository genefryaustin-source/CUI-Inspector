def can_upload(role):
    return role in ("superadmin", "tenant_admin", "user")

def can_manage_users(role):
    return role in ("superadmin", "tenant_admin")

def can_view_all_tenants(role):
    return role in ("superadmin", "auditor")

def can_export_manifest(role):
    return role in ("superadmin", "tenant_admin", "auditor")

def is_read_only(role):
    return role == "auditor"

