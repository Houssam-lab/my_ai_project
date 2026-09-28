#!/usr/bin/env python3
"""Discover and *invoke* currently free OpenRouter text models.

Catalog presence is not proof of answerability.  This probe fetches today's
catalog, selects free text-generation models, then sends one tiny Arabic chat
completion to each candidate.  It emits no API key and can export the first
working models to GitHub Actions through ``--github-env``.
"""

from __future__ import annotations

import argparse
import json
import os
import time
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

BASE_URL = "https://openrouter.ai/api/v1"
EXCLUDED = (
    "audio",
    "embed",
    "guard",
    "moderation",
    "safety",
    "span-",
    "image",
    "recraft",
    "riverflow",
    "upscal",
    "search",
)


@dataclass
class ProbeResult:
    model: str
    ok: bool
    status: int | None
    seconds: float
    chars: int
    error: str | None = None


def _zero(value: object) -> bool:
    try:
        return float(str(value)) == 0.0
    except (TypeError, ValueError):
        return False


def free_text_models(payload: dict[str, Any]) -> list[str]:
    """Return suitable free chat model IDs, newest first."""
    ranked: list[tuple[int, int, str]] = []
    for item in payload.get("data", []):
        if not isinstance(item, dict):
            continue
        model = str(item.get("id", ""))
        lowered = f"{model} {item.get('name', '')}".lower()
        pricing = item.get("pricing") or {}
        architecture = item.get("architecture") or {}
        outputs = architecture.get("output_modalities") or []
        modality = str(architecture.get("modality", ""))
        is_text = "text" in outputs or modality.endswith("->text")
        is_free = (
            model.endswith(":free")
            and _zero(pricing.get("prompt"))
            and _zero(pricing.get("completion"))
        )
        if not is_free or not is_text or any(word in lowered for word in EXCLUDED):
            continue
        # Prefer general instruction/chat models over narrow or anonymous entries.
        quality = sum(
            token in lowered for token in ("instruct", "chat", "qwen", "gemma", "nemotron")
        )
        ranked.append((quality, int(item.get("created", 0) or 0), model))
    ranked.sort(reverse=True)
    return [model for _, _, model in ranked]


