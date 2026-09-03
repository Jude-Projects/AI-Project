import json
import logging
from datetime import datetime

import pytest

from role_manager import (
    RoleConflictError,
    RoleUpdateFailureError,
    UnauthorizedAccessError,
    assign_role,
    check_access,
    update_role,
)


def test_assign_role_grants_role_specific_features():
    assign_role("user-1", "Data Engineer", admin_id="admin-1")

    assert check_access("user-1", "inspect_schema") is True
    assert check_access("user-1", "profile_data") is True


def test_assign_role_denies_features_outside_the_role():
    assign_role("user-2", "Executive", admin_id="admin-1")

    assert check_access("user-2", "inspect_schema") is False
    assert check_access("user-2", "upload_csv") is False


def test_update_role_changes_access_accordingly():
    user_id = "user-4"
    assign_role(user_id, "Business User", admin_id="admin-1")
    assert check_access(user_id, "ask_questions") is True
    assert check_access(user_id, "inspect_schema") is False

    update_role(user_id, "Data Engineer", admin_id="admin-1")

    assert check_access(user_id, "inspect_schema") is True
    assert check_access(user_id, "ask_questions") is False


def test_assign_role_raises_on_conflict_when_user_already_has_a_role():
    assign_role("user-5", "Business User", admin_id="admin-1")

    with pytest.raises(RoleConflictError):
        assign_role("user-5", "Executive", admin_id="admin-1")


def test_assign_role_raises_on_conflict_for_unrecognized_role():
    with pytest.raises(RoleConflictError):
        assign_role("user-6", "Superuser", admin_id="admin-1")


def test_update_role_raises_on_failure_when_user_has_no_existing_role():
    with pytest.raises(RoleUpdateFailureError):
        update_role("user-7", "Executive", admin_id="admin-1")


def test_update_role_raises_on_failure_for_unrecognized_role():
    assign_role("user-8", "Business User", admin_id="admin-1")

    with pytest.raises(RoleUpdateFailureError):
        update_role("user-8", "Superuser", admin_id="admin-1")


def test_check_access_raises_unauthorized_for_user_with_no_role():
    with pytest.raises(UnauthorizedAccessError):
        check_access("user-never-assigned", "ask_questions")


def test_assign_role_logs_admin_user_and_role(caplog):
    with caplog.at_level(logging.INFO, logger="role_manager"):
        assign_role("user-3", "Business User", admin_id="admin-1")

    assert len(caplog.records) == 1
    logged = json.loads(caplog.records[0].message)
    assert logged["event"] == "role_assigned"
    assert logged["admin_id"] == "admin-1"
    assert logged["user_id"] == "user-3"
    assert logged["role"] == "Business User"
    # Fails loudly if "timestamp" is missing or not a real ISO-8601 datetime,
    # rather than silently accepting any string in that field.
    datetime.fromisoformat(logged["timestamp"])
