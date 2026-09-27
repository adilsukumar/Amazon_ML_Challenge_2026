# Candidate-generation workstream (Snehal)

Named owner: [Snehal Dixit](https://github.com/snehaldixitofficial)  
Tracking issue: [#1](https://github.com/adilsukumar/Amazon_ML_Challenge_2026/issues/1)  
Deadline: 27 September 2026, 11:59 PM IST.

Adil is covering this work while Snehal is unavailable. Commit authorship must reflect the person who actually makes each change. Do not use Snehal's account or name for Adil-authored commits; credit Snehal for her own work when she contributes.

## Goal and boundary

Improve candidate recall without losing blocking scalability. The current v1 exact-key generator is in `code/business_entity_resolution/src/entity_resolution/exact_matcher.py`. It produced 1,442,667 test candidate links for 1,732,544 Source 1 rows (0.833 links/query on average), but its recall ceiling is limited by exact keys. The official challenge also values a **small** final candidate set per Source 1 entity, so do not simply dump broad fuzzy neighbors.

This workstream owns retrieval/blocking and `candidate_pairs.tsv`. Bhumika owns pair scoring and final match decisions. Preserve a clean interface: a stream of `(source1_entity_id, candidate_entity_id)` pairs with no truth leakage.

Adil has added `src/entity_resolution/prefix_blocker.py` as an **experimental**, test-covered channel that adds at most eight same-country, eight-character name-prefix candidates per Source 1 row. It is not included in the submitted outputs and must not be called a score improvement until full training recall and candidate-volume measurements finish. The public leaderboard baseline is 0.407; this does not establish any score for the new channel.

## Start here

1. Obtain the official ZIP privately from Adil and extract the seven TSVs under local `dataset/`. Never commit the dataset.
2. Run the standard tests from `code/business_entity_resolution`: `python -m unittest discover -s tests -v`.
3. Read [`code/business_entity_resolution/README.md`](../code/business_entity_resolution/README.md) to reproduce the v1 baseline.
4. Work on a `blocking/...` branch or fork-based PR. Do not replace the validated v1 outputs during an active Unstop upload.

## First deliverable: measured incremental blocker

- Make a seeded held-out split by complete Source 1 entities. Train any token statistics on the training fold only; retrieve validation queries without using their truth labels.
- Add one bounded retrieval channel to exact keys: for example rare name tokens with address/numeric corroboration, or character n-gram TF-IDF top-K within country. Keep country open-set; France must work at inference.
- Deduplicate candidates, cap candidates per query, and never compare every S1 record with every S2/S3 record.
- Measure positive-pair recall, fraction of S1 entities whose **entire** truth set is retained, mean/p95/max candidates per query, country/source slices, wall-clock time, and memory use. Compare against the existing exact-key blocker on the same validation split.
- Add tests for punctuation, Unicode, missing address/name, cross-source IDs, and deterministic ordering.
- Emit all test Source 1 IDs in `candidate_pairs.tsv`, including empty rows. Every final predicted ID must be a subset of candidates. Run `src/official_validate_submission.py` with `--check-ids` before proposing a release.

Submit a PR with code, tests, exact commands, metrics, runtime, and an explanation of the candidate-count/recall trade-off. Coordinate candidate-list format with Bhumika so her scorer can consume it.

## Paste into your Codex chat

> Work on the candidate-generation assignment in `docs/SNEHAL_README.md` and issue #1. Start with a held-out Source 1 validation of the existing exact-key blocker, then add one bounded high-recall retrieval channel using only the official data. Measure recall ceiling and candidate volume, test edge cases, and open a PR from the actual author's account. Do not use external business-identity lookup or commit raw data. Preserve the validated v1 files until Adil integrates a measured improvement.

