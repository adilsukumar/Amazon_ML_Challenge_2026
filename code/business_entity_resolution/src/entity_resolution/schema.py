"""Strict, dependency-free validation for the supplied TSV schemas."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


SOURCE_COLUMNS = ("entity_id", "business_name", "business_address", "country")
GROUND_TRUTH_COLUMNS = ("source1_entity_id", "matched_entity_ids")


@dataclass(frozen=True)
class FileAudit:
    path: Path
    rows: int
    empty_name: int
    empty_address: int
    empty_country: int


def _require_header(path: Path, actual: Iterable[str] | None, expected: tuple[str, ...]) -> None:
    actual_tuple = tuple(actual or ())
    if actual_tuple != expected:
        raise ValueError(
            f"{path}: expected columns {expected}, found {actual_tuple}. "
            "Confirm this is a tab-separated file."
        )


def audit_source_file(path: Path, expected_prefix: str) -> FileAudit:
    """Validate one source file and return basic counts."""

    seen: set[str] = set()
    rows = empty_name = empty_address = empty_country = 0

    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        _require_header(path, reader.fieldnames, SOURCE_COLUMNS)
        for line_number, row in enumerate(reader, start=2):
            rows += 1
            entity_id = row["entity_id"].strip()
            if not entity_id.startswith(expected_prefix):
                raise ValueError(
                    f"{path}:{line_number}: entity_id {entity_id!r} does not "
                    f"start with {expected_prefix!r}"
                )
            if entity_id in seen:
                raise ValueError(f"{path}:{line_number}: duplicate entity_id {entity_id!r}")
            seen.add(entity_id)
            empty_name += not row["business_name"].strip()
            empty_address += not row["business_address"].strip()
            empty_country += not row["country"].strip()

    return FileAudit(path, rows, empty_name, empty_address, empty_country)


def audit_ground_truth(path: Path) -> int:
    """Validate ground-truth ID shapes and return its row count."""

    seen: set[str] = set()
    rows = 0
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        _require_header(path, reader.fieldnames, GROUND_TRUTH_COLUMNS)
        for line_number, row in enumerate(reader, start=2):
            rows += 1
            source1_id = row["source1_entity_id"].strip()
            if not source1_id.startswith("S1-"):
                raise ValueError(f"{path}:{line_number}: invalid Source 1 ID {source1_id!r}")
            if source1_id in seen:
                raise ValueError(f"{path}:{line_number}: duplicate Source 1 ID {source1_id!r}")
            seen.add(source1_id)
            matches = [value.strip() for value in row["matched_entity_ids"].split(",") if value.strip()]
            if len(matches) != len(set(matches)):
                raise ValueError(f"{path}:{line_number}: duplicate match IDs")
            invalid = [value for value in matches if not value.startswith(("S2-", "S3-"))]
            if invalid:
                raise ValueError(f"{path}:{line_number}: invalid match IDs {invalid[:3]}")
    return rows

