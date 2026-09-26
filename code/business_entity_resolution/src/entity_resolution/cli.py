"""Command-line entry points for the entity resolution pipeline."""

from __future__ import annotations

import argparse
from pathlib import Path

from .schema import audit_ground_truth, audit_source_file


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
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if args.command == "audit-schema":
        return _audit_schema(args.dataset_dir)
    raise AssertionError(f"unhandled command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())

