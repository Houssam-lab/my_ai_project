"""ISS-214 — an admin is shown the student view whenever user-service answers ``/me``.

Login goes to user-service first and its ``UserResponse`` carries ``is_admin``, so the
first screen is right. The frontend then calls ``/api/security/user/me`` and overwrites
the user with the answer. That call reaches user-service's ``/api/v1/users/me``, whose
``UserOut`` has **no** ``is_admin`` field — only ``roles``. The boundary read
``user_data.get("is_admin", False)``, so every admin became a student on every page load
while user-service was running (the default in Codespaces, ``supervisor.sh`` :8001).

The older test in ``test_auth_boundary_migration.py`` hid this: it feeds ``get_me`` a
hand-written dict *with* ``is_admin``, a shape the service never returns. The payloads
here are built from the service's own response models, as FastAPI serializes them.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.boundaries.auth_boundary_service import (
    AuthBoundaryService,
    _is_admin_from_service,
)
from app.services.rbac import ADMIN_ROLE, STANDARD_ROLE
from microservices.user_service.src.schemas.auth import (
    AuthResponse,
    RegisterResponse,
    UserResponse,
)
from microservices.user_service.src.schemas.ums import UserOut, UserStatus
from microservices.user_service.src.services.rbac import ADMIN_ROLE as SERVICE_ADMIN_ROLE

_CLIENT = "app.services.boundaries.auth_boundary_service.user_service_client"


def _wire(model: object) -> dict[str, object]:
    """The JSON body FastAPI sends for a ``response_model`` (it serializes by alias)."""
    return model.model_dump(mode="json", by_alias=True)  # type: ignore[attr-defined]


def _users_me(roles: list[str]) -> dict[str, object]:
    return _wire(
        UserOut(
            id=1,
            email="owner@example.org",
            full_name="Owner",
            is_active=True,
            status=UserStatus.ACTIVE,
            roles=roles,
        )
    )


@pytest.fixture
def service() -> AuthBoundaryService:
    return AuthBoundaryService(AsyncMock())


@pytest.mark.asyncio
async def test_me_from_user_service_keeps_an_admin_admin(service: AuthBoundaryService) -> None:
    payload = _users_me([ADMIN_ROLE])
    assert "is_admin" not in payload  # the shape that caused ISS-214
    with patch(_CLIENT) as client:
        client.get_me = AsyncMock(return_value=payload)
        service.persistence.get_user_by_id = AsyncMock()

        result = await service.get_current_user("token")

    assert result["is_admin"] is True
    service.persistence.get_user_by_id.assert_not_called()


@pytest.mark.asyncio
async def test_me_from_user_service_keeps_a_student_a_student(
    service: AuthBoundaryService,
) -> None:
    with patch(_CLIENT) as client:
        client.get_me = AsyncMock(return_value=_users_me(["USER", STANDARD_ROLE]))

        result = await service.get_current_user("token")

    assert result["is_admin"] is False


@pytest.mark.asyncio
async def test_login_through_user_service_passes_the_admin_flag(
    service: AuthBoundaryService,
) -> None:
    body = _wire(
        AuthResponse(
            access_token="t",
            user=UserResponse(id=1, name="Owner", email="owner@example.org", is_admin=True),
            landing_path="/admin",
        )
    )
    request = MagicMock()
    request.headers.get.return_value = "agent"
    with (
        patch(_CLIENT) as client,
        patch("app.services.boundaries.auth_boundary_service.chrono_shield") as shield,
    ):
        shield.check_allowance = AsyncMock()
        client.login_user = AsyncMock(return_value=body)

        result = await service.authenticate_user("owner@example.org", "pw", request)

    assert result["user"]["is_admin"] is True
    assert result["landing_path"] == "/admin"


@pytest.mark.asyncio
async def test_register_through_user_service_never_grants_admin(
    service: AuthBoundaryService,
) -> None:
    body = _wire(
        RegisterResponse(
            message="ok",
            user=UserResponse(id=2, name="New", email="new@example.org"),
        )
    )
    with patch(_CLIENT) as client:
        client.register_user = AsyncMock(return_value=body)

        result = await service.register_user("New", "new@example.org", "pw")

    assert result["user"]["is_admin"] is False


@pytest.mark.parametrize(
    ("user_data", "expected"),
    [
        ({"is_admin": True}, True),
        ({"roles": [ADMIN_ROLE]}, True),
        ({"is_admin": False, "roles": [ADMIN_ROLE]}, True),
        ({"roles": ["USER", STANDARD_ROLE]}, False),
        ({}, False),
        ({"roles": None}, False),
        # A string is not a list of roles: "ADMIN" in "NOT_ADMIN" would be a substring match.
        ({"roles": "NOT_ADMIN"}, False),
        ({"roles": ["admin"]}, False),
        ({"is_admin": "true"}, False),
    ],
    ids=[
        "explicit-flag",
        "admin-role",
        "role-wins-over-false-flag",
        "student-roles",
        "nothing",
        "roles-null",
        "roles-is-a-string",
        "role-name-is-exact",
        "flag-must-be-a-bool",
    ],
)
def test_admin_is_read_from_the_flag_or_the_role(
    user_data: dict[str, object], expected: bool
) -> None:
    assert _is_admin_from_service(user_data) is expected


def test_the_service_still_reports_admin_through_roles() -> None:
    """Drift guard: the fix reads ``roles`` and the role name both sides agree on."""
    assert "roles" in UserOut.model_fields
    assert SERVICE_ADMIN_ROLE == ADMIN_ROLE
