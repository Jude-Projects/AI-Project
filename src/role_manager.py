import json
import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

# REQ-009 names the four roles but not their feature access - this mapping is
# invented, tied to this repo's actual built capabilities, not a given spec.
ROLE_PERMISSIONS = {
    "Business User": {"ask_questions", "view_visualizations", "view_explanations", "follow_up_questions"},
    "Data Analyst": {
        "ask_questions",
        "view_visualizations",
        "view_explanations",
        "follow_up_questions",
        "upload_csv",
        "generate_reports",
        "analyze_data",
    },
    "Data Engineer": {"inspect_schema", "profile_data", "connect_sql"},
    "Executive": {"view_executive_summaries"},
}

_USER_ROLES: dict = {}


class RoleConflictError(Exception):
    pass


class RoleUpdateFailureError(Exception):
    pass


class UnauthorizedAccessError(Exception):
    pass


def assign_role(user_id: str, role: str, admin_id: str) -> dict:
    if user_id in _USER_ROLES:
        raise RoleConflictError(
            f"User '{user_id}' already has a role assigned "
            f"('{_USER_ROLES[user_id]}'). Use update_role() to change it."
        )
    if role not in ROLE_PERMISSIONS:
        raise RoleConflictError(
            f"'{role}' is not a recognized role. "
            f"Supported roles: {sorted(ROLE_PERMISSIONS)}."
        )

    _USER_ROLES[user_id] = role

    logger.info(
        json.dumps(
            {
                "event": "role_assigned",
                "admin_id": admin_id,
                "user_id": user_id,
                "role": role,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )
    )

    return {"user_id": user_id, "role": role, "features": sorted(ROLE_PERMISSIONS[role])}


def update_role(user_id: str, new_role: str, admin_id: str) -> dict:
    if user_id not in _USER_ROLES:
        raise RoleUpdateFailureError(
            f"User '{user_id}' has no existing role to update. Use "
            f"assign_role() first."
        )
    if new_role not in ROLE_PERMISSIONS:
        raise RoleUpdateFailureError(
            f"'{new_role}' is not a recognized role. "
            f"Supported roles: {sorted(ROLE_PERMISSIONS)}."
        )

    _USER_ROLES[user_id] = new_role

    logger.info(
        json.dumps(
            {
                "event": "role_updated",
                "admin_id": admin_id,
                "user_id": user_id,
                "role": new_role,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )
    )

    return {"user_id": user_id, "role": new_role, "features": sorted(ROLE_PERMISSIONS[new_role])}


def check_access(user_id: str, feature: str) -> bool:
    if user_id not in _USER_ROLES:
        raise UnauthorizedAccessError(f"User '{user_id}' has no assigned role.")

    role = _USER_ROLES[user_id]
    return feature in ROLE_PERMISSIONS[role]
