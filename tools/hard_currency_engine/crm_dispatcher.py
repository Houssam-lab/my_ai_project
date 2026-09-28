#!/usr/bin/env python3
"""
Module CRM Dispatcher — Hard Currency Engine
Génère des **brouillons** de messages de prospection à partir de la base de cibles.

⚠️ Ce module n'envoie rien. Le dossier de sortie s'appelait ``dispatched_2026`` et a été
lu comme un journal d'envois ; il s'appelle désormais ``drafts_2026`` et chaque fichier
porte l'en-tête ``STATUS: DRAFT``. Le seul journal des envois réels est
``docs/commercial/outreach/CONTACT_LEDGER.csv`` (D-297).

Corridors actifs (dossier 2026-09-28 §11 : 9 corridors → 1 + canal de financement) :
FR_PDP, FR_VULN_SECTOR, BE_PEPPOL (référentiels e-facturation) et GLOBAL_AI_LABS
(candidatures d'évaluateur — canal de financement personnel, D-282). Les cibles marquées
``EXCLU`` et les corridors retirés (CBAM, ZATCA, EAA, agences dev, export agro, subventions)
sont ignorés : leurs outils sont retirés ou hors périmètre, et un message qui promet ce que
l'outil ne fait pas est une dette, pas un contact.
"""

from __future__ import annotations

import csv
import re
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DRAFTS_DIR = _REPO_ROOT / "docs" / "commercial" / "outreach" / "drafts_2026"

ACTIVE_CORRIDORS = frozenset({"FR_PDP", "FR_VULN_SECTOR", "BE_PEPPOL", "GLOBAL_AI_LABS"})
EXCLUDED_STATUSES = frozenset({"EXCLU", "STOP", "SANS_REPONSE"})

DRAFT_BANNER = (
    "STATUS: DRAFT — NOT SENT. Lorsque ce message part réellement, ajoutez une ligne "
    "EMAIL_SENT (ou FORM_SUBMITTED / LINKEDIN_SENT) dans docs/commercial/outreach/CONTACT_LEDGER.csv."
)

SIGNATURE = "Houssam Benmerah\nh.benmerah@univ-eltarf.dz"


