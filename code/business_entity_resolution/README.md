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

Training and inference commands will be added after the data audit establishes
the dataset scale and resource constraints.

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
