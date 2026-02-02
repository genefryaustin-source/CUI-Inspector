from db import get_db
from utils import now_iso

def log_event(user, action, target=""):
    con = get_db()
    con.execute(
        """
        INSERT INTO audit_log
        (user_email, role, tenant_id, action, target, timestamp)
        VALUES (?,?,?,?,?,?)
        """,
        (
            user["email"],
            user["role"],
            user["tenant_id"],
            action,
            target,
            now_iso(),
        ),
    )
    con.commit()
