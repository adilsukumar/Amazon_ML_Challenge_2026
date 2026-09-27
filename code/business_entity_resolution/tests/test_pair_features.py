import unittest

from entity_resolution.pair_features import (
    build_pair_features,
    numeric_tokens,
    token_containment,
    token_jaccard,
)


class PairFeatureTests(unittest.TestCase):
    def test_token_similarity(self):
        self.assertAlmostEqual(
            token_jaccard("Green Palace Hotel", "green palace"), 2 / 3
        )
        self.assertEqual(
            token_containment("Green Palace Hotel", "green palace"), 1.0
        )

    def test_numeric_features_and_missingness(self):
        f = build_pair_features(
            source_name="ACME 24",
            source_address="12 MG Road Unit 5",
            target_name="Acme 24",
            target_address="12 MG Rd Unit 7",
        )
        self.assertEqual(f["name_exact"], 1.0)
        self.assertEqual(f["address_numeric_overlap"], 1.0)
        self.assertEqual(f["address_numeric_conflict"], 0.0)
        self.assertEqual(numeric_tokens("B-12 / 004"), {"12", "004"})

    def test_unicode_and_empty_fields_are_safe(self):
        f = build_pair_features(
            source_name="Café Délice",
            source_address="",
            target_name="CAFÉ DÉLICE",
            target_address="",
        )
        self.assertEqual(f["name_exact"], 1.0)
        self.assertEqual(f["source_address_missing"], 1.0)
        self.assertEqual(f["target_address_missing"], 1.0)


if __name__ == "__main__":
    unittest.main()
