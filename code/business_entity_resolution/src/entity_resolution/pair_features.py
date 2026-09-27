"""Interpretable pair features for business-entity matching."""

from __future__ import annotations

import re
from difflib import SequenceMatcher
from typing import Iterable

from .exact_matcher import normalize

_NUMBER_RE = re.compile(r"\d+")


def _tokens(value: str) -> set[str]:
    return set(normalize(value).split())


def token_jaccard(left: str, right: str) -> float:
    a, b = _tokens(left), _tokens(right)
    if not a and not b:
        return 1.0
    union = a | b
    return len(a & b) / len(union) if union else 0.0


def token_containment(left: str, right: str) -> float:
    a, b = _tokens(left), _tokens(right)
    if not a and not b:
        return 1.0
    if not a or not b:
        return 0.0
    return len(a & b) / min(len(a), len(b))


def sequence_ratio(left: str, right: str) -> float:
    return SequenceMatcher(None, normalize(left), normalize(right)).ratio()


def numeric_tokens(value: str) -> set[str]:
    return set(_NUMBER_RE.findall(normalize(value)))


def numeric_features(left: str, right: str, prefix: str) -> dict[str, float]:
    a, b = numeric_tokens(left), numeric_tokens(right)
    inter = a & b
    return {
        f"{prefix}_numeric_overlap": float(len(inter)),
        f"{prefix}_numeric_exact": float(bool(a) and a == b),
        f"{prefix}_numeric_conflict": float(bool(a) and bool(b) and not inter),
    }


def build_pair_features(
    *,
    source_name: str,
    source_address: str,
    target_name: str,
    target_address: str,
) -> dict[str, float]:
    """Return deterministic, label-free features for one candidate pair."""
    sn, tn = normalize(source_name), normalize(target_name)
    sa, ta = normalize(source_address), normalize(target_address)
    sn_tok, tn_tok = _tokens(source_name), _tokens(target_name)
    sa_tok, ta_tok = _tokens(source_address), _tokens(target_address)

    features = {
        "name_exact": float(bool(sn) and sn == tn),
        "name_jaccard": token_jaccard(source_name, target_name),
        "name_containment": token_containment(source_name, target_name),
        "name_sequence": sequence_ratio(source_name, target_name),
        "name_length_diff": float(abs(len(sn) - len(tn))),
        "shared_name_tokens": float(len(sn_tok & tn_tok)),
        "address_exact": float(bool(sa) and sa == ta),
        "address_jaccard": token_jaccard(source_address, target_address),
        "address_containment": token_containment(source_address, target_address),
        "address_sequence": sequence_ratio(source_address, target_address),
        "address_length_diff": float(abs(len(sa) - len(ta))),
        "shared_address_tokens": float(len(sa_tok & ta_tok)),
        "source_name_missing": float(not sn),
        "target_name_missing": float(not tn),
        "source_address_missing": float(not sa),
        "target_address_missing": float(not ta),
        "both_exact": float(bool(sn) and bool(sa) and sn == tn and sa == ta),
        "neither_exact": float(sn != tn and sa != ta),
    }
    features.update(numeric_features(source_address, target_address, "address"))
    features.update(numeric_features(source_name, target_name, "name"))
    return features


FEATURE_NAMES = tuple(
    build_pair_features(
        source_name="a", source_address="1 x", target_name="b", target_address="2 y"
    ).keys()
)


def vectorize(feature_rows: Iterable[dict[str, float]]) -> list[list[float]]:
    return [[float(row[name]) for name in FEATURE_NAMES] for row in feature_rows]
