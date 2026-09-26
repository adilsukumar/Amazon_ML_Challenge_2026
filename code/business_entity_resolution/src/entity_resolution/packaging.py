"""Build the final competition ZIP with the required directory structure."""

from __future__ import annotations

from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile


EXCLUDED_PARTS = {"__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache"}
EXCLUDED_SUFFIXES = {".pyc", ".pyo"}


def _should_include(path: Path) -> bool:
    return not (set(path.parts) & EXCLUDED_PARTS) and path.suffix not in EXCLUDED_SUFFIXES


def build_submission_zip(
    *,
    team_name: str,
    code_dir: Path,
    output_dir: Path,
    documentation_path: Path,
    destination_dir: Path,
) -> Path:
    """Create `<team_name>_submission.zip` after checking required inputs."""

    required = (
        output_dir / "matching_results.tsv",
        output_dir / "candidate_pairs.tsv",
        code_dir / "README.md",
        code_dir / "requirements.txt",
        documentation_path,
    )
    missing = [str(path) for path in required if not path.is_file()]
    if missing:
        raise FileNotFoundError("cannot package; missing required files:\n- " + "\n- ".join(missing))
    if not team_name or any(character in team_name for character in "\\/:*?\"<>|"):
        raise ValueError("team_name must be a non-empty filename-safe value")

    destination_dir.mkdir(parents=True, exist_ok=True)
    zip_path = destination_dir / f"{team_name}_submission.zip"
    with ZipFile(zip_path, "w", compression=ZIP_DEFLATED, compresslevel=9) as archive:
        archive.write(required[0], "output/matching_results.tsv")
        archive.write(required[1], "output/candidate_pairs.tsv")
        for path in sorted(code_dir.rglob("*")):
            if path.is_file() and _should_include(path.relative_to(code_dir)):
                archive.write(path, Path("code/business_entity_resolution") / path.relative_to(code_dir))
        archive.write(documentation_path, "Documentation_template.md")
    return zip_path

