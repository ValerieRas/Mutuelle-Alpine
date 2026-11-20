# Consignes pour les assistants IA du projet MAA

## Avant de répondre

Lire le [contexte partagé](CONTEXTE.md), la consigne du lot concerné et les dernières entrées du [journal](docs/USAGE-IA.TXT). S’appuyer sur les fichiers du dépôt et distinguer ce qui est prévu de ce qui a été réalisé.

## Livrable et accompagnement

Respecter le format et le périmètre demandés dans le cahier de TP. Donner les explications pédagogiques dans la conversation. Préserver les contributions des autres membres. Les données des tables `bronze.assures` et `bronze.enquetes`, même fictives, doivent rester sur la machine lors d’un usage d’IA.

## Journal obligatoire à chaque appel à une IA

1. À chaque demande et à chaque relance, mettre à jour `docs/USAGE-IA.TXT`. Pour la suite du même travail, compléter l’entrée existante en gardant la trace de la demande précédente. Pour un nouvel objectif, attribuer le prochain identifiant disponible.
2. Renseigner tous les champs du modèle : ID, date, auteur, lot TP, outil, pourquoi, demande, résultat, refus ou correction, vérification et temps. Identifier le membre qui a réellement fait la demande.
3. Si une information manque, poser la question à la personne dans la réponse. Regrouper les questions et compléter l’entrée dès son retour. Une validation en attente reste indiquée comme telle. Si la personne confirme qu’une mesure est impossible à estimer, consigner sa réponse.
4. Pour le résultat final, reprendre le statut du modèle correspondant à la décision exprimée. Pour la vérification, préciser ce qui a effectivement été relu, testé ou comparé, et par qui.
5. Dans le champ TEMPS, distinguer le délai de réponse de l’IA, le temps d’analyse ou de relecture de la personne et son estimation du temps gagné ou perdu par rapport au même travail sans IA. Préciser si chaque durée est mesurée ou estimée. Si les durées se recouvrent, les garder séparées.
6. Quand l’assistant ne peut pas éditer le dépôt, fournir l’entrée à reporter dans le journal et demander au membre de la reporter.
