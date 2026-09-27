#!/usr/bin/env python3
"""
Module CBAM Calculator — Hard Currency Engine
Calculateur d'arbitrage carbone et générateur de déclarations XML pour le Mécanisme d'Ajustement Carbone aux Frontières (UE).
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from xml.dom import minidom

CBAM_CATALOG = {
    "72071114": {
        "nom": "Billettes d'acier non allié (Filière DRI-EAF)",
        "secteur": "Acier / Fer",
        "see_default": 1.629,
        "see_actual_dz": 0.950,
        "bm_free_alloc": 0.453,
        "installation_nom": "Tosyali Iron Steel Industry Algerie SPA",
        "installation_pays": "DZ",
        "installation_coordonnees": "35.807, -0.278",
    },
    "72142000": {
        "nom": "Ronds à béton crénelés (Rebar)",
        "secteur": "Acier / Construction",
        "see_default": 1.780,
        "see_actual_dz": 1.050,
        "bm_free_alloc": 0.410,
        "installation_nom": "Algerian Qatari Steel (AQS)",
        "installation_pays": "DZ",
        "installation_coordonnees": "36.758, 6.042",
    },
    "31021000": {
        "nom": "Urée contenant plus de 45% d'azote",
        "secteur": "Engrais azotés",
        "see_default": 1.340,
        "see_actual_dz": 0.880,
        "bm_free_alloc": 0.380,
        "installation_nom": "Sorfert Algerie SPA",
        "installation_pays": "DZ",
        "installation_coordonnees": "35.815, -0.290",
    },
    "28141000": {
        "nom": "Ammoniac anhydre",
        "secteur": "Engrais / Chimie",
        "see_default": 2.250,
        "see_actual_dz": 1.720,
        "bm_free_alloc": 0.520,
        "installation_nom": "Fertial Annaba / Sorfert",
        "installation_pays": "DZ",
        "installation_coordonnees": "36.850, 7.760",
    },
    "25231000": {
        "nom": "Clinkers de ciment",
        "secteur": "Ciment",
        "see_default": 0.870,
        "see_actual_dz": 0.760,
        "bm_free_alloc": 0.693,
        "installation_nom": "GICA Biskra / LafargeHolcim Algérie",
        "installation_pays": "DZ",
        "installation_coordonnees": "34.850, 5.730",
    },
    "72083900": {
        "nom": "Produits laminés plats en fer/acier (Coils à chaud)",
        "secteur": "Acier / Produits plats",
        "see_default": 2.100,
        "see_actual_dz": 1.150,
        "bm_free_alloc": 0.510,
        "installation_nom": "Tosyali Iron Steel Industry Algerie SPA (Bethioua)",
        "installation_pays": "DZ",
        "installation_coordonnees": "35.807, -0.278",
    },
    "72131000": {
        "nom": "Fil machine (Wire rod) crénelé en couronnes",
        "secteur": "Acier / Produits longs",
        "see_default": 1.850,
        "see_actual_dz": 1.080,
        "bm_free_alloc": 0.430,
        "installation_nom": "Algerian Qatari Steel (AQS Bellara)",
        "installation_pays": "DZ",
        "installation_coordonnees": "36.758, 6.042",
    },
    "25232900": {
        "nom": "Ciment Portland ordinaire gris",
        "secteur": "Ciment",
        "see_default": 0.760,
        "see_actual_dz": 0.620,
        "bm_free_alloc": 0.540,
        "installation_nom": "Groupe Industriel des Ciments d'Algérie (GICA)",
        "installation_pays": "DZ",
        "installation_coordonnees": "36.700, 3.050",
    },
    "31023090": {
        "nom": "Nitrate d'ammonium",
        "secteur": "Engrais azotés",
        "see_default": 1.550,
        "see_actual_dz": 0.990,
        "bm_free_alloc": 0.440,
        "installation_nom": "Fertial Annaba / Arzew",
        "installation_pays": "DZ",
        "installation_coordonnees": "36.850, 7.760",
    },
    "76011000": {
        "nom": "Aluminium non allié sous forme brute (Lingots)",
        "secteur": "Aluminium",
        "see_default": 8.600,
        "see_actual_dz": 4.200,
        "bm_free_alloc": 1.450,
        "installation_nom": "Complexe Métallurgique Algérien",
        "installation_pays": "DZ",
        "installation_coordonnees": "36.750, 5.050",
    },
}

CBAM_FACTOR_2026 = 0.975
CERT_PRICE_DEFAULT = 75.0
PENALTY_RATE = 100.0


def calculate_cbam(
    hs_code: str,
    tonnes: float,
    see_override: float | None = None,
    cert_price: float = CERT_PRICE_DEFAULT,
) -> dict:
    if hs_code not in CBAM_CATALOG:
        raise ValueError(f"Code SH {hs_code} non répertorié.")

    item = CBAM_CATALOG[hs_code]
    see_act = see_override if see_override is not None else item["see_actual_dz"]
    see_def = item["see_default"]
    bm = item["bm_free_alloc"]

    exp_factor = 1.0 - CBAM_FACTOR_2026

    net_def_t = max(0.0, see_def - bm * CBAM_FACTOR_2026) * exp_factor
    net_act_t = max(0.0, see_act - bm * CBAM_FACTOR_2026) * exp_factor

    cost_def = tonnes * net_def_t * cert_price
    cost_act = tonnes * net_act_t * cert_price

    saving_total = cost_def - cost_act
    penalty_avoided = tonnes * see_act * PENALTY_RATE

    return {
        "code_hs": hs_code,
        "produit": item["nom"],
        "secteur": item["secteur"],
        "installation": item["installation_nom"],
        "pays_origine": item["installation_pays"],
        "tonnes": tonnes,
        "prix_certificat": cert_price,
        "see_default": see_def,
        "see_actual": see_act,
        "gain_carbone_tonne": see_def - see_act,
        "cout_default": cost_def,
        "cout_actual": cost_act,
        "economie_totale": saving_total,
        "economie_par_tonne": saving_total / tonnes if tonnes > 0 else 0.0,
        "penalite_evitee": penalty_avoided,
    }


def generate_sensitivity_table(res: dict) -> list[dict]:
    """Analyse de sensibilité financière selon différents cours du quota carbone EU ETS."""
    prices = [65.0, 75.0, 85.0, 95.0, 105.0]
    out = []
    tonnes = res["tonnes"]
    see_def = res["see_default"]
    see_act = res["see_actual"]
    item = CBAM_CATALOG.get(res["code_hs"], {})
    bm = item.get("bm_free_alloc", 0.45)
    exp_factor = 1.0 - CBAM_FACTOR_2026
    net_def_t = max(0.0, see_def - bm * CBAM_FACTOR_2026) * exp_factor
    net_act_t = max(0.0, see_act - bm * CBAM_FACTOR_2026) * exp_factor

    for p in prices:
        cost_def = tonnes * net_def_t * p
        cost_act = tonnes * net_act_t * p
        sav = cost_def - cost_act
        out.append(
            {
                "prix_co2": p,
                "cout_defaut": cost_def,
                "cout_reel": cost_act,
                "economie_eur": sav,
            }
        )
    return out


def calculate_cbam_batch(manifest_rows: list[dict], cert_price: float = CERT_PRICE_DEFAULT) -> dict:
    """Calcul consolidé pour un manifeste de cargaison multi-produits."""
    items = []
    total_tonnes = 0.0
    total_saving = 0.0
    total_def_cost = 0.0
    total_act_cost = 0.0

    for row in manifest_rows:
        hs = str(row.get("code_hs") or row.get("hs") or "").strip()
        if hs not in CBAM_CATALOG:
            continue
        t = float(row.get("tonnes") or 0.0)
        see_ov = float(row["see_actual"]) if row.get("see_actual") else None
        single_res = calculate_cbam(hs, t, see_override=see_ov, cert_price=cert_price)
        items.append(single_res)
        total_tonnes += t
        total_saving += single_res["economie_totale"]
        total_def_cost += single_res["cout_default"]
        total_act_cost += single_res["cout_actual"]

    return {
        "nb_lignes": len(items),
        "total_tonnes": total_tonnes,
        "total_cout_defaut": total_def_cost,
        "total_cout_reel": total_act_cost,
        "economie_globale_eur": total_saving,
        "lignes": items,
    }


def generate_cbam_xml(res: dict, declarant_eori: str = "FR12345678900012") -> str:
    """Génère un extrait XML conforme au portail déclaratif CBAM de la Commission Européenne."""
    root = ET.Element(
        "CBAMDeclaration",
        attrib={
            "xmlns": "urn:eu:cbam:v1:declaration",
            "regulation": "EU-2023-956",
            "year": "2026",
        },
    )

    declarant = ET.SubElement(root, "AuthorisedDeclarant")
    ET.SubElement(declarant, "EORINumber").text = declarant_eori
    ET.SubElement(declarant, "Role").text = "IMPORTER"

    goods_item = ET.SubElement(root, "ImportedGoodsItem")
    ET.SubElement(goods_item, "CNCode").text = res["code_hs"]
    ET.SubElement(goods_item, "Description").text = res["produit"]
    ET.SubElement(goods_item, "MassInTonnes").text = f"{res['tonnes']:.2f}"
    ET.SubElement(goods_item, "CountryOfOrigin").text = res["pays_origine"]

    installation = ET.SubElement(goods_item, "ProductionInstallation")
    ET.SubElement(installation, "Name").text = res["installation"]
    ET.SubElement(installation, "Country").text = res["pays_origine"]

    emissions = ET.SubElement(goods_item, "EmbeddedEmissions")
    ET.SubElement(emissions, "CalculationMethod").text = "ACTUAL_INSTALLATION_DATA"
    ET.SubElement(emissions, "SpecificDirectEmissions").text = f"{res['see_actual']:.4f}"
    ET.SubElement(emissions, "SpecificIndirectEmissions").text = "0.0000"
    ET.SubElement(emissions, "DefaultValueAvoided").text = f"{res['see_default']:.4f}"

    financial = ET.SubElement(goods_item, "FinancialImpact")
    ET.SubElement(
        financial, "TotalCertificatesRequired"
    ).text = f"{(res['cout_actual'] / res['prix_certificat']):.2f}"
    ET.SubElement(financial, "CarbonCostSavingsEUR").text = f"{res['economie_totale']:.2f}"

    rough_string = ET.tostring(root, "utf-8")
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="  ")


def generate_cbam_batch_xml(batch_res: dict, declarant_eori: str = "FR12345678900012") -> str:
    """Génère une déclaration consolidée multi-marchandises conforme au registre CBAM européen."""
    root = ET.Element(
        "CBAMDeclaration",
        attrib={
            "xmlns": "urn:eu:cbam:v1:declaration",
            "regulation": "EU-2023-956",
            "year": "2026",
        },
    )

    declarant = ET.SubElement(root, "AuthorisedDeclarant")
    ET.SubElement(declarant, "EORINumber").text = declarant_eori
    ET.SubElement(declarant, "Role").text = "IMPORTER"

    summary = ET.SubElement(root, "DeclarationSummary")
    ET.SubElement(summary, "TotalGoodsItems").text = str(batch_res.get("nb_lignes", 0))
    ET.SubElement(summary, "TotalMassTonnes").text = f"{batch_res.get('total_tonnes', 0.0):.2f}"
    ET.SubElement(
        summary, "TotalSavingsEUR"
    ).text = f"{batch_res.get('economie_globale_eur', 0.0):.2f}"

    for item in batch_res.get("lignes", []):
        goods_item = ET.SubElement(root, "ImportedGoodsItem")
        ET.SubElement(goods_item, "CNCode").text = item["code_hs"]
        ET.SubElement(goods_item, "Description").text = item["produit"]
        ET.SubElement(goods_item, "MassInTonnes").text = f"{item['tonnes']:.2f}"
        ET.SubElement(goods_item, "CountryOfOrigin").text = item["pays_origine"]

        installation = ET.SubElement(goods_item, "ProductionInstallation")
        ET.SubElement(installation, "Name").text = item["installation"]
        ET.SubElement(installation, "Country").text = item["pays_origine"]

        emissions = ET.SubElement(goods_item, "EmbeddedEmissions")
        ET.SubElement(emissions, "CalculationMethod").text = "ACTUAL_INSTALLATION_DATA"
        ET.SubElement(emissions, "SpecificDirectEmissions").text = f"{item['see_actual']:.4f}"
        ET.SubElement(emissions, "SpecificIndirectEmissions").text = "0.0000"
        ET.SubElement(emissions, "DefaultValueAvoided").text = f"{item['see_default']:.4f}"

        financial = ET.SubElement(goods_item, "FinancialImpact")
        cert_p = item["prix_certificat"] if item.get("prix_certificat") else 75.0
        ET.SubElement(
            financial, "TotalCertificatesRequired"
        ).text = f"{(item['cout_actual'] / cert_p):.2f}"
        ET.SubElement(financial, "CarbonCostSavingsEUR").text = f"{item['economie_totale']:.2f}"

    rough_string = ET.tostring(root, "utf-8")
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="  ")
