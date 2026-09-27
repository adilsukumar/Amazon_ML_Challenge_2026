# Business Entity Resolution Pipeline

This directory is the self-contained competition implementation.

## Development smoke test

From this directory, run:

```bash
python -m unittest discover -s tests -v
```

The initial test suite uses only the Python standard library and does not require
the private competition dataset.

## Validate local dataset structure

After placing the competition files under the repository-level `dataset/`
directory:

```bash
python -m entity_resolution.cli audit-schema --dataset-dir ../../dataset
```

During development, either install the package in editable mode or set
`PYTHONPATH=src` before invoking the module directly.

```bash
python -m pip install -e .
```

## Reproduce the exact-key baseline

The following commands use only the supplied data and Python standard library.
Run from this directory after `python -m pip install -e .`, or set
`PYTHONPATH=src`. Use fresh database paths for each run; the commands refuse to
overwrite an existing database.

```bash
entity-resolution exact-train \
  --train-dir ../../dataset/train \
  --database ../../artifacts/exact_train.sqlite \
  --report ../../artifacts/reports/exact_train.json

entity-resolution exact-predict \
  --test-dir ../../dataset/test \
  --database ../../artifacts/exact_test.sqlite \
  --output-dir ../../output \
  --rule union

python src/official_validate_submission.py \
  --matching ../../output/matching_results.tsv \
  --candidate ../../output/candidate_pairs.tsv \
  --test-dir ../../dataset/test --check-ids
```

The `union` rule had the highest development-set macro F0.5 of the four exact
rules evaluated. See the methodology document for metrics and limitations.

## Validate generated output

```bash
entity-resolution validate-output \
  --matching ../../output/matching_results.tsv \
  --candidate ../../output/candidate_pairs.tsv \
  --test-dir ../../dataset/test
```

## Build the final package

Run this only after both output files and the filled methodology document exist:

```bash
entity-resolution package-submission \
  --team-name YOUR_TEAM_NAME \
  --code-dir . \
  --output-dir ../../output \
  --documentation ../../Documentation_template.md \
  --destination-dir ../../dist
```
