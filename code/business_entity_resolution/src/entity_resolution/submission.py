"""Create and validate competition submission TSV files."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Sequence


@dataclass(frozen=True)
class SubmissionAudit:
    source_entities: int
    candidate_links: int
    predicted_links: int


class SubmissionValidationError(ValueError):
    """Raised when competition output violates a submission contract."""


def read_entity_ids(path: Path, expected_prefix: str) -> list[str]:
    """Read and validate the entity_id column from a source TSV."""

    ids: list[str] = []
    seen: set[str] = set()
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        if not reader.fieldnames or "entity_id" not in reader.fieldnames:
            raise SubmissionValidationError(f"{path}: missing entity_id column")
        for line_number, row in enumerate(reader, start=2):
            entity_id = row["entity_id"].strip()
            if not entity_id.startswith(expected_prefix):
                raise SubmissionValidationError(
                    f"{path}:{line_number}: invalid ID prefix for {entity_id!r}"
                )
            if entity_id in seen:
                raise SubmissionValidationError(
                    f"{path}:{line_number}: duplicate entity_id {entity_id!r}"
                )
            seen.add(entity_id)
            ids.append(entity_id)
    return ids


def _validate_values(values: Sequence[str], allowed_targets: set[str]) -> None:
    if len(values) != len(set(values)):
        raise SubmissionValidationError("an ID list contains duplicate values")
    invalid = [value for value in values if value not in allowed_targets]
    if invalid:
        raise SubmissionValidationError(f"unknown or invalid target IDs: {invalid[:3]}")


def write_id_lists(
    path: Path,
    source_ids: Sequence[str],
    values_by_source: Mapping[str, Sequence[str]],
    *,
    list_column: str,
    allowed_targets: set[str],
) -> None:
    """Write deterministic, unquoted ID-list output with all Source 1 rows."""

    unknown_sources = values_by_source.keys() - set(source_ids)
    if unknown_sources:
        raise SubmissionValidationError(
            f"output contains unknown Source 1 IDs: {sorted(unknown_sources)[:3]}"
        )

    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(
            handle,
            delimiter="\t",
            lineterminator="\n",
            quoting=csv.QUOTE_NONE,
            escapechar="\\",
        )
        writer.writerow(("source1_entity_id", list_column))
        for source_id in source_ids:
            values = sorted(values_by_source.get(source_id, ()))
            _validate_values(values, allowed_targets)
            writer.writerow((source_id, ",".join(values)))


def read_id_lists(path: Path, list_column: str) -> dict[str, tuple[str, ...]]:
    """Read an output TSV while rejecting duplicates and formatting mistakes."""

    result: dict[str, tuple[str, ...]] = {}
    expected_header = ("source1_entity_id", list_column)
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        if tuple(reader.fieldnames or ()) != expected_header:
            raise SubmissionValidationError(
                f"{path}: expected columns {expected_header}, found {reader.fieldnames}"
            )
        for line_number, row in enumerate(reader, start=2):
            source_id = row["source1_entity_id"]
            if source_id != source_id.strip() or not source_id.startswith("S1-"):
                raise SubmissionValidationError(
                    f"{path}:{line_number}: malformed Source 1 ID {source_id!r}"
                )
            if source_id in result:
                raise SubmissionValidationError(
                    f"{path}:{line_number}: duplicate Source 1 ID {source_id!r}"
                )
            raw = row[list_column]
            values = tuple(raw.split(",")) if raw else ()
            if any(not value or value != value.strip() for value in values):
                raise SubmissionValidationError(
                    f"{path}:{line_number}: malformed comma-separated ID list"
                )
            if len(values) != len(set(values)):
                raise SubmissionValidationError(
                    f"{path}:{line_number}: duplicate target IDs"
                )
            result[source_id] = values
    return result


def validate_submission(
    matching_path: Path,
    candidate_path: Path,
    test_dir: Path,
) -> SubmissionAudit:
    """Validate both files against IDs from the supplied test sources."""

    source_ids = read_entity_ids(test_dir / "test_source1.tsv", "S1-")
    target_ids = set(read_entity_ids(test_dir / "test_source2.tsv", "S2-"))
    target_ids.update(read_entity_ids(test_dir / "test_source3.tsv", "S3-"))

    matches = read_id_lists(matching_path, "matched_entity_ids")
    candidates = read_id_lists(candidate_path, "candidate_entity_ids")
    expected_sources = set(source_ids)
    for label, actual in (("matching", matches), ("candidate", candidates)):
        if set(actual) != expected_sources:
            missing = sorted(expected_sources - set(actual))[:3]
            extra = sorted(set(actual) - expected_sources)[:3]
            raise SubmissionValidationError(
                f"{label} rows do not match Source 1 IDs; missing={missing}, extra={extra}"
            )
        for values in actual.values():
            _validate_values(values, target_ids)

    for source_id, predicted in matches.items():
        outside_candidates = set(predicted) - set(candidates[source_id])
        if outside_candidates:
            raise SubmissionValidationError(
                f"{source_id}: matches absent from candidates: {sorted(outside_candidates)}"
            )

    return SubmissionAudit(
        source_entities=len(source_ids),
        candidate_links=sum(map(len, candidates.values())),
        predicted_links=sum(map(len, matches.values())),
    )

