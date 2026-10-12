import datetime
import uuid
from typing import Dict, Any, Optional

def log_marks_audit(
    db,
    actor_uid: str,
    actor_email: str,
    actor_role: str,
    action: str,
    course_id: str,
    student_uid: str,
    old_value: Optional[Dict[str, Any]],
    new_value: Optional[Dict[str, Any]],
    ip_address: Optional[str] = None
) -> str:
    """
    Creates an immutable audit log entry in the 'audit_logs' collection.
    """
    log_id = str(uuid.uuid4())
    audit_data = {
        "id": log_id,
        "actor_uid": actor_uid,
        "actor_email": actor_email,
        "actor_role": actor_role,
        "action": action, # 'CREATE_MARKS', 'UPDATE_MARKS', 'BULK_UPLOAD_MARKS'
        "course_id": course_id,
        "student_uid": student_uid,
        "old_value": old_value,
        "new_value": new_value,
        "ip_address": ip_address or "127.0.0.1",
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat()
    }
    
    try:
        db.collection("audit_logs").document(log_id).set(audit_data)
        return log_id
    except Exception as e:
        print(f"Error writing audit log: {e}")
        return ""
