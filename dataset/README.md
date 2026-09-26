# Local competition data

Place the official Amazon ML Challenge 2026 files here. The data files are ignored
by Git and must never be committed.

```text
dataset/
├── train/
│   ├── train_source1.tsv
│   ├── train_source2.tsv
│   ├── train_source3.tsv
│   └── train_ground_truth.tsv
└── test/
    ├── test_source1.tsv
    ├── test_source2.tsv
    └── test_source3.tsv
```

After copying the files, run from `code/business_entity_resolution/`:

```bash
entity-resolution audit-schema --dataset-dir ../../dataset
```

Do not substitute data found in public repositories or external sources. Use only
the official files supplied to the team through the competition portal.

