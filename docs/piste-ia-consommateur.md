# L1 · Piste IA du consommateur Kafka

Le consommateur et le chargement des quatre CSV étaient déjà intégrés à `main` par la PR #5. Pour cette piste, un agent a proposé une ébauche de la boucle de lecture en réutilisant le consommateur de l’équipe. La revue a porté sur ce qui se passe entre la réception d’un lot, son écriture en Bronze et la confirmation de sa lecture à Kafka.

| Point | Comportement vérifié | Intervention sur cette branche |
|---|---|---|
| Commit des offsets | DuckDB valide tout le lot, puis le consommateur confirme à Kafka le prochain offset de chaque partition. Un échec d’écriture annule le lot et laisse les offsets disponibles pour la reprise. | La logique existante a passé les tests. Ajout d’un test où le broker accepte le commit d’une partition et refuse celui de l’autre. Le consommateur signale l’erreur et la partition refusée peut être relue. |
| Arrêt propre | Sur Ctrl+C ou SIGTERM, le consommateur termine le lot déjà reçu et ferme la connexion Kafka. DuckDB est ensuite fermé. | Un test a reproduit un arrêt prématuré après une perte temporaire d’attribution. Le délai de 30 secondes partait du lancement du programme. Il repart désormais au début de chaque perte d’attribution. Une demande d’arrêt pendant une lecture vide reste prioritaire sur l’expiration du délai. |
| Idempotence | La clé `(source, partition, offset)` identifie une livraison Kafka. Relire cette position conserve la ligne existante et son horodatage. Deux événements au même contenu mais à des positions différentes restent en Bronze. | Conservation de la clé existante et vérification du rejeu de la seule partition refusée, puis du topic entier. |

### Vérification sur Kafka local

Le producteur du projet a publié le fichier du kit une seule fois, dans un topic de test à trois partitions. Le même groupe de consommateurs et la même base DuckDB temporaire ont servi aux trois lectures.

| Exécution | Messages lus | Lignes ajoutées | Total Bronze |
|---|---:|---:|---:|
| Première lecture | 12 080 | 12 080 | 12 080 |
| Redémarrage du même groupe | 0 | 0 | 12 080 |
| Relecture avec `--from-beginning` | 12 080 | 0 | 12 080 |

Les prochains offsets confirmés sont 3 927, 4 076 et 4 077 pour les partitions 0, 1 et 2. Les contenus correspondent au fichier du kit, répétitions comprises. Après le rejeu, chaque ligne et son horodatage ont été comparés à la première lecture. Republier le fichier créerait de nouveaux offsets et constituerait une nouvelle ingestion.

Les tests automatisés du dépôt se relancent depuis la racine avec `python -m pytest -q tests`. Les erreurs d’écriture, le refus de commit par partition et la perte d’attribution sont simulés. La première lecture, la reprise et le rejeu ont aussi été exercés sur un broker Docker réel.
