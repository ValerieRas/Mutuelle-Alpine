# Installation et plan B
## Prérequis poste
- 8 Go RAM minimum (profil socle), 16 Go conseillés pour lineage + ml simultanés · 10 Go disque · Docker Desktop ou Docker Engine + Compose v2 · Python 3.11 · Git
- Ollama : `ollama pull qwen2.5:1.5b` (RAG) et `ollama pull qwen2.5-coder:1.5b` (revue de code ; le 7B, Apache 2.0, est meilleur si le poste le permet)
## Budget mémoire indicatif
| Service | RAM |
|---|---|
| Apache Kafka KRaft (heap 512 Mo) | ~0,8 Go (Redpanda : ~0,6 Go) |
| API + Prometheus + Pushgateway + Grafana | ~0,7 Go |
| Marquez + Postgres | ~0,7 Go |
| MLflow serveur | ~0,3 Go |
| Ollama qwen2.5:1.5b | ~1,2 Go |
| Embeddings fastembed (pendant le calcul) | ~0,6 Go |
**Règle : ne jamais lancer tous les profils en même temps sur 8 Go.** Arrêter `lineage` avant de lancer Ollama.
## Outils lourds (démo formateur)
- **OpenMetadata** : quickstart Docker officiel (≥ 6 Go dédiés). Démo : ingestion des métadonnées dbt (`manifest.json`, `catalog.json`) + tags de classification. Les apprenants tiennent le catalogue « as code » (`governance/catalogue.yml`).
- **Langfuse v3** (Postgres, ClickHouse, Redis, MinIO) : docker compose officiel. Démo des traces de `rag/ask.py`.
## Plans B
| Problème | Plan B |
|---|---|
| Docker indisponible | `make bronze-file` (sans Kafka), Qdrant local embarqué, MLflow en fichiers, API via uvicorn |
| Ollama trop lent | modèle 0.5b / 1.5b, ou poste formateur partagé (`OLLAMA_URL=http://<ip-formateur>:11434`) |
| Téléchargement de modèles bloqué | pré-charger le cache fastembed et les modèles Ollama sur clé USB |
| Embeddings trop longs | `rag/similarity_feature.py` ne calcule qu'une fois par description distincte ; lancer pendant la pause |
