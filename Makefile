# Raccourcis — chaque cible correspond à un lot du cahier de TP
PY ?= python
.PHONY: data bronze dbt quality lineage embeddings train ethics api traffic drift review all clean
data:        ## L0 — générer les données fictives (déterministe, seed 42)
	$(PY) data/generator/generate_data.py --seed 42
bronze:      ## L1 — ingestion (référentiels batch + événements Kafka)
	$(PY) ingestion/load_referentiels.py
	$(PY) ingestion/producer.py && $(PY) ingestion/consumer_to_lake.py
bronze-file: ## L1 — plan B sans Kafka
	$(PY) ingestion/load_referentiels.py
	$(PY) ingestion/consumer_to_lake.py --from-file data/raw/sinistres_events.jsonl
dbt:         ## L2/L4 — transformations + tests
	cd dbt/maa && dbt build --profiles-dir .
quality:     ## L4 — contrat producteur (Great Expectations)
	$(PY) quality/gx_bronze_sinistres.py
lineage:     ## L3 — lignée vers Marquez (profil lineage)
	cd dbt/maa && OPENLINEAGE_URL=http://localhost:5002 OPENLINEAGE_NAMESPACE=maa dbt-ol build --profiles-dir .
	OPENLINEAGE_URL=http://localhost:5002 $(PY) governance/lineage_emit.py
embeddings:  ## L6 — RAG + feature de similarité
	$(PY) rag/index_documents.py && $(PY) rag/similarity_feature.py
train:       ## L5 — entraînement + MLflow
	$(PY) ml/train.py
ethics:      ## L9 — SHAP + Fairlearn + k-anonymat
	$(PY) ethics/explain_and_fairness.py && $(PY) ethics/anonymisation_k.py
api:         ## L7 — API en local
	uvicorn api.main:app --port 8000
traffic:     ## L8 — trafic de janvier 2026 (dérive)
	$(PY) ingestion/consumer_to_lake.py --from-file data/raw/sinistres_events_2026_01.jsonl
	cd dbt/maa && dbt build --profiles-dir .
	$(PY) monitoring/simulate_traffic.py --periode 2026-01
drift:       ## L8 — rapport de dérive + push Prometheus
	$(PY) monitoring/drift.py --pushgateway localhost:9091
review:      ## L4 — revue IA du diff dbt (Ollama)
	$(PY) llm/review_dbt.py --base origin/main
all: data bronze-file dbt quality embeddings train ethics
clean:
	rm -rf warehouse qdrant_data mlruns ml/artifacts monitoring/predictions.jsonl
