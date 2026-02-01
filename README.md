# CUI Inspector – Modular Multi-Tenant (Streamlit Cloud-safe)

## Included feature updates (all 4)
1. **Evidence integrity verification**: Verify Evidence Vault recomputes SHA-256 and compares to DB.
2. **Full text / metadata search**: inspection_text_index stores safe excerpts + metadata for filtering.
3. **Artifact diff + compare runs**: Compare Runs shows hash/risk/pattern/category deltas between two inspections.
4. **Role-based access**: users table + login + audit trail + SuperAdmin + Tenant Admin + Auditor.

## Tenant Admin setup
- SuperAdmin creates a tenant (Tenants page).
- SuperAdmin goes to Users page, selects the tenant in sidebar, creates a user with role `tenant_admin`.
- Tenant Admin logs in and can create `viewer` / `analyst` users for that tenant.

## Optional break-glass recovery (Streamlit Secrets)
Set in Streamlit Cloud Secrets:
SUPERADMIN_RECOVERY="ENABLED"
SUPERADMIN_RECOVERY_PASSWORD="StrongPasswordHere"
Remove secrets after recovery.
