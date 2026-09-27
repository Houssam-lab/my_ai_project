#!/usr/bin/env python3
"""
Hard Currency Engine (HCE) — Master Command Line Interface
Exécution unifiée des modules d'audit, de calcul carbone, de conformité et de prospection commerciale.
"""

from __future__ import annotations

import argparse
import csv
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
from tools.hard_currency_engine.cbam_calculator import (
    CBAM_CATALOG,
    calculate_cbam,
    calculate_cbam_batch,
    generate_cbam_batch_xml,
    generate_cbam_xml,
    generate_sensitivity_table,
)
from tools.hard_currency_engine.crm_dispatcher import dispatch_campaign
from tools.hard_currency_engine.eaa_scanner import (
    audit_html_content,
    generate_declaration_accessibilite,
)
from tools.hard_currency_engine.france_validator import (
    audit_french_csv,
    export_cleaned_french_csv,
    format_french_report,
)
from tools.hard_currency_engine.zatca_validator import (
    audit_zatca_batch,
    decode_zatca_tlv,
    encode_zatca_tlv,
    generate_sample_zatca_ubl_xml,
    repair_zatca_chain,
)


def cmd_france(args):
    path = Path(args.csv_file)
    res = audit_french_csv(path)
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


def _print_cbam_catalog():
    print("Produits industriels CBAM configurés :")
    for k, v in CBAM_CATALOG.items():
        print(f"  - {k} : {v['nom']} ({v['secteur']}) -> Installation: {v['installation_nom']}")


def _run_cbam_manifest(
    manifest_path: str,
    price: float,
    as_json: bool,
    batch_xml: str | None = None,
    eori: str = "FR12345678900012",
):
    p = Path(manifest_path)
    lines = [
        line
        for line in p.read_text(encoding="utf-8-sig").splitlines()
        if not line.strip().startswith("#")
    ]
    if not lines:
        print("Erreur : Fichier manifeste vide ou non valide.", file=sys.stderr)
        return
    delimiter = ";" if ";" in lines[0] else ","
    reader = csv.DictReader(lines, delimiter=delimiter)
    rows = list(reader)
    batch_res = calculate_cbam_batch(rows, cert_price=price)
    if as_json:
        print(json.dumps(batch_res, indent=2, ensure_ascii=False))
    else:
        print("=" * 80)
        print(f"RAPPORT DE MANIFESTE CBAM CONSOLIDÉ — {p.name}")
        print(
            f"Lignes traitées : {batch_res['nb_lignes']} | Tonnage total : {batch_res['total_tonnes']:,.0f} t"
        )
        print(f"Coût total valeurs par défaut : {batch_res['total_cout_defaut']:,.2f} €")
        print(f"Coût total données réelles     : {batch_res['total_cout_reel']:,.2f} €")
        print(f"💰 ÉCONOMIE NETTE GLOBALE      : {batch_res['economie_globale_eur']:,.2f} €")
        print("=" * 80)

    if batch_xml:
        xml_str = generate_cbam_batch_xml(batch_res, declarant_eori=eori)
        Path(batch_xml).write_text(xml_str, encoding="utf-8")
        print(f"✅ Déclaration XML consolidée exportée dans : {batch_xml}")


def cmd_cbam(args):
    if args.list:
        _print_cbam_catalog()
        return

    if args.manifest:
        _run_cbam_manifest(
            args.manifest,
            args.price,
            args.json,
            args.batch_xml,
            getattr(args, "eori", "FR12345678900012") or "FR12345678900012",
        )
        return

    if not args.hs or args.tonnes is None:
        print("Erreur : --hs et --tonnes sont obligatoires pour le calcul.", file=sys.stderr)
        sys.exit(1)

    res = calculate_cbam(args.hs, args.tonnes, args.see_actual, args.price)
    if args.json:
        print(json.dumps(res, indent=2, ensure_ascii=False))
        return

    print("=" * 80)
    print(f"RAPPORT D'ARBITRAGE CBAM (UE 2025/2620) — {res['produit']}")
    print(f"Installation d'origine : {res['installation']} ({res['pays_origine']})")
    print(f"Volume : {res['tonnes']:,.0f} t | Prix CO2 : {res['prix_certificat']:.2f} €/t")
    print(f"Émission défaut UE (avec markup) : {res['see_default']:.3f} tCO2/t")
    print(
        f"Émission réelle mesurée Algérie  : {res['see_actual']:.3f} tCO2/t (-{(res['gain_carbone_tonne'] / res['see_default'] * 100):.1f}%)"
    )
    print(f"Coût certificats avec valeur par défaut : {res['cout_default']:,.2f} €")
    print(f"Coût certificats avec données réelles   : {res['cout_actual']:,.2f} €")
    print(
        f"💰 ÉCONOMIE NETTE POUR L'IMPORTATEUR    : {res['economie_totale']:,.2f} € ({res['economie_par_tonne']:.2f} €/t)"
    )
    print(f"🛡️  Pénalité réglementaire évitée (100€/t): {res['penalite_evitee']:,.2f} €")
    print("=" * 80)

    if args.sensitivity:
        sens = generate_sensitivity_table(res)
        print("\nANALYSE DE SENSIBILITÉ SELON COURS DU QUOTA ETS :")
        print("| Prix CO2 (€/t) | Coût Défaut (€) | Coût Réel (€) | Économie Nette (€) |")
        print("|---|---|---|---|")
        for row in sens:
            print(
                f"| {row['prix_co2']:.0f} € | {row['cout_defaut']:,.2f} € | {row['cout_reel']:,.2f} € | {row['economie_eur']:,.2f} € |"
            )

    if args.xml:
        xml_content = generate_cbam_xml(res)
        Path(args.xml).write_text(xml_content, encoding="utf-8")
        print(f"\n✅ Fichier XML déclaratif généré dans : {args.xml}")


