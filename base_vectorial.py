from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Iterator


@dataclass(frozen=True, slots=True)
class PromptRecord:
    id: str
    text: str
    metadata: dict
    tags: tuple[str, ...]
    created_at: str
    updated_at: str


class PromptRepository:
    """Repositorio SQLite de prompts. No realiza búsqueda vectorial."""

    def __init__(self, db_path: str | Path = "data/prompts.db") -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    @contextmanager
    def _connection(self) -> Iterator[sqlite3.Connection]:
        connection = self._connect()
        try:
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def _initialize(self) -> None:
        with self._connection() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS prompts (
                    id TEXT PRIMARY KEY,
                    text TEXT NOT NULL CHECK(length(trim(text)) > 0),
                    metadata TEXT NOT NULL DEFAULT '{}',
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS tags (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE
                );

                CREATE TABLE IF NOT EXISTS prompt_tags (
                    prompt_id TEXT NOT NULL REFERENCES prompts(id) ON DELETE CASCADE,
                    tag_id INTEGER NOT NULL REFERENCES tags(id) ON DELETE CASCADE,
                    PRIMARY KEY (prompt_id, tag_id)
                );

                CREATE INDEX IF NOT EXISTS idx_prompts_text ON prompts(text);
                """
            )

    def upsert(
        self,
        prompt_id: str,
        text: str,
        metadata: dict | None = None,
        tags: Iterable[str] = (),
    ) -> None:
        prompt_id = prompt_id.strip()
        text = text.strip()
        if not prompt_id or not text:
            raise ValueError("prompt_id y text son obligatorios")
        normalized_tags = sorted({tag.strip() for tag in tags if tag.strip()})
        metadata_json = json.dumps(metadata or {}, ensure_ascii=False, sort_keys=True)

        with self._connection() as connection:
            connection.execute(
                """
                INSERT INTO prompts(id, text, metadata)
                VALUES (?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    text = excluded.text,
                    metadata = excluded.metadata,
                    updated_at = CURRENT_TIMESTAMP
                """,
                (prompt_id, text, metadata_json),
            )
            connection.execute("DELETE FROM prompt_tags WHERE prompt_id = ?", (prompt_id,))
            for tag in normalized_tags:
                connection.execute("INSERT OR IGNORE INTO tags(name) VALUES (?)", (tag,))
                connection.execute(
                    """
                    INSERT INTO prompt_tags(prompt_id, tag_id)
                    SELECT ?, id FROM tags WHERE name = ?
                    """,
                    (prompt_id, tag),
                )
            _delete_orphan_tags(connection)

    def get(self, prompt_id: str) -> PromptRecord | None:
        with self._connection() as connection:
            row = connection.execute(
                "SELECT * FROM prompts WHERE id = ?", (prompt_id,)
            ).fetchone()
            if row is None:
                return None
            return _to_record(row, _fetch_tags(connection, prompt_id))

    def search(self, query: str, limit: int = 10) -> list[PromptRecord]:
        if limit <= 0:
            raise ValueError("limit debe ser mayor que cero")
        with self._connection() as connection:
            rows = connection.execute(
                """
                SELECT * FROM prompts
                WHERE lower(text) LIKE lower(?)
                ORDER BY updated_at DESC, id
                LIMIT ?
                """,
                (f"%{query.strip()}%", limit),
            ).fetchall()
            return [
                _to_record(row, _fetch_tags(connection, row["id"]))
                for row in rows
            ]

    def delete(self, prompt_id: str) -> bool:
        with self._connection() as connection:
            cursor = connection.execute("DELETE FROM prompts WHERE id = ?", (prompt_id,))
            _delete_orphan_tags(connection)
            return cursor.rowcount > 0

    def count(self) -> int:
        with self._connection() as connection:
            return int(connection.execute("SELECT COUNT(*) FROM prompts").fetchone()[0])


def _fetch_tags(connection: sqlite3.Connection, prompt_id: str) -> tuple[str, ...]:
    return tuple(
        item["name"]
        for item in connection.execute(
            """
            SELECT t.name
            FROM tags t
            JOIN prompt_tags pt ON pt.tag_id = t.id
            WHERE pt.prompt_id = ?
            ORDER BY t.name
            """,
            (prompt_id,),
        )
    )


def _delete_orphan_tags(connection: sqlite3.Connection) -> None:
    connection.execute(
        "DELETE FROM tags WHERE NOT EXISTS "
        "(SELECT 1 FROM prompt_tags pt WHERE pt.tag_id = tags.id)"
    )


def _to_record(row: sqlite3.Row, tags: tuple[str, ...]) -> PromptRecord:
    return PromptRecord(
        id=row["id"],
        text=row["text"],
        metadata=json.loads(row["metadata"]),
        tags=tags,
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


BaseVectorial = PromptRepository
