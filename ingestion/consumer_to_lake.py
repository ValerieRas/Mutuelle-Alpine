"""L1 — TODO : consommer le topic maa.sinistres.declares.v1 et écrire la couche BRONZE dans DuckDB.
Exigences (cahier de TP, lot L1) :
 - table bronze.sinistres_events (payload JSON brut + partition + offset + ingested_at + source)
 - commit des offsets APRÈS écriture (pourquoi ?)
 - option --from-file (plan B sans Kafka) produisant le même schéma
"""
