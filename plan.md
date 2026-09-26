# Winning Blueprint — Amazon ML Challenge 2026

## 1. Mission

Build a reproducible, competition-compliant business entity resolution system
that maps each Source 1 entity to all matching Source 2 and Source 3 records while
maximizing macro F0.5.

F0.5 weights precision more heavily than recall. A false match can be especially
costly for a true singleton, so the final decision layer must be conservative.
Candidate generation has a different job: retain nearly every true match so the
matcher has the opportunity to score it.

The strategy is:

1. Retrieve broadly.
2. Measure the candidate recall ceiling.
3. Rank pairs with diverse, interpretable similarity features.
4. Tune final set predictions directly against macro F0.5.
5. Reject uncertain matches and protect singletons.

## 2. Definition of done

- A clean environment can reproduce training, validation, inference, and both
  output TSV files from documented commands.
- Validation uses held-out Source 1 entities and reports macro F0.5 at entity-set
  level.
- Candidate generation has measured recall, candidates per query, and reduction
  ratio by source and country.
- The final threshold is selected using out-of-fold or untouched validation
  predictions rather than training predictions.
- Every experiment has a configuration, seed, metrics, runtime, and conclusion.
- Official submission validation passes with no warnings.
- The final ZIP has the exact required structure, code, pinned dependencies,
  outputs, and methodology document.
- No stage uses prohibited external identity lookup or data augmentation.

## 3. Team operating model

Three parallel workstreams minimize overlap while preserving shared review.
Replace the placeholder identities in `CONTRIBUTORS.md` as soon as GitHub handles
are known.

| Workstream | Primary owner | Responsibilities | Main deliverables |
|---|---|---|---|
| Integration and evaluation | Adil | Repository architecture, deterministic pipeline, entity-level metric, output validation, packaging, release integration | CLI, configs, tests, validated releases |
| Data and candidate generation | Teammate A | Profiling, normalization, blocking, nearest-neighbour retrieval, candidate-recall analysis, performance tuning | Data report, blocker, candidate metrics |
| Features and matching model | Teammate B | Pair construction, hard negatives, feature engineering, model training, calibration, threshold studies | Feature pipeline, trained model, ablations |

Shared responsibilities:

- Every pull request receives at least one teammate review.
- No leaderboard result is trusted without a saved configuration and local
  validation report.
- The author of a major component is not its only reviewer.
- Methodology documentation is updated with relevant architectural changes.

### Weekly rhythm

- Start: agree on the smallest experiments that answer the current uncertainty.
- During: work on independent branches and post concise experiment results.
- Integration: merge only reproducible improvements.
- Submission: validate artifacts, tag the exact commit, and log leaderboard
  feedback without overfitting to it.

## 4. Phased execution plan

### Phase 0 — Foundation

Goal: make collaboration safe before modeling begins.

- [x] Initialize the Git repository and `main` branch.
- [x] Add the competition blueprint and contribution workflow.
- [ ] Add all three teammate names and GitHub handles.
- [ ] Add the official validator and documentation template.
- [ ] Place the seven TSV files under local `dataset/train` and `dataset/test`.
- [ ] Add a Python package, configuration, logging, and test runner.
- [ ] Add CI for unit tests and formatting without requiring private datasets.

Exit gate: every teammate can clone the repository, create the environment, and
run a smoke test.

### Phase 1 — Data audit and evaluation harness

Goal: understand the problem quantitatively and make the metric trustworthy.

- Validate TSV schemas, encodings, ID prefixes, uniqueness, and empty fields.
- Profile rows, missingness, scripts, lengths, token frequencies, and country
  distributions for all sources.
- Expand ground truth into positive pairs while retaining empty singleton rows.
- Implement exact per-entity macro F0.5, precision, recall, and singleton accuracy.
- Split by complete Source 1 entities. Never randomly split generated pairs.
- Create a fixed validation manifest committed without proprietary record data.
- Test metric edge cases: empty/empty, empty/non-empty, duplicate predictions, and
  partially correct multi-match sets.

Exit gate: a checked data report and unit-tested evaluator agree with hand-worked
examples.

### Phase 2 — High-recall candidate generation

Goal: create a fast candidate set whose recall ceiling does not bottleneck the
matcher.

Build separate Source 1→Source 2 and Source 1→Source 3 retrieval, then union:

- Exact normalized name and strong normalized address keys
- Rare name-token and address-token overlap
- Numeric token agreement for building, street, unit, and postal fragments
- Word and character n-gram TF-IDF nearest neighbours
- Conservative acronym and legal-suffix variants
- Country-compatible retrieval with a label-agnostic fallback
- Fallback top-K retrieval for records missed by strict blocks

