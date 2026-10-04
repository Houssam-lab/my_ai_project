"""اختبارات ماسح الحواجز المعمارية لضمان الالتزام بالحدود."""

from pathlib import Path

from scripts import ci_guardrails


def _write_python(tmp_path: Path, relative: str, content: str) -> Path:
    """ينشئ ملف بايثون مؤقتًا داخل المسار المحدد ويعيد موقعه."""
    file_path = tmp_path / relative
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(content, encoding="utf-8")
    return file_path


def test_guardrails_flags_print_in_app_file(tmp_path: Path) -> None:
    file_path = _write_python(
        tmp_path,
        "app/services/example.py",
        "def run():\n    print('hello')\n",
    )

    errors = ci_guardrails.check_file(file_path)

    assert any("print()" in error or "print" in error for error in errors)


def test_guardrails_fail_closed_on_unparseable_python(tmp_path: Path) -> None:
    file_path = _write_python(
        tmp_path,
        "app/services/broken.py",
        "def broken(:\n    pass\n",
    )

    errors = ci_guardrails.check_file(file_path)

    assert any("Unable to parse Python source" in error for error in errors)
    assert any("fail closed" in error for error in errors)


def test_guardrails_allows_print_in_scripts(tmp_path: Path) -> None:
    file_path = _write_python(
        tmp_path,
        "scripts/tool.py",
        "def run():\n    print('allowed')\n",
    )

    errors = ci_guardrails.check_file(file_path)

    assert errors == []


def test_guardrails_flags_any_usage(tmp_path: Path) -> None:
    any_token = "A" + "ny"
    file_path = _write_python(
        tmp_path,
        "microservices/service_a/typing_violation.py",
        f"from typing import {any_token}\nvalue: {any_token} = 1\n",
    )

    errors = ci_guardrails.check_file(file_path)

    assert any("forbidden" in error for error in errors)


def test_guardrails_flags_cross_service_import(tmp_path: Path) -> None:
    file_path = _write_python(
        tmp_path,
        "microservices/service_a/handler.py",
        "from microservices.service_b import api\n",
    )

    errors = ci_guardrails.check_file(file_path)

    assert any("Cross-service import forbidden" in error for error in errors)


def test_guardrails_flags_microservice_monolith_leak(tmp_path: Path) -> None:
    file_path = _write_python(
        tmp_path,
        "microservices/service_a/handler.py",
        "from app.services import accounts\n",
    )

    errors = ci_guardrails.check_file(file_path)

    assert any("Monolith Leak" in error or "app.services" in error for error in errors)


def test_guardrails_blocks_monolith_importing_microservices(tmp_path: Path) -> None:
    file_path = _write_python(
        tmp_path,
        "app/services/legacy.py",
        "from microservices.user_service import api\n",
    )

    errors = ci_guardrails.check_file(file_path)

    assert any("Monolith cannot import" in error for error in errors)


def test_guardrails_allows_microservice_app_core_import(tmp_path: Path) -> None:
    file_path = _write_python(
        tmp_path,
        "microservices/service_a/handler.py",
        "from app.core import logging\n",
    )

    errors = ci_guardrails.check_file(file_path)

    assert errors == []


def test_guardrails_flags_admin_db_imports(tmp_path: Path) -> None:
    file_path = _write_python(
        tmp_path,
        "app/api/routers/admin_reports.py",
        "import sqlalchemy\n",
    )

    errors = ci_guardrails.check_file(file_path)

    assert any("UI/API Layer cannot import DB module" in error for error in errors)


def test_guardrails_flags_direct_engine_creation(tmp_path: Path) -> None:
    file_path = _write_python(
        tmp_path,
        "app/infrastructure/db.py",
        "from sqlalchemy.ext.asyncio import create_async_engine\n"
        "engine = create_async_engine('sqlite+aiosqlite://')\n",
    )

    errors = ci_guardrails.check_file(file_path)

    assert any("create_async_engine" in error for error in errors)


def test_guardrails_flags_schema_autocreate(tmp_path: Path) -> None:
    file_path = _write_python(
        tmp_path,
        "app/infrastructure/schema.py",
        "from sqlmodel import SQLModel\nSQLModel.metadata.create_all()\n",
    )

    errors = ci_guardrails.check_file(file_path)

    assert any("create_all" in error for error in errors)


def test_guardrails_flags_schema_autocreate_reference(tmp_path: Path) -> None:
    file_path = _write_python(
        tmp_path,
        "app/infrastructure/schema.py",
        "from sqlmodel import SQLModel\n"
        "async def init(conn):\n"
        "    await conn.run_sync(SQLModel.metadata.create_all)\n",
    )

    errors = ci_guardrails.check_file(file_path)

    assert any("create_all" in error for error in errors)


