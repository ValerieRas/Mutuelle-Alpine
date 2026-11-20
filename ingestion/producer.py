"""Producteur Kafka (Apache Kafka KRaft, ou Redpanda compatible) : rejoue les déclarations de sinistres comme un flux d'événements.

    python ingestion/producer.py --file data/raw/sinistres_events.jsonl --rate 200
"""
import argparse, json, time
from confluent_kafka import Producer

ap = argparse.ArgumentParser()
ap.add_argument("--file", default="data/raw/sinistres_events.jsonl")
ap.add_argument("--topic", default="maa.sinistres.declares.v1")
ap.add_argument("--bootstrap", default="localhost:19092")
ap.add_argument("--rate", type=float, default=0, help="messages/s (0 = max)")
args = ap.parse_args()

p = Producer({"bootstrap.servers": args.bootstrap, "enable.idempotence": True, "acks": "all"})
n = 0
with open(args.file, encoding="utf-8") as f:
    for line in f:
        evt = json.loads(line)
        # Clé = id_sinistre -> même partition pour un même sinistre (ordre garanti par clé)
        p.produce(args.topic, key=evt["id_sinistre"], value=line.encode("utf-8"),
                  headers={"schema_version": "1", "producer": "maa-declaration-app"})
        n += 1
        if n % 1000 == 0:
            p.flush(); print(f"{n} événements publiés")
        if args.rate:
            time.sleep(1 / args.rate)
p.flush()
print(f"Terminé : {n} événements publiés sur {args.topic}")
