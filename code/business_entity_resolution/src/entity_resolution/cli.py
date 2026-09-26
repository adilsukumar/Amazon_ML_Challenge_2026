"""Command-line entry points for the entity resolution pipeline."""

from __future__ import annotations

import argparse
from pathlib import Path

from .packaging import build_submission_zip
from .schema import audit_ground_truth, audit_source_file
from .submission import validate_submission


def _audit_schema(dataset_dir: Path) -> int:
    files = (
        (dataset_dir / "train" / "train_source1.tsv", "S1-"),
        (dataset_dir / "train" / "train_source2.tsv", "S2-"),
        (dataset_dir / "train" / "train_source3.tsv", "S3-"),
        (dataset_dir / "test" / "test_source1.tsv", "S1-"),
        (dataset_dir / "test" / "test_source2.tsv", "S2-"),
        (dataset_dir / "test" / "test_source3.tsv", "S3-"),
    )
    missing = [str(path) for path, _ in files if not path.is_file()]
    truth_path = dataset_dir / "train" / "train_ground_truth.tsv"
    if not truth_path.is_file():
        missing.append(str(truth_path))
    if missing:
        raise FileNotFoundError("missing required files:\n- " + "\n- ".join(missing))

    for path, prefix in files:
        audit = audit_source_file(path, prefix)
        print(
            f"{path.name}: rows={audit.rows:,}, empty_name={audit.empty_name:,}, "
            f"empty_address={audit.empty_address:,}, empty_country={audit.empty_country:,}"
        )
    print(f"{truth_path.name}: rows={audit_ground_truth(truth_path):,}")
    print("Schema audit: PASS")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    audit_parser = subparsers.add_parser("audit-schema", help="validate competition TSV schemas")
    audit_parser.add_argument("--dataset-dir", type=Path, required=True)

    output_parser = subparsers.add_parser(
        "validate-output", help="validate candidate and matching output files"
    )
    output_parser.add_argument("--matching", type=Path, required=True)
    output_parser.add_argument("--candidate", type=Path, required=True)
    output_parser.add_argument("--test-dir", type=Path, required=True)

    package_parser = subparsers.add_parser(
        "package-submission", help="build the final required submission ZIP"
    )
    package_parser.add_argument("--team-name", required=True)
    package_parser.add_argument("--code-dir", type=Path, default=Path.cwd())
    package_parser.add_argument("--output-dir", type=Path, required=True)
    package_parser.add_argument("--documentation", type=Path, required=True)
    package_parser.add_argument("--destination-dir", type=Path, required=True)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if args.command == "audit-schema":
        return _audit_schema(args.dataset_dir)
    if args.command == "validate-output":
        audit = validate_submission(args.matching, args.candidate, args.test_dir)
        print(
            f"Submission validation: PASS; source_entities={audit.source_entities:,}, "
            f"candidates={audit.candidate_links:,}, predictions={audit.predicted_links:,}"
        )
        return 0
    if args.command == "package-submission":
        path = build_submission_zip(
            team_name=args.team_name,
            code_dir=args.code_dir,
            output_dir=args.output_dir,
            documentation_path=args.documentation,
            destination_dir=args.destination_dir,
        )
        print(f"Created {path}")
        return 0
    raise AssertionError(f"unhandled command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