def _handle_zatca_batch(batch_file: str, repair_out: str | None, as_json: bool):
    data = json.loads(Path(batch_file).read_text(encoding="utf-8"))
    invoices = data if isinstance(data, list) else data.get("invoices", [])
    audit_res = audit_zatca_batch(invoices)
    if as_json and not repair_out:
        print(json.dumps(audit_res, indent=2, ensure_ascii=False))
        return

    print("=" * 80)
    print(f"AUDIT DE CHAÎNE DE FACTURES ZATCA — {len(invoices)} factures")
    print(
        f"Statut : {'🟢 Séquence intègre' if audit_res['est_valide'] else '🔴 Ruptures de chaîne détectées'}"
    )
    for a in audit_res["anomalies"]:
        print(f"  - {a}")
    print("=" * 80)

    if repair_out:
        repaired, actions = repair_zatca_chain(invoices)
        Path(repair_out).write_text(
            json.dumps(repaired, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        print(f"✅ Séquence réparée ({len(actions)} corrections) écrite dans : {repair_out}")


def cmd_zatca(args):
    if args.audit_batch:
        _handle_zatca_batch(args.audit_batch, args.repair_out, args.json)
    elif args.qr_encode:
        parts = args.qr_encode.split("|")
        if len(parts) < 5:
            print(
                "Format attendu pour --qr-encode : 'Vendeur|TVA15|ISO_Time|Total|TotalTVA'",
                file=sys.stderr,
            )
            sys.exit(1)
        b64 = encode_zatca_tlv(parts[0], parts[1], parts[2], parts[3], parts[4])
        print(f"TLV Base64 QR Code :\n{b64}")
    elif args.qr_decode:
        decoded = decode_zatca_tlv(args.qr_decode)
        if args.json:
            print(json.dumps(decoded, indent=2, ensure_ascii=False))
            return
        print("QR Code TLV Décodé :")
        for tag, val in sorted(decoded.items()):
            print(f"  Tag {tag} : {val}")
    elif getattr(args, "ubl", False):
        sample_data = {
            "id": "INV-2026-001",
            "uuid": "a1b2c3d4-e5f6-4a5b-8c9d-0e1f2a3b4c5d",
            "icv": 1,
            "seller_vat": "300000000000003",
            "total": 50000.0,
            "vat": 7500.0,
        }
        xml_ubl = generate_sample_zatca_ubl_xml(sample_data)
        if getattr(args, "out", None):
            Path(args.out).write_text(xml_ubl, encoding="utf-8")
            print(f"✅ Facture UBL ZATCA générée dans : {args.out}")
        else:
            print(xml_ubl)
    else:
        print("Utilisez --qr-encode, --qr-decode, --audit-batch ou --ubl.")


def cmd_eaa(args):
    html_text = (
        Path(args.html_file).read_text(encoding="utf-8")
        if Path(args.html_file).exists()
        else args.html_file
    )
    res = audit_html_content(html_text)
    if args.json:
        print(json.dumps(res, indent=2, ensure_ascii=False))
        return

    print("=" * 80)
    print(
        f"AUDIT D'ACCESSIBILITÉ WEB (EAA / WCAG 2.1 AA) — Score: {res['score_accessibilite']:.0f}/100"
    )
    print(
        f"Images : {res['total_images']} | Formulaires : {res['total_inputs']} | Liens : {res['total_liens']} | Boutons : {res['total_boutons']}"
    )
    print(
        f"Statut : {'🟢 Conforme' if res['est_conforme'] else '🔴 Non-conformités critiques détectées'}"
    )
    print("-" * 80)
    for niveau, ref, msg in res["anomalies"]:
        print(f"  [{niveau}] {ref} : {msg}")
    print("=" * 80)

    if args.remediation and res["guide_remediation"]:
        print("\nGUIDE TECHNIQUE DE REMÉDIATION :")
        for item in res["guide_remediation"]:
            print(f"\n[{item['criticite']}] {item['norme']} - {item['constat']}")
            print(f"Conseil : {item['conseil']}")
            print(f"Solution : {item['snippet_solution']}")

    if getattr(args, "remediate_out", None):
        Path(args.remediate_out).write_text(res["code_html_assaini"], encoding="utf-8")
        print(f"\n✅ Code HTML assaini écrit dans : {args.remediate_out}")

    if args.declaration:
        decl = generate_declaration_accessibilite(
            args.company or "Entreprise E-commerce",
            "Boutique en ligne",
            "https://example.com",
            taux_conformite=res["score_accessibilite"],
        )
        Path(args.declaration).write_text(decl, encoding="utf-8")
        print(f"\n✅ Déclaration d'accessibilité légale générée : {args.declaration}")


def cmd_crm(args):
    csv_file = Path(args.targets_csv)
    out_dir = Path(args.output_dir)
    files = dispatch_campaign(csv_file, out_dir)
    print(
        f"✅ Campagne générée avec succès : {len(files)} messages prêts à l'envoi dans '{out_dir}'."
    )


def main():  # noqa: PLR0915 — CLI dispatch table; each branch delegates to a command
    parser = argparse.ArgumentParser(
        description="Hard Currency Engine — Suite d'outils d'exportation de services"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # France
    p_fr = subparsers.add_parser("france", help="Audit référentiels RFE France")
    p_fr.add_argument("csv_file", help="CSV de tiers à auditer")
    p_fr.add_argument("--out", help="Fichier rapport markdown de sortie")
    p_fr.add_argument("--csv-out", help="Exporter le CSV assaini et enrichi")
    p_fr.add_argument("--json", action="store_true", help="Sortie JSON")

    # Belgium
    p_be = subparsers.add_parser("belgium", help="Audit référentiels Peppol Belgique")
    p_be.add_argument("csv_file", help="CSV de tiers à auditer")
    p_be.add_argument("--out", help="Fichier rapport markdown de sortie")
    p_be.add_argument("--csv-out", help="Exporter le CSV assaini Peppol")
    p_be.add_argument("--json", action="store_true", help="Sortie JSON")

    # CBAM
    p_cb = subparsers.add_parser("cbam", help="Calculateur d'économies CBAM")
    p_cb.add_argument("--hs", help="Code SH (ex: 72071114, 31021000)")
    p_cb.add_argument("--tonnes", type=float, help="Volume en tonnes")
    p_cb.add_argument("--see-actual", type=float, help="Valeur réelle d'émissions tCO2/t")
    p_cb.add_argument("--price", type=float, default=75.0, help="Prix du certificat ETS")
    p_cb.add_argument("--xml", help="Chemin du fichier XML de déclaration à exporter")
    p_cb.add_argument("--batch-xml", help="Chemin du fichier XML de déclaration consolidée")
    p_cb.add_argument("--eori", default="FR12345678900012", help="Numéro EORI du déclarant")
    p_cb.add_argument("--manifest", help="Fichier CSV de manifeste multi-cargaisons")
    p_cb.add_argument(
        "--sensitivity", action="store_true", help="Générer la table de sensibilité financière"
    )
    p_cb.add_argument("--list", action="store_true", help="Lister les produits supportés")
    p_cb.add_argument("--json", action="store_true", help="Sortie JSON")

    # ZATCA
    p_za = subparsers.add_parser("zatca", help="Validation et encodage ZATCA")
    p_za.add_argument(
        "--qr-encode", help="Encoder un QR TLV (format: Vendeur|TVA|Time|Total|TotalTVA)"
    )
    p_za.add_argument("--qr-decode", help="Décoder une chaîne QR Base64")
    p_za.add_argument("--audit-batch", help="Fichier JSON d'un lot de factures à auditer")
    p_za.add_argument("--repair-out", help="Fichier JSON de sortie pour le lot réparé")
    p_za.add_argument(
        "--ubl", action="store_true", help="Générer un exemple de facture XML UBL 2.1 ZATCA"
    )
    p_za.add_argument("--out", help="Fichier de sortie")
    p_za.add_argument("--json", action="store_true", help="Sortie JSON")

    # EAA
    p_ea = subparsers.add_parser("eaa", help="Scanner d'accessibilité EAA")
    p_ea.add_argument("html_file", help="Fichier HTML à auditer")
    p_ea.add_argument("--company", help="Nom de l'entreprise")
    p_ea.add_argument("--declaration", help="Fichier de sortie de la déclaration légale")
    p_ea.add_argument(
        "--remediation", action="store_true", help="Afficher les snippets de remédiation"
    )
    p_ea.add_argument("--remediate-out", help="Fichier HTML assaini de sortie")
    p_ea.add_argument("--json", action="store_true", help="Sortie JSON")

    # CRM
    p_cr = subparsers.add_parser("crm", help="Dispatch de campagne de prospection")
    p_cr.add_argument("targets_csv", help="CSV des cibles qualifiées")
    p_cr.add_argument(
        "--output-dir", default="outreach_campaign", help="Répertoire de sortie des emails"
    )

    args = parser.parse_args()

    if args.command == "france":
        cmd_france(args)
    elif args.command == "belgium":
        cmd_belgium(args)
    elif args.command == "cbam":
        cmd_cbam(args)
    elif args.command == "zatca":
        cmd_zatca(args)
    elif args.command == "eaa":
        cmd_eaa(args)
    elif args.command == "crm":
        cmd_crm(args)


if __name__ == "__main__":
    main()
