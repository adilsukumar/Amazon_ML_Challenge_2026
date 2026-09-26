import unittest

from entity_resolution.metrics import macro_fbeta, score_entity


class ScoreEntityTests(unittest.TestCase):
    def test_both_empty_is_perfect(self) -> None:
        self.assertEqual(score_entity(set(), set()).fbeta, 1.0)

    def test_false_match_on_singleton_is_zero(self) -> None:
        self.assertEqual(score_entity(set(), {"S2-1"}).fbeta, 0.0)

    def test_missing_all_truth_is_zero(self) -> None:
        self.assertEqual(score_entity({"S2-1"}, set()).fbeta, 0.0)

    def test_problem_statement_example(self) -> None:
        result = score_entity(
            {"S2-00047", "S3-00812"},
            {"S2-00047", "S2-00193", "S3-00812"},
        )
        self.assertAlmostEqual(result.precision, 2 / 3)
        self.assertEqual(result.recall, 1.0)
        self.assertAlmostEqual(result.fbeta, 5 / 7)

    def test_macro_includes_missing_prediction_as_empty(self) -> None:
        truth = {"S1-1": {"S2-1"}, "S1-2": set()}
        predictions = {"S1-1": {"S2-1"}}
        self.assertEqual(macro_fbeta(truth, predictions), 1.0)

    def test_unknown_prediction_entity_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            macro_fbeta({"S1-1": set()}, {"S1-2": set()})


if __name__ == "__main__":
    unittest.main()