Normalization must preserve raw and normalized representations. Avoid rules that
collapse distinct businesses because they share common legal words or generic
address tokens.

Measure:

- Positive-pair recall overall and by source/country
- Fraction of Source 1 entities retaining every true match
- Mean, median, p95, and maximum candidate counts
- Reduction ratio and wall-clock/memory cost
- Recall for missing fields, transliteration, token reordering, and multiple truth
  matches

Exit gate: recall is stable across validation slices and candidate volume is
practical for the feature pipeline.

### Phase 3 — Precision baseline

Goal: produce the first end-to-end valid submission quickly.

- Calculate name and address TF-IDF cosine similarities.
- Add token Jaccard, containment, edit/sequence, exact-normalized, acronym, numeric
  agreement, missingness, and retrieval-rank features.
- Establish a transparent weighted-score baseline.
- Tune its threshold on validation for macro F0.5.
- Generate both competition TSV files and run the official validator.

Exit gate: one command creates a valid submission and validation report.

### Phase 4 — Supervised matcher

Goal: outperform the heuristic baseline without losing reproducibility.

- Train on all positives plus hard negatives retrieved by the actual blocker.
- Use a permissively licensed gradient-boosted tree model such as LightGBM.
- Control negative sampling while retaining ambiguous near-matches.
- Add source, missingness, length, rank, margin, token-rarity, and cross-field
  agreement features.
- Generate out-of-fold scores for unbiased threshold and calibration work.
- Compare one global model against source-aware features or separate source models.
- Use a global fallback for unseen countries; do not limit logic to US and India.

Exit gate: the model beats the baseline and does not silently regress singleton
accuracy or major validation slices.

### Phase 5 — Entity-level decision optimization

Goal: convert pair scores into precision-oriented match sets.

Test with validation evidence:

- Global probability threshold
- Separate Source 2 and Source 3 thresholds
- Minimum score plus top-vs-second confidence margin
- High-confidence exact-match rules
- Abstention rules for ambiguous near-ties
- Probability calibration
- Per-query dynamic thresholds based on score distribution

Do not impose one-to-one matching or global target exclusivity unless the data
rules and validation evidence support that constraint. The task permits multiple
matches per Source 1 entity but does not specify global exclusivity.

Exit gate: the selected policy is frozen from validation and accompanied by a
threshold-sensitivity report.

### Phase 6 — Advanced experiments

Goal: spend complexity only where error analysis predicts a gain.

- Transliteration-aware character signals
- Phonetic similarity where appropriate
- Address-component extraction without external lookup
- Weak supervision for normalization variants
- Compact multilingual embeddings from a license-compliant model
- Retrieval/model ensembles
- A second-stage model for ambiguous scores

Every experiment compares against the current champion using the same split,
candidate universe, seed policy, and entity metric. Remove features that add
material latency or fragility without repeatable gain.

Exit gate: final components survive ablation and resource-budget checks.

### Phase 7 — Final training, submission, and audit

Goal: produce the exact artifact that can be reproduced and reviewed.

- Freeze code, configuration, dependencies, and thresholds.
- Retrain using the agreed full-data protocol.
- Generate `candidate_pairs.tsv` from the exact set scored by the matcher.
- Generate `matching_results.tsv`, preserving empty singleton rows.
- Run the official validator and internal semantic checks.
- Fill the methodology template with architecture, blocking, model, features,
  validation, ablations, licenses, resources, and reproduction commands.
- Build the required ZIP and inspect it in a clean directory.
- Tag the release commit and record the submission result.

Exit gate: clean-room reproduction succeeds and all output checks pass.

## 5. Validation design

### Primary split

Use a deterministic group split keyed by Source 1 entity. All positives and
generated negatives associated with one Source 1 entity remain in the same fold.
Keep a fixed holdout and use grouped cross-validation when compute permits.

### Primary metric

For Source 1 entity `i`, compare the predicted ID set with the true ID set and
calculate F0.5. Empty/empty receives 1.0; empty/non-empty or non-empty/empty receives
0.0. Average across every Source 1 entity, including singletons.

### Diagnostics

- Candidate pair recall and complete-entity candidate recall
- Pairwise precision-recall curve
- Macro precision, recall, and F0.5
- Singleton accuracy and false-positive rate
- Average predicted matches per entity
- Scores by source, country, missingness, and match cardinality
- Runtime, peak memory, and artifact sizes

## 6. Experiment protocol

Every experiment record contains:

