#!/usr/bin/env python3
"""
Module EAA Scanner — Hard Currency Engine
Audit d'accessibilité web (WCAG 2.1 niveau AA / EN 301 549) et générateur de Déclaration d'accessibilité légale (EAA).
"""

from __future__ import annotations

import re


def _check_html_tag_and_title(html_str: str, findings: list):
    html_tag = re.search(r"<html([^>]*)>", html_str, re.IGNORECASE)
    if not html_tag:
        findings.append(("CRITIQUE", "Structure", "Balise <html> absente"))
    elif not re.search(r'\blang\s*=\s*["\'][a-zA-Z]{2}', html_tag.group(1)):
        findings.append(
            ("CRITIQUE", "WCAG 3.1.1", "Attribut 'lang' absent ou non valide sur <html>")
        )

    title_match = re.search(r"<title>(.*?)</title>", html_str, re.IGNORECASE | re.DOTALL)
    if not title_match or not title_match.group(1).strip():
        findings.append(("MAJEUR", "WCAG 2.4.2", "Balise <title> manquante ou vide"))


def _check_images(html_str: str, findings: list) -> int:
    img_tags = re.findall(r"<img([^>]*)>", html_str, re.IGNORECASE)
    missing_alt = 0
    generic_alt = 0
    for img in img_tags:
        alt_match = re.search(r'\balt\s*=\s*["\'](.*?)["\']', img, re.IGNORECASE)
        if not alt_match:
            missing_alt += 1
        elif alt_match.group(1).strip().lower() in (
            "image",
            "photo",
            "img",
            "icon",
            "visuel",
            "logo",
        ):
            generic_alt += 1

    if missing_alt > 0:
        findings.append(("CRITIQUE", "WCAG 1.1.1", f"{missing_alt} image(s) sans attribut 'alt'"))
    if generic_alt > 0:
        findings.append(
            (
                "MOYEN",
                "WCAG 1.1.1",
                f"{generic_alt} image(s) avec description générique non descriptive",
            )
        )
    return len(img_tags)


def _check_inputs(html_str: str, findings: list) -> int:
    inputs = re.findall(r"<input([^>]*)>", html_str, re.IGNORECASE)
    missing_labels = 0
    for inp in inputs:
        type_match = re.search(r'\btype\s*=\s*["\'](.*?)["\']', inp, re.IGNORECASE)
        inp_type = type_match.group(1).lower() if type_match else "text"
        if inp_type in ("hidden", "submit", "button", "reset"):
            continue

        has_aria = bool(re.search(r"\b(aria-label|aria-labelledby)\s*=", inp, re.IGNORECASE))
        has_id = bool(re.search(r"\bid\s*=", inp, re.IGNORECASE))

        if not has_aria:
            if has_id:
                id_val = re.search(r'\bid\s*=\s*["\'](.*?)["\']', inp, re.IGNORECASE).group(1)
                label_for = re.search(
                    rf'<label[^>]*\bfor\s*=\s*["\']{re.escape(id_val)}["\']',
                    html_str,
                    re.IGNORECASE,
                )
                if not label_for:
                    missing_labels += 1
            else:
                missing_labels += 1

    if missing_labels > 0:
        findings.append(
            (
                "CRITIQUE",
                "WCAG 1.3.1 / 3.3.2",
                f"{missing_labels} champ(s) de formulaire sans étiquette (<label>)",
            )
        )
    return len(inputs)


def _check_links(html_str: str, findings: list) -> int:
    links = re.findall(r"<a([^>]*)>(.*?)</a>", html_str, re.IGNORECASE | re.DOTALL)
    bad_links = 0
    generic_words = {
        "cliquez ici",
        "en savoir plus",
        "lire la suite",
        "ici",
        "click here",
        "read more",
    }
    for lattr, ltext in links:
        raw_text = re.sub(r"<[^>]+>", "", ltext).strip().lower()
        has_aria = bool(re.search(r"\baria-label\s*=", lattr, re.IGNORECASE))
        if not has_aria and (not raw_text or raw_text in generic_words):
            bad_links += 1

    if bad_links > 0:
        findings.append(
            (
                "MAJEUR",
                "WCAG 2.4.4",
                f"{bad_links} lien(s) vide(s) ou au libellé non explicite sans aria-label",
            )
        )
    return len(links)


