# Features / Matching v1

Owner: Bhumika Aswal (@SpRinG-1303)  
Branch: `model/features-matching-v1`  
Seed: `2026`

## Scope

This experiment adds the supervised matching layer requested in `plan.md` without
changing candidate generation. The matcher is designed to consume pairs emitted by
the blocker, label positives from ground truth, retain blocker-derived hard
negatives, split by complete Source 1 entities, and tune decisions on a held-out
Source 1 split.

## Features

Name: exact normalized equality, token Jaccard, token containment,
SequenceMatcher ratio, length difference, shared token count.

Address: exact normalized equality, token Jaccard, token containment,
SequenceMatcher ratio, length difference, shared token count.

Numeric: numeric overlap count, exact-set agreement, conflict indicators for
name and address.

Missingness/cross-field: source/target missing flags, both-exact and
neither-exact flags.

## Model

One bounded `HistGradientBoostingClassifier` with seed 2026. All positives are
kept; hard negatives are selected from actual blocker candidates using exact,
sequence, token-overlap, and numeric-agreement signals.

## Validation protocol

- deterministic 80/20 split by Source 1 entity
- no pair-level random split
- singleton entities remain in evaluation
- threshold sweep: 0.30, 0.40, 0.50, 0.60, 0.65, 0.70, 0.75, 0.80, 0.85,
  0.90, 0.95
- report macro F0.5, macro precision, macro recall, and singleton accuracy
- compare the v1 exact-key rule on the same held-out Source 1 entities

## Current status

Code and synthetic unit tests are included. Real-data metrics are intentionally
**not reported here** because the supplied competition TSVs/candidate database
were unavailable in the coding workspace. Do not substitute synthetic scores for
competition validation.

Historical reference from `docs/submission_log.md`: v1 development macro F0.5
= **0.389347**. That value is not an independent holdout score and must not be
used as the fair comparison for this experiment.

## Reproduction

From `code/business_entity_resolution`:

```bash
python -m pip install -e .
python -m pytest -q
```

For the real experiment, place the official dataset in the repository's
documented local dataset paths, generate the blocker candidate database, then
join each candidate pair to raw Source 1/target fields and call
`build_pair_features`, `label_candidate_pairs`, `split_source1_ids`,
`select_training_examples`, `fit_model`, and the threshold helpers in
`entity_resolution.matcher`.

Real metrics must be added only after the same held-out Source 1 manifest is used
for both the supervised matcher and v1 exact-key baseline.
