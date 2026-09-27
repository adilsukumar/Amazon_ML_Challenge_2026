import csv
import tempfile
import unittest
from pathlib import Path

from entity_resolution.exact_matcher import (
    build_database,
    evaluate_rules,
    generate_candidates,
    normalize,
    write_outputs,
)


def write_source(path: Path, rows: list[tuple[str, str, str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
        writer.writerow(("entity_id", "business_name", "business_address", "country"))
        writer.writerows(rows)


class ExactMatcherTests(unittest.TestCase):
    def test_normalization(self) -> None:
        self.assertEqual(normalize("  ACME & Sons, Ltd. "), "acme and sons ltd")

    def test_end_to_end_exact_match(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_source(
                root / "s1.tsv",
                [("S1-1", "Acme & Sons", "1 Main St.", "US"), ("S1-2", "Solo", "2 Road", "US")],
            )
            write_source(
                root / "s2.tsv",
                [("S2-1", "ACME and Sons", "1 Main St", "US")],
            )
            write_source(root / "s3.tsv", [("S3-1", "Other", "Elsewhere", "US")])
            (root / "truth.tsv").write_text(
                "source1_entity_id\tmatched_entity_ids\nS1-1\tS2-1\nS1-2\t\n",
                encoding="utf-8",
            )
            connection = build_database(
                database_path=root / "test.sqlite",
                source1_path=root / "s1.tsv",
                source2_path=root / "s2.tsv",
                source3_path=root / "s3.tsv",
                truth_path=root / "truth.tsv",
            )
            try:
                generate_candidates(connection)
                report = evaluate_rules(connection)
                matching, candidates = write_outputs(connection, root / "output", rule="both")
            finally:
                connection.close()
            self.assertEqual(report["both"]["macro_f0_5"], 1.0)
            self.assertIn("S1-1\tS2-1", matching.read_text(encoding="utf-8"))
            self.assertIn("S1-2\t\n", candidates.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