def test_guardrails_allows_schema_autocreate_in_migrations(tmp_path: Path) -> None:
    file_path = _write_python(
        tmp_path,
        "migrations/versions/1234_init.py",
        "from sqlmodel import SQLModel\nSQLModel.metadata.create_all()\n",
    )

    errors = ci_guardrails.check_file(file_path)

    assert errors == []


def test_guardrails_flags_direct_engine_creation_sync(tmp_path: Path) -> None:
    file_path = _write_python(
        tmp_path,
        "app/infrastructure/sync_db.py",
        "from sqlalchemy import create_engine\nengine = create_engine('sqlite://')\n",
    )

    errors = ci_guardrails.check_file(file_path)

    assert any("create_engine" in error for error in errors)


def test_guardrails_allows_create_engine_in_scripts(tmp_path: Path) -> None:
    file_path = _write_python(
        tmp_path,
        "scripts/db_maintenance.py",
        "from sqlalchemy import create_engine\nengine = create_engine('sqlite://')\n",
    )

    errors = ci_guardrails.check_file(file_path)

    assert errors == []


def test_guardrails_allows_create_engine_in_tests(tmp_path: Path) -> None:
    file_path = _write_python(
        tmp_path,
        "tests/helpers/test_db.py",
        "from sqlalchemy import create_engine\nengine = create_engine('sqlite://')\n",
    )

    errors = ci_guardrails.check_file(file_path)

    assert errors == []


def test_guardrails_allows_create_async_engine_in_scripts(tmp_path: Path) -> None:
    file_path = _write_python(
        tmp_path,
        "scripts/async_db_maintenance.py",
        "from sqlalchemy.ext.asyncio import create_async_engine\n"
        "engine = create_async_engine('sqlite+aiosqlite://')\n",
    )

    errors = ci_guardrails.check_file(file_path)

    assert errors == []


def test_guardrails_flags_sessionmaker_usage(tmp_path: Path) -> None:
    file_path = _write_python(
        tmp_path,
        "app/infrastructure/session_factory.py",
        "from sqlalchemy.orm import sessionmaker\nSessionLocal = sessionmaker()\n",
    )

    errors = ci_guardrails.check_file(file_path)

    assert any("sessionmaker" in error for error in errors)


def test_guardrails_allows_sessionmaker_in_scripts(tmp_path: Path) -> None:
    file_path = _write_python(
        tmp_path,
        "scripts/seed_db.py",
        "from sqlalchemy.orm import sessionmaker\nSessionLocal = sessionmaker()\n",
    )

    errors = ci_guardrails.check_file(file_path)

    assert errors == []


def test_guardrails_allows_sessionmaker_in_tests(tmp_path: Path) -> None:
    file_path = _write_python(
        tmp_path,
        "tests/helpers/session_factory.py",
        "from sqlalchemy.orm import sessionmaker\nSessionLocal = sessionmaker()\n",
    )

    errors = ci_guardrails.check_file(file_path)

    assert errors == []


def test_guardrails_allows_async_sessionmaker_in_scripts(tmp_path: Path) -> None:
    file_path = _write_python(
        tmp_path,
        "scripts/async_session_factory.py",
        "from sqlalchemy.ext.asyncio import async_sessionmaker\n"
        "SessionLocal = async_sessionmaker()\n",
    )

    errors = ci_guardrails.check_file(file_path)

    assert errors == []


def test_guardrails_allows_async_sessionmaker_in_tests(tmp_path: Path) -> None:
    file_path = _write_python(
        tmp_path,
        "tests/helpers/async_session_factory.py",
        "from sqlalchemy.ext.asyncio import async_sessionmaker\n"
        "SessionLocal = async_sessionmaker()\n",
    )

    errors = ci_guardrails.check_file(file_path)

    assert errors == []


def test_guardrails_allows_db_factory_in_core(tmp_path: Path) -> None:
    file_path = _write_python(
        tmp_path,
        "app/core/database.py",
        "from sqlalchemy import create_engine\n"
        "from sqlalchemy.orm import sessionmaker\n"
        "engine = create_engine('sqlite://')\n"
        "SessionLocal = sessionmaker()\n",
    )

    errors = ci_guardrails.check_file(file_path)

    assert errors == []


def test_guardrails_allows_create_engine_in_migrations_env(tmp_path: Path) -> None:
    file_path = _write_python(
        tmp_path,
        "migrations/env.py",
        "from sqlalchemy import create_engine\nengine = create_engine('sqlite://')\n",
    )

    errors = ci_guardrails.check_file(file_path)

    assert errors == []
