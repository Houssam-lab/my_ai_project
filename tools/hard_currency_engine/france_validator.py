#!/usr/bin/env python3
"""
Module France Validator — Hard Currency Engine
Audit et assainissement des référentiels clients/fournisseurs pour la réforme de la facturation électronique française (RFE).
"""

from __future__ import annotations

import csv
import re
import unicodedata
from pathlib import Path


def strip_accents(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")


def norm(s: str) -> str:
    s = strip_accents((s or "").upper())
    return re.sub(r"[^A-Z0-9]", "", s)


def luhn_ok(digits: str) -> bool:
    """Vérification de l'algorithme de Luhn officiel."""
    if not digits.isdigit():
        return False
    total, length = 0, len(digits)
    for i, ch in enumerate(digits):
        d = int(ch)
        if (length - i) % 2 == 0:
            d *= 2
            if d > 9:
                d -= 9
        total += d
    return total % 10 == 0


def siren_check(siren: str) -> tuple[bool, str, str]:
    """Validation d'un SIREN (9 chiffres, Luhn)."""
    s = re.sub(r"\D", "", siren or "")
    if len(s) != 9:
        return False, s, f"Longueur {len(s)} ≠ 9"
    if not luhn_ok(s):
        return False, s, "Échec contrôle Luhn"
    return True, s, "OK"


def siret_check(siret: str) -> tuple[bool, str, str]:
    """Validation d'un SIRET (14 chiffres, Luhn, avec règle officielle La Poste)."""
    s = re.sub(r"\D", "", siret or "")
    if len(s) != 14:
        return False, s, f"Longueur {len(s)} ≠ 14"
    if s.startswith("356000000"):
        sum_digits = sum(int(ch) for ch in s)
        if sum_digits % 10 == 0:
            return True, s, "OK (La Poste)"
        return False, s, "Échec contrôle somme La Poste"
    if not luhn_ok(s):
        return False, s, "Échec contrôle Luhn"
    return True, s, "OK"


def tva_fr_check(tva: str) -> tuple[bool, str, str]:
    """Validation du numéro de TVA intracommunautaire français ou intra-UE."""
    t = re.sub(r"[\s.]", "", (tva or "").upper())
    if not t:
        return False, t, "TVA vide"
    if not t.startswith("FR"):
        eu_match = re.fullmatch(r"([A-Z]{2})([A-Z0-9]{2,12})", t)
        if eu_match and eu_match.group(1) in (
            "AT",
            "BE",
            "BG",
            "CY",
            "CZ",
            "DE",
            "DK",
            "EE",
            "ES",
            "FI",
            "GR",
            "HR",
            "HU",
            "IE",
            "IT",
            "LT",
            "LU",
            "LV",
            "MT",
            "NL",
            "PL",
            "PT",
            "RO",
            "SE",
            "SI",
            "SK",
        ):
            return True, t, f"OK (Intra-UE {eu_match.group(1)})"
        return False, t, "Format invalide (attendu FR + 2 chiffres + 9 chiffres SIREN)"
    m = re.fullmatch(r"FR(\d{2})(\d{9})", t)
    if not m:
        return False, t, "Format invalide (attendu FR + 2 chiffres + 9 chiffres SIREN)"
    key, siren = m.group(1), m.group(2)
    expected_key = str((12 + 3 * (int(siren) % 97)) % 97).zfill(2)
    if key != expected_key:
        return False, t, f"Clé erronée ({key} ≠ attendu {expected_key})"
    return True, t, "OK"


def validate_french_postal_code(cp: str) -> tuple[bool, str, str]:
    """Valide et assainit un code postal français (5 chiffres, départements métropole et DOM-TOM)."""
    raw = re.sub(r"\D", "", cp or "")
    if len(raw) == 4:
        raw = "0" + raw
    if len(raw) != 5:
        return False, raw, f"Longueur {len(raw)} ≠ 5 chiffres"
    dept = raw[:2]
    dom_tom = ("971", "972", "973", "974", "975", "976", "977", "978", "984", "986", "987", "988")
    valid_depts = {"20", *(f"{i:02d}" for i in range(1, 96))}
    if dept in valid_depts or raw[:3] in dom_tom:
        return True, raw, "OK"
    return False, raw, f"Département {dept} inconnu"


def compute_french_vat_key(siren: str) -> str:
    """Calcule le numéro complet de TVA intracommunautaire français à partir du SIREN."""
    s = re.sub(r"\D", "", siren or "")
    if len(s) != 9 or not s.isdigit():
        return ""
    key = str((12 + 3 * (int(s) % 97)) % 97).zfill(2)
    return f"FR{key}{s}"


def _read_csv_lines_multi_encoding(csv_path: Path) -> list[str]:
    encodings = ["utf-8-sig", "utf-8", "cp1252", "iso-8859-1", "latin1"]
    raw_bytes = csv_path.read_bytes()
    for enc in encodings:
        try:
            text = raw_bytes.decode(enc)
            return [
                line for line in text.splitlines(keepends=True) if not line.strip().startswith("#")
            ]
        except UnicodeDecodeError:
            continue
    text = raw_bytes.decode("utf-8", errors="replace")
    return [line for line in text.splitlines(keepends=True) if not line.strip().startswith("#")]


def export_cleaned_french_csv(results: dict, out_path: Path) -> Path:
    annotees = results.get("annotees", [])
    if not annotees:
        out_path.write_text("", encoding="utf-8")
        return out_path
    fields = list(annotees[0].keys())
    with open(out_path, mode="w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fields, delimiter=";")
        writer.writeheader()
        writer.writerows(annotees)
    return out_path


def _validate_french_row(  # noqa: PLR0912, PLR0915 — one pass mirrors the regulatory checklist
    row: dict, cols: dict, line_no: int, seen_dedup: dict
) -> tuple[list[str], bool, bool, bool]:
    line_errors = []
    nom_val = row.get(cols["nom"], "") if cols["nom"] else ""
    siren_val = row.get(cols["siren"], "") if cols["siren"] else ""
    siret_val = row.get(cols["siret"], "") if cols["siret"] else ""
    tva_val = row.get(cols["tva"], "") if cols["tva"] else ""
    cp_val = row.get(cols["cp"], "") if cols["cp"] else ""

    has_siren_err = False
    has_siret_err = False
    has_tva_err = False

    if siren_val:
        ok_s, _, msg_s = siren_check(siren_val)
        if not ok_s:
            has_siren_err = True
            line_errors.append(f"SIREN_INVALID({msg_s})")
    elif siret_val:
        siren_from_siret = re.sub(r"\D", "", siret_val)[:9]
        ok_s, _, msg_s = siren_check(siren_from_siret)
        if not ok_s:
            has_siren_err = True
            line_errors.append(f"SIREN_DERIVE_INVALID({msg_s})")
    elif tva_val and tva_val.upper().startswith("FR"):
        tva_digits = re.sub(r"\D", "", tva_val)
        if len(tva_digits) == 11:
            siren_from_tva = tva_digits[2:]
            ok_s, _, msg_s = siren_check(siren_from_tva)
            if not ok_s:
                has_siren_err = True
                line_errors.append(f"SIREN_DERIVE_TVA_INVALID({msg_s})")
        else:
            has_siren_err = True
            line_errors.append("SIREN_MANQUANT")
    else:
        has_siren_err = True
        line_errors.append("SIREN_MANQUANT")

    if siret_val:
        ok_st, _, msg_st = siret_check(siret_val)
        if not ok_st:
            has_siret_err = True
            line_errors.append(f"SIRET_INVALID({msg_st})")

    if tva_val:
        ok_tva, _, msg_tva = tva_fr_check(tva_val)
        if not ok_tva:
            has_tva_err = True
            line_errors.append(f"TVA_INVALID({msg_tva})")

    if cp_val:
        ok_cp, _, msg_cp = validate_french_postal_code(cp_val)
        if not ok_cp:
            line_errors.append(f"CP_INVALID({msg_cp})")

    dedup_key = f"{norm(nom_val)}_{norm(cp_val)}"
    if len(dedup_key) > 5:
        if dedup_key in seen_dedup:
            line_errors.append(f"DOUBLON_AVEC_LIGNE_{seen_dedup[dedup_key]}")
        else:
            seen_dedup[dedup_key] = line_no

    return line_errors, has_siren_err, has_siret_err, has_tva_err


def audit_french_csv(csv_path: Path) -> dict:
    """Audit complet d'un fichier CSV de tiers pour le marché français."""
    if not csv_path.exists():
        raise FileNotFoundError(f"Fichier introuvable : {csv_path}")

    results = {
        "total": 0,
        "valides": 0,
        "erreurs_siren": 0,
        "erreurs_siret": 0,
        "erreurs_tva": 0,
        "doublons": 0,
        "anomalies": [],
        "annotees": [],
    }

    seen_dedup: dict[str, int] = {}
    valid_lines = _read_csv_lines_multi_encoding(csv_path)
    if not valid_lines:
        return results

    delimiter = ";" if ";" in valid_lines[0] else ","
    reader = csv.DictReader(valid_lines, delimiter=delimiter)
    fields = reader.fieldnames or []

    cols = {
        "nom": next(
            (c for c in fields if re.search(r"nom|raison|client|fournisseur", c, re.I)), None
        ),
        "siren": next((c for c in fields if re.search(r"siren", c, re.I)), None),
        "siret": next((c for c in fields if re.search(r"siret", c, re.I)), None),
        "tva": next((c for c in fields if re.search(r"tva|vat", c, re.I)), None),
        "cp": next((c for c in fields if re.search(r"cp|postal|zip", c, re.I)), None),
    }

    for line_no, row in enumerate(reader, start=2):
        results["total"] += 1
        line_errors, err_siren, err_siret, err_tva = _validate_french_row(
            row, cols, line_no, seen_dedup
        )
        if err_siren:
            results["erreurs_siren"] += 1
        if err_siret:
            results["erreurs_siret"] += 1
        if err_tva:
            results["erreurs_tva"] += 1
        if any("DOUBLON" in err for err in line_errors):
            results["doublons"] += 1

        nom_val = row.get(cols["nom"], "") if cols["nom"] else ""
        siren_val = row.get(cols["siren"], "") if cols["siren"] else ""
        siret_val = row.get(cols["siret"], "") if cols["siret"] else ""

        if line_errors:
            results["anomalies"].append(
                {
                    "ligne": line_no,
                    "nom": nom_val,
                    "siren": siren_val or siret_val[:9] if siret_val else "",
                    "erreurs": line_errors,
                }
            )
        else:
            results["valides"] += 1

        row_ann = dict(row)
        clean_s = (
            re.sub(r"\D", "", siren_val)
            or (re.sub(r"\D", "", siret_val)[:9] if siret_val else "")
            or (
                re.sub(r"\D", "", row.get(cols["tva"], ""))[2:]
                if cols["tva"]
                and (row.get(cols["tva"], "") or "").upper().startswith("FR")
                and len(re.sub(r"\D", "", row.get(cols["tva"], ""))) == 11
                else ""
            )
        )
        row_ann["ANOMALIES_RFE"] = "; ".join(line_errors) if line_errors else "CONFORME"
        row_ann["STATUT_RFE"] = "CONFORME" if not line_errors else "A_CORRIGER"
        row_ann["SIREN_ASSAINI"] = clean_s if clean_s and luhn_ok(clean_s) else ""
        row_ann["TVA_FR_CALCULEE"] = (
            compute_french_vat_key(clean_s) if clean_s and luhn_ok(clean_s) else ""
        )
        if cols["cp"] and row.get(cols["cp"]):
            _, healed_cp, _ = validate_french_postal_code(row.get(cols["cp"], ""))
            row_ann["CP_ASSAINI"] = healed_cp
        results["annotees"].append(row_ann)

    return results


def format_french_report(results: dict, filename: str) -> str:
    total = results["total"]
    valides = results["valides"]
    pct = (valides / total * 100) if total > 0 else 0.0

    lines = [
        f"# Rapport d'Audit Référentiels RFE France — {filename}",
        "**Date :** 2026-09-24 · **Cadre Réglementaire :** Réforme Facturation Électronique (DGFiP / Factur-X)",
        "",
        "## 1. Synthèse de Conformité",
        "| Indicateur | Résultat | Statut |",
        "|---|---|---|",
        f"| Fiches traitées | **{total}** | Base totale |",
        f"| Fiches prêtes à l'émission | **{valides}** ({pct:.1f}%) | "
        f"{'🟢 Excellent' if pct > 90 else '🔴 Blocages majeurs détectés'} |",
        f"| Erreurs SIREN / SIRET | **{results['erreurs_siren'] + results['erreurs_siret']}** | Rejet immédiat sur l'annuaire |",
        f"| Erreurs TVA intracommunautaire | **{results['erreurs_tva']}** | Risque d'invalidation fiscale |",
        f"| Doublons détectés | **{results['doublons']}** | Risque de multi-routage |",
        "",
        "## 2. Risques Financiers pour l'Entreprise",
        "- **Pénalités de conformité :** 50 € par facture non conforme (plafonnée à 15 000 €/an par assujetti).",
        f"- **Impact immédiat :** {total - valides} fiches tiers nécessitent une remédiation avant injection dans votre PDP.",
        "",
        "## 3. Plan d'Action Recommandé",
        "1. Correction algorithmique des SIREN et dérivation automatique des TVA conformes.",
        "2. Rapprochement avec la base INSEE Sirene via API publique.",
        "3. Fusion des fiches doublons.",
    ]

    if results["anomalies"]:
        lines.append("")
        lines.append("## 4. Échantillon des Anomalies")
        lines.append("| Ligne | Nom | SIREN | Erreurs Détectées |")
        lines.append("|---|---|---|---|")
        for item in results["anomalies"][:15]:
            lines.append(
                f"| {item['ligne']} | {item['nom']} | {item['siren']} | {', '.join(item['erreurs'])} |"
            )

    return "\n".join(lines)
