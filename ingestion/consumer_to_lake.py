"""L1 : événements bruts Kafka ou JSONL vers DuckDB, sans nettoyage métier.

Depuis la racine du projet :
    python ingestion/consumer_to_lake.py
    python ingestion/consumer_to_lake.py --from-beginning
    python ingestion/consumer_to_lake.py --from-file data/raw/sinistres_events.jsonl --database warehouse/file-check.duckdb

Le mode Kafka s'arrête après --idle-timeout secondes sans message une fois
les partitions attribuées (0 : écoute continue). Ctrl+C termine le lot en cours.
Le groupe stable reprend ses offsets ; --from-beginning force leur relecture.
Si la base est reconstruite mais que le groupe existe, utiliser --from-beginning.
La clé technique conserve les répétitions métier et ignore les mêmes offsets.
Une republication ou une recréation du topic n'est pas un simple rejeu : ne pas
réutiliser cette identité de source pour un topic supprimé puis recréé.
Les validations Kafka et fichier doivent utiliser des bases distinctes : leurs
sources diffèrent et une ingestion des deux dans la même base cumule les lignes.
"""
from __future__ import annotations

import argparse
import hashlib
import signal
import sys
import time
from pathlib import Path
from threading import Event

import duckdb

ROOT = Path(__file__).resolve().parents[1]
INSERT = '''
    INSERT INTO bronze.sinistres_events
        (payload, "partition", "offset", source)
    VALUES (?, ?, ?, ?)
    ON CONFLICT (source, "partition", "offset") DO NOTHING
'''


def initialize(connection):
    connection.execute("CREATE SCHEMA IF NOT EXISTS bronze")
    connection.execute('''
        CREATE TABLE IF NOT EXISTS bronze.sinistres_events (
            payload VARCHAR NOT NULL,
            "partition" INTEGER NOT NULL,
            "offset" BIGINT NOT NULL,
            ingested_at TIMESTAMPTZ NOT NULL DEFAULT current_timestamp,
            source VARCHAR NOT NULL,
            PRIMARY KEY (source, "partition", "offset")
        )
    ''')


def write_batch(connection, rows):
    """Un lot est durable en entier, ou aucune de ses lignes n'est conservée."""
    if not rows:
        return
    connection.execute("BEGIN TRANSACTION")
    try:
        connection.executemany(INSERT, rows)
        connection.execute("COMMIT")
    except BaseException:
        connection.execute("ROLLBACK")
        raise


def write_kafka_batch(connection, consumer, messages):
    from confluent_kafka import TopicPartition

    rows = []
    next_offsets = {}
    for message in messages:
        if message.error():
            raise RuntimeError(str(message.error()))
        value = message.value()
        if value is None:
            raise ValueError("Message Kafka sans payload ; offsets non confirmés.")
        rows.append((value.decode("utf-8"), message.partition(), message.offset(),
                     f"kafka:{message.topic()}"))
        key = (message.topic(), message.partition())
        next_offsets[key] = max(next_offsets.get(key, 0), message.offset() + 1)

    write_batch(connection, rows)
    # Kafka attend la position du PROCHAIN message ; jamais avant le COMMIT DuckDB.
    offsets = [TopicPartition(topic, partition, offset)
               for (topic, partition), offset in next_offsets.items()]
    if offsets:
        committed = consumer.commit(offsets=offsets, asynchronous=False)
        for partition in committed or []:
            if partition.error:
                raise RuntimeError(str(partition.error))


def consume_file(connection, path, batch_size, stop):
    """Une version de fichier = une source ; une ligne = un offset (base zéro)."""
    with path.open("rb") as stream:
        digest = hashlib.file_digest(stream, "sha256").hexdigest()
    source = f"file:{digest}"
    rows = []
    processed = 0
    with path.open(encoding="utf-8") as stream:
        for offset, line in enumerate(stream):
            if stop.is_set():
                break
            rows.append((line, 0, offset, source))
            processed += 1
            if len(rows) >= batch_size:
                write_batch(connection, rows)
                rows.clear()
        write_batch(connection, rows)
    return processed


