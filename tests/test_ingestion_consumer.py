"""Tests L1 : conservation du brut, rejeu et frontière DuckDB/Kafka."""
import importlib.util
import signal
from collections import Counter
from pathlib import Path
from threading import Event
from types import SimpleNamespace

import duckdb
import pytest

spec = importlib.util.spec_from_file_location(
    "consumer_to_lake", Path(__file__).resolve().parents[1] / "ingestion/consumer_to_lake.py"
)
ingestion = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ingestion)


def test_file_replay_keeps_identical_lines_and_original_timestamp(tmp_path):
    path = tmp_path / "events.jsonl"
    raw = '{"id_sinistre":"TEST", "montant_declare":"1234,56"}\n'
    path.write_text(raw * 2, encoding="utf-8")
    with duckdb.connect(":memory:") as connection:
        ingestion.initialize(connection)
        assert ingestion.consume_file(connection, path, 1, Event()) == 2
        original = connection.execute('SELECT * FROM bronze.sinistres_events ORDER BY "offset"').fetchall()
        assert len(original) == 2
        assert [row[0] for row in original] == [raw, raw]
        assert ingestion.consume_file(connection, path, 10, Event()) == 2
        assert connection.execute('SELECT * FROM bronze.sinistres_events ORDER BY "offset"').fetchall() == original


class Message:
    def __init__(self, offset, partition=0):
        self.position, self.part = offset, partition

    def topic(self): return "test"
    def partition(self): return self.part
    def offset(self): return self.position
    def value(self): return b'{"id_sinistre":"TEST"}\n'
    def error(self): return None


def test_commit_failure_after_durable_write_is_safe_to_replay():
    with duckdb.connect(":memory:") as connection:
        ingestion.initialize(connection)

        def failed_commit(**kwargs):
            assert connection.execute("SELECT count(*) FROM bronze.sinistres_events").fetchone()[0] == 3
            raise RuntimeError("Kafka indisponible après écriture")

        messages = [Message(4), Message(5), Message(9, 1)]
        with pytest.raises(RuntimeError, match="après écriture"):
            ingestion.write_kafka_batch(connection, SimpleNamespace(commit=failed_commit), messages)
        captured = []

        def commit(**kwargs):
            assert kwargs["asynchronous"] is False
            captured.extend((p.partition, p.offset) for p in kwargs["offsets"])

        ingestion.write_kafka_batch(connection, SimpleNamespace(commit=commit), messages)
        assert sorted(captured) == [(0, 6), (1, 10)]
        assert connection.execute("SELECT count(*) FROM bronze.sinistres_events").fetchone()[0] == 3


def test_failed_transaction_does_not_commit_kafka():
    with duckdb.connect(":memory:") as connection:
        ingestion.initialize(connection)
        # Une contrainte refusant le payload simule une erreur d'écriture réelle.
        connection.execute('DROP TABLE bronze.sinistres_events')
        connection.execute('''CREATE TABLE bronze.sinistres_events (
            payload VARCHAR CHECK (payload = 'allowed'), "partition" INTEGER,
            "offset" BIGINT, source VARCHAR, PRIMARY KEY(source, "partition", "offset"))''')
        committed = []
        consumer = SimpleNamespace(commit=lambda **kwargs: committed.append(kwargs))
        valid = Message(0)
        valid.value = lambda: b"allowed"
        with pytest.raises(duckdb.ConstraintException):
            ingestion.write_kafka_batch(connection, consumer, [valid, Message(1)])
        assert committed == []
        assert connection.execute("SELECT count(*) FROM bronze.sinistres_events").fetchone()[0] == 0
        # Le rollback doit avoir libéré la transaction.
        connection.execute("BEGIN")
        connection.execute("ROLLBACK")


def test_full_file_cli_and_replay(tmp_path):
    source = ingestion.ROOT / "data/raw/sinistres_events.jsonl"
    database = tmp_path / "file.duckdb"
    args = ["--database", str(database), "--from-file", str(source)]
    assert ingestion.main(args) == 0
    with duckdb.connect(str(database), read_only=True) as connection:
        original = connection.execute('SELECT * FROM bronze.sinistres_events ORDER BY "offset"').fetchall()
        assert len(original) == 12080
        with source.open(encoding="utf-8") as stream:
            assert [row[0] for row in original] == list(stream)
        assert len(Counter(row[0] for row in original)) == 12000
    assert ingestion.main(args) == 0
    with duckdb.connect(str(database), read_only=True) as connection:
        assert connection.execute('SELECT * FROM bronze.sinistres_events ORDER BY "offset"').fetchall() == original


def test_ctrl_c_finishes_current_batch_and_closes_resources(tmp_path, monkeypatch):
    import confluent_kafka

    closed = []
    committed = []

    class Consumer:
        def __init__(self, config):
            assert config["enable.auto.commit"] is False
            assert config["enable.auto.offset.store"] is False

        def subscribe(self, topics): pass

        def consume(self, **kwargs):
            signal.raise_signal(signal.SIGINT)
            return [Message(0)]

        def commit(self, **kwargs):
            committed.append(kwargs)

        def close(self):
            closed.append(True)

    monkeypatch.setattr(confluent_kafka, "Consumer", Consumer)
    database = tmp_path / "interrupted.duckdb"
    assert ingestion.main(["--database", str(database)]) == 0
    assert closed == [True]
    assert len(committed) == 1
    with duckdb.connect(str(database), read_only=True) as connection:
        assert connection.execute("SELECT count(*) FROM bronze.sinistres_events").fetchone()[0] == 1
