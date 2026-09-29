#!/usr/bin/env python3
"""
Module France Validator — Hard Currency Engine
Audit et assainissement des référentiels clients/fournisseurs pour la réforme de la facturation électronique française (RFE).
"""

from __future__ import annotations

import csv
import json
import re
import unicodedata
import urllib.parse
import urllib.request
from collections.abc import Callable
from datetime import date
from pathlib import Path

from tools.hard_currency_engine.contracts import flag_duplicate

#: Base publique « Recherche d'entreprises » (INSEE/DINUM) — la seule source qui dit si une
#: entreprise est radiée. Sans elle, le contrôle est purement algorithmique (clés Luhn/TVA).
SIRENE_API_URL = "https://recherche-entreprises.api.gouv.fr/search"

#: Une entreprise est active quand `etat_administratif == "A"` ; « C » = cessée/radiée.
_SIRENE_ACTIVE = "A"


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
        # Règle INSEE : les SIRET de La Poste ne suivent pas Luhn ; ils sont valides
        # lorsque la somme des chiffres est un multiple de 5 (et non de 10).
        sum_digits = sum(int(ch) for ch in s)
        if sum_digits % 5 == 0:
            return True, s, "OK (La Poste)"
        return False, s, "Échec contrôle somme La Poste (multiple de 5 attendu)"
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


