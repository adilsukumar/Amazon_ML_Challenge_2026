# Submission log

## v1 — exact-key baseline — 27 September 2026

- Git commit: `3457bf6`.
- Decision rule: `union` of exact normalized name and exact normalized address
  candidates within the same country.
- Training-set development macro F0.5: **0.389347**. This is not an independent
  holdout score; the same labeled set was used to compare four deterministic
  rules.
- Training candidate recall: **20.6139%** across 7,638,365 links.
- Training pair precision for selected rule: **92.3901%**.
- Test Source 1 rows: **1,732,544**.
- Test candidate links: **1,442,667** (0.833 per Source 1 row).
- Nonempty test predictions: **849,982** Source 1 rows.
- Official validator: **PASS** with `--check-ids`.
- Files: `outputs/matching_results.tsv`, `outputs/candidate_pairs.tsv`, and
  `outputs/Adil Sukumar_submission.zip` in the local workspace. The output files
  are excluded from Git because they are generated from the official dataset.
- Portal submission: **not yet uploaded**. Record the leaderboard score and
  submission time here after upload.

Next experiment: increase candidate recall with bounded fuzzy retrieval while
tracking candidates per Source 1 row and macro F0.5 on a fixed holdout.
