"""Disk-backed high-precision exact-normalization baseline.

The implementation streams the large TSV files into SQLite, so it runs on a
16 GB laptop without loading the full dataset into memory.
"""

from __future__ import annotations

import csv
import re
import sqlite3
import unicodedata
from itertools import groupby
from pathlib import Path
from typing import Iterable, Iterator


NON_ALNUM = re.compile(r"[^\w]+", flags=re.UNICODE)
WHITESPACE = re.compile(r"\s+")


def normalize(value: str) -> str:
    value = unicodedata.normalize("NFKC", value).casefold().replace("&", " and ")
    value = NON_ALNUM.sub(" ", value)
    return WHITESPACE.sub(" ", value).strip()


def connect(path: Path) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    connection.executescript(
        """
        PRAGMA journal_mode=OFF;
        PRAGMA synchronous=OFF;
        PRAGMA temp_store=FILE;
        PRAGMA cache_size=-262144;
        PRAGMA locking_mode=EXCLUSIVE;
        """
    )
    return connection


def _source_rows(path: Path) -> Iterator[tuple[str, str, str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t", quoting=csv.QUOTE_NONE)
        for row in reader:
            yield (
                row["entity_id"],
                normalize(row["country"]),
                normalize(row["business_name"]),
                normalize(row["business_address"]),
            )


def _batched(rows: Iterable[tuple], size: int = 20_000) -> Iterator[list[tuple]]:
    batch: list[tuple] = []
    for row in rows:
        batch.append(row)
        if len(batch) >= size:
            yield batch
            batch = []
    if batch:
        yield batch


def _insert_source(
    connection: sqlite3.Connection,
    table: str,
    path: Path,
) -> int:
    count = 0
    statement = f"INSERT INTO {table}(entity_id,country,name,address) VALUES (?,?,?,?)"
    for batch in _batched(_source_rows(path)):
        connection.executemany(statement, batch)
        count += len(batch)
        if count % 1_000_000 < len(batch):
            print(f"ingested {table}: {count:,}", flush=True)
    connection.commit()
    return count


def _insert_truth(connection: sqlite3.Connection, path: Path) -> tuple[int, int]:
    entity_count = link_count = 0

    def rows() -> Iterator[tuple[str, str]]:
        nonlocal entity_count, link_count
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle, delimiter="\t", quoting=csv.QUOTE_NONE)
            for row in reader:
                entity_count += 1
                raw = row["matched_entity_ids"].strip()
                if raw:
                    for target_id in raw.split(","):
                        link_count += 1
                        yield row["source1_entity_id"], target_id

    for batch in _batched(rows()):
        connection.executemany(
            "INSERT INTO truth_links(s1_id,target_id) VALUES (?,?)", batch
        )
    connection.commit()
    return entity_count, link_count


def build_database(
    *,
    database_path: Path,
    source1_path: Path,
    source2_path: Path,
    source3_path: Path,
    truth_path: Path | None = None,
) -> sqlite3.Connection:
    if database_path.exists():
        raise FileExistsError(f"refusing to overwrite existing database: {database_path}")
    connection = connect(database_path)
    connection.executescript(
        """
        CREATE TABLE s1(
            entity_id TEXT PRIMARY KEY,
            country TEXT NOT NULL,
            name TEXT NOT NULL,
            address TEXT NOT NULL
        ) WITHOUT ROWID;
        CREATE TABLE targets(
            entity_id TEXT PRIMARY KEY,
            country TEXT NOT NULL,
            name TEXT NOT NULL,
            address TEXT NOT NULL
        ) WITHOUT ROWID;
        CREATE TABLE truth_links(
            s1_id TEXT NOT NULL,
            target_id TEXT NOT NULL,
            PRIMARY KEY(s1_id,target_id)
        ) WITHOUT ROWID;
        """
    )
    _insert_source(connection, "s1", source1_path)
    _insert_source(connection, "targets", source2_path)
    _insert_source(connection, "targets", source3_path)
    if truth_path is not None:
        entities, links = _insert_truth(connection, truth_path)
        print(f"ingested truth: entities={entities:,}, links={links:,}", flush=True)

    print("building indexes", flush=True)
    connection.executescript(
        """
        CREATE INDEX s1_both_idx ON s1(country,name,address);
        CREATE INDEX target_both_idx ON targets(country,name,address);
        CREATE INDEX s1_name_idx ON s1(country,name);
        CREATE INDEX target_name_idx ON targets(country,name);
        CREATE INDEX s1_address_idx ON s1(country,address);
        CREATE INDEX target_address_idx ON targets(country,address);
        CREATE INDEX truth_target_idx ON truth_links(target_id,s1_id);
        ANALYZE;
        """
    )
    connection.commit()
    return connection


def generate_candidates(connection: sqlite3.Connection) -> None:
    print("building exact-key candidates", flush=True)
    connection.executescript(
        """
        CREATE TABLE candidates(
            s1_id TEXT NOT NULL,
            target_id TEXT NOT NULL,
            name_eq INTEGER NOT NULL,
            address_eq INTEGER NOT NULL,
            PRIMARY KEY(s1_id,target_id)
        ) WITHOUT ROWID;

        INSERT INTO candidates(s1_id,target_id,name_eq,address_eq)
        SELECT s.entity_id,t.entity_id,1,1
        FROM s1 s INDEXED BY s1_both_idx
        JOIN targets t INDEXED BY target_both_idx
          ON t.country=s.country AND t.name=s.name AND t.address=s.address
        WHERE s.name<>'' AND s.address<>'';

        CREATE TEMP TABLE unique_s1_names AS
        SELECT country,name
        FROM s1
        WHERE length(name)>=5
        GROUP BY country,name
        HAVING count(*)=1;
        CREATE INDEX unique_s1_names_idx ON unique_s1_names(country,name);

        INSERT INTO candidates(s1_id,target_id,name_eq,address_eq)
        SELECT s.entity_id,t.entity_id,1,CASE WHEN s.address=t.address AND s.address<>'' THEN 1 ELSE 0 END
        FROM unique_s1_names k
        JOIN s1 s ON s.country=k.country AND s.name=k.name
        JOIN targets t ON t.country=k.country AND t.name=k.name
        WHERE 1
        ON CONFLICT(s1_id,target_id) DO UPDATE SET name_eq=1;

        CREATE TEMP TABLE unique_s1_addresses AS
        SELECT country,address
        FROM s1
        WHERE length(address)>=8
        GROUP BY country,address
        HAVING count(*)=1;
        CREATE INDEX unique_s1_addresses_idx ON unique_s1_addresses(country,address);

        INSERT INTO candidates(s1_id,target_id,name_eq,address_eq)
        SELECT s.entity_id,t.entity_id,CASE WHEN s.name=t.name AND s.name<>'' THEN 1 ELSE 0 END,1
        FROM unique_s1_addresses k
        JOIN s1 s ON s.country=k.country AND s.address=k.address
        JOIN targets t ON t.country=k.country AND t.address=k.address
        WHERE 1
        ON CONFLICT(s1_id,target_id) DO UPDATE SET address_eq=1;

        CREATE INDEX candidate_target_idx ON candidates(target_id,s1_id);
        ANALYZE;
        """
    )
    connection.commit()
    count = connection.execute("SELECT count(*) FROM candidates").fetchone()[0]
    print(f"candidates={count:,}", flush=True)


RULES = {
    "both": "name_eq=1 AND address_eq=1",
    "name": "name_eq=1",
    "address": "address_eq=1",
    "union": "name_eq=1 OR address_eq=1",
}


def evaluate_rules(connection: sqlite3.Connection) -> dict[str, dict[str, float]]:
    total_truth = connection.execute("SELECT count(*) FROM truth_links").fetchone()[0]
    candidate_tp = connection.execute(
        """SELECT count(*) FROM candidates c
           JOIN truth_links t ON t.s1_id=c.s1_id AND t.target_id=c.target_id"""
    ).fetchone()[0]
    results: dict[str, dict[str, float]] = {}
    for name, condition in RULES.items():
        query = f"""
        WITH
        true_counts AS (
          SELECT s1_id,count(*) AS n FROM truth_links GROUP BY s1_id
        ),
        pred_counts AS (
          SELECT s1_id,count(*) AS n FROM candidates WHERE {condition} GROUP BY s1_id
        ),
        tp_counts AS (
          SELECT c.s1_id,count(*) AS n
          FROM candidates c JOIN truth_links t
            ON t.s1_id=c.s1_id AND t.target_id=c.target_id
          WHERE {condition}
          GROUP BY c.s1_id
        )
        SELECT
          avg(CASE
            WHEN coalesce(tc.n,0)=0 AND coalesce(pc.n,0)=0 THEN 1.0
            WHEN coalesce(tc.n,0)=0 OR coalesce(pc.n,0)=0 THEN 0.0
            ELSE 1.25*coalesce(tp.n,0)/(0.25*tc.n+pc.n)
          END),
          coalesce(sum(pc.n),0),
          coalesce(sum(tp.n),0)
        FROM s1 s
        LEFT JOIN true_counts tc ON tc.s1_id=s.entity_id
        LEFT JOIN pred_counts pc ON pc.s1_id=s.entity_id
        LEFT JOIN tp_counts tp ON tp.s1_id=s.entity_id
        """
        macro, predicted, true_positive = connection.execute(query).fetchone()
        precision = true_positive / predicted if predicted else 0.0
        recall = true_positive / total_truth if total_truth else 0.0
        results[name] = {
            "macro_f0_5": float(macro),
            "pair_precision": precision,
            "pair_recall": recall,
            "predicted_links": int(predicted),
            "true_positive_links": int(true_positive),
        }
        print(name, results[name], flush=True)
    results["candidate_set"] = {
        "pair_recall": candidate_tp / total_truth if total_truth else 0.0,
        "true_positive_links": int(candidate_tp),
        "truth_links": int(total_truth),
        "candidate_links": connection.execute("SELECT count(*) FROM candidates").fetchone()[0],
    }
    return results


def _grouped_pairs(cursor: sqlite3.Cursor) -> Iterator[tuple[str, list[str]]]:
    for source_id, rows in groupby(cursor, key=lambda row: row[0]):
        yield source_id, [row[1] for row in rows]


def write_outputs(
    connection: sqlite3.Connection,
    output_dir: Path,
    *,
    rule: str,
) -> tuple[Path, Path]:
    if rule not in RULES:
        raise ValueError(f"unknown rule: {rule}")
    output_dir.mkdir(parents=True, exist_ok=True)
    matching_path = output_dir / "matching_results.tsv"
    candidate_path = output_dir / "candidate_pairs.tsv"
    candidate_groups = iter(
        _grouped_pairs(
            connection.execute("SELECT s1_id,target_id FROM candidates ORDER BY s1_id,target_id")
        )
    )
    match_groups = iter(
        _grouped_pairs(
            connection.execute(
                f"SELECT s1_id,target_id FROM candidates WHERE {RULES[rule]} "
                "ORDER BY s1_id,target_id"
            )
        )
    )
    candidate_group = next(candidate_groups, None)
    match_group = next(match_groups, None)
    with (
        matching_path.open("w", encoding="utf-8", newline="") as matching,
        candidate_path.open("w", encoding="utf-8", newline="") as candidates,
    ):
        matching_writer = csv.writer(matching, delimiter="\t", lineterminator="\n")
        candidate_writer = csv.writer(candidates, delimiter="\t", lineterminator="\n")
        matching_writer.writerow(("source1_entity_id", "matched_entity_ids"))
        candidate_writer.writerow(("source1_entity_id", "candidate_entity_ids"))
        for (source_id,) in connection.execute("SELECT entity_id FROM s1 ORDER BY entity_id"):
            candidate_ids: list[str] = []
            match_ids: list[str] = []
            if candidate_group and candidate_group[0] == source_id:
                candidate_ids = candidate_group[1]
                candidate_group = next(candidate_groups, None)
            if match_group and match_group[0] == source_id:
                match_ids = match_group[1]
                match_group = next(match_groups, None)
            matching_writer.writerow((source_id, ",".join(match_ids)))
            candidate_writer.writerow((source_id, ",".join(candidate_ids)))
    return matching_path, candidate_path
