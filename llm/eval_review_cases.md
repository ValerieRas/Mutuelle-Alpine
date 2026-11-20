# Jeu d'évaluation de la revue IA (à compléter par l'équipe)
Injecter volontairement ces défauts dans une branche et vérifier si le LLM les détecte. Consigner dans USAGE-IA.TXT.
| # | Défaut injecté | Attendu | Détecté ? (oui/non/partiel) | Faux positifs relevés |
|---|----------------|---------|-----------------------------|-----------------------|
| 1 | Jointure fct_sinistres -> dim_contrat sur id_assure (fan-out) | BLOQUANT | | |
| 2 | `email` ajouté à dim_assure | BLOQUANT (RGPD) | | |
| 3 | Suppression du `where rn = 1` (doublons Kafka) | MAJEUR | | |
| 4 | `tranche_age` ajoutée aux features | MAJEUR (équité) | | |
| 5 | Test `unique` retiré sur id_sinistre | MAJEUR | | |
| 6 | Renommage d'une colonne sous contrat | BLOQUANT (data contract) | | |
