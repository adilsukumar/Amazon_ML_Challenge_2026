# Bhumika's work: precision-focused matcher

Owner: [Bhumika Aswal](https://github.com/SpRinG-1303)  
Tracking issue: [#2](https://github.com/adilsukumar/Amazon_ML_Challenge_2026/issues/2)  
Deadline: 27 September 2026, 11:59 PM IST. Send a tested PR well before the deadline so integration and final packaging have time.

## Goal and boundary

Improve the final `matching_results.tsv` score using only the supplied competition data. The current exact-key matcher in `code/business_entity_resolution/src/entity_resolution/exact_matcher.py` is a reproducible v1 fallback. Its reported 0.38935 macro F0.5 is **in-sample**, not a held-out or leaderboard result. Do not claim a model beats it until both are evaluated on the same held-out Source 1 entities.

You own pair features, pair scoring/modeling, and the entity-level decision threshold. Snehal's workstream owns improved candidate generation. Start with the exact-key candidates so your code and tests do not wait for that workstream. Keep the candidate-input interface separate so a better blocker can be plugged in later.

## Start here

1. Clone or fork the repo and read [`CONTRIBUTING.md`](../CONTRIBUTING.md) and [`code/business_entity_resolution/README.md`](../code/business_entity_resolution/README.md).
2. Ask Adil for the official `student_resource.zip` privately. Extract its seven TSVs into local `dataset/train/` and `dataset/test/`; never commit or upload the raw dataset to the public repo.
3. From `code/business_entity_resolution`, run `python -m pip install -e .` and `python -m unittest discover -s tests -v`.
4. Work in a `model/...` branch. You currently have public read access; if GitHub does not allow a direct push, push to your fork and open a PR against `main`.

## First deliverable: an honest validation experiment

- Create a fixed, seeded split by **Source 1 entity**, retaining each entity's complete truth set and singletons. Do not split generated pairs randomly.
- Generate candidates without using validation labels. Record candidate recall ceiling and candidates per Source 1 entity.
- Build positive pairs from `train_ground_truth.tsv` and hard negatives from retrieved non-matches. Avoid treating every unlisted pair as a useful easy negative.
- Add a compact feature set: normalized name/address exact flags, token overlap/Jaccard, character similarity, numeric-token agreement, missingness, and source prefix. Preserve country as an open-set string; France appears only at test time.
- Train a permissively licensed model (or a transparent weighted scorer if installation/time is tight). Tune the final threshold on validation for **macro F0.5 per Source 1 entity**, including empty/empty singleton correctness.
- Compare against the exact-key baseline on the **same validation split**. Report precision, recall, macro F0.5, singleton accuracy, candidate recall, candidate-count distribution, runtime, and seed.

## Files and integration contract

Place implementation under `code/business_entity_resolution/src/entity_resolution/`, tests under `code/business_entity_resolution/tests/`, and a short experiment report under `docs/`. Provide a command that reads the official TSVs and writes `output/matching_results.tsv` with exactly one tab-separated row per test Source 1 ID. Every emitted match must be an S2/S3 ID present in that entity's `candidate_pairs.tsv` list. Do not overwrite Adil's validated v1 outputs until your change passes the official validator and its held-out metric is better.

Your PR should include the command, configuration/threshold, seed, metrics, runtime, and a note on any license/dependency. Alert Adil as soon as a verified improvement is ready; he owns final integration and the submission ZIP.

## Paste into your Codex chat

> Work on my Bhumika matcher assignment in `docs/BHUMIKA_README.md` and issue #2. First inspect the repo and available private dataset, then implement the smallest reproducible held-out Source 1 validation and a precision-focused pair matcher. Add tests, measure macro F0.5 and singleton accuracy against the exact-key baseline on the same split, and open a PR from my branch/fork. Do not use external business-identity lookup, commit raw data, or claim an unmeasured improvement. Tell me exactly what input or access is missing before changing scope.

