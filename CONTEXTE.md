# Mutuelle Alpine Assurances · Contexte du projet

## À quelle décision sert le système ?

La Mutuelle Alpine Assurances (MAA) est une mutuelle fictive grenobloise d’assurance auto et habitation. Elle reçoit environ 4 000 déclarations de sinistre par an. Ses quatre enquêteurs sélectionnent aujourd’hui les dossiers à examiner selon leur expérience. Le projet du cours de gouvernance et modélisation de la donnée consiste à construire, déployer et superviser une chaîne data et IA open source qui les aide à prioriser les revues.

Chaque déclaration reçoit un score et une orientation vers le circuit standard ou la revue renforcée. Un refus d’indemnisation relève d’une décision humaine. Pour chaque score, la mutuelle doit pouvoir retrouver les versions des données et du modèle, expliquer les facteurs à un gestionnaire et examiner les écarts de traitement entre groupes d’assurés. Le seuil de revue doit être justifié par la charge que les quatre enquêteurs peuvent absorber. Leur capacité chiffrée reste à établir.

**Équipe MAA** · BADIN-LÉGER Maxence, RASOLOFOARISON Valérie et Hammadi Sabrina. Le dépôt et les preuves de vérification permettent à chacun de reprendre le travail des deux autres.

## Quelles données utilise-t-on ?

| Source dans le kit | Usage et précaution |
| --- | --- |
| `sinistres_events.jsonl` | Flux historique de 12 080 événements. Les doublons de rejeu, montants mal formés et autres anomalies sont intentionnels. Conserver le brut pour pouvoir expliquer les corrections. |
| `assures.csv`, `contrats.csv`, `prestataires.csv` | Référentiels chargés par lots. Les données synthétiques d’identité et de contact se traitent comme des données personnelles. |
| `enquetes.csv` | Seuls les dossiers enquêtés ont une conclusion connue. Un dossier sans conclusion garde un label inconnu. L’historique reflète aussi les choix passés des enquêteurs. |
| `sinistres_events_2026_01.jsonl` | Lot de 800 déclarations réservé au diagnostic de dérive du L8. |
| `data/docs/` | Conditions générales auto et habitation et guide interne. Pour l’assistant documentaire, filtrer les passages du guide selon le profil `anti_fraude` dès la recherche. |

Le générateur du kit permet de reproduire les données avec `make data`. Les identifiants directs sont exclus de gold et de ML. Le sel de pseudonymisation reste hors du dépôt. Les colonnes `_audit_*` (âge, sexe, zone) sont réservées aux comparaisons d’équité et exclues des variables prédictives.

## Où chercher selon la demande ?

Les repères ci-dessous décrivent les **attendus du cours**. Vérifier leur réalisation sur la branche de travail avant d’annoncer un résultat. Le détail de chaque exercice et ses critères de fin figurent dans le [cahier de TP](https://github.com/Laudroid/Live_Gouvernance_modelisation/blob/main/03_TP_fil_rouge/03_cahier_TP_fil_rouge.pdf).

| Lot | Résultat à démontrer | Point d’entrée du dépôt |
| --- | --- | --- |
| L0 · Cadrage | Environnement opérationnel, un schéma des flux, couches, outils et consommateurs, dix lignes sur la réussite métier et un journal IA initialisé. | [Installation](docs/INSTALL.md), [architecture cible](docs/architecture.md), cible `docs/succes.md` |
| L1 · Ingestion | Déclarations via Kafka, quatre CSV en batch vers DuckDB. Bronze conserve le brut et sa provenance. Avec le jeu du kit, 12 080 événements et aucune ligne supplémentaire au rejeu. | `ingestion/`, `docker-compose.yml` |
| L2 · Modélisation | dbt type et dédoublonne en silver. En gold, une ligne par sinistre valide, avec dimensions assuré, contrat, prestataire et date. Cibles du kit : 11 883 valides, 117 rejets motivés et `dbt build` réussi. | `dbt/maa/models/` |
| L3 · Gouvernance | Catalogue, responsables et accès, RACI, registre RGPD, rétention et minimisation. Montrer la lignée de Kafka au modèle avec OpenLineage et Marquez et prouver que le contrat détecte une rupture de schéma. | `governance/`, `dbt/maa/` |
| L4 · Qualité et revue IA | Conditions d’entrée vérifiées avec Great Expectations, tests dbt dans la CI et évaluation des détections et faux positifs du relecteur local sur six défauts. | `quality/`, `dbt/maa/tests/`, `llm/eval_review_cases.md` |
| L5 · Modèle | Comparer au moins deux algorithmes en tenant compte de la rareté des fraudes et de la capacité de revue. Suivre les expériences et versionner le modèle retenu dans MLflow. | `ml/` |
| L6 · Assistant documentaire | Réponses sourcées ou abstention, droits d’accès dans la recherche, dix questions de test. Évaluer aussi l’apport d’une similarité avec les fraudes déjà confirmées à la date du sinistre. | `rag/`, `data/docs/` |
| L7 · API | FastAPI sous Docker expose `/score`, `/health` et `/metrics`. Le score porte une orientation, une version de modèle et un identifiant de trace. Au moins quatre tests pytest. | `api/`, `docker-compose.yml` |
| L8 · Supervision | Tableau de bord technique et métier, trois alertes au minimum dont une métier, diagnostic des causes de dérive en janvier 2026 et politique de réentraînement. | `monitoring/` |
| L9 · Éthique | Expliquer les scores avec SHAP, comparer les groupes avec Fairlearn, tester une atténuation et évaluer l’anonymisation. Argumenter la qualification AI Act, l’article 22 du RGPD et la correspondance ISO 42001. | `ethics/`, `governance/` |

L’orchestration avec Dagster est un bonus. Pour les commandes et les solutions de repli prévues par le kit, consulter le [Makefile](Makefile) et le [guide d’installation](docs/INSTALL.md).

## Qu’attend-on de l’équipe à la remise ?

- **Jalons.** Après J1, présenter le modèle en étoile et un build dbt réussi. Après J2, présenter le dossier de gouvernance et la première qualification AI Act. Après J3, montrer l’API et le tableau de bord et préparer la première version du rapport d’éthique.
- **Dépôt final.** Remettre le lien et le tag `v1.0` la veille de J4 au plus tard à 23 h 59. Un clone neuf doit permettre de relancer la chaîne à partir du README. Inclure les preuves de gouvernance, de tests, de versionnement, de supervision et de dérive, le rapport d’éthique de 8 à 12 pages et le journal IA avec bilan.
- **Soutenance.** 20 minutes de présentation, dont 10 de démonstration en direct depuis une déclaration jusqu’au score, au tableau de bord et à l’explication SHAP. Suivent 15 minutes de questions individuelles. Chaque membre doit pouvoir expliquer les choix, leurs limites et le travail du groupe.
- **Évaluation.** Le barème d’équipe sur 20 couvre la gouvernance (4), les pipelines (4), le modèle et son déploiement (4), la supervision (3), l’IA générative (2) et l’éthique (3). Le journal doit documenter au moins dix usages, les corrections ou refus réels, les vérifications et un bilan final. La grille détaille la modulation individuelle et les causes de zéro sur un critère. [Grille d’évaluation](https://github.com/Laudroid/Live_Gouvernance_modelisation/blob/main/03_TP_fil_rouge/04_grille_evaluation.pdf)