def _check_buttons(html_str: str, findings: list) -> int:
    buttons = re.findall(r"<button([^>]*)>(.*?)</button>", html_str, re.IGNORECASE | re.DOTALL)
    bad_buttons = 0
    for battr, btext in buttons:
        raw_text = re.sub(r"<[^>]+>", "", btext).strip()
        has_aria = bool(re.search(r"\b(aria-label|aria-labelledby)\s*=", battr, re.IGNORECASE))
        if not has_aria and not raw_text:
            bad_buttons += 1

    if bad_buttons > 0:
        findings.append(
            (
                "CRITIQUE",
                "WCAG 4.1.2",
                f"{bad_buttons} bouton(s) sans nom accessible (texte visible ou aria-label manquant)",
            )
        )
    return len(buttons)


def _check_form_controls(html_str: str, findings: list):
    selects = re.findall(r"<select([^>]*)>", html_str, re.IGNORECASE)
    textareas = re.findall(r"<textarea([^>]*)>", html_str, re.IGNORECASE)
    unlabelled = 0

    for elem in (*selects, *textareas):
        has_aria = bool(re.search(r"\b(aria-label|aria-labelledby)\s*=", elem, re.IGNORECASE))
        has_id = bool(re.search(r'\bid\s*=\s*["\'](.*?)["\']', elem, re.IGNORECASE))
        if not has_aria:
            if has_id:
                id_val = re.search(r'\bid\s*=\s*["\'](.*?)["\']', elem, re.IGNORECASE).group(1)
                label_for = re.search(
                    rf'<label[^>]*\bfor\s*=\s*["\']{re.escape(id_val)}["\']',
                    html_str,
                    re.IGNORECASE,
                )
                if not label_for:
                    unlabelled += 1
            else:
                unlabelled += 1

    if unlabelled > 0:
        findings.append(
            (
                "CRITIQUE",
                "WCAG 1.3.1 / 3.3.2",
                f"{unlabelled} liste(s) déroulante(s) ou zone(s) de texte sans étiquette (<label>)",
            )
        )


def _check_viewport_and_landmarks(html_str: str, findings: list):
    viewport = re.search(r'<meta[^>]*name\s*=\s*["\']viewport["\'][^>]*>', html_str, re.IGNORECASE)
    if viewport:
        content = viewport.group(0)
        if re.search(
            r"user-scalable\s*=\s*no|maximum-scale\s*=\s*1(\.0)?\b", content, re.IGNORECASE
        ):
            findings.append(
                (
                    "MAJEUR",
                    "WCAG 1.4.4",
                    "Le zoom mobile est bloqué (user-scalable=no ou maximum-scale=1)",
                )
            )

    has_main = bool(re.search(r"<main\b|role\s*=\s*['\"]main['\"]", html_str, re.IGNORECASE))
    if not has_main:
        findings.append(("MOYEN", "WCAG 1.3.1 / 2.4.1", "Zone de contenu principal <main> absente"))


def _check_headings_and_tables(html_str: str, findings: list):
    headings = [int(m.group(1)) for m in re.finditer(r"<h([1-6])\b", html_str, re.IGNORECASE)]
    if headings and headings[0] != 1:
        findings.append(
            ("MAJEUR", "WCAG 2.4.1", f"La page commence par <h{headings[0]}> au lieu de <h1>")
        )

    for i in range(len(headings) - 1):
        if headings[i + 1] > headings[i] + 1:
            findings.append(
                (
                    "MOYEN",
                    "WCAG 1.3.1",
                    f"Rupture de hiérarchie : saut de <h{headings[i]}> à <h{headings[i + 1]}> sans niveau intermédiaire",
                )
            )
            break

    tables = re.findall(r"<table\b[^>]*>(.*?)</table>", html_str, re.IGNORECASE | re.DOTALL)
    for table_content in tables:
        if not re.search(r"<th\b", table_content, re.IGNORECASE):
            findings.append(
                (
                    "MAJEUR",
                    "WCAG 1.3.1",
                    "Tableau de données sans en-tête <th> déclaré",
                )
            )
            break