def sirene_lookup(siren: str, timeout: int = 10) -> dict:
    """Interroge la base publique Recherche d'entreprises pour un SIREN.

    Retourne ``{"trouve": True, "actif": bool, "etat": str, "nom_officiel": str}``,
    ``{"trouve": False}`` si le SIREN est inconnu, ou ``{"trouve": None, "erreur": …}``
    quand le réseau est indisponible — le rapport dit alors « indisponible », jamais « OK ».
    """
    query = urllib.parse.urlencode({"q": siren, "limit": 1})
    request = urllib.request.Request(
        f"{SIRENE_API_URL}?{query}", headers={"User-Agent": "hard-currency-engine/1.0"}
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            data = json.loads(response.read().decode("utf-8"))
    except Exception as exc:  # réseau/quota indisponible → dégradation explicite
        return {"trouve": None, "erreur": str(exc)[:120]}
    results = data.get("results") or []
    if not results:
        return {"trouve": False}
    entry = results[0]
    etat = entry.get("etat_administratif") or "?"
    return {
        "trouve": True,
        "etat": etat,
        "actif": etat == _SIRENE_ACTIVE,
        "nom_officiel": (entry.get("nom_complet") or "").upper(),
    }


def _sirene_flags(clean_siren: str, lookup: Callable[[str], dict]) -> tuple[list[str], str, str]:
    """(erreurs SIRENE, statut, nom officiel) pour un SIREN syntaxiquement valide."""
    info = lookup(clean_siren)
    if info.get("trouve") is None:
        return [], "INDISPONIBLE", ""
    if info.get("trouve") is False:
        return ["SIREN_INCONNU_SIRENE(aucune entreprise pour ce SIREN)"], "INCONNU", ""
    nom = info.get("nom_officiel") or ""
    if not info.get("actif"):
        return [f"ENTREPRISE_RADIEE(etat={info.get('etat', '?')})"], "RADIEE", nom
    return [], "ACTIVE", nom


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

    dedup_keys = []
    siren_key = _clean_siren(row, cols)
    if len(siren_key) == 9:
        dedup_keys.append(f"SIREN:{siren_key}")
    name_cp_key = f"{norm(nom_val)}_{norm(cp_val)}"
    if len(name_cp_key) > 5:
        dedup_keys.append(f"NOM_CP:{name_cp_key}")
    flag_duplicate(line_errors, seen_dedup, line_no, dedup_keys)

    return line_errors, has_siren_err, has_siret_err, has_tva_err


def audit_french_csv(
    csv_path: Path,
    *,
    online: bool = False,
    lookup: Callable[[str], dict] | None = None,
) -> dict:
    """Audit complet d'un fichier CSV de tiers pour le marché français.

    ``online=True`` rapproche chaque SIREN syntaxiquement valide de la base SIRENE publique
    (entreprises radiées, SIREN inconnus). ``lookup`` permet d'injecter la fonction de
    recherche (tests hors réseau) ; par défaut ``sirene_lookup``.
    """
    if not csv_path.exists():
        raise FileNotFoundError(f"Fichier introuvable : {csv_path}")

    results = {
        "total": 0,
        "valides": 0,
        "erreurs_siren": 0,
        "erreurs_siret": 0,
        "erreurs_tva": 0,
        "doublons": 0,
        "online": online,
        "radiees": 0,
        "sirene_inconnues": 0,
        "sirene_indisponible": 0,
        "anomalies": [],
        "annotees": [],
    }
    resolver = lookup or sirene_lookup

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
        _process_french_row(row, cols, line_no, seen_dedup, results, online, resolver)

    return results


def _clean_siren(row: dict, cols: dict) -> str:
    """SIREN à 9 chiffres dérivé, dans l'ordre : colonne SIREN, SIRET, numéro de TVA FR."""
    siren_val = row.get(cols["siren"], "") if cols["siren"] else ""
    siret_val = row.get(cols["siret"], "") if cols["siret"] else ""
    tva_val = (row.get(cols["tva"], "") or "") if cols["tva"] else ""
    tva_digits = re.sub(r"\D", "", tva_val)
    return (
        re.sub(r"\D", "", siren_val)
        or (re.sub(r"\D", "", siret_val)[:9] if siret_val else "")
        or (tva_digits[2:] if tva_val.upper().startswith("FR") and len(tva_digits) == 11 else "")
    )


def _process_french_row(
    row: dict,
    cols: dict,
    line_no: int,
    seen_dedup: dict,
    results: dict,
    online: bool,
    resolver: Callable[[str], dict],
) -> None:
    """Valide une ligne, la compte, l'annote et l'ajoute à `results` (mutation volontaire)."""
    results["total"] += 1
    line_errors, err_siren, err_siret, err_tva = _validate_french_row(
        row, cols, line_no, seen_dedup
    )
    results["erreurs_siren"] += int(err_siren)
    results["erreurs_siret"] += int(err_siret)
    results["erreurs_tva"] += int(err_tva)
    results["doublons"] += int(any("DOUBLON" in err for err in line_errors))

    nom_val = row.get(cols["nom"], "") if cols["nom"] else ""
    siren_val = row.get(cols["siren"], "") if cols["siren"] else ""
    clean_s = _clean_siren(row, cols)
    siren_ok = len(clean_s) == 9 and luhn_ok(clean_s)

    sirene_statut, sirene_nom = "", ""
    if online and siren_ok:
        sirene_errors, sirene_statut, sirene_nom = _sirene_flags(clean_s, resolver)
        line_errors.extend(sirene_errors)
        counter = {
            "RADIEE": "radiees",
            "INCONNU": "sirene_inconnues",
            "INDISPONIBLE": "sirene_indisponible",
        }
        if sirene_statut in counter:
            results[counter[sirene_statut]] += 1

    if line_errors:
        results["anomalies"].append(
            {
                "ligne": line_no,
                "nom": nom_val,
                # Précédence : l'ancien `a or b if c else ""` renvoyait "" dès que la
                # colonne SIRET manquait, même avec un SIREN présent.
                "siren": re.sub(r"\D", "", siren_val) or clean_s,
                "erreurs": line_errors,
            }
        )
    else:
        results["valides"] += 1

    row_ann = dict(row)
    row_ann["ANOMALIES_RFE"] = "; ".join(line_errors) if line_errors else "CONFORME"
    row_ann["STATUT_RFE"] = "CONFORME" if not line_errors else "A_CORRIGER"
    row_ann["SIREN_ASSAINI"] = clean_s if siren_ok else ""
    row_ann["TVA_FR_CALCULEE"] = compute_french_vat_key(clean_s) if siren_ok else ""
    if cols["cp"] and row.get(cols["cp"]):
        _, healed_cp, _ = validate_french_postal_code(row.get(cols["cp"], ""))
        row_ann["CP_ASSAINI"] = healed_cp
    if online:
        row_ann["SIRENE_STATUT"] = sirene_statut or "NON_VERIFIE"
        row_ann["SIRENE_NOM_OFFICIEL"] = sirene_nom
    results["annotees"].append(row_ann)


def format_french_report(results: dict, filename: str, report_date: date | None = None) -> str:
    total = results["total"]
    valides = results["valides"]
    pct = (valides / total * 100) if total > 0 else 0.0
    online = bool(results.get("online"))
    when = (report_date or date.today()).isoformat()
    perimetre = (
        "contrôles algorithmiques + rapprochement SIRENE (base publique)"
        if online
        else "contrôles algorithmiques hors ligne (clés Luhn/TVA, doublons) — sans rapprochement SIRENE"
    )

    lines = [
        f"# Rapport d'Audit Référentiels RFE France — {filename}",
        f"**Date :** {when} · **Cadre Réglementaire :** Réforme Facturation Électronique (DGFiP / Factur-X)",
        f"**Périmètre du contrôle :** {perimetre}",
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
    ]
    if online:
        lines += [
            f"| Entreprises radiées (SIRENE) | **{results.get('radiees', 0)}** | Facture à un tiers disparu |",
            f"| SIREN inconnus de SIRENE | **{results.get('sirene_inconnues', 0)}** | Identifiant à vérifier avec le tiers |",
            f"| Fiches non vérifiables (SIRENE indisponible) | **{results.get('sirene_indisponible', 0)}** | À relancer — pas un « OK » |",
        ]
    lines += [
        "",
        "## 2. Risques Financiers pour l'Entreprise",
        "- **Pénalités de conformité :** 50 € par facture émise hors format électronique "
        "(plafond 15 000 €/an), dès l'obligation d'émission : 1er septembre 2026 pour les grandes "
        "entreprises et ETI, 1er septembre 2027 pour les PME et micro-entreprises (loi de finances 2026).",
        f"- **Impact immédiat :** {total - valides} fiches tiers nécessitent une remédiation avant injection dans votre PDP.",
        "",
        "## 3. Plan d'Action Recommandé",
        "1. Correction des SIREN/SIRET invalides et dérivation des numéros de TVA conformes.",
        (
            "2. Traiter les entreprises radiées et les SIREN inconnus de SIRENE avec le tiers concerné."
            if online
            else "2. Ce rapport est hors ligne : le rapprochement SIRENE (radiations, raisons sociales) s'exécute avec l'option `--online`."
        ),
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
