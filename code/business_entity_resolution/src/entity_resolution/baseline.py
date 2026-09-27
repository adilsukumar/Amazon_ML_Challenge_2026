"""Fast emergency baselines that obey every submission contract."""

from __future__ import annotations

import csv
from pathlib import Path


def write_singleton_baseline(test_source1: Path, output_dir: Path) -> tuple[Path, Path, int]:
    """Predict every test Source 1 record as a singleton.

    This is intentionally conservative and exists as a guaranteed-valid fallback.
    It must be replaced by the trained matcher for the final competitive submission.
    """

    output_dir.mkdir(parents=True, exist_ok=True)
    matching_path = output_dir / "matching_results.tsv"
    candidate_path = output_dir / "candidate_pairs.tsv"
    rows = 0
    with (
        test_source1.open("r", encoding="utf-8-sig", newline="") as source,
        matching_path.open("w", encoding="utf-8", newline="") as matching,
        candidate_path.open("w", encoding="utf-8", newline="") as candidates,
    ):
        reader = csv.DictReader(source, delimiter="\t")
        if not reader.fieldnames or "entity_id" not in reader.fieldnames:
            raise ValueError(f"{test_source1}: missing entity_id column")
        matching_writer = csv.writer(matching, delimiter="\t", lineterminator="\n")
        candidate_writer = csv.writer(candidates, delimiter="\t", lineterminator="\n")
        matching_writer.writerow(("source1_entity_id", "matched_entity_ids"))
        candidate_writer.writerow(("source1_entity_id", "candidate_entity_ids"))
        for row in reader:
            entity_id = row["entity_id"].strip()
            if not entity_id.startswith("S1-"):
                raise ValueError(f"invalid Source 1 ID: {entity_id!r}")
            matching_writer.writerow((entity_id, ""))
            candidate_writer.writerow((entity_id, ""))
            rows += 1
    return matching_path, candidate_path, rows
