import tempfile
import unittest
from pathlib import Path
from zipfile import ZipFile

from entity_resolution.packaging import build_submission_zip


class PackagingTests(unittest.TestCase):
    def test_required_archive_layout(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            code_dir = root / "code-source"
            output_dir = root / "output-source"
            destination = root / "dist"
            code_dir.mkdir()
            output_dir.mkdir()
            (code_dir / "src").mkdir()
            (code_dir / "README.md").write_text("run me", encoding="utf-8")
            (code_dir / "requirements.txt").write_text("", encoding="utf-8")
            (code_dir / "src" / "main.py").write_text("print('ok')", encoding="utf-8")
            (code_dir / "src" / "ignored.pyc").write_bytes(b"cache")
            (output_dir / "matching_results.tsv").write_text("matching", encoding="utf-8")
            (output_dir / "candidate_pairs.tsv").write_text("candidates", encoding="utf-8")
            documentation = root / "method.md"
            documentation.write_text("method", encoding="utf-8")

            archive_path = build_submission_zip(
                team_name="winning-team",
                code_dir=code_dir,
                output_dir=output_dir,
                documentation_path=documentation,
                destination_dir=destination,
            )

            with ZipFile(archive_path) as archive:
                names = set(archive.namelist())
            self.assertIn("output/matching_results.tsv", names)
            self.assertIn("output/candidate_pairs.tsv", names)
            self.assertIn("code/business_entity_resolution/src/main.py", names)
            self.assertIn("Documentation_template.md", names)
            self.assertNotIn("code/business_entity_resolution/src/ignored.pyc", names)


if __name__ == "__main__":
    unittest.main()

