from datetime import datetime, timedelta, timezone
from pathlib import Path
import sqlite3


class PostedHistory:
    def __init__(self, db_path: str):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self):
        return sqlite3.connect(self.db_path)

    def _initialize(self):
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS posted_items (
                    item_id TEXT PRIMARY KEY,
                    legacy_item_id TEXT,
                    title TEXT,
                    category TEXT,
                    affiliate_url TEXT,
                    first_posted TEXT NOT NULL,
                    last_posted TEXT NOT NULL,
                    times_posted INTEGER NOT NULL DEFAULT 1,
                    last_score REAL
                )
                """
            )
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_posted_items_last_posted
                ON posted_items(last_posted)
                """
            )
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_posted_items_legacy_item_id
                ON posted_items(legacy_item_id)
                """
            )

    def recent_item_ids(self, cooldown_days: int) -> set[str]:
        cutoff = datetime.now(timezone.utc) - timedelta(
            days=max(int(cooldown_days), 0)
        )
        cutoff_text = cutoff.isoformat()

        ids = set()

        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT item_id, legacy_item_id
                FROM posted_items
                WHERE last_posted >= ?
                """,
                (cutoff_text,),
            ).fetchall()

        for item_id, legacy_item_id in rows:
            if item_id:
                ids.add(str(item_id))
            if legacy_item_id:
                ids.add(str(legacy_item_id))

        return ids

    def mark_posted(self, product, score=None):
        now = datetime.now(timezone.utc).isoformat()
        item_id = str(product.item_id or product.legacy_item_id or "")
        if not item_id:
            raise ValueError("Cannot save posted history without an eBay item ID.")

        legacy_item_id = str(product.legacy_item_id or "")
        score_value = None
        if isinstance(score, dict):
            score_value = score.get("total")
        elif score is not None:
            score_value = float(score)

        with self._connect() as conn:
            existing = conn.execute(
                """
                SELECT first_posted, times_posted
                FROM posted_items
                WHERE item_id = ?
                """,
                (item_id,),
            ).fetchone()

            if existing:
                first_posted, times_posted = existing
                conn.execute(
                    """
                    UPDATE posted_items
                    SET legacy_item_id = ?,
                        title = ?,
                        category = ?,
                        affiliate_url = ?,
                        last_posted = ?,
                        times_posted = ?,
                        last_score = ?
                    WHERE item_id = ?
                    """,
                    (
                        legacy_item_id,
                        product.title,
                        product.search_category,
                        product.affiliate_url,
                        now,
                        int(times_posted or 0) + 1,
                        score_value,
                        item_id,
                    ),
                )
            else:
                conn.execute(
                    """
                    INSERT INTO posted_items (
                        item_id,
                        legacy_item_id,
                        title,
                        category,
                        affiliate_url,
                        first_posted,
                        last_posted,
                        times_posted,
                        last_score
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?)
                    """,
                    (
                        item_id,
                        legacy_item_id,
                        product.title,
                        product.search_category,
                        product.affiliate_url,
                        now,
                        now,
                        score_value,
                    ),
                )

    def posted_count(self) -> int:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT COUNT(*) FROM posted_items"
            ).fetchone()
        return int(row[0] if row else 0)
