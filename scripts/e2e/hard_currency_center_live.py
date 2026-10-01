#!/usr/bin/env python3
"""رحلة «مركز العملة الصعبة» الحيّة (D-305) — خادمٌ يعمل فعلاً، لا محاكاة.

ما تُثبته على خادمٍ مُقلَعٍ مع قاعدته الحقيقية:

  • الدخول: المدير بكلمة سرّه · كلمةٌ خاطئة ⇒ 401 · ثمّ الصحيحة فوراً ⇒ 200 (لا قفل يحبس المالك)
  • الحدود: بلا رمز ⇒ 401 · رمز طالبٍ على كلّ نقطةٍ ⇒ 403
  • الأرقام: تدقيق الفوترة FR/BE مطابقٌ للمحرّك حرفياً · قرار CBAM مطابقٌ لـ``first_sellable_year``
  • الرفض: ملفٌّ غير CSV ⇒ 415 · ملفٌّ أكبر من الحدّ ⇒ 413
  • الحجب: أصناف الاختراق بلا نصوص المسابير (L5)
  • ⛔ لا صفّ في جداول الرسائل من أيّ نداءٍ للمركز (§6.5)
  • محادثة المدير على ``/admin/api/chat/ws`` بلا 4401، ومحادثة الطالب بإطارٍ نهائيٍّ واحد

⛔ لا كلمة سرّ في الكود ولا قيمةٌ افتراضية لها — البيئة وحدها:
``E2E_ADMIN_EMAIL`` · ``E2E_ADMIN_PASSWORD`` · ``E2E_STUDENT_EMAIL`` · ``E2E_STUDENT_PASSWORD``
· ``E2E_BACKEND`` · ``APP_DATABASE_URL`` (للعدّ قبل/بعد في جداول الرسائل)
· ``ORCHESTRATOR_SERVICE_URL`` (لقراءة جاهزية رسم LangGraph من الخدمة نفسها).

    python scripts/e2e/hard_currency_center_live.py --json-output /tmp/hc-live.json
"""

from __future__ import annotations

import argparse
import asyncio
import base64
import json
import os
import sys
import tempfile
import time
from dataclasses import asdict, dataclass
from pathlib import Path

import asyncpg
import httpx

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from scripts.e2e.live_student_journey import _run_turn
from shared.research import cbam_pin
from tools.hard_currency_engine.belgium_validator import audit_belgian_csv
from tools.hard_currency_engine.france_validator import audit_french_csv

BASE_PATH = "/admin/api/hard-currency"
DEMO = REPO_ROOT / "docs" / "commercial" / "outreach" / "demo"
DEMOS = {
    "fr": ("DEMO_20_FICHES.csv", audit_french_csv),
    "be": ("DEMO_BELGIUM_PEPPOL_20_FICHES.csv", audit_belgian_csv),
}
GET_ENDPOINTS = ("/frontier", "/cbam/codes", "/cbam/codes/2523100090", "/redteam/classes")
CBAM_CODE = "2523100090"
MESSAGE_TABLES = ("customer_messages", "admin_messages")


@dataclass
class Check:
    name: str
    ok: bool
    detail: str
    seconds: float


