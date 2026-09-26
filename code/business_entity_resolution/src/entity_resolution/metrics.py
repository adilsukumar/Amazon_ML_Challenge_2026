"""Entity-set metrics matching the competition's macro F0.5 definition."""

from __future__ import annotations

from dataclasses import dataclass
from typing import AbstractSet, Iterable, Mapping


@dataclass(frozen=True)
class EntityScore:
    """Precision, recall, and F-beta for one Source 1 entity."""

    precision: float
    recall: float
    fbeta: float


def score_entity(
    truth: AbstractSet[str],
    prediction: AbstractSet[str],
    *,
    beta: float = 0.5,
) -> EntityScore:
    """Score one entity's predicted match set.

    The challenge assigns a perfect score when truth and prediction are both
    empty. If exactly one is empty, all three metrics are zero.
    """

    if beta <= 0:
        raise ValueError("beta must be positive")

    if not truth and not prediction:
        return EntityScore(precision=1.0, recall=1.0, fbeta=1.0)
    if not truth or not prediction:
        return EntityScore(precision=0.0, recall=0.0, fbeta=0.0)

    true_positives = len(truth & prediction)
    precision = true_positives / len(prediction)
    recall = true_positives / len(truth)
    beta_squared = beta * beta
    denominator = beta_squared * precision + recall
    fbeta = (
        (1 + beta_squared) * precision * recall / denominator
        if denominator
        else 0.0
    )
    return EntityScore(precision=precision, recall=recall, fbeta=fbeta)


def macro_fbeta(
    truth_by_entity: Mapping[str, AbstractSet[str]],
    predictions_by_entity: Mapping[str, AbstractSet[str]],
    *,
    beta: float = 0.5,
) -> float:
    """Return entity-level macro F-beta over every truth Source 1 entity.

    Predictions for unknown Source 1 IDs are rejected instead of silently
    ignored because they indicate a submission-generation bug.
    """

    unknown_ids = predictions_by_entity.keys() - truth_by_entity.keys()
    if unknown_ids:
        sample = sorted(unknown_ids)[:3]
        raise ValueError(f"predictions contain unknown Source 1 IDs: {sample}")
    if not truth_by_entity:
        raise ValueError("truth_by_entity must not be empty")

    scores: Iterable[float] = (
        score_entity(
            truth,
            predictions_by_entity.get(entity_id, frozenset()),
            beta=beta,
        ).fbeta
        for entity_id, truth in truth_by_entity.items()
    )
    return sum(scores) / len(truth_by_entity)

