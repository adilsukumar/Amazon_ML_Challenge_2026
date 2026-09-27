# Amazon ML Challenge 2026: Business Entity Resolution

**Team name:** Adil Sukumar

**Team members:** Adil Sukumar, Snehal Dixit, Bhumika Aswal

**Submission date:** 27 September 2026
**Version:** Exact-key baseline v1 (`union` decision rule)

## 1. Executive summary

We built a disk-backed, deterministic entity-resolution pipeline using only the
official competition TSVs. It normalizes text, retrieves candidate Source 2/3
records through selective exact name and address keys within each country, and
predicts the union of these candidates. The same scored set is emitted as
`candidate_pairs.tsv`, preserving an auditable blocking stage.

## 2. Methodology

### 2.1 Problem analysis

The official training set contains 2,206,821 Source 1 records and 7,638,365
ground-truth links. Only 123,247 Source 1 records (5.58%) are singletons, so an
all-empty prediction is a poor competitive baseline. The test set has 1,732,544
Source 1 records, including 259,452 from France, which is absent from training.
Our normalizer and blocker treat country labels as open strings; France therefore
uses the same path as US and India.

### 2.2 Solution strategy

The current deliverable is a compact, high-precision baseline. Input TSVs are
streamed into SQLite to avoid loading the full dataset into memory. Names,
addresses, and country labels are Unicode NFKC normalized, casefolded, stripped
of punctuation, and whitespace normalized. An ampersand is converted to `and`.
Raw source files are not modified.

The pipeline uses exact-key blocking and a deterministic rule matcher. It does
not use an external identity database, geocoder, API, or pretrained model.

## 3. Candidate generation

The candidate set is the union of:

1. Equal normalized name and address in the same country, with both fields
   nonempty.
2. Equal normalized name in the same country when that name occurs once in
   Source 1 and is at least five characters long.
3. Equal normalized address in the same country when that address occurs once
   in Source 1 and is at least eight characters long.

The uniqueness condition suppresses broad joins on common business names and
addresses. Candidates are deduplicated by `(source1_entity_id,
candidate_entity_id)` in SQLite. There is no all-pairs comparison, no hardcoded
country list, and no top-K cut on a retrieved key. The exact set scored by the
matching rule is written to `candidate_pairs.tsv`.

On full training data this generated 1,704,260 candidate pairs, or 0.772 per
Source 1 record. It retained 1,574,568 of 7,638,365 true links (20.61% pair
recall). On test data it generated 1,442,667 candidates, or 0.833 per Source 1
record. Candidate counts by test country were 624,241 (US), 508,023 (India),
and 310,403 (France).

This is deliberately compact, but its 20.61% training recall is the clear
limitation of this version. A future blocker should add selective fuzzy retrieval
while measuring recall, candidate volume, and runtime.

## 4. Matching model

**Features:** Boolean equality of normalized name and normalized address,
after the country-compatible blocking described above.

**Model:** Deterministic `union` rule. A candidate with either equality signal
is predicted as a match. Since the candidate generator emits only these three
exact-key cases, all candidates are scored and selected. No learned model or
license-restricted model is used in this version.

**Selection:** Four rule variants were compared on labeled training data:
both fields, name, address, and their union. The union had the highest measured
macro F0.5. This comparison used the same training set for rule choice and
reporting, so the 0.3893 figure is an in-sample development score, not an
independent holdout estimate. The test labels remain unseen.

## 5. Results and error analysis

| Rule | Macro F0.5 on training | Pair precision | Pair recall | Predicted links |
|---|---:|---:|---:|---:|
| Both fields | 0.0828 | 1.0000 | 0.0130 | 99,283 |
| Name | 0.2952 | 0.8997 | 0.1409 | 1,196,174 |
| Address | 0.2004 | 0.9840 | 0.0782 | 607,369 |
| Union (selected) | 0.3893 | 0.9239 | 0.2061 | 1,704,260 |

The principal false negatives are expected to be records with typos,
transliterations, abbreviations, and address or name changes that do not survive
normalization. Generic names may be filtered by the Source 1 uniqueness rule.
False positives may occur for businesses sharing a distinctive name or address;
the name-only development precision was 89.97%.

The generated test outputs contain exactly 1,732,544 rows each; 849,982 rows
contain one or more candidates and predictions, and 882,562 have empty lists.
Amazon's official `utils/validate_submission.py --check-ids` returned `PASS` on
both files.

## 6. Reproduction and audit

The code is self-contained under `code/business_entity_resolution/`; it uses
Python 3.10+ and only the standard library. From that directory, with
`PYTHONPATH=src` (or after `python -m pip install -e .`), run:

```bash
python -m entity_resolution.cli exact-train \
  --train-dir ../../dataset/train \
  --database ../../artifacts/exact_train.sqlite \
  --report ../../artifacts/reports/exact_train.json

python -m entity_resolution.cli exact-predict \
  --test-dir ../../dataset/test \
  --database ../../artifacts/exact_test.sqlite \
  --output-dir ../../output \
  --rule union

python src/official_validate_submission.py \
  --matching ../../output/matching_results.tsv \
  --candidate ../../output/candidate_pairs.tsv \
  --test-dir ../../dataset/test --check-ids
```

The database commands refuse to overwrite an existing database. Use new paths
for a new run. Each TSV writer emits exactly one Source 1 row in sorted ID order,
deduplicated S2/S3 IDs, and an empty field for singletons.

`src/entity_resolution/exact_matcher.py` implements ingestion, normalization,
blocking, rule evaluation, and output generation. `src/entity_resolution/cli.py`
provides the commands. The organizer's validator is copied unmodified into
`src/official_validate_submission.py` so the packaged code remains self-contained.
The package also contains unit tests.

## 7. Next iteration

The next competitive step is a fuzzy retrieval stage with measured candidate
recall and a pairwise matcher trained on hard negatives. The v1 artifact is
preserved so later work can be compared against a reproducible baseline.
