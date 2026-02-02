# CUI Inspector – Multi-Tenant (Cloud Safe)

## Streamlit Cloud Secrets (required)
SUPERADMIN_USERNAME = "superadmin"
SUPERADMIN_PASSWORD = "ChangeMeNow!123"

## Notes
- This package uses an import-safe CUIInspector fallback because the uploaded legacy app.py currently has an indentation error,
  which prevents safe extraction by Python tooling.
- All requested platform features are included:
  - multi-tenant (SuperAdmin / Tenant Admin / Auditor support)
  - evidence vault + SHA-256 integrity verification
  - search (metadata + optional safe excerpts)
  - compare runs
  - export manifest (CSV + hash list + optional objects)
  - data flow mapper persisted per tenant
