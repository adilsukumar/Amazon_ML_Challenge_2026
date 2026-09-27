import unittest

from entity_resolution.matcher import (
    PairExample,
    evaluate_threshold,
    label_candidate_pairs,
    predictions_at_threshold,
    select_training_examples,
    split_source1_ids,
)


def _f(name=0.0, address=0.0):
    return {
        "name_exact": name,
        "address_exact": address,
        "name_sequence": name,
        "address_sequence": address,
        "name_jaccard": name,
        "address_jaccard": address,
        "address_numeric_overlap": 0.0,
    }


class MatcherTests(unittest.TestCase):
    def test_split_is_deterministic_and_disjoint(self):
        ids = [f"S1_{i}" for i in range(200)]
        train1, val1 = split_source1_ids(ids)
        train2, val2 = split_source1_ids(ids)
        self.assertEqual((train1, val1), (train2, val2))
        self.assertFalse(train1 & val1)
        self.assertEqual(train1 | val1, set(ids))

    def test_labeling_and_hard_negative_selection(self):
        truth = {"S1": {"T1"}}
        rows = [
            ("S1", "T1", _f(1, 1)),
            ("S1", "T2", _f(1, 0)),
            ("S1", "T3", _f(0, 0)),
        ]
        examples = label_candidate_pairs(rows, truth)
        self.assertEqual([e.label for e in examples], [1, 0, 0])
        selected = select_training_examples(examples, negatives_per_positive=1)
        self.assertEqual({e.target_id for e in selected}, {"T1", "T2"})

    def test_thresholding_preserves_singletons(self):
        examples = [
            PairExample("S1", "T1", _f(), 1),
            PairExample("S2", "T2", _f(), 0),
        ]
        pred = predictions_at_threshold(
            [(examples[0], 0.9), (examples[1], 0.2)], ["S1", "S2"], 0.5
        )
        metrics = evaluate_threshold({"S1": {"T1"}, "S2": set()}, pred)
        self.assertEqual(pred, {"S1": {"T1"}, "S2": set()})
        self.assertEqual(metrics["macro_f0_5"], 1.0)
        self.assertEqual(metrics["singleton_accuracy"], 1.0)


if __name__ == "__main__":
    unittest.main()
