import sqlite3
import unittest

from entity_resolution.prefix_blocker import add_prefix_candidates


class PrefixBlockerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.connection = sqlite3.connect(":memory:")
        self.connection.executescript(
            """CREATE TABLE s1(entity_id TEXT PRIMARY KEY,country TEXT,name TEXT,address TEXT);
               CREATE TABLE targets(entity_id TEXT PRIMARY KEY,country TEXT,name TEXT,address TEXT);
               CREATE TABLE candidates(
                 s1_id TEXT,target_id TEXT,name_eq INTEGER,address_eq INTEGER,
                 PRIMARY KEY(s1_id,target_id)
               );"""
        )

    def tearDown(self) -> None:
        self.connection.close()

    def test_retrieves_typo_with_bounded_group_and_keeps_exact_flags(self) -> None:
        self.connection.executemany(
            "INSERT INTO s1 VALUES (?,?,?,?)",
            [("S1-1", "india", "sunflower tech", "1 road")],
        )
        self.connection.executemany(
            "INSERT INTO targets VALUES (?,?,?,?)",
            [
                ("S2-1", "india", "sunflower technology", "2 road"),
                ("S3-1", "india", "sunflower tech", "1 road"),
                ("S2-2", "france", "sunflower techno", "1 road"),
            ],
        )
        self.connection.execute("INSERT INTO candidates VALUES ('S1-1','S3-1',1,1)")
        self.assertEqual(add_prefix_candidates(self.connection, max_group_size=2), 1)
        self.assertEqual(
            self.connection.execute(
                "SELECT target_id,name_eq,address_eq FROM candidates ORDER BY target_id"
            ).fetchall(),
            [("S2-1", 0, 0), ("S3-1", 1, 1)],
        )
        self.assertEqual(add_prefix_candidates(self.connection, max_group_size=2), 0)

    def test_skips_large_groups_and_short_names(self) -> None:
        self.connection.executemany(
            "INSERT INTO s1 VALUES (?,?,?,?)",
            [("S1-1", "india", "abcdefgh name", ""), ("S1-2", "india", "short", "")],
        )
        self.connection.executemany(
            "INSERT INTO targets VALUES (?,?,?,?)",
            [
                ("S2-1", "india", "abcdefgh one", ""),
                ("S2-2", "india", "abcdefgh two", ""),
                ("S2-3", "india", "short", ""),
            ],
        )
        self.assertEqual(add_prefix_candidates(self.connection, max_group_size=1), 0)
        with self.assertRaises(ValueError):
            add_prefix_candidates(self.connection, max_group_size=0)


if __name__ == "__main__":
    unittest.main()
