# Rapport d'Audit Référentiels RFE France — DEMO_20_FICHES.csv
**Date :** 2026-09-29 · **Cadre Réglementaire :** Réforme Facturation Électronique (DGFiP / Factur-X)
**Périmètre du contrôle :** contrôles algorithmiques hors ligne (clés Luhn/TVA, doublons) — sans rapprochement SIRENE

## 1. Synthèse de Conformité
| Indicateur | Résultat | Statut |
|---|---|---|
| Fiches traitées | **20** | Base totale |
| Fiches prêtes à l'émission | **0** (0.0%) | 🔴 Blocages majeurs détectés |
| Erreurs SIREN / SIRET | **36** | Rejet immédiat sur l'annuaire |
| Erreurs TVA intracommunautaire | **18** | Risque d'invalidation fiscale |
| Doublons détectés | **2** | Risque de multi-routage |

## 2. Risques Financiers pour l'Entreprise
- **Pénalités de conformité :** 50 € par facture émise hors format électronique (plafond 15 000 €/an), dès l'obligation d'émission : 1er septembre 2026 pour les grandes entreprises et ETI, 1er septembre 2027 pour les PME et micro-entreprises (loi de finances 2026).
- **Impact immédiat :** 20 fiches tiers nécessitent une remédiation avant injection dans votre PDP.

## 3. Plan d'Action Recommandé
1. Correction des SIREN/SIRET invalides et dérivation des numéros de TVA conformes.
2. Ce rapport est hors ligne : le rapprochement SIRENE (radiations, raisons sociales) s'exécute avec l'option `--online`.
3. Fusion des fiches doublons.

## 4. Échantillon des Anomalies
| Ligne | Nom | SIREN | Erreurs Détectées |
|---|---|---|---|
| 2 | STE EXEMPLE BETA | 123456789 | SIREN_INVALID(Échec contrôle Luhn), SIRET_INVALID(Échec contrôle Luhn), TVA_INVALID(Clé erronée (40 ≠ attendu 32)) |
| 3 | GARAGE DUPONT & FILS | 804556219 | SIREN_INVALID(Échec contrôle Luhn), SIRET_INVALID(Échec contrôle Luhn), TVA_INVALID(Clé erronée (40 ≠ attendu 15)) |
| 4 | BOULANGERIE MARTIN | 803245672 | SIREN_INVALID(Échec contrôle Luhn), SIRET_INVALID(Échec contrôle Luhn), TVA_INVALID(Clé erronée (40 ≠ attendu 75)) |
| 5 | Boulangerie Martin SAS | 803245672 | SIREN_INVALID(Échec contrôle Luhn), SIRET_INVALID(Échec contrôle Luhn), TVA_INVALID(Clé erronée (40 ≠ attendu 75)), DOUBLON_AVEC_LIGNE_4 |
| 6 | MENUISERIE LEBRUN | 902133458 | SIREN_INVALID(Échec contrôle Luhn), SIRET_INVALID(Échec contrôle Luhn), TVA_INVALID(Clé erronée (40 ≠ attendu 88)) |
| 7 | SARL TECH SOLUTIONS | 903881245 | SIREN_INVALID(Échec contrôle Luhn), SIRET_INVALID(Échec contrôle Luhn), TVA_INVALID(Format invalide (attendu FR + 2 chiffres + 9 chiffres SIREN)) |
| 8 | PHARMACIE CENTRALE | 509447112 | SIREN_INVALID(Échec contrôle Luhn), SIRET_INVALID(Échec contrôle Luhn), TVA_INVALID(Clé erronée (50 ≠ attendu 36)) |
| 9 | CABINET MOREL CONSEIL | 752290884 | SIREN_INVALID(Échec contrôle Luhn), SIRET_INVALID(Échec contrôle Luhn), TVA_INVALID(Clé erronée (40 ≠ attendu 48)) |
| 10 | FLEURISTE LA ROSE | 821993507 | SIREN_INVALID(Échec contrôle Luhn) |
| 11 | TRANSPORTS DUPONT (radiée) | 891004437 | SIREN_INVALID(Échec contrôle Luhn), SIRET_INVALID(Échec contrôle Luhn), TVA_INVALID(Clé erronée (40 ≠ attendu 37)) |
| 12 | RESTAURANT LE GOURMET | 843712609 | SIREN_INVALID(Échec contrôle Luhn), SIRET_INVALID(Échec contrôle Luhn), TVA_INVALID(Clé erronée (40 ≠ attendu 51)) |
| 13 | AGENCE IMMO HORIZON | 884520331 | SIREN_INVALID(Échec contrôle Luhn), SIRET_INVALID(Échec contrôle Luhn), TVA_INVALID(Clé erronée (40 ≠ attendu 02)) |
| 14 | Agence Immo Horizon | 884520331 | SIREN_INVALID(Échec contrôle Luhn), SIRET_INVALID(Échec contrôle Luhn), TVA_INVALID(Clé erronée (40 ≠ attendu 02)), DOUBLON_AVEC_LIGNE_13 |
| 15 | PRESSING NETPLUS | 875601442 | SIREN_INVALID(Échec contrôle Luhn), SIRET_INVALID(Échec contrôle Luhn) |
| 16 | AUTO-ECOLE CONDUITE+ | 853940221 | SIREN_INVALID(Échec contrôle Luhn), SIRET_INVALID(Échec contrôle Luhn), TVA_INVALID(Clé erronée (40 ≠ attendu 41)) |