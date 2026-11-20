"""Tests du batch sur des exemples construits, sans données personnelles du kit."""
import csv
import importlib.util
from pathlib import Path

import duckdb
import pytest

spec = importlib.util.spec_from_file_location(
    "load_referentiels", Path(__file__).resolve().parents[1] / "ingestion/load_referentiels.py"
)
batch = importlib.util.module_from_spec(spec)
spec.loader.exec_module(batch)


def write_csv(path, rows):
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(["id_test", "valeur", "code"])
        writer.writerows(rows)


@pytest.fixture
def sources(tmp_path):
    for dataset in batch.DATASETS:
        write_csv(tmp_path / f"{dataset}.csv", [
            ["TEST-1", "1234,56", "00123"],
            ["TEST-1", "1234,56", "00123"],
            ["TEST-2", "", "NA"],
            ["TEST-3", 'texte, "cité"\nseconde ligne', "00000"],
        ])
    return tmp_path


def test_raw_values_duplicates_and_idempotent_replay(sources):
    with duckdb.connect(":memory:") as connection:
        result = batch.load_referentiels(connection, sources, batch_size=2)
        assert [r["added"] for r in result] == [4] * 4
        original = connection.execute("SELECT * FROM bronze.assures ORDER BY _row_number").fetchall()
        assert [row[:3] for row in original] == [
            ("TEST-1", "1234,56", "00123"), ("TEST-1", "1234,56", "00123"),
            ("TEST-2", "", "NA"), ("TEST-3", 'texte, "cité"\nseconde ligne', "00000"),
        ]
        assert all(row[1] == "VARCHAR" for row in connection.execute("DESCRIBE bronze.assures").fetchall()[:3])
        result = batch.load_referentiels(connection, sources)
        assert [r["added"] for r in result] == [0] * 4
        assert connection.execute("SELECT * FROM bronze.assures ORDER BY _row_number").fetchall() == original
        assert connection.execute("SELECT count(*) FROM bronze.ingestion_batches").fetchone()[0] == 4


def test_changed_file_adds_snapshot_and_keeps_previous_version(sources):
    with duckdb.connect(":memory:") as connection:
        batch.load_referentiels(connection, sources)
        write_csv(sources / "contrats.csv", [["TEST-NEW", "9,99", "00001"]])
        result = batch.load_referentiels(connection, sources)
        assert [r["added"] for r in result] == [0, 1, 0, 0]
        assert connection.execute("SELECT count(*), count(DISTINCT _batch_id) FROM bronze.contrats").fetchone() == (5, 2)
        assert connection.execute("SELECT count(*) FROM bronze.ingestion_batches").fetchone()[0] == 5


def test_invalid_last_file_rolls_back_other_snapshots(sources):
    with duckdb.connect(":memory:") as connection:
        batch.load_referentiels(connection, sources)
        before = connection.execute("SELECT * FROM bronze.assures ORDER BY _row_number").fetchall()
        write_csv(sources / "assures.csv", [["NEW", "test", "00001"]])
        (sources / "enquetes.csv").write_text("id_test,valeur,code\ninvalid,row\n", encoding="utf-8")
        with pytest.raises(ValueError, match="Nombre de champs"):
            batch.load_referentiels(connection, sources)
        assert connection.execute("SELECT * FROM bronze.assures ORDER BY _row_number").fetchall() == before
        assert connection.execute("SELECT count(*) FROM bronze.ingestion_batches").fetchone()[0] == 4


def test_schema_change_is_rejected_without_partial_loading(sources):
    with duckdb.connect(":memory:") as connection:
        batch.load_referentiels(connection, sources)
        (sources / "contrats.csv").write_text("id_test,new_column\nTEST,example\n", encoding="utf-8")
        with pytest.raises(ValueError, match="Schéma incompatible"):
            batch.load_referentiels(connection, sources)
        assert connection.execute("SELECT count(*) FROM bronze.ingestion_batches").fetchone()[0] == 4
