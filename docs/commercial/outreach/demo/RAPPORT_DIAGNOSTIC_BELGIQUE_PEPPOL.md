# Rapport de Diagnostic Peppol Belgique — DEMO_BELGIUM_PEPPOL_20_FICHES.csv
**Date :** 2026-09-29 · **Cadre :** Arrêté Royal Facturation Électronique B2B Obligatoire
**Périmètre du contrôle :** contrôles algorithmiques hors ligne (Modulo 97, TVA, codes postaux, doublons) — l'inscription effective à l'annuaire Peppol se vérifie via les liens fournis dans le CSV

## 1. Synthèse de Conformité Peppol
| Indicateur | Valeur | Statut |
|---|---|---|
| Total fiches auditées | **20** | Base totale |
| Fiches 100% compatibles Peppol | **3** (15.0%) | 🔴 Risque de rejet de facturation |
| Numéros BCE / KBO invalides | **16** | Risque d'amende 1 500 € à 5 000 € |
| Numéros de TVA invalides | **14** | Risque de non-déductibilité TVA |
| Doublons détectés | **2** | Risque d'incohérence comptable |

## 2. Risques Financiers Immédiats
Depuis le 1er janvier 2026 (fin de la tolérance au 31 mars 2026) :
- 17 fiches bloqueront les flux entrants/sortants sur Exact Online, WinBooks ou Clearfacts.
- Amendes administratives jusqu'à 5 000 € par infraction constatée par le SPF Finances.

## 3. Échantillon des Anomalies
| Ligne | Nom | BCE | Erreurs Détectées |
|---|---|---|---|
| 5 | Boulangerie Saint-Aubain SA | 0435.889.195 | DOUBLON_AVEC_LIGNE_4 |
| 6 | Menuiserie Mosane SPRL | 0465.191.244 | BCE_INVALID(Échec Modulo 97 (trouvé=44, attendu=14)), TVA_INVALID(TVA invalide: Échec Modulo 97 (trouvé=44, attendu=14)) |
| 7 | Tech Solutions Bruxelles | 0892.456.789 | BCE_INVALID(Échec Modulo 97 (trouvé=89, attendu=15)), TVA_INVALID(TVA invalide: Échec Modulo 97 (trouvé=89, attendu=15)) |
| 8 | Pharmacie du Centre | 0402.891.234 | BCE_INVALID(Échec Modulo 97 (trouvé=34, attendu=80)), TVA_INVALID(TVA invalide: Échec Modulo 97 (trouvé=34, attendu=80)) |
| 9 | Transport & Logistique Hainaut | 0451.923.473 | BCE_INVALID(Échec Modulo 97 (trouvé=73, attendu=93)), TVA_INVALID(TVA invalide: Échec Modulo 97 (trouvé=73, attendu=93)) |
| 10 | Boucherie des Ardennes | 0821.993.570 | BCE_INVALID(Échec Modulo 97 (trouvé=70, attendu=39)) |
| 11 | Societe Radiée SPRL (Ancienne) | 0891.004.422 | BCE_INVALID(Échec Modulo 97 (trouvé=22, attendu=85)), TVA_INVALID(TVA invalide: Échec Modulo 97 (trouvé=22, attendu=85)) |
| 12 | Restaurant Leffe Dinant | 0843.712.656 | BCE_INVALID(Échec Modulo 97 (trouvé=56, attendu=31)), TVA_INVALID(TVA invalide: Échec Modulo 97 (trouvé=56, attendu=31)) |
| 13 | Immobiliere Namuroise | 0884.520.318 | BCE_INVALID(Échec Modulo 97 (trouvé=18, attendu=33)), TVA_INVALID(TVA invalide: Échec Modulo 97 (trouvé=18, attendu=33)) |
| 14 | Immobilière Namuroise SA | 0884.520.318 | BCE_INVALID(Échec Modulo 97 (trouvé=18, attendu=33)), TVA_INVALID(TVA invalide: Échec Modulo 97 (trouvé=18, attendu=33)), DOUBLON_AVEC_LIGNE_13 |
| 15 | Nettoyage Industriel Wallonie | 0875.601.442 | BCE_INVALID(Échec Modulo 97 (trouvé=42, attendu=79)) |
| 16 | Auto-Ecole Conduite Pro | 0853.940.245 | BCE_INVALID(Échec Modulo 97 (trouvé=45, attendu=90)), TVA_INVALID(TVA invalide: Échec Modulo 97 (trouvé=45, attendu=90)) |
| 17 | Electricite & Câblage Sambre | 0904.018.876 | BCE_INVALID(Échec Modulo 97 (trouvé=76, attendu=18)), TVA_INVALID(TVA invalide: Échec Modulo 97 (trouvé=76, attendu=18)) |
| 18 | Brasserie Artisanale d'Ecaussinnes | 0862.774.020 | BCE_INVALID(Échec Modulo 97 (trouvé=20, attendu=22)), TVA_INVALID(TVA invalide: Échec Modulo 97 (trouvé=20, attendu=22)) |
| 19 | Studio Graphique & Print | 0899.201.388 | BCE_INVALID(Échec Modulo 97 (trouvé=88, attendu=81)), TVA_INVALID(TVA invalide: Échec Modulo 97 (trouvé=88, attendu=81)) |