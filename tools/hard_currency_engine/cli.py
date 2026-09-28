#!/usr/bin/env python3
"""
Hard Currency Engine (HCE) — Command Line Interface du parcours client.

Trois commandes seulement (``CUSTOMER_PATH_COMMANDS``) : l'audit France (RFE), l'audit
Belgique (Peppol) et la génération de brouillons de prospection. Les anciennes commandes
``cbam``, ``zatca`` et ``eaa`` ont été **retirées du parcours client le 2026-09-28**
(dossier : docs/commercial/HARD_CURRENCY_OPPORTUNITY_DOSSIER_2026-09-28.md §10) : le
calculateur CBAM réintroduisait un facteur 0,025 déjà retiré (≈ 71× d'écart sur les
billettes) avec des « émissions mesurées » inventées ; la « réparation » ZATCA hachait une
chaîne arbitraire sans signature ; la déclaration EAA fixait lieu, date et constats en dur.
Les modules restent sur le disque pour l'historique ; aucun ne doit produire un livrable
client. Réintroduire l'un d'eux exige un test comparatif contre la source officielle.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Assurer la résolution des imports relatifs et absolus
_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from tools.hard_currency_engine.belgium_validator import (
    audit_belgian_csv,
    export_cleaned_belgian_csv,
    format_belgian_report,
)
from tools.hard_currency_engine.crm_dispatcher import (
    DEFAULT_DRAFTS_DIR,
    dispatch_campaign,
)
from tools.hard_currency_engine.france_validator import (
    audit_french_csv,
    export_cleaned_french_csv,
    format_french_report,
)

#: Les seules commandes exposées à un fichier client.
CUSTOMER_PATH_COMMANDS: tuple[str, ...] = ("france", "belgium", "crm")


def cmd_france(args):
    path = Path(args.csv_file)
    res = audit_french_csv(path, online=bool(args.online))
    if args.json:
        print(json.dumps(res, indent=2, ensure_ascii=False))
        return

    report = format_french_report(res, path.name)
    if args.out:
        Path(args.out).write_text(report, encoding="utf-8")
        print(f"✅ Rapport France écrit dans : {args.out}")
    else:
        print(report)

    if args.csv_out:
        out_p = export_cleaned_french_csv(res, Path(args.csv_out))
        print(f"✅ CSV assaini exporté dans : {out_p}")


def cmd_belgium(args):
    path = Path(args.csv_file)
    res = audit_belgian_csv(path)
    if args.json:
        print(json.dumps(res, indent=2, ensure_ascii=False))
        return

    report = format_belgian_report(res, path.name)
    if args.out:
        Path(args.out).write_text(report, encoding="utf-8")
        print(f"✅ Rapport Belgique écrit dans : {args.out}")
    else:
        print(report)

    if args.csv_out:
        out_p = export_cleaned_belgian_csv(res, Path(args.csv_out))
        print(f"✅ CSV assaini Peppol exporté dans : {out_p}")


def cmd_crm(args):
    csv_file = Path(args.targets_csv)
    out_dir = Path(args.output_dir)
    files = dispatch_campaign(csv_file, out_dir)
    print(
        f"✅ {len(files)} brouillons générés dans '{out_dir}'. Rien n'a été envoyé : "
        "chaque envoi réel se consigne dans docs/commercial/outreach/CONTACT_LEDGER.csv."
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Hard Currency Engine — audit de référentiels tiers (France RFE · Belgique Peppol) et brouillons de prospection"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # France
    p_fr = subparsers.add_parser("france", help="Audit référentiels RFE France")
    p_fr.add_argument("csv_file", help="CSV de tiers à auditer")
    p_fr.add_argument("--out", help="Fichier rapport markdown de sortie")
    p_fr.add_argument("--csv-out", help="Exporter le CSV assaini et enrichi")
    p_fr.add_argument(
        "--online",
        action="store_true",
        help="Rapprocher chaque SIREN de la base SIRENE publique (entreprises radiées, SIREN inconnus)",
    )
    p_fr.add_argument("--json", action="store_true", help="Sortie JSON")

    # Belgium
    p_be = subparsers.add_parser("belgium", help="Audit référentiels Peppol Belgique")
    p_be.add_argument("csv_file", help="CSV de tiers à auditer")
    p_be.add_argument("--out", help="Fichier rapport markdown de sortie")
    p_be.add_argument("--csv-out", help="Exporter le CSV assaini Peppol")
    p_be.add_argument("--json", action="store_true", help="Sortie JSON")

    # CRM
    p_cr = subparsers.add_parser(
        "crm", help="Génération de brouillons de prospection (rien n'est envoyé)"
    )
    p_cr.add_argument("targets_csv", help="CSV des cibles qualifiées")
    p_cr.add_argument(
        "--output-dir",
        default=str(DEFAULT_DRAFTS_DIR),
        help="Répertoire des brouillons (défaut : docs/commercial/outreach/drafts_2026)",
    )
    return parser


def main(argv: list[str] | None = None):
    args = build_parser().parse_args(argv)

    if args.command == "france":
        cmd_france(args)
    elif args.command == "belgium":
        cmd_belgium(args)
    elif args.command == "crm":
        cmd_crm(args)


if __name__ == "__main__":
    main()
