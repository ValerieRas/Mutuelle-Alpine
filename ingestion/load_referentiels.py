"""L1 : chargement batch des quatre référentiels CSV dans DuckDB Bronze.

    python ingestion/load_referentiels.py
    python ingestion/load_referentiels.py --data-dir data/raw --database warehouse/maa.duckdb

Les valeurs restent en texte : aucun typage métier, nettoyage ou dédoublonnage.
Un contenu SHA-256 déjà chargé pour un référentiel est ignoré. Un contenu modifié
ajoute un snapshot complet, sans écraser l'historique ; Silver devra sélectionner
le snapshot pertinent avant de faire des jointures (lot L2).
bronze.ingestion_batches trace aussi les fichiers sans ligne de données.
Les quatre fichiers sont validés dans une seule transaction DuckDB.

Choix batch : les sources fournies sont des exports CSV et une fraîcheur quotidienne
peut suffire aux référentiels. C'est une hypothèse à confirmer avec le métier.
Le CDC demanderait une base source, son journal de changements et une exploitation
plus coûteuse, à justifier si une fraîcheur plus faible devient nécessaire.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import sys
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parents[1]
DATASETS = ("assures", "contrats", "prestataires", "enquetes")
METADATA = ("_batch_id", "_row_number", "_source_file", "_ingested_at")


def identifier(name):
    """Protéger les noms de colonnes du CSV, jamais utilisés comme SQL libre."""
    return '"' + name.replace('"', '""') + '"'


def read_source(path):
    # Empreinte et parsing portent sur les mêmes octets, même si le fichier change.
    content = path.read_bytes()
    batch_id = hashlib.sha256(content).hexdigest()
    reader = csv.reader(io.StringIO(content.decode("utf-8-sig"), newline=""), strict=True)
    columns = next(reader, [])
    if (not columns or any(not name for name in columns)
            or len({name.casefold() for name in columns}) != len(columns)
            or {name.casefold() for name in columns}.intersection(METADATA)):
        raise ValueError(f"En-tête invalide ou colonnes réservées dans {path.name}.")
    rows = []
    for row in reader:
        if len(row) != len(columns):
            # Ne jamais exposer le contenu personnel de la ligne dans l'erreur.
            raise ValueError(f"Nombre de champs incorrect dans {path.name}, ligne physique {reader.line_num}.")
        rows.append(row)
    return columns, rows, batch_id


def load_referentiels(connection, data_dir, batch_size=1000):
    """Snapshots append-only ; un échec annule les quatre imports et leur suivi."""
    if batch_size <= 0:
        raise ValueError("La taille des lots doit être positive.")
    results = []
    connection.execute("BEGIN TRANSACTION")
    try:
        connection.execute("CREATE SCHEMA IF NOT EXISTS bronze")
        connection.execute('''
            CREATE TABLE IF NOT EXISTS bronze.ingestion_batches (
                dataset VARCHAR NOT NULL,
                batch_id VARCHAR NOT NULL,
                source_file VARCHAR NOT NULL,
                ingested_at TIMESTAMPTZ NOT NULL DEFAULT current_timestamp,
                row_count BIGINT NOT NULL,
                PRIMARY KEY (dataset, batch_id)
            )
        ''')
        for dataset in DATASETS:
            path = data_dir / f"{dataset}.csv"
            columns, rows, batch_id = read_source(path)
            table = f"bronze.{identifier(dataset)}"
            fields = ", ".join(f"{identifier(column)} VARCHAR" for column in columns)
            connection.execute(f'''
                CREATE TABLE IF NOT EXISTS {table} (
                    {fields},
                    _batch_id VARCHAR NOT NULL,
                    _row_number BIGINT NOT NULL,
                    _source_file VARCHAR NOT NULL,
                    _ingested_at TIMESTAMPTZ NOT NULL DEFAULT current_timestamp,
                    PRIMARY KEY (_batch_id, _row_number)
                )
            ''')
            actual_columns = [row[0] for row in connection.execute(f"DESCRIBE {table}").fetchall()]
            if actual_columns != columns + list(METADATA):
                raise ValueError(f"Schéma incompatible pour {dataset} ; migration explicite nécessaire.")
            loaded = connection.execute(
                "SELECT 1 FROM bronze.ingestion_batches WHERE dataset = ? AND batch_id = ?",
                [dataset, batch_id],
            ).fetchone() is not None
            if not loaded:
                names = ", ".join(identifier(name) for name in columns)
                # Les UNNEST parallèles transposent les colonnes sans conversion métier.
                values = ", ".join("unnest(?)" for _ in columns)
                statement = f'''
                    INSERT INTO {table} ({names}, _batch_id, _row_number, _source_file)
                    SELECT {values}, ?, unnest(?), ?
                '''
                for start in range(0, len(rows), batch_size):
                    part = rows[start:start + batch_size]
                    parameters = [list(column) for column in zip(*part)]
                    parameters.extend([batch_id, list(range(start + 1, start + len(part) + 1)),
                                       str(path.resolve())])
                    connection.execute(statement, parameters)
                connection.execute('''
                    INSERT INTO bronze.ingestion_batches
                        (dataset, batch_id, source_file, row_count)
                    VALUES (?, ?, ?, ?)
                ''', [dataset, batch_id, str(path.resolve()), len(rows)])
            total = connection.execute(f"SELECT count(*) FROM {table}").fetchone()[0]
            results.append({"dataset": dataset, "read": len(rows),
                            "added": 0 if loaded else len(rows), "total": total})
        connection.execute("COMMIT")
    except BaseException:
        connection.execute("ROLLBACK")
        raise
    return results


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", type=Path, default=ROOT / "warehouse/maa.duckdb")
    parser.add_argument("--data-dir", type=Path, default=ROOT / "data/raw")
    args = parser.parse_args(argv)
    try:
        args.database.parent.mkdir(parents=True, exist_ok=True)
        with duckdb.connect(str(args.database)) as connection:
            results = load_referentiels(connection, args.data_dir)
        for result in results:
            print(f"bronze.{result['dataset']} | Lus : {result['read']} | "
                  f"Ajoutés : {result['added']} | Total : {result['total']}")
        return 0
    except Exception as error:
        # Les exceptions SQL/CSV peuvent inclure des valeurs sensibles : type seul.
        print(f"Chargement annulé ({type(error).__name__}). "
              "Vérifier les fichiers CSV et leur schéma ; aucun import partiel validé.",
              file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
