"""Optional, bounded name-prefix candidate channel.

This is an experiment, not part of the validated v1 submission. It adds at
most ``max_group_size`` target IDs per Source 1 row and never uses labels.
Call it after ``generate_candidates`` on a training database, measure recall
and candidate volume, and only then consider it for final prediction.
"""

from __future__ import annotations

import sqlite3


PREFIX_LENGTH = 8


def add_prefix_candidates(
    connection: sqlite3.Connection, *, max_group_size: int = 8
) -> int:
    """Add same-country name-prefix matches from small target groups only.

    Names shorter than eight normalized characters are skipped. A prefix whose
    target-side group exceeds ``max_group_size`` is skipped entirely, so each
    query adds no more than that many candidates. Existing exact candidates and
    their equality flags are retained. Returns the number of new pairs.
    """
    if max_group_size < 1:
        raise ValueError("max_group_size must be positive")

    before = connection.execute("SELECT count(*) FROM candidates").fetchone()[0]
    connection.execute(
        "CREATE INDEX IF NOT EXISTS target_prefix8_idx "
        "ON targets(country, substr(name,1,8))"
    )
    connection.execute("DROP TABLE IF EXISTS temp.eligible_name_prefixes")
    connection.execute(
        """CREATE TEMP TABLE eligible_name_prefixes AS
           SELECT country, substr(name,1,8) AS prefix
           FROM targets
           WHERE length(name)>=8
           GROUP BY country, substr(name,1,8)
           HAVING count(*)<=?""",
        (max_group_size,),
    )
    connection.execute(
        "CREATE INDEX eligible_name_prefixes_idx "
        "ON eligible_name_prefixes(country,prefix)"
    )
    connection.execute(
        """INSERT INTO candidates(s1_id,target_id,name_eq,address_eq)
           SELECT s.entity_id,t.entity_id,
                  CASE WHEN s.name=t.name AND s.name<>'' THEN 1 ELSE 0 END,
                  CASE WHEN s.address=t.address AND s.address<>'' THEN 1 ELSE 0 END
           FROM s1 s
           JOIN eligible_name_prefixes p
             ON p.country=s.country AND p.prefix=substr(s.name,1,8)
           JOIN targets t
             ON t.country=p.country AND substr(t.name,1,8)=p.prefix
           WHERE length(s.name)>=8
           ON CONFLICT(s1_id,target_id) DO NOTHING"""
    )
    connection.commit()
    after = connection.execute("SELECT count(*) FROM candidates").fetchone()[0]
    return after - before
