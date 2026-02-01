# Multi-tenant CUI Portal

## Roles
- superadmin: manage tenants, create tenant_admins, create auditors (cross-tenant), view all audit logs.
- tenant_admin: manage users in their tenant.
- auditor (read-only): may switch tenants and generate manifests/verify/search/diff (UI enforcement is best-effort).
- analyst/viewer: tenant-bound.

## DB / Repo
- SQLite: data/evidence_mt.db
- Repo: data/repo/ (content-addressed objects + versioned refs)

## FedRAMP/CMMC Evidence Manifest
Use 📦 Evidence Manifest to generate manifest.csv + hashes.sha256.txt (and optional objects/) in a ZIP.