def consume_kafka(connection, args, stop):
    from confluent_kafka import Consumer, OFFSET_BEGINNING

    consumer = Consumer({
        "bootstrap.servers": args.bootstrap,
        "group.id": args.group,
        "enable.auto.commit": False,
        "enable.auto.offset.store": False,
        "auto.offset.reset": "earliest",
    })
    processed = 0
    last_message = unassigned_since = time.monotonic()
    try:
        if args.from_beginning:
            def on_assign(client, partitions):
                for partition in partitions:
                    partition.offset = OFFSET_BEGINNING
                client.assign(partitions)
            consumer.subscribe([args.topic], on_assign=on_assign)
        else:
            consumer.subscribe([args.topic])
        while not stop.is_set():
            messages = consumer.consume(num_messages=args.batch_size, timeout=1.0)
            now = time.monotonic()
            if messages:
                write_kafka_batch(connection, consumer, messages)
                processed += len(messages)
                last_message = time.monotonic()
                unassigned_since = None
            elif stop.is_set():
                break
            elif consumer.assignment():
                if unassigned_since is not None:
                    last_message = now
                    unassigned_since = None
                if args.idle_timeout and now - last_message >= args.idle_timeout:
                    break
            else:
                # L'absence de broker ou d'attribution n'est pas une fin réussie.
                if unassigned_since is None:
                    unassigned_since = now
                if now - unassigned_since >= 30:
                    raise RuntimeError("Aucune partition attribuée après 30 s ; vérifier Kafka et le topic.")
    finally:
        # L'auto-commit est désactivé : close() ne confirme aucun lot non écrit.
        consumer.close()
    return processed


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", type=Path, default=ROOT / "warehouse/maa.duckdb")
    parser.add_argument("--from-file", type=Path, help="JSONL local, sans connexion Kafka")
    parser.add_argument("--bootstrap", default="localhost:19092")
    parser.add_argument("--topic", default="maa.sinistres.declares.v1")
    parser.add_argument("--group", default="maa-bronze-v1")
    parser.add_argument("--from-beginning", action="store_true", help="Relire Kafka depuis le début")
    parser.add_argument("--batch-size", type=int, default=500)
    parser.add_argument("--idle-timeout", type=float, default=5, help="Secondes sans message ; 0 = continu")
    args = parser.parse_args(argv)
    if args.batch_size <= 0 or args.idle_timeout < 0:
        parser.error("--batch-size doit être positif et --idle-timeout positif ou nul")
    if args.from_file and args.from_beginning:
        parser.error("--from-beginning concerne uniquement Kafka")
    return args


def main(argv=None):
    args = parse_args(argv)
    stop = Event()
    previous_handlers = {}
    for signum in (signal.SIGINT, signal.SIGTERM):
        previous_handlers[signum] = signal.signal(signum, lambda *_: stop.set())
    try:
        args.database.parent.mkdir(parents=True, exist_ok=True)
        with duckdb.connect(str(args.database)) as connection:
            initialize(connection)
            before = connection.execute("SELECT count(*) FROM bronze.sinistres_events").fetchone()[0]
            if args.from_file:
                processed = consume_file(connection, args.from_file, args.batch_size, stop)
            else:
                processed = consume_kafka(connection, args, stop)
            after = connection.execute("SELECT count(*) FROM bronze.sinistres_events").fetchone()[0]
        print(f"Lus : {processed} | Ajoutés : {after - before} | Total Bronze : {after}")
        if stop.is_set():
            print("Arrêt demandé : dernier lot écrit et ressources fermées.")
        return 0
    except Exception as error:
        print(f"Échec de l'ingestion : {error}", file=sys.stderr)
        return 1
    finally:
        for signum, handler in previous_handlers.items():
            signal.signal(signum, handler)


if __name__ == "__main__":
    raise SystemExit(main())
