# Modèle — Accord de confidentialité et de traitement des données (NDA + DPA)

> **⚠️ À valider par un juriste avant toute signature.** Ce texte est un squelette de
> travail pour la prestation « fiabilisation de référentiels tiers » vendue depuis l'Algérie
> à des cabinets et entreprises de l'UE. Il ne constitue pas un avis juridique. Les champs
> `[…]` sont à compléter. Référence de fond : clauses contractuelles types de la Commission
> européenne (décision 2021/914) et fiches CNIL sur les transferts hors UE.
>
> **Pourquoi ce fichier existe :** le guide de terrain promettait un « DPA » qui n'existait
> nulle part dans le dépôt, et affirmait « zéro donnée personnelle » alors que l'offre
> confirme des contacts de facturation (nom, e-mail) — qui sont des données personnelles.
> Un modèle honnête vaut mieux qu'une promesse.

---

## 1. Parties

- **Client (responsable de traitement) :** `[Raison sociale]`, `[SIREN/BCE]`, `[adresse]`, représenté par `[nom, fonction]`.
- **Prestataire (sous-traitant) :** Houssam Benmerah, prestataire de services numériques, `[statut : auto-entrepreneur — carte ANAE n° … / à compléter après obtention]`, `[adresse]`, Algérie.

## 2. Objet et périmètre

Le Prestataire réalise, pour le Client, un contrôle et un assainissement de fichiers de tiers (clients / fournisseurs) en vue de la facturation électronique : validation d'identifiants d'entreprise (SIREN/SIRET/TVA/BCE), dédoublonnage, normalisation d'adresses postales, rapprochement avec des bases publiques d'entreprises (SIRENE, KBO).

**Hors périmètre (exclusion expresse) :** tenue de comptabilité, écritures, déclarations fiscales, conseil fiscal ou juridique, paramétrage des outils du Client. Le Prestataire n'accède à aucun système du Client ; il traite uniquement un export fichier transmis par le Client.

## 3. Données traitées

| Catégorie | Exemples | Personnelles ? |
|---|---|---|
| Identifiants d'entreprise | SIREN, SIRET, n° TVA, BCE/KBO, raison sociale, adresse du siège | Non (personnes morales), **sauf** entreprises individuelles (nom du dirigeant = donnée personnelle) |
| Contacts de facturation | nom, prénom, e-mail, téléphone professionnel | **Oui** |
| Données financières | aucune (montants, RIB/IBAN exclus du périmètre) | — |

Le Client s'engage à **retirer les colonnes non nécessaires** (IBAN, montants, données de santé, etc.) avant transmission. Le Prestataire supprime sans traitement toute colonne hors périmètre reçue par erreur et en informe le Client.

## 4. Base et finalité

Traitement pour le compte du Client, sur instruction documentée (le présent accord et le bon de commande), à la seule finalité de mise en conformité des référentiels pour la facturation électronique. Aucune réutilisation, aucun enrichissement à des fins propres, aucune constitution de base par le Prestataire.

## 5. Transfert hors Union européenne

Le Prestataire est établi en Algérie, pays ne bénéficiant pas d'une décision d'adéquation. Les parties conviennent :

1. d'annexer les **clauses contractuelles types** (module « responsable → sous-traitant ») de la décision d'exécution (UE) 2021/914 ; **ou**
2. à défaut, de limiter la transmission aux seules données de personnes morales (colonnes contacts retirées), le Client conservant la vérification des contacts.

`[Option retenue : ☐ 1 ☐ 2 — à cocher après avis juridique]`

## 6. Sécurité

- Transmission par canal chiffré (lien de partage protégé ou pièce jointe chiffrée ; mot de passe transmis par un autre canal).
- Traitement sur un poste dédié, disque chiffré, sans copie sur service tiers (aucun envoi du fichier à une API externe autre que les bases publiques d'entreprises, interrogées **par identifiant d'entreprise uniquement**).
- Journal des accès tenu par le Prestataire et fourni au Client sur demande.

## 7. Durée de conservation et suppression

Suppression définitive du fichier source, des fichiers intermédiaires et des livrables **au plus tard `[15]` jours** après acceptation de la livraison, avec confirmation écrite. Le Client peut demander une suppression anticipée à tout moment.

## 8. Sous-traitance ultérieure

Aucune. Toute évolution requiert l'accord écrit préalable du Client.

## 9. Assistance et incidents

Le Prestataire informe le Client de toute violation de données dans les **`[48]` heures** suivant sa découverte et l'assiste dans ses obligations (notification, réponse aux personnes concernées).

## 10. Confidentialité (NDA)

Le Prestataire s'interdit toute divulgation des données, fichiers, listes de tiers et informations commerciales du Client, pendant la mission et **`[3]` ans** après. Les livrables anonymisés (statistiques agrégées sans nom de tiers) peuvent être utilisés comme référence uniquement avec l'accord écrit du Client.

## 11. Audit et documentation

Le Client peut demander la documentation des traitements (outils utilisés, versions, journaux). Les outils sont déterministes et publics (`tools/hard_currency_engine`, dépôt NAAS-Agentic-Core) ; aucun modèle d'IA générative n'intervient dans le traitement des données.

## 12. Droit applicable et durée

`[Droit applicable et juridiction — à déterminer avec le juriste ; la plateforme d'intermédiation (Malt) impose ses propres conditions pour les missions qu'elle porte.]`

---

Fait en deux exemplaires, le `[date]`.

| Pour le Client | Pour le Prestataire |
|---|---|
| `[nom, fonction, signature]` | Houssam Benmerah |