def load_targets(csv_path: Path) -> list[dict]:
    if not csv_path.exists():
        raise FileNotFoundError(f"Fichier de cibles introuvable : {csv_path}")

    with open(csv_path, encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        return list(reader)


def is_dispatchable(target: dict) -> bool:
    """Une cible reçoit un brouillon seulement si son corridor est actif et son statut non exclu."""
    status = (target.get("statut") or "").strip().upper()
    corridor = (target.get("corridor") or "").strip()
    return corridor in ACTIVE_CORRIDORS and status not in EXCLUDED_STATUSES


def generate_personalized_dispatch(target: dict) -> dict:
    """Génère le texte final personnalisé pour une cible donnée."""
    nom = target.get("nom_entite", "Cher Partenaire")
    corridor = target.get("corridor", "")
    role = target.get("role_cible", "Direction")
    email = target.get("contact_cible", "")
    hook = target.get("hook_accroche", "")

    if corridor in ("FR_PDP", "FR_VULN_SECTOR"):
        subject = f"Vos rejets Factur-X : fiabilisation référentiels — {nom}"
        body = f"""Bonjour,

Votre structure {nom} prépare activement l'échéance de la facturation électronique.

Constat terrain : {hook}

Je prends en charge la fiabilisation de vos fichiers clients/fournisseurs :
- Contrôle des SIREN/SIRET (clé Luhn) et des numéros de TVA intracommunautaire (clé de contrôle).
- Rapprochement avec la base SIRENE publique : entreprises radiées, SIREN inconnus.
- Dédoublonnage et normalisation des codes postaux ; livraison d'un fichier prêt à importer.

Test gratuit : vous m'adressez un export de 20 fiches (CSV), je vous livre le diagnostic sous 24 h.

Puis-je vous adresser ce premier rapport ?

Bien cordialement,

{SIGNATURE}
Consultant Référentiels Données & Facturation Électronique
"""
    elif corridor == "BE_PEPPOL":
        subject = f"Peppol Belgique : mise en conformité des bases clients — {nom}"
        body = f"""Bonjour,

Depuis janvier 2026, l'obligation Peppol B2B est en vigueur en Belgique et les amendes administratives (1 500 à 5 000 €) s'appliquent.

Constat : {hook}

Je réalise l'audit d'intégrité de vos bases tiers :
- Contrôle Modulo 97 des numéros BCE / KBO et des numéros de TVA.
- Construction de l'identifiant Peppol (0208:…) à partir du numéro BCE validé, avec lien de vérification vers l'annuaire Peppol.
- Dédoublonnage et contrôle des codes postaux ; livraison d'un fichier prêt à importer.

Je vous propose un audit gratuit de 20 fiches sous 24 h, sans engagement.

Seriez-vous ouvert à ce que je vous transmette ce diagnostic ?

Cordialement,

{SIGNATURE}
Consultant Référentiels Peppol
"""
    elif corridor == "GLOBAL_AI_LABS":
        subject = f"Multilingual AI Evaluation Specialist Application — {nom}"
        body = f"""Dear Hiring Team at {nom},

I am submitting my profile as a multilingual AI evaluation engineer (Arabic, French, Darija, Python).

Value proposition: {hook}

Available 20-30h/week with daily availability on CET/UTC timezones. Ready for skill assessments immediately.

Best regards,

{SIGNATURE}
"""
    else:
        subject = f"Opportunité de collaboration B2B — {nom}"
        body = f"""Bonjour,

Dans le cadre de nos activités d'ingénierie et d'exportation de services : {hook}

Disponible pour un court échange technique.

Cordialement,
{SIGNATURE}
"""

    return {
        "id": target.get("id"),
        "destinataire": nom,
        "email": email,
        "corridor": corridor,
        "role": role,
        "objet": subject,
        "corps": body.strip(),
    }


def withdrawal_reason(target: dict) -> str:
    """Pourquoi une cible ne reçoit pas de brouillon — la raison est écrite, jamais tue."""
    status = (target.get("statut") or "").strip().upper()
    corridor = (target.get("corridor") or "").strip()
    if status in EXCLUDED_STATUSES:
        return f"statut cible = {status} (opposition au démarchage ou cible écartée)"
    if corridor not in ACTIVE_CORRIDORS:
        return (
            f"corridor {corridor} retiré le 2026-09-28 : outil retiré du parcours client "
            "(CBAM/ZATCA/EAA) ou hors du périmètre unique (dossier §11)"
        )
    return "non admissible"


def _draft_filename(packet: dict) -> str:
    safe_name = re.sub(r"[^A-Za-z0-9_-]", "_", packet["destinataire"])
    return f"{int(packet['id']):02d}_{packet['corridor']}_{safe_name}.txt"


def dispatch_campaign(csv_path: Path, output_dir: Path) -> list[Path]:
    """Écrit un brouillon par cible admissible et une fiche de retrait pour les autres.

    Retourne uniquement les brouillons actifs. Les cibles écartées reçoivent un fichier
    ``WITHDRAWN`` au même nom : le dossier reste complet, aucun fichier n'est supprimé,
    et personne ne peut lire une absence comme un oubli. N'envoie rien.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    targets = load_targets(csv_path)
    generated_files = []

    for t in targets:
        packet = generate_personalized_dispatch(t)
        file_path = output_dir / _draft_filename(packet)
        if not is_dispatchable(t):
            file_path.write_text(
                f"STATUS: WITHDRAWN — NE PAS ENVOYER.\n"
                f"DESTINATAIRE: {packet['destinataire']}\n"
                f"CORRIDOR: {packet['corridor']}\n"
                f"RAISON: {withdrawal_reason(t)}\n",
                encoding="utf-8",
            )
            continue

        content = f"""{DRAFT_BANNER}
TO: {packet["email"]}
SUBJECT: {packet["objet"]}
DESTINATAIRE: {packet["destinataire"]} ({packet["role"]})
CORRIDOR: {packet["corridor"]}
================================================================================
{packet["corps"]}
"""
        file_path.write_text(content, encoding="utf-8")
        generated_files.append(file_path)

    return generated_files
