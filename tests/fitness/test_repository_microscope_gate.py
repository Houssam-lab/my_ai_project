from __future__ import annotations

from scripts.fitness import check_repository_microscope as gate


def _valid_payload() -> tuple[dict, dict]:
    computed = {
        "mode": gate.MODE,
        "file_count_excluding_packet": 2,
        "total_bytes_excluding_packet": 10,
        "total_newlines_excluding_packet": 1,
        "sha256_excluding_packet": "abc123",
        "packet_excluded_for_non_circular_hash": gate.PACKET_REL,
    }
    packet = {
        "repository_microscope": {
            **computed,
            "applies_to_existing_code": True,
            "applies_to_future_code": True,
            "old_before_new": True,
            "grandfathering_forbidden": True,
            "legacy_rule_ar": "القديم داخل النطاق.",
            "future_rule_ar": "المستقبل داخل النطاق.",
            "operator_attestation_ar": "إثبات غير دائري.",
        }
    }
    return packet, computed


def test_repository_microscope_accepts_matching_full_scope_payload() -> None:
    packet, computed = _valid_payload()

    assert gate.validate_payload(packet, computed) == []


def test_repository_microscope_rejects_stale_byte_census() -> None:
    packet, computed = _valid_payload()
    packet["repository_microscope"]["sha256_excluding_packet"] = "stale"

    failures = gate.validate_payload(packet, computed)

    assert len(failures) >= 1
    assert any("sha256_excluding_packet" in failure for failure in failures)


def test_repository_microscope_rejects_future_only_scope() -> None:
    packet, computed = _valid_payload()
    packet["repository_microscope"]["applies_to_existing_code"] = False
    packet["repository_microscope"]["old_before_new"] = False

    failures = gate.validate_payload(packet, computed)

    assert len(failures) >= 1
    assert any("applies_to_existing_code" in failure for failure in failures)
