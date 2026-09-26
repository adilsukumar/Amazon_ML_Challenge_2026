import csv
import tempfile
import unittest
from pathlib import Path

from entity_resolution.submission import (
    SubmissionValidationError,
    validate_submission,
    write_id_lists,
)


def write_source(path: Path, ids: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
        writer.writerow(("entity_id", "business_name", "business_address", "country"))
        for entity_id in ids:
            writer.writerow((entity_id, "Name", "Address", "US"))


class SubmissionTests(unittest.TestCase):
    def test_round_trip_valid_submission(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            test_dir = root / "test"
            test_dir.mkdir()
            write_source(test_dir / "test_source1.tsv", ["S1-1", "S1-2"])
            write_source(test_dir / "test_source2.tsv", ["S2-1"])
            write_source(test_dir / "test_source3.tsv", ["S3-1"])
            allowed = {"S2-1", "S3-1"}
            candidate_path = root / "candidate_pairs.tsv"
            matching_path = root / "matching_results.tsv"
            write_id_lists(
                candidate_path,
                ["S1-1", "S1-2"],
                {"S1-1": ["S3-1", "S2-1"]},
                list_column="candidate_entity_ids",
                allowed_targets=allowed,
            )
            write_id_lists(
                matching_path,
                ["S1-1", "S1-2"],
                {"S1-1": ["S2-1"]},
                list_column="matched_entity_ids",
                allowed_targets=allowed,
            )
            audit = validate_submission(matching_path, candidate_path, test_dir)
            self.assertEqual(audit.source_entities, 2)
            self.assertEqual(audit.candidate_links, 2)
            self.assertEqual(audit.predicted_links, 1)
            lines = matching_path.read_text(encoding="utf-8").splitlines()
            self.assertEqual(lines[-1], "S1-2\t")

    def test_match_must_be_candidate(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            test_dir = root / "test"
            test_dir.mkdir()
            write_source(test_dir / "test_source1.tsv", ["S1-1"])
            write_source(test_dir / "test_source2.tsv", ["S2-1"])
            write_source(test_dir / "test_source3.tsv", [])
            matching = root / "matching.tsv"
            candidate = root / "candidate.tsv"
            write_id_lists(
                matching,
                ["S1-1"],
                {"S1-1": ["S2-1"]},
                list_column="matched_entity_ids",
                allowed_targets={"S2-1"},
            )
            write_id_lists(
                candidate,
                ["S1-1"],
                {},
                list_column="candidate_entity_ids",
                allowed_targets={"S2-1"},
            )
            with self.assertRaises(SubmissionValidationError):
                validate_submission(matching, candidate, test_dir)


if __name__ == "__main__":
    unittest.main()

