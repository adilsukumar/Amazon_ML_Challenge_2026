# Amazon ML Challenge 2026 — Business Entity Resolution

This repository contains our team’s end-to-end solution for the Amazon ML
Challenge 2026 Business Entity Resolution task.

The objective is to link every Source 1 business record to zero or more matching
records from Source 2 and Source 3. The leaderboard metric is macro-averaged
F0.5, so the project is deliberately optimized for precision while preserving a
high-recall candidate-generation stage.

## Current status

The project is in its foundation phase. The competition blueprint, team workflow,
and repository conventions are defined; data profiling and the first reproducible
baseline are next.

See [plan.md](plan.md) for the technical blueprint, work breakdown, experiment
gates, and submission checklist.

## Planned repository layout

```text
.
├── code/business_entity_resolution/
│   ├── src/entity_resolution/
│   ├── tests/
│   ├── README.md
│   └── requirements.txt
├── dataset/                         # local only; never committed
│   ├── train/
│   └── test/
├── docs/
├── experiments/
├── output/                          # generated competition TSVs
├── utils/
├── CONTRIBUTORS.md
├── CONTRIBUTING.md
└── plan.md
```

## Non-negotiable rules

- Use only the supplied competition data; no external entity lookup, geocoding,
  business registry, or enrichment service.
- Treat country labels as an open set. France appears only in test data, and the
  pipeline must process it without special-case failure.
- Generate exactly one output row for every Source 1 test entity.
- Every predicted match must be a valid Source 2 or Source 3 test ID and must also
  appear in that entity’s final candidate list.
- Prefer reproducible experiments and measured validation gains over speculative
  complexity.

## Team

The active team has three members. Team identities and ownership are maintained in
[CONTRIBUTORS.md](CONTRIBUTORS.md). GitHub’s contributor graph will credit each
person after they commit using an email linked to their own GitHub account.

## Collaboration

Read [CONTRIBUTING.md](CONTRIBUTING.md) before starting work. In short: work on a
small branch, add or update tests, record experiment results, and merge through a
reviewed pull request.