def compute_accessibility_score(findings: list[tuple[str, str, str]]) -> float:
    weights = {"CRITIQUE": 15, "MAJEUR": 8, "MOYEN": 4, "MINEUR": 2}
    penalty = sum(weights.get(f[0], 5) for f in findings)
    return float(max(0, 100 - penalty))


def generate_remediation_guide(findings: list[tuple[str, str, str]]) -> list[dict]:
    snippets = []
    for crit, ref, desc in findings:
        d_lower = desc.lower()
        if "alt" in d_lower:
            advice = "Ajouter un attribut alt descriptif à chaque image informative, ou alt='' si décorative."
            snippet = '<img src="produit.jpg" alt="Description précise du produit">'
        elif "lang" in d_lower:
            advice = "Spécifier la langue principale du document dans la balise html."
            snippet = '<html lang="fr">'
        elif "champ" in d_lower or "étiquette" in d_lower:
            advice = "Lier chaque champ de formulaire à une balise <label for='...'>."
            snippet = '<label for="nom">Nom</label>\n<input type="text" id="nom" name="nom">'
        elif "lien" in d_lower:
            advice = (
                "Remplacer les textes de lien vagues par des libellés explicites ou un aria-label."
            )
            snippet = '<a href="/catalogue" aria-label="Voir tout le catalogue">En savoir plus</a>'
        elif "hiérarchie" in d_lower or "titre" in d_lower:
            advice = "Respecter la hiérarchie séquentielle des titres (h1, puis h2, sans sauter de niveau)."
            snippet = "<h1>Titre Principal</h1>\n<h2>Section</h2>\n<h3>Sous-section</h3>"
        elif "tableau" in d_lower:
            advice = "Déclarer des en-têtes <th> avec attribut scope pour structurer les colonnes."
            snippet = '<table><thead><tr><th scope="col">Article</th><th scope="col">Prix</th></tr></thead></table>'
        else:
            advice = "Corriger selon les critères de conformité WCAG 2.1 AA."
            snippet = "<!-- Solution conforme requise -->"

        snippets.append(
            {
                "criticite": crit,
                "norme": ref,
                "constat": desc,
                "conseil": advice,
                "snippet_solution": snippet,
            }
        )
    return snippets


def remediate_html_content(html_str: str) -> tuple[str, list[str]]:
    """Génère une version corrigée du code HTML en injectant les attributs d'accessibilité manquants."""
    remediated = html_str
    actions: list[str] = []

    # 1. Injecter lang="fr" si html est sans lang
    if re.search(r"<html\b(?![^>]*\blang\b)[^>]*>", remediated, re.IGNORECASE):
        remediated = re.sub(
            r"<html\b([^>]*)>",
            r'<html\1 lang="fr">',
            remediated,
            count=1,
            flags=re.IGNORECASE,
        )
        actions.append('Ajout de l\'attribut lang="fr" sur <html>')

    # 2. Injecter un alt="" sur les images sans alt
    def fix_img_alt(m):
        tag = m.group(0)
        if not re.search(r"\balt\s*=", tag, re.IGNORECASE):
            actions.append('Ajout d\'attribut alt="" sur balise <img>')
            return tag[:-1] + ' alt="">'
        return tag

    remediated = re.sub(r"<img\b[^>]*>", fix_img_alt, remediated, flags=re.IGNORECASE)

    # 3. Corriger le blocage du zoom viewport
    if re.search(
        r"user-scalable\s*=\s*no|maximum-scale\s*=\s*1(\.0)?\b", remediated, re.IGNORECASE
    ):
        remediated = re.sub(
            r"user-scalable\s*=\s*no", "user-scalable=yes", remediated, flags=re.IGNORECASE
        )
        actions.append("Déblocage du zoom utilisateur dans le viewport")

    # 4. Injecter balise <main> si absente
    if (
        not re.search(r"<main\b|role\s*=\s*['\"]main['\"]", remediated, re.IGNORECASE)
        and "<body>" in remediated
        and "</body>" in remediated
    ):
        remediated = remediated.replace("<body>", "<body>\n<main>", 1)
        remediated = remediated.replace("</body>", "</main>\n</body>", 1)
        actions.append("Encapsulation du contenu du body dans une balise <main>")

    return remediated, actions