def request_json(
    url: str, *, key: str, body: dict[str, Any] | None, timeout: float
) -> tuple[int, dict[str, Any]]:
    data = json.dumps(body).encode() if body is not None else None
    headers = {"Accept": "application/json", "Authorization": f"Bearer {key}"}
    if data is not None:
        headers["Content-Type"] = "application/json"
    request = urllib.request.Request(
        url, data=data, headers=headers, method="POST" if data else "GET"
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return response.status, json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        try:
            payload = json.loads(exc.read().decode("utf-8", errors="replace"))
        except ValueError:
            payload = {"error": {"message": f"HTTP {exc.code}"}}
        return exc.code, payload


def _error_message(payload: dict[str, Any]) -> str:
    error = payload.get("error")
    if isinstance(error, dict):
        message = error.get("message") or error.get("code") or "provider error"
    else:
        message = error or "provider error"
    # Keep annotations useful but bounded; never include request headers/key.
    return " ".join(str(message).split())[:240]


def probe(base_url: str, key: str, model: str, timeout: float) -> ProbeResult:
    started = time.monotonic()
    try:
        status, payload = request_json(
            f"{base_url.rstrip('/')}/chat/completions",
            key=key,
            timeout=timeout,
            body={
                "model": model,
                "messages": [
                    {
                        "role": "user",
                        "content": "أجب بكلمتين فقط: ما عاصمة الجزائر؟",
                    }
                ],
                "temperature": 0,
                "max_tokens": 32,
            },
        )
        content = ""
        choices = payload.get("choices")
        if status < 400 and isinstance(choices, list) and choices:
            message = choices[0].get("message") if isinstance(choices[0], dict) else None
            if isinstance(message, dict) and isinstance(message.get("content"), str):
                content = message["content"].strip()
        ok = bool(content)
        return ProbeResult(
            model=model,
            ok=ok,
            status=status,
            seconds=round(time.monotonic() - started, 2),
            chars=len(content),
            error=None if ok else _error_message(payload),
        )
    except Exception as exc:
        return ProbeResult(
            model=model,
            ok=False,
            status=None,
            seconds=round(time.monotonic() - started, 2),
            chars=0,
            error=f"{type(exc).__name__}: {str(exc)[:180]}",
        )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=6)
    parser.add_argument("--timeout", type=float, default=35)
    parser.add_argument(
        "--reserve",
        type=int,
        default=14,
        help="free requests to preserve for the downstream answerability matrix",
    )
    parser.add_argument("--base-url", default=os.getenv("OPENROUTER_BASE_URL", BASE_URL))
    parser.add_argument("--github-env", type=Path)
    parser.add_argument("--json-output", type=Path)
    args = parser.parse_args()

    key = os.getenv("OPENROUTER_API_KEY", "").strip()
    if not key:
        print("❌ OPENROUTER_API_KEY is missing")
        return 2

    try:
        _, key_payload = request_json(
            f"{args.base_url.rstrip('/')}/key", key=key, body=None, timeout=args.timeout
        )
        key_data = key_payload.get("data", {}) if isinstance(key_payload, dict) else {}
        free_quota = key_data.get("free_model_daily_requests", {})
        remaining_raw = free_quota.get("remaining") if isinstance(free_quota, dict) else None
        remaining = int(remaining_raw) if remaining_raw is not None else None
        used = free_quota.get("used", "unknown") if isinstance(free_quota, dict) else "unknown"
        daily_limit = (
            free_quota.get("limit", "unknown") if isinstance(free_quota, dict) else "unknown"
        )
        print(f"free quota used={used} limit={daily_limit} remaining={remaining_raw}")
        if remaining is not None and remaining <= args.reserve:
            print(
                f"❌ free quota cannot fund E2E: remaining={remaining}, "
                f"reserved_for_matrix={args.reserve}; resets at 00:00 UTC"
            )
            return 3

        _, catalog = request_json(
            f"{args.base_url.rstrip('/')}/models", key=key, body=None, timeout=args.timeout
        )
    except Exception as exc:
        print(f"❌ catalog/quota unavailable: {type(exc).__name__}: {exc}")
        return 2

    probe_budget = args.limit if remaining is None else min(args.limit, remaining - args.reserve)
    candidates = free_text_models(catalog)[: max(1, probe_budget)]
    print(
        f"catalog free text candidates={len(free_text_models(catalog))}; probing={len(candidates)}"
    )
    if not candidates:
        print("❌ no free text-generation candidates in the live catalog")
        return 1

    results: list[ProbeResult] = []
    for model in candidates:
        result = probe(args.base_url, key, model, args.timeout)
        results.append(result)
        mark = "✅" if result.ok else "❌"
        detail = f"chars={result.chars}" if result.ok else f"error={result.error}"
        print(f"{mark} {model} http={result.status} {result.seconds:.2f}s {detail}")

    working = [result.model for result in results if result.ok]
    document = {
        "candidates": len(candidates),
        "working": working,
        "results": [asdict(result) for result in results],
    }
    if args.json_output:
        args.json_output.write_text(json.dumps(document, ensure_ascii=False, indent=2) + "\n")
    if working and args.github_env:
        with args.github_env.open("a") as env:
            env.write(f"OPENROUTER_PRIMARY_MODEL={working[0]}\n")
            env.write(f"OPENROUTER_EXTRA_MODELS={','.join(working[1:3])}\n")
    if not working:
        print("❌ catalog listed free models, but none returned textual content")
        return 1
    print(f"SELECTED primary={working[0]} fallbacks={','.join(working[1:3]) or '-'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
