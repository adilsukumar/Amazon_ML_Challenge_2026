import tempfile
import unittest
from pathlib import Path

from entity_resolution.baseline import write_singleton_baseline


class SingletonBaselineTests(unittest.TestCase):
    def test_writes_all_entities_with_empty_lists(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "test_source1.tsv"
            source.write_text(
                "entity_id\tbusiness_name\tbusiness_address\tcountry\n"
                "S1-2\tB\tAddr\tUS\nS1-1\tA\tAddr\tIndia\n",
                encoding="utf-8",
            )
            matching, candidates, rows = write_singleton_baseline(source, root / "output")
            self.assertEqual(rows, 2)
            self.assertEqual(
                matching.read_text(encoding="utf-8"),
                "source1_entity_id\tmatched_entity_ids\nS1-2\t\nS1-1\t\n",
            )
            self.assertEqual(
                candidates.read_text(encoding="utf-8"),
                "source1_entity_id\tcandidate_entity_ids\nS1-2\t\nS1-1\t\n",
            )


if __name__ == "__main__":
    unittest.main()
