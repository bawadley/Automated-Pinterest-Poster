from datetime import datetime, timedelta, timezone
from pathlib import Path
import json
import sqlite3


class TipHistory:
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
                CREATE TABLE IF NOT EXISTS posted_tips (
                    tip_id TEXT PRIMARY KEY,
                    category TEXT NOT NULL,
                    title TEXT NOT NULL,
                    first_posted TEXT NOT NULL,
                    last_posted TEXT NOT NULL,
                    times_posted INTEGER NOT NULL DEFAULT 1
                )
                """
            )

            columns = {
                row[1]
                for row in conn.execute(
                    "PRAGMA table_info(posted_tips)"
                ).fetchall()
            }

            if "content_json" not in columns:
                conn.execute(
                    "ALTER TABLE posted_tips ADD COLUMN content_json TEXT"
                )

    def recent_tip_ids(self, cooldown_days: int) -> set[str]:
        cutoff = datetime.now(timezone.utc) - timedelta(
            days=max(int(cooldown_days), 0)
        )
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT tip_id
                FROM posted_tips
                WHERE last_posted >= ?
                """,
                (cutoff.isoformat(),),
            ).fetchall()
        return {row[0] for row in rows if row and row[0]}

    def recent_posted_items(
        self,
        cooldown_days: int,
        limit: int = 100,
    ) -> list[dict]:
        cutoff = datetime.now(timezone.utc) - timedelta(
            days=max(int(cooldown_days), 0)
        )

        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT tip_id, category, title, content_json, last_posted
                FROM posted_tips
                WHERE last_posted >= ?
                ORDER BY last_posted DESC
                LIMIT ?
                """,
                (
                    cutoff.isoformat(),
                    max(int(limit), 1),
                ),
            ).fetchall()

        items = []
        for tip_id, category, title, content_json, last_posted in rows:
            content = None
            if content_json:
                try:
                    content = json.loads(content_json)
                except Exception:
                    content = None

            items.append(
                {
                    "tip_id": tip_id,
                    "category": category,
                    "title": title,
                    "content": content,
                    "last_posted": last_posted,
                }
            )
        return items

    def mark_posted(self, tip: dict, category_name: str):
        now = datetime.now(timezone.utc).isoformat()
        tip_id = tip["id"]
        content_json = json.dumps(
            tip,
            ensure_ascii=False,
            separators=(",", ":"),
        )

        with self._connect() as conn:
            existing = conn.execute(
                "SELECT first_posted, times_posted FROM posted_tips WHERE tip_id = ?",
                (tip_id,),
            ).fetchone()

            if existing:
                conn.execute(
                    """
                    UPDATE posted_tips
                    SET category = ?,
                        title = ?,
                        content_json = ?,
                        last_posted = ?,
                        times_posted = ?
                    WHERE tip_id = ?
                    """,
                    (
                        category_name,
                        tip["title"],
                        content_json,
                        now,
                        int(existing[1] or 0) + 1,
                        tip_id,
                    ),
                )
            else:
                conn.execute(
                    """
                    INSERT INTO posted_tips (
                        tip_id,
                        category,
                        title,
                        content_json,
                        first_posted,
                        last_posted,
                        times_posted
                    )
                    VALUES (?, ?, ?, ?, ?, ?, 1)
                    """,
                    (
                        tip_id,
                        category_name,
                        tip["title"],
                        content_json,
                        now,
                        now,
                    ),
                )

    def posted_count(self) -> int:
        with self._connect() as conn:
            row = conn.execute("SELECT COUNT(*) FROM posted_tips").fetchone()
        return int(row[0] if row else 0)
