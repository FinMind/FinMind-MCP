"""Durable async job store for long-running MCP tool calls."""

from __future__ import annotations

import json
import sqlite3
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class JobRecord:
    handle_id: str
    tool_name: str
    status: str
    arguments: dict[str, Any]
    original_query: str
    result: str | None = None
    error: str | None = None


class SQLiteJobStore:
    """Small SQLite-backed handleId store.

    This is intentionally minimal: the MCP tool returns a handle immediately,
    background work updates the row, and polling can resume from another store
    instance in the same process or after a process restart.
    """

    def __init__(self, db_path: str | Path):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.db_path) as conn:
            self._initialize(conn)

    def _initialize(self, conn: sqlite3.Connection) -> None:
        conn.execute(
            """
            create table if not exists jobs (
                handle_id text primary key,
                tool_name text not null,
                status text not null,
                arguments_json text not null,
                original_query text not null,
                result text,
                error text,
                created_at text not null,
                updated_at text not null
            )
            """
        )

    def create(
        self,
        *,
        tool_name: str,
        arguments: dict[str, Any],
        original_query: str,
    ) -> JobRecord:
        handle_id = uuid.uuid4().hex[:12]
        now = datetime.now(UTC).replace(microsecond=0).isoformat()
        args_json = json.dumps(arguments, ensure_ascii=False, sort_keys=True)
        with sqlite3.connect(self.db_path) as conn:
            self._initialize(conn)
            conn.execute(
                """
                insert into jobs (
                    handle_id, tool_name, status, arguments_json,
                    original_query, result, error, created_at, updated_at
                ) values (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    handle_id,
                    tool_name,
                    "processing",
                    args_json,
                    original_query,
                    None,
                    None,
                    now,
                    now,
                ),
            )
        return JobRecord(
            handle_id=handle_id,
            tool_name=tool_name,
            status="processing",
            arguments=dict(arguments),
            original_query=original_query,
        )

    def get(self, handle_id: str) -> JobRecord | None:
        with sqlite3.connect(self.db_path) as conn:
            self._initialize(conn)
            row = conn.execute(
                """
                select handle_id, tool_name, status, arguments_json,
                       original_query, result, error
                from jobs
                where handle_id = ?
                """,
                (handle_id,),
            ).fetchone()
        if row is None:
            return None
        return JobRecord(
            handle_id=str(row[0]),
            tool_name=str(row[1]),
            status=str(row[2]),
            arguments=json.loads(row[3]),
            original_query=str(row[4]),
            result=row[5],
            error=row[6],
        )

    def complete(self, handle_id: str, result: str) -> None:
        now = datetime.now(UTC).replace(microsecond=0).isoformat()
        with sqlite3.connect(self.db_path) as conn:
            self._initialize(conn)
            conn.execute(
                """
                update jobs
                set status = ?, result = ?, error = ?, updated_at = ?
                where handle_id = ?
                """,
                ("completed", result, None, now, handle_id),
            )

    def fail(self, handle_id: str, error: str) -> None:
        now = datetime.now(UTC).replace(microsecond=0).isoformat()
        with sqlite3.connect(self.db_path) as conn:
            self._initialize(conn)
            conn.execute(
                """
                update jobs
                set status = ?, error = ?, updated_at = ?
                where handle_id = ?
                """,
                ("failed", error, now, handle_id),
            )
