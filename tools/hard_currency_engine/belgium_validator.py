#!/usr/bin/env python3
"""
Module Belgium Validator — Hard Currency Engine
Audit et mise en conformité des référentiels clients/fournisseurs pour Peppol Belgique (B2B).
"""

from __future__ import annotations

import csv
import re
import unicodedata
from datetime import date
from pathlib import Path


def strip_accents(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")


def norm(s: str) -> str:
    s = strip_accents((s or "").upper())
    return re.sub(r"[^A-Z0-9]", "", s)


#: En-têtes (normalisés : sans accents, minuscules, alphanumériques) désignant sans ambiguïté
#: la colonne du numéro d'entreprise, en français et en néerlandais.
_BCE_HEADERS = frozenset(
    {
        "bce",
        "kbo",
        "cbe",
        "nbce",
        "nkbo",
        "numerobce",
        "numerokbo",
        "kbonummer",
        "bcenummer",
        "numeroentreprise",
        "numerodentreprise",
        "nentreprise",
        "ondernemingsnummer",
        "ondernemingsnr",
        "enterprisenumber",
        "entreprise",
        "siren",
    }
)
_NAME_HEADER = re.compile(r"nom|raison|naam|name|client|fournisseur|leverancier|klant", re.I)


def _find_bce_column(fields: list[str]) -> str | None:
    """Colonne du numéro BCE/KBO — jamais une colonne de nom (`Nom_entreprise` contient
    « entreprise » et faisait valider la raison sociale comme numéro : 100 % de faux rejets)."""
    normalized = {field: re.sub(r"[^a-z0-9]", "", strip_accents(field).lower()) for field in fields}
    for field, key in normalized.items():
        if key in _BCE_HEADERS:
            return field
    for field in fields:
        if _NAME_HEADER.search(field):
            continue
        if re.search(r"bce|kbo|ondernemingsnummer|entreprise|siren", field, re.I):
            return field
    return None


def validate_bce_modulo97(raw_number: str) -> tuple[bool, str, str]:
    """Validation d'un numéro d'entreprise belge KBO/BCE par Modulo 97."""
    digits = re.sub(r"\D", "", raw_number or "")
    if len(digits) == 9:
        digits = "0" + digits

    if len(digits) != 10:
        return False, digits, f"Longueur {len(digits)} ≠ 10"

    if digits[0] not in ("0", "1"):
        return False, digits, f"Le numéro doit débuter par 0 ou 1 ({digits[0]})"

    base8 = int(digits[:8])
    checksum = int(digits[8:])
    rem = base8 % 97
    expected = 97 if rem == 0 else (97 - rem)

    if checksum != expected:
        return False, digits, f"Échec Modulo 97 (trouvé={checksum:02d}, attendu={expected:02d})"

    formatted = f"{digits[:4]}.{digits[4:7]}.{digits[7:]}"
    return True, formatted, "OK"


def format_peppol_id(bce_clean: str) -> str:
    digits = re.sub(r"\D", "", bce_clean)
    if len(digits) == 9:
        digits = "0" + digits
    return f"0208:{digits}"


def get_peppol_directory_url(bce_clean: str) -> str:
    """Génère l'URL officielle de vérification sur l'annuaire européen Peppol Directory."""
    digits = re.sub(r"\D", "", bce_clean)
    if len(digits) == 9:
        digits = "0" + digits
    return f"https://directory.peppol.eu/participant/iso6523-actorid-upis%3A%3A0208%3A{digits}"


def get_kbo_public_url(bce_clean: str) -> str:
    """Génère l'URL de consultation directe sur la Banque-Carrefour des Entreprises (BCE / KBO)."""
    digits = re.sub(r"\D", "", bce_clean)
    if len(digits) == 9:
        digits = "0" + digits
    return f"https://kbopub.economie.fgov.be/kbopub/zoeknummerform.html?numero={digits}"


def validate_belgian_postal_code(cp: str) -> tuple[bool, str, str]:
    """Validation du code postal belge (4 chiffres compris entre 1000 et 9992)."""
    digits = re.sub(r"\D", "", cp or "")
    if len(digits) != 4:
        return False, digits, f"Longueur {len(digits)} ≠ 4 chiffres"
    val = int(digits)
    if 1000 <= val <= 9992:
        return True, digits, "OK"
    return False, digits, f"Code postal {digits} hors plage belge (1000-9992)"


def validate_belgian_vat(vat_str: str) -> tuple[bool, str, str]:
    raw = (vat_str or "").strip().upper().replace(" ", "").replace(".", "")
    if not raw.startswith("BE"):
        return False, raw, "Préfixe BE manquant"
    bce_part = raw[2:]
    ok, num, err = validate_bce_modulo97(bce_part)
    if not ok:
        return False, raw, f"TVA invalide: {err}"
    return True, f"BE{num.replace('.', '')}", "OK"


def _validate_belgian_row(
    row: dict, cols: dict, line_no: int, seen_dedup: dict
) -> tuple[list[str], bool, bool]:
    line_errors = []
    nom_val = row.get(cols["nom"], "") if cols["nom"] else ""
    bce_val = row.get(cols["bce"], "") if cols["bce"] else ""
    tva_val = row.get(cols["tva"], "") if cols["tva"] else ""
    cp_val = row.get(cols["cp"], "") if cols["cp"] else ""

    err_bce = False
    err_tva = False

    if bce_val:
        ok_bce, _clean_bce, msg_bce = validate_bce_modulo97(bce_val)
        if not ok_bce:
            err_bce = True
            line_errors.append(f"BCE_INVALID({msg_bce})")
    elif tva_val and tva_val.upper().startswith("BE"):
        ok_bce, _clean_bce, msg_bce = validate_bce_modulo97(tva_val[2:])
        if not ok_bce:
            err_bce = True
            line_errors.append(f"BCE_DERIVE_TVA_INVALID({msg_bce})")
    else:
        err_bce = True
        line_errors.append("BCE_MANQUANT")

    if tva_val:
        ok_tva, _clean_tva, msg_tva = validate_belgian_vat(tva_val)
        if not ok_tva:
            err_tva = True
            line_errors.append(f"TVA_INVALID({msg_tva})")

    if cp_val:
        ok_cp, _, msg_cp = validate_belgian_postal_code(cp_val)
        if not ok_cp:
            line_errors.append(f"CP_INVALID({msg_cp})")

    dedup_key = f"{norm(nom_val)}_{norm(cp_val)}"
    if len(dedup_key) > 5:
        if dedup_key in seen_dedup:
            line_errors.append(f"DOUBLON_AVEC_LIGNE_{seen_dedup[dedup_key]}")
        else:
            seen_dedup[dedup_key] = line_no

    return line_errors, err_bce, err_tva


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


def export_cleaned_belgian_csv(results: dict, out_path: Path) -> Path:
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


def audit_belgian_csv(csv_path: Path) -> dict:
    if not csv_path.exists():
        raise FileNotFoundError(f"Fichier introuvable : {csv_path}")

    results = {
        "total": 0,
        "valides": 0,
        "erreurs_bce": 0,
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
        "nom": next((c for c in fields if _NAME_HEADER.search(c)), None),
        "bce": _find_bce_column(fields),
        "tva": next((c for c in fields if re.search(r"tva|vat|btw", c, re.I)), None),
        "cp": next((c for c in fields if re.search(r"cp|postal|zip|postcode", c, re.I)), None),
    }

    for line_no, row in enumerate(reader, start=2):
        results["total"] += 1
        line_errors, err_bce, err_tva = _validate_belgian_row(row, cols, line_no, seen_dedup)
        if err_bce:
            results["erreurs_bce"] += 1
        if err_tva:
            results["erreurs_tva"] += 1
        if any("DOUBLON" in err for err in line_errors):
            results["doublons"] += 1

        nom_val = row.get(cols["nom"], "") if cols["nom"] else ""
        bce_val = row.get(cols["bce"], "") if cols["bce"] else ""

        if line_errors:
            results["anomalies"].append(
                {
                    "ligne": line_no,
                    "nom": nom_val,
                    "bce": bce_val,
                    "erreurs": line_errors,
                }
            )
        else:
            results["valides"] += 1

        row_ann = dict(row)
        clean_bce_digits = re.sub(r"\D", "", bce_val) or (
            re.sub(r"\D", "", row.get(cols["tva"], ""))[2:]
            if cols["tva"] and (row.get(cols["tva"], "") or "").upper().startswith("BE")
            else ""
        )
        if len(clean_bce_digits) == 9:
            clean_bce_digits = "0" + clean_bce_digits

        ok_mod97, formatted_bce, _ = (
            validate_bce_modulo97(clean_bce_digits)
            if len(clean_bce_digits) == 10
            else (False, clean_bce_digits, "")
        )

        row_ann["ANOMALIES_PEPPOL"] = "; ".join(line_errors) if line_errors else "CONFORME"
        row_ann["PEPPOL_ID"] = format_peppol_id(clean_bce_digits) if ok_mod97 else "A_CORRIGER"
        row_ann["STATUT_PEPPOL"] = "COMPATIBLE" if not line_errors else "NON_CONFORME"
        row_ann["BCE_ASSAINI"] = formatted_bce if ok_mod97 else ""
        row_ann["TVA_BE_CALCULEE"] = f"BE{clean_bce_digits}" if ok_mod97 else ""
        row_ann["PEPPOL_DIRECTORY_URL"] = (
            get_peppol_directory_url(clean_bce_digits) if ok_mod97 else ""
        )
        row_ann["KBO_LOOKUP_URL"] = get_kbo_public_url(clean_bce_digits) if ok_mod97 else ""
        if cols["cp"] and row.get(cols["cp"]):
            _, healed_cp, _ = validate_belgian_postal_code(row.get(cols["cp"], ""))
            row_ann["CP_ASSAINI"] = healed_cp
        results["annotees"].append(row_ann)

    return results


def format_belgian_report(results: dict, filename: str, report_date: date | None = None) -> str:
    total = results["total"]
    valides = results["valides"]
    pct = (valides / total * 100) if total > 0 else 0.0
    when = (report_date or date.today()).isoformat()

    lines = [
        f"# Rapport de Diagnostic Peppol Belgique — {filename}",
        f"**Date :** {when} · **Cadre :** Arrêté Royal Facturation Électronique B2B Obligatoire",
        "**Périmètre du contrôle :** contrôles algorithmiques hors ligne (Modulo 97, TVA, codes postaux, doublons) — l'inscription effective à l'annuaire Peppol se vérifie via les liens fournis dans le CSV",
        "",
        "## 1. Synthèse de Conformité Peppol",
        "| Indicateur | Valeur | Statut |",
        "|---|---|---|",
        f"| Total fiches auditées | **{total}** | Base totale |",
        f"| Fiches 100% compatibles Peppol | **{valides}** ({pct:.1f}%) | "
        f"{'🟢 Prêt' if pct > 90 else '🔴 Risque de rejet de facturation'} |",
        f"| Numéros BCE / KBO invalides | **{results['erreurs_bce']}** | Risque d'amende 1 500 € à 5 000 € |",
        f"| Numéros de TVA invalides | **{results['erreurs_tva']}** | Risque de non-déductibilité TVA |",
        f"| Doublons détectés | **{results['doublons']}** | Risque d'incohérence comptable |",
        "",
        "## 2. Risques Financiers Immédiats",
        "Depuis le 1er janvier 2026 (fin de la tolérance au 31 mars 2026) :",
        f"- {total - valides} fiches bloqueront les flux entrants/sortants sur Exact Online, WinBooks ou Clearfacts.",
        "- Amendes administratives jusqu'à 5 000 € par infraction constatée par le SPF Finances.",
    ]

    if results.get("anomalies"):
        lines.append("")
        lines.append("## 3. Échantillon des Anomalies")
        lines.append("| Ligne | Nom | BCE | Erreurs Détectées |")
        lines.append("|---|---|---|---|")
        for item in results["anomalies"][:15]:
            lines.append(
                f"| {item['ligne']} | {item['nom']} | {item['bce']} | {', '.join(item['erreurs'])} |"
            )
    return "\n".join(lines)
