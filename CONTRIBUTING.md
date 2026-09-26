# Contributing

## Before starting

1. Read `plan.md` and select an unowned backlog item.
2. Confirm the component interface with the relevant workstream owner.
3. Create a branch from the latest `main`.

Recommended branch names:

- `data/<topic>`
- `blocking/<topic>`
- `features/<topic>`
- `model/<topic>`
- `evaluation/<topic>`
- `docs/<topic>`
- `fix/<topic>`

## Commits

Use concise conventional commit messages, for example:

```text
feat(blocking): add character n-gram retrieval
test(metric): cover singleton prediction cases
docs(experiment): record threshold ablation
fix(output): preserve empty match fields
```

Commit logical milestones rather than entire days of unrelated work. Never commit
competition datasets, credentials, local environments, caches, or unreviewed large
model artifacts.

Configure Git with an email linked to your GitHub account so your work appears in
GitHub’s contributor graph:

```bash
git config user.name "Your Name"
git config user.email "your-linked-email@example.com"
```

GitHub’s privacy `noreply` email is suitable when it is linked to the account.

## Pull requests

Every pull request should explain:

- The hypothesis or problem
- What changed
- How it was tested
- Validation metrics before and after, if applicable
- Runtime or memory effects
- Any new files, configuration, or reproduction steps

At least one teammate should review the pull request. Do not merge a model or
blocking change solely because it improves a public leaderboard score.

## Tests and reproducibility

- Add unit tests for parsing, metrics, candidate contracts, and output contracts.
- Use deterministic seeds where supported.
- Keep configurations in version control.
- Store aggregate experiment metrics, never proprietary dataset rows.
- Ensure a clean clone can run smoke tests without the private dataset.

## Data and compliance

This competition prohibits external business identity lookup and enrichment. Do
not call geocoders, map services, registries, search engines, entity-resolution
APIs, or external business databases. Libraries and pretrained models are allowed
only when they meet the competition’s license and parameter constraints and do not
perform prohibited data lookup.