def audit_html_content(html_str: str) -> dict:
    """Analyse un contenu HTML pour détecter les non-conformités critiques EAA / WCAG 2.1 AA."""
    findings: list[tuple[str, str, str]] = []
    _check_html_tag_and_title(html_str, findings)
    total_imgs = _check_images(html_str, findings)
    total_inputs = _check_inputs(html_str, findings)
    total_liens = _check_links(html_str, findings)
    total_buttons = _check_buttons(html_str, findings)
    _check_form_controls(html_str, findings)
    _check_viewport_and_landmarks(html_str, findings)
    _check_headings_and_tables(html_str, findings)
    score = compute_accessibility_score(findings)
    remediated_html, fixes_applied = remediate_html_content(html_str)

    return {
        "total_images": total_imgs,
        "total_inputs": total_inputs,
        "total_liens": total_liens,
        "total_boutons": total_buttons,
        "score_accessibilite": score,
        "anomalies": findings,
        "est_conforme": len(findings) == 0,
        "guide_remediation": generate_remediation_guide(findings),
        "remediation_actions": fixes_applied,
        "code_html_assaini": remediated_html,
    }


def generate_declaration_accessibilite(
    nom_entreprise: str, nom_site: str, url_site: str, taux_conformite: float = 65.0
) -> str:
    """Génère le texte légal français obligatoire pour la Déclaration d'accessibilité (évite l'amende de 25 000 €)."""
    statut = (
        "totalement conforme"
        if taux_conformite == 100.0
        else ("partiellement conforme" if taux_conformite >= 50.0 else "non conforme")
    )

    return f"""# Déclaration d’accessibilité — {nom_site}

**{nom_entreprise}** s’engage à rendre ses services numériques accessibles conformément à l’article 47 de la loi n° 2005-102 du 11 février 2005 et à la directive européenne (UE) 2019/882 (European Accessibility Act).

À cette fin, elle met en œuvre la stratégie et le plan d’action d'accessibilité numérique.
Cette déclaration s'applique au site : **{url_site}**.

## État de conformité
Le site web **{nom_site}** est **{statut}** avec le Référentiel Général d’Amélioration de l’Accessibilité (RGAA) version 4.1.2 et les règles WCAG 2.1 niveau AA, en raison des non-conformités et dérogations énumérées ci-dessous.

### Résultats des tests
L'audit d'accessibilité réalisé le 24 septembre 2026 révèle que :
- **{taux_conformite:.1f}%** des critères du référentiel sont respectés.

## Contenus non accessibles
Les contenus listés ci-dessous ne sont pas accessibles pour les raisons suivantes :
- Absence d'alternatives textuelles sur certains visuels produits.
- Étiquettes de formulaires partiellement manquantes sur le tunnel de commande.
- Amélioration en cours de la navigation au clavier.

## Voie de recours et signalement
Si vous constatez un défaut d’accessibilité vous empêchant d’accéder à un contenu ou une fonctionnalité du site, vous êtes invité à nous le signaler :
- Formulaire de contact accessibilité : contact@{nom_site.lower().replace(" ", "")}.com
- Référent accessibilité : conformite-accessibilite@{nom_site.lower().replace(" ", "")}.com

*Fait à Paris, le 24 septembre 2026.*
"""