```yaml
experiment_id: ""
git_commit: ""
date: ""
owner: ""
hypothesis: ""
data_manifest: ""
validation_split: ""
candidate_config: ""
feature_config: ""
model_config: ""
decision_config: ""
seed: 2026
metrics: {}
runtime_and_memory: ""
result: keep | reject | investigate
notes: ""
```

Change one concept per ablation when practical. Store the champion configuration
in version control; filenames such as `final2` or `best_latest` are not experiment
tracking.

## 7. GitHub workflow and visible contribution history

1. Sync `main` before beginning a task.
2. Create a focused branch such as `data/profile-report`, `blocking/tfidf`, or
   `model/lightgbm-baseline`.
3. Commit milestones using `feat:`, `fix:`, `docs:`, `test:`, `refactor:`, `perf:`,
   or `chore:`.
4. Push the branch and open a pull request referencing the backlog item or issue.
5. Include validation evidence and schema/configuration changes in the PR.
6. Obtain at least one teammate review before merge.
7. Prefer squash merge for noisy experiments; preserve meaningful standalone
   commits where their history aids reproduction.

GitHub counts a teammate as a contributor when their commits are authored with an
email connected to their GitHub account and those commits reach the default branch.
`CONTRIBUTORS.md` provides human-readable credit but does not replace authorship.

Never rewrite shared history, commit datasets or secrets, or add a teammate as a
co-author unless they genuinely contributed and agree to the attribution.

## 8. Repository contracts

### Data

- Read TSVs with an explicit tab separator.
- Keep IDs as strings.
- Keep raw text immutable; derive normalized columns alongside it.
- Treat country as an open string label.
- Keep competition datasets out of Git.

### Candidates

- Include only Source 2 or Source 3 IDs from the relevant split.
- Deduplicate and sort deterministically.
- Export exactly the universe scored by the final matcher.
- Ensure every predicted match exists in its candidate list.

### Outputs

- Write exactly one row per Source 1 test ID in deterministic order.
- Serialize empty lists as empty fields.
- Never emit quoting, whitespace padding, or duplicate IDs in ID lists.
- Match specified headers and tab delimiters exactly.

## 9. Risk register

| Risk | Early signal | Mitigation |
|---|---|---|
| Candidate recall bottleneck | True pair absent from candidates | Union blockers; measure ceiling before model tuning |
| Singleton false merges | Pair recall high but macro F0.5 weak | Tune abstention on entity-level validation |
| Leakage | Implausibly strong random-pair score | Split Source 1 entities before pair generation |
| France failure | Country-specific rules dominate | Open-set normalization and agnostic fallback |
| Resource failure | Candidate explosion or memory spike | Batch retrieval/scoring; profile and cap stages |
| Leaderboard overfitting | Public gain without local gain | Fixed validation and submission log |
| Irreproducible result | Score cannot be rebuilt | Configs, seeds, manifests, tagged releases |
| Compliance failure | External lookup or bad license | Data-lineage and dependency/license audit |
| Merge conflicts | Concurrent edits to core files | Module ownership, interfaces, small PRs |

## 10. Immediate backlog

### P0 — now

- [ ] Add teammate names, GitHub handles, and preferred areas.
- [ ] Obtain and locally place datasets and official validator.
- [ ] Record file sizes and compute: CPU, RAM, GPU, and disk.
- [ ] Scaffold package, CLI, configuration, logging, and tests.
- [ ] Implement schema validation and exact macro F0.5 tests.
- [ ] Produce the first data-profile report.

### P1 — after audit

- [ ] Implement normalization with raw-value preservation.
- [ ] Implement exact and rare-token blockers.
- [ ] Implement batched character TF-IDF nearest-neighbour retrieval.
- [ ] Report candidate recall and resource usage.
- [ ] Build the weighted-similarity baseline.
- [ ] Produce and validate the first submission files.

### P2 — competitive iteration

- [ ] Add hard-negative mining and a LightGBM matcher.
- [ ] Run grouped cross-validation and out-of-fold threshold tuning.
- [ ] Perform error taxonomy and feature ablations.
- [ ] Test targeted advanced features.
- [ ] Freeze, document, package, and tag the final solution.

## 11. Decision principles

- Optimize candidate generation for recall and final matching for precision-weighted
  macro F0.5.
- Require reproducible validation gain before changing the architecture.
- Prefer simpler systems when results tie.
- Treat singletons as a first-class outcome.
- Treat unseen-country support as an architectural constraint.
- Build to win, while ensuring every leaderboard point survives private evaluation,
  compliance review, and clean-room reproduction.