def _env(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise SystemExit(f"❌ {name} غير مضبوط — بيانات الدخول من البيئة وحدها.")
    return value


def _jwt_roles(token: str) -> list[str]:
    payload = token.split(".")[1]
    payload += "=" * (-len(payload) % 4)
    claims = json.loads(base64.urlsafe_b64decode(payload))
    return [str(role) for role in claims.get("roles") or []]


class Journey:
    def __init__(self, base: str) -> None:
        self.base = base
        self.checks: list[Check] = []
        self.client = httpx.AsyncClient(base_url=base, timeout=60.0)

    def record(self, name: str, ok: bool, detail: str, started: float) -> None:
        self.checks.append(Check(name, ok, detail, round(time.perf_counter() - started, 3)))
        mark = "✅" if ok else "❌"
        print(f"{mark} {name} — {detail}", flush=True)

    async def login(self, email: str, password: str) -> httpx.Response:
        return await self.client.post(
            "/api/security/login", json={"email": email, "password": password}
        )


async def _message_rows(dsn: str) -> dict[str, int]:
    conn = await asyncpg.connect(dsn.replace("postgresql+asyncpg://", "postgresql://"))
    try:
        return {t: int(await conn.fetchval(f"select count(*) from {t}")) for t in MESSAGE_TABLES}
    finally:
        await conn.close()


async def _check_logins(
    j: Journey, admin: tuple[str, str], student: tuple[str, str]
) -> tuple[str, str]:
    started = time.perf_counter()
    first = await j.login(*admin)
    roles = _jwt_roles(first.json()["access_token"]) if first.status_code == 200 else []
    j.record(
        "دخول المدير بكلمة سرّه",
        first.status_code == 200 and "ADMIN" in roles,
        f"HTTP {first.status_code} · roles={roles}",
        started,
    )

    started = time.perf_counter()
    wrong = await j.login(admin[0], admin[1] + "-wrong")
    j.record("كلمة سرٍّ خاطئة تُرفَض", wrong.status_code == 401, f"HTTP {wrong.status_code}", started)

    started = time.perf_counter()
    again = await j.login(*admin)
    j.record(
        "الصحيحة تُقبَل مباشرةً بعد الخاطئة (لا قفل)",
        again.status_code == 200,
        f"HTTP {again.status_code}",
        started,
    )

    started = time.perf_counter()
    stud = await j.login(*student)
    j.record("دخول الطالب", stud.status_code == 200, f"HTTP {stud.status_code}", started)
    return again.json()["access_token"], stud.json()["access_token"]


async def _check_boundaries(j: Journey, student_token: str) -> None:
    started = time.perf_counter()
    anon = await j.client.get(f"{BASE_PATH}/frontier")
    j.record("بلا رمز ⇒ 401", anon.status_code == 401, f"HTTP {anon.status_code}", started)

    headers = {"Authorization": f"Bearer {student_token}"}
    started = time.perf_counter()
    codes = [
        (await j.client.get(f"{BASE_PATH}{p}", headers=headers)).status_code for p in GET_ENDPOINTS
    ]
    content = (DEMO / DEMOS["fr"][0]).read_bytes()
    codes.append(
        (
            await j.client.post(
                f"{BASE_PATH}/einvoicing-audits",
                headers=headers,
                files={"file": ("x.csv", content, "text/csv")},
                data={"corridor": "fr"},
            )
        ).status_code
    )
    codes.append(
        (
            await j.client.post(
                f"{BASE_PATH}/cbam/codes/{CBAM_CODE}/decision",
                headers=headers,
                json={"see_actual": 0.6},
            )
        ).status_code
    )
    j.record(
        "رمز الطالب على كلّ نقاط المركز ⇒ 403",
        set(codes) == {403},
        f"{codes}",
        started,
    )


async def _check_frontier(j: Journey, headers: dict[str, str]) -> None:
    started = time.perf_counter()
    response = await j.client.get(f"{BASE_PATH}/frontier", headers=headers)
    data = response.json()
    committed = json.loads((REPO_ROOT / "docs/commercial/VALUE_CHAIN.json").read_text("utf-8"))
    expected = {p["id"]: p["classification"] for p in committed["derived"]["paths"]}
    live = {p["id"]: p["classification"] for p in data.get("paths", [])}
    j.record(
        "خريطة الجبهة = الاشتقاق المُلتزَم",
        response.status_code == 200
        and live == expected
        and data.get("committed_snapshot_current") is True,
        f"HTTP {response.status_code} · {len(live)} مساراً · commercial_evidence="
        f"{data.get('by_classification', {}).get('commercial_evidence')}",
        started,
    )


async def _check_audits(j: Journey, headers: dict[str, str]) -> None:
    for corridor, (name, engine) in DEMOS.items():
        started = time.perf_counter()
        content = (DEMO / name).read_bytes()
        response = await j.client.post(
            f"{BASE_PATH}/einvoicing-audits",
            headers=headers,
            files={"file": (name, content, "text/csv")},
            data={"corridor": corridor},
        )
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / name
            path.write_bytes(content)
            direct = engine(path)
        summary = response.json().get("summary", {}) if response.status_code == 200 else {}
        keys = [k for k in summary if k in direct]
        same = bool(keys) and all(summary[k] == direct[k] for k in keys)
        j.record(
            f"تدقيق {corridor.upper()} مطابقٌ للمحرّك",
            response.status_code == 200 and same and response.json().get("stored") is False,
            f"HTTP {response.status_code} · {', '.join(f'{k}={summary.get(k)}' for k in keys)}",
            started,
        )

    started = time.perf_counter()
    not_csv = await j.client.post(
        f"{BASE_PATH}/einvoicing-audits",
        headers=headers,
        files={"file": ("notes.txt", b"hello", "text/plain")},
        data={"corridor": "fr"},
    )
    big = await j.client.post(
        f"{BASE_PATH}/einvoicing-audits",
        headers=headers,
        files={"file": ("big.csv", b"a;b\n" * (700 * 1024), "text/csv")},
        data={"corridor": "fr"},
    )
    j.record(
        "غير CSV ⇒ 415 · أكبر من الحدّ ⇒ 413",
        (not_csv.status_code, big.status_code) == (415, 413),
        f"HTTP {not_csv.status_code} · HTTP {big.status_code}",
        started,
    )


async def _check_cbam(j: Journey, headers: dict[str, str]) -> None:
    started = time.perf_counter()
    codes = (await j.client.get(f"{BASE_PATH}/cbam/codes", headers=headers)).json()
    j.record(
        "رموز CBAM المدبوسة",
        len(codes.get("codes", [])) == len(cbam_pin.pinned_codes()),
        f"{len(codes.get('codes', []))} رمزاً · بصمة {str(codes['provenance']['inputs_fingerprint'])[:12]}",
        started,
    )
    for see in (0.6, 5.0):
        started = time.perf_counter()
        live = (
            await j.client.post(
                f"{BASE_PATH}/cbam/codes/{CBAM_CODE}/decision",
                headers=headers,
                json={"see_actual": see},
            )
        ).json()
        direct = cbam_pin.first_sellable_year(CBAM_CODE, see)
        j.record(
            f"قرار CBAM {CBAM_CODE} عند {see} tCO₂e/t = المحرّك",
            live.get("first_sellable_year") == direct["first_sellable_year"]
            and live.get("never_within_horizon") == direct["never_within_horizon"],
            f"السنة {live.get('first_sellable_year')} · لا ضمن الأفق={live.get('never_within_horizon')}",
            started,
        )


async def _check_redteam(j: Journey, headers: dict[str, str]) -> None:
    started = time.perf_counter()
    data = (await j.client.get(f"{BASE_PATH}/redteam/classes", headers=headers)).json()
    leaked = [
        c.get("class_id") for c in data.get("classes", []) if "probe" in c or "reproduction" in c
    ]
    j.record(
        "أصناف الاختراق بلا نصوص المسابير",
        bool(data.get("classes")) and not leaked,
        f"{len(data.get('classes', []))} أصناف · {data.get('publishable_count')} قابلة للنشر",
        started,
    )


async def _check_graph(j: Journey, orchestrator: str) -> None:
    """هل LangGraph يعمل؟ — يُقرأ من الخدمة نفسها لا من سجلّها (سؤال المالك 2026-10-01)."""
    started = time.perf_counter()
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            health = (await client.get(f"{orchestrator}/health")).json()
    except Exception as exc:
        j.record("رسم LangGraph جاهز", False, f"{type(exc).__name__}: {str(exc)[:160]}", started)
        return
    ok = (
        health.get("graph_ready") is True
        and health.get("checkpointer_backend") == "postgres"
        and health.get("database") == "ok"
    )
    j.record(
        "رسم LangGraph جاهز",
        ok,
        f"graph_ready={health.get('graph_ready')} · checkpointer={health.get('checkpointer_backend')}"
        f" · database={health.get('database')} · startup={health.get('startup_state')}",
        started,
    )


async def _check_chat(j: Journey, admin_token: str, student_token: str) -> None:
    ws = j.base.replace("http://", "ws://").replace("https://", "wss://")
    for label, path, token, question in (
        ("محادثة المدير", "/admin/api/chat/ws", admin_token, "السلام عليكم"),
        ("محادثة الطالب", "/api/chat/ws", student_token, "اشرح لي قانون أوم"),
    ):
        started = time.perf_counter()
        try:
            turn = await _run_turn(f"{ws}{path}", token, question)
        except Exception as exc:  # 4401 يظهر هنا رفضاً للمصافحة
            j.record(label, False, f"{type(exc).__name__}: {str(exc)[:160]}", started)
            continue
        ok = turn.terminal_frames == 1 and bool(turn.content.strip()) and not turn.spoken_error
        j.record(
            label,
            ok,
            f"«{question}» ⇒ {turn.terminal_frames} إطار نهائي · {len(turn.content)} حرفاً · "
            f"أوّل محتوى {turn.first_content_s and round(turn.first_content_s, 1)}ث"
            + (f" · خطأ: {turn.spoken_error[:120]}" if turn.spoken_error else ""),
            started,
        )


async def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json-output", default="")
    args = parser.parse_args()

    base = os.environ.get("E2E_BACKEND", "http://127.0.0.1:8000")
    admin = (_env("E2E_ADMIN_EMAIL"), _env("E2E_ADMIN_PASSWORD"))
    student = (_env("E2E_STUDENT_EMAIL"), _env("E2E_STUDENT_PASSWORD"))
    dsn = _env("APP_DATABASE_URL")

    j = Journey(base)
    try:
        admin_token, student_token = await _check_logins(j, admin, student)
        headers = {"Authorization": f"Bearer {admin_token}"}
        before = await _message_rows(dsn)
        await _check_boundaries(j, student_token)
        await _check_frontier(j, headers)
        await _check_audits(j, headers)
        await _check_cbam(j, headers)
        await _check_redteam(j, headers)
        after = await _message_rows(dsn)
        started = time.perf_counter()
        j.record(
            "لا صفّ في جداول الرسائل من المركز", before == after, f"{before} ⇒ {after}", started
        )
        await _check_graph(j, os.environ.get("ORCHESTRATOR_SERVICE_URL", "http://127.0.0.1:8006"))
        await _check_chat(j, admin_token, student_token)
    finally:
        await j.client.aclose()

    failed = [c for c in j.checks if not c.ok]
    print(f"\n{'❌' if failed else '✅'} {len(j.checks) - len(failed)}/{len(j.checks)} فحصاً ناجحاً")
    if args.json_output:
        Path(args.json_output).write_text(
            json.dumps([asdict(c) for c in j.checks], ensure_ascii=False, indent=2), "utf-8"
        )
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
