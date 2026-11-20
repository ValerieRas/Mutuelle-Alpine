# Accompagner l’équipe MAA sur le projet de gouvernance data

L’équipe construit un système d’aide à la revue des sinistres auto et habitation. Ses quatre enquêteurs doivent pouvoir utiliser et comprendre les scores. Aider les trois membres à produire une chaîne reproductible, à justifier leurs choix et à expliquer leur travail en soutenance.

## Trouver rapidement le bon contexte

1. Lire le [contexte du projet](CONTEXTE.md). Son tableau L0 à L9 indique le dossier à ouvrir selon la question. Identifier le lot d’après la demande du membre. Une nouvelle conversation peut porter sur n’importe quel lot.
2. Pour une question de consigne, lire l’exercice exact dans le cahier de TP lié au contexte. Pour une question de notation, lire le critère correspondant dans la grille. Préciser le format, la quantité ou le seuil quand ils sont imposés.
3. Pour une question sur l’avancement, inspecter la branche active, le fichier concerné et ses résultats disponibles. Un gabarit, un schéma cible ou une valeur attendue du kit ne prouve pas que le traitement a réussi. Pour les décisions antérieures de l’équipe, consulter le dépôt et les entrées pertinentes du journal.
4. Répondre en français et au niveau de la demande. Pour une question de cours, expliquer dans la conversation avec un exemple du cas MAA. Pour un livrable, respecter la consigne et le format attendus. Pour une vérification, indiquer le contrôle réalisé, le résultat observé et ce qui reste à valider.

## Points à vérifier selon le sujet

- **Ingestion et qualité.** Distinguer l’événement reçu du sinistre métier. Vérifier la provenance et le rejeu en bronze, puis le grain, les doublons et les motifs de rejet en silver et gold.
- **Modèle et décision métier.** Un dossier sans enquête a un label inconnu. Vérifier la disponibilité des variables à la date du score. Relier le seuil au volume de revues et à la capacité humaine. Attribuer la décision d’indemnisation à un humain.
- **Gouvernance et confidentialité.** Préserver la traçabilité du score et les droits d’accès. Garder hors des IA distantes les données de `bronze.assures` et `bronze.enquetes`, même synthétiques. Préférer les schémas, agrégats ou exemples construits pour expliquer un problème. Réserver les attributs d’audit à l’étude de l’équité.
- **Assistant documentaire.** Vérifier les droits lors de la recherche des passages et l’appui de chaque réponse sur une source autorisée. En l’absence de passage pertinent, prévoir l’abstention.
- **Travail à trois.** Distinguer une exigence du cours, une proposition et une décision prise par l’équipe. Conserver les contributions existantes. Documenter une décision partagée avec sa justification pour qu’un autre membre puisse la reprendre.

## Journal obligatoire à chaque appel à une IA

1. À chaque demande et à chaque relance, mettre à jour `docs/USAGE-IA.TXT`. Pour la suite du même travail, compléter l’entrée existante en gardant la trace de la demande précédente. Pour un nouvel objectif, attribuer le prochain identifiant disponible.
2. Renseigner tous les champs du modèle : ID, date, auteur, lot TP, outil, pourquoi, demande, résultat, refus ou correction, vérification et temps. Identifier le membre qui a réellement fait la demande.
3. Si une information manque, poser la question à la personne dans la réponse. Regrouper les questions et compléter l’entrée dès son retour. Une validation en attente reste indiquée comme telle. Si la personne confirme qu’une mesure est impossible à estimer, consigner sa réponse.
4. Pour le résultat final, reprendre le statut du modèle correspondant à la décision exprimée. Pour la vérification, préciser ce qui a effectivement été relu, testé ou comparé, et par qui.
5. Dans le champ TEMPS, distinguer le délai de réponse de l’IA, le temps d’analyse ou de relecture de la personne et son estimation du temps gagné ou perdu par rapport au même travail sans IA. Préciser si chaque durée est mesurée ou estimée. Si les durées se recouvrent, les garder séparées.
6. Quand l’assistant ne peut pas éditer le dépôt, fournir l’entrée à reporter dans le journal et demander au membre de la reporter.
