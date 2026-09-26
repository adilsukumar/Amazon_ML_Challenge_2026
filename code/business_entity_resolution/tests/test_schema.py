import tempfile
import unittest
from pathlib import Path

from entity_resolution.schema import audit_ground_truth, audit_source_file


class SchemaAuditTests(unittest.TestCase):
    def test_valid_source_file(self) -> None:
        content = (
            "entity_id\tbusiness_name\tbusiness_address\tcountry\n"
            "S1-1\tExample Ltd\t1 Main St\tUS\n"
            "S1-2\t\tNear Station\tIndia\n"
        )
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "source.tsv"
            path.write_text(content, encoding="utf-8")
            audit = audit_source_file(path, "S1-")
        self.assertEqual(audit.rows, 2)
        self.assertEqual(audit.empty_name, 1)

    def test_comma_separated_file_is_rejected(self) -> None:
        content = "entity_id,business_name,business_address,country\nS1-1,A,B,US\n"
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "source.tsv"
            path.write_text(content, encoding="utf-8")
            with self.assertRaises(ValueError):
                audit_source_file(path, "S1-")

    def test_ground_truth_rejects_source1_match(self) -> None:
        content = "source1_entity_id\tmatched_entity_ids\nS1-1\tS1-2\n"
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "truth.tsv"
            path.write_text(content, encoding="utf-8")
            with self.assertRaises(ValueError):
                audit_ground_truth(path)


if __name__ == "__main__":
    unittest.main()

