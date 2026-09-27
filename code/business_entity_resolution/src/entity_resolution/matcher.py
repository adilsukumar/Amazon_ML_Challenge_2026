"""Minimal supervised matcher for blocker candidate pairs."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Iterable, Mapping, Sequence

from .metrics import score_entity
from .pair_features import vectorize

SEED = 2026
THRESHOLDS = (0.30, 0.40, 0.50, 0.60, 0.65, 0.70, 0.75, 0.80, 0.85, 0.90, 0.95)


@dataclass(frozen=True)
class PairExample:
    source1_id: str
    target_id: str
    features: dict[str, float]
    label: int


def split_source1_ids(
    source1_ids: Iterable[str], *, validation_fraction: float = 0.20, seed: int = SEED
) -> tuple[set[str], set[str]]:
    """Deterministically split complete Source 1 entities, never individual pairs."""
    if not 0 < validation_fraction < 1:
        raise ValueError("validation_fraction must be between 0 and 1")
    train, validation = set(), set()
    cutoff = int(validation_fraction * 10_000)
    for entity_id in sorted(set(source1_ids)):
        digest = hashlib.sha256(f"{seed}:{entity_id}".encode()).digest()
        bucket = int.from_bytes(digest[:4], "big") % 10_000
        (validation if bucket < cutoff else train).add(entity_id)
    return train, validation


def label_candidate_pairs(
    pairs: Iterable[tuple[str, str, dict[str, float]]],
    truth_by_entity: Mapping[str, set[str]],
) -> list[PairExample]:
    return [
        PairExample(s1, target, features, int(target in truth_by_entity.get(s1, set())))
        for s1, target, features in pairs
    ]


def hard_negative_key(example: PairExample) -> tuple[float, ...]:
    f = example.features
    return (
        f.get("name_exact", 0.0) + f.get("address_exact", 0.0),
        f.get("name_sequence", 0.0) + f.get("address_sequence", 0.0),
        f.get("name_jaccard", 0.0) + f.get("address_jaccard", 0.0),
        f.get("address_numeric_overlap", 0.0),
    )


def select_training_examples(
    examples: Sequence[PairExample], *, negatives_per_positive: int = 5
) -> list[PairExample]:
    """Keep all positives and the hardest blocker-derived negatives per query."""
    by_query: dict[str, list[PairExample]] = {}
    for ex in examples:
        by_query.setdefault(ex.source1_id, []).append(ex)

    selected: list[PairExample] = []
    for rows in by_query.values():
        positives = [r for r in rows if r.label]
        negatives = sorted(
            (r for r in rows if not r.label),
            key=hard_negative_key,
            reverse=True,
        )
        selected.extend(positives)
        cap = max(negatives_per_positive, negatives_per_positive * len(positives))
        selected.extend(negatives[:cap])
    return selected


def fit_model(examples: Sequence[PairExample]):
    """Fit one bounded sklearn tree model; dependency is imported lazily."""
    from sklearn.ensemble import HistGradientBoostingClassifier

    if not examples or len({e.label for e in examples}) < 2:
        raise ValueError("training requires both positive and negative examples")
    model = HistGradientBoostingClassifier(
        learning_rate=0.08,
        max_iter=150,
        max_leaf_nodes=15,
        l2_regularization=1.0,
        random_state=SEED,
    )
    model.fit(vectorize(e.features for e in examples), [e.label for e in examples])
    return model


def score_examples(model, examples: Sequence[PairExample]) -> list[tuple[PairExample, float]]:
    probs = model.predict_proba(vectorize(e.features for e in examples))[:, 1]
    return list(zip(examples, map(float, probs)))


def predictions_at_threshold(
    scored: Iterable[tuple[PairExample, float]],
    source1_ids: Iterable[str],
    threshold: float,
) -> dict[str, set[str]]:
    result = {entity_id: set() for entity_id in source1_ids}
    for example, score in scored:
        if score >= threshold:
            result.setdefault(example.source1_id, set()).add(example.target_id)
    return result


def evaluate_threshold(
    truth_by_entity: Mapping[str, set[str]],
    predictions: Mapping[str, set[str]],
) -> dict[str, float]:
    scores = [
        score_entity(truth, predictions.get(s1, set()), beta=0.5)
        for s1, truth in truth_by_entity.items()
    ]
    singletons = [s1 for s1, truth in truth_by_entity.items() if not truth]
    singleton_correct = sum(not predictions.get(s1, set()) for s1 in singletons)
    return {
        "macro_f0_5": sum(s.fbeta for s in scores) / len(scores),
        "macro_precision": sum(s.precision for s in scores) / len(scores),
        "macro_recall": sum(s.recall for s in scores) / len(scores),
        "singleton_accuracy": singleton_correct / len(singletons) if singletons else 1.0,
    }
