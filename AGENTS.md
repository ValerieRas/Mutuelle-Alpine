# Accompagner l’équipe MAA sur le projet de gouvernance data

L’équipe construit un système d’aide à la revue des sinistres auto et habitation. Ses quatre enquêteurs doivent pouvoir utiliser et comprendre les scores. Aider les trois membres à produire une chaîne reproductible, à justifier leurs choix et à expliquer leur travail en soutenance.

## Trouver rapidement le bon contexte

1. Lire le [contexte du projet](CONTEXTE.md). Son tableau L0 à L9 indique le dossier à ouvrir selon la question. Identifier le lot d’après la demande du membre. Une nouvelle conversation peut porter sur n’importe quel lot.
2. Pour une question de consigne, lire l’exercice exact dans le cahier de TP lié au contexte. Pour une question de notation, lire le critère correspondant dans la grille. Préciser le format, la quantité ou le seuil quand ils sont imposés.
3. Pour une question sur l’avancement, inspecter la branche active, le fichier concerné et ses résultats disponibles. Un gabarit, un schéma cible ou une valeur attendue du kit ne prouve pas que le traitement a réussi. Pour les décisions antérieures de l’équipe, consulter le dépôt et les entrées pertinentes du journal.
4. Répondre en français et au niveau de la demande. Pour une question de cours, expliquer dans la conversation avec un exemple du cas MAA. Pour un livrable, respecter la consigne et le format attendus. Pour une vérification, indiquer le contrôle réalisé, le résultat observé et ce qui reste à valider.

## Priorité des consignes et livrables

- Les consignes explicites du cours et du cahier de TP priment sur les conventions de `AGENTS.md`, de `CONTEXTE.md` et du README : respecter le contenu, le format, la quantité et les chemins de livraison demandés.
- Lorsqu’une question demande un livrable documentaire, créer le fichier dans `docs/`, sauf si le cours impose un autre emplacement. Y écrire la réponse finale et signaler son chemin dans la conversation.
- Si l’énoncé donne un nom de fichier, utiliser exactement ce nom : pour L0, exercice 4, `docs/architecture.md` ; pour L0, exercice 5, `docs/succes.md`.
- Si aucun nom n’est imposé, choisir un nom correspondant à l’intitulé de l’exercice, en minuscules, sans accents ni espaces, avec des tirets entre les mots et l’extension `.md` pour une réponse textuelle.

## Git et branches

- Sans validation explicite du livrable concerné, ne pas créer de commit ni effectuer de push. Garder les modifications locales pour leur relecture par l’équipe.
- Quand le membre valide explicitement un livrable, cette validation autorise les commits, le push et la création de la pull request (PR) pour ce livrable et son journal IA. Vérifier l’état Git et les diffs, effectuer les contrôles adaptés, puis committer et pousser les modifications concernées. Préserver les modifications étrangères au livrable.
- Si les commits sont déjà créés, pousser seulement ceux qui restent locaux ; s’ils sont déjà poussés, créer directement la PR. Dans tous les cas, créer une PR après validation, ou mettre à jour la PR existante pour la même branche et la même cible sans créer de doublon. Si aucun diff ne permet de créer une PR, signaler ce constat sans fabriquer de changement.
- Respecter les conventions de commit et de PR du dépôt ainsi que sa branche cible. Le titre et la description de la PR doivent correspondre au diff réel et préciser le problème traité, les changements et les vérifications effectuées. La validation autorise la création ou la mise à jour de la PR, pas sa fusion.
- Après création effective de la PR, ajouter son numéro à la suite du statut dans le champ RÉSULTAT de l’entrée correspondante de docs/USAGE-IA.TXT : `ACCEPTÉ — PR créée : #<numéro>` ou `ACCEPTÉ APRÈS CORRECTION — PR créée : #<numéro>`. Pour une PR existante, conserver son numéro. Commiter et pousser cette mise à jour du journal sur la même branche afin qu’elle figure dans la PR. Ne jamais annoncer une PR créée avant confirmation de sa création.
- Nommer les nouvelles branches selon Git Flow : `feature/<sujet>` pour une évolution ou un exercice, `hotfix/<sujet>` pour une correction urgente de production, `release/<version>` pour préparer une livraison. Utiliser un sujet court en minuscules, sans accents ni espaces et séparé par des tirets, par exemple `feature/l0-e5-definition-succes`.
- Respecter les branches de base du dépôt (`main` et `develop` si elle existe). Ne pas créer `develop`, renommer une branche existante ou restructurer le dépôt sans demande explicite.

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
4. Conserver toute la traçabilité : demandes initiales, relances, corrections, refus, vérifications et validations. Compléter les entrées sans effacer leur historique ; ajouter à la suite du résultat la création effective de la PR et son numéro selon la règle Git ci-dessus. Pour le résultat final, reprendre le statut du modèle correspondant à la décision exprimée. Pour la vérification, préciser ce qui a effectivement été relu, testé ou comparé, et par qui.
5. Dans le champ TEMPS, distinguer le délai de réponse de l’IA, le temps d’analyse ou de relecture de la personne et son estimation du temps gagné ou perdu par rapport au même travail sans IA. Préciser si chaque durée est mesurée ou estimée. Si les durées se recouvrent, les garder séparées.
6. Quand l’assistant ne peut pas éditer le dépôt, fournir l’entrée à reporter dans le journal et demander au membre de la reporter.
