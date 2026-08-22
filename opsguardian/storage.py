from __future__ import annotations

import sqlite3
import threading
from pathlib import Path
from typing import Protocol

from .config import settings
from .models import Incident, utcnow


class Store(Protocol):
    def upsert(self, incident: Incident) -> None: ...
    def get(self, incident_id: str) -> Incident | None: ...
    def list(self, limit: int = 20) -> list[Incident]: ...
    def clear(self) -> None: ...


class SQLiteStore:
    def __init__(self, path: str = "opsguardian.db") -> None:
        self.path = Path(path)
        self.lock = threading.Lock()
        self._init()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.path, check_same_thread=False)

    def _init(self) -> None:
        with self._connect() as con:
            con.execute("CREATE TABLE IF NOT EXISTS incidents (id TEXT PRIMARY KEY, updated_at TEXT NOT NULL, payload TEXT NOT NULL)")

    def upsert(self, incident: Incident) -> None:
        incident.updated_at = utcnow()
        payload = incident.model_dump_json()
        with self.lock, self._connect() as con:
            con.execute("INSERT INTO incidents(id, updated_at, payload) VALUES (?, ?, ?) ON CONFLICT(id) DO UPDATE SET updated_at=excluded.updated_at, payload=excluded.payload", (incident.id, incident.updated_at, payload))

    def get(self, incident_id: str) -> Incident | None:
        with self.lock, self._connect() as con:
            row = con.execute("SELECT payload FROM incidents WHERE id=?", (incident_id,)).fetchone()
        return Incident.model_validate_json(row[0]) if row else None

    def list(self, limit: int = 20) -> list[Incident]:
        with self.lock, self._connect() as con:
            rows = con.execute("SELECT payload FROM incidents ORDER BY updated_at DESC LIMIT ?", (limit,)).fetchall()
        return [Incident.model_validate_json(row[0]) for row in rows]

    def clear(self) -> None:
        with self.lock, self._connect() as con:
            con.execute("DELETE FROM incidents")


class DynamoDBStore:
    def __init__(self) -> None:
        import boto3
        self.table = boto3.resource("dynamodb", region_name=settings.aws_region).Table(settings.dynamodb_table)

    def upsert(self, incident: Incident) -> None:
        incident.updated_at = utcnow()
        self.table.put_item(Item={"incident_id": incident.id, "updated_at": incident.updated_at, "payload": incident.model_dump_json()})

    def get(self, incident_id: str) -> Incident | None:
        item = self.table.get_item(Key={"incident_id": incident_id}).get("Item")
        return Incident.model_validate_json(item["payload"]) if item else None

    def list(self, limit: int = 20) -> list[Incident]:
        items: list[dict] = []
        scan_kwargs: dict = {}
        while True:
            response = self.table.scan(**scan_kwargs)
            items.extend(response.get("Items", []))
            last_key = response.get("LastEvaluatedKey")
            if not last_key:
                break
            scan_kwargs["ExclusiveStartKey"] = last_key
        items.sort(key=lambda i: i.get("updated_at", ""), reverse=True)
        return [Incident.model_validate_json(item["payload"]) for item in items[: max(limit, 0)]]

    def clear(self) -> None:
        scan_kwargs = {"ProjectionExpression": "incident_id"}
        while True:
            response = self.table.scan(**scan_kwargs)
            with self.table.batch_writer() as batch:
                for item in response.get("Items", []):
                    batch.delete_item(Key={"incident_id": item["incident_id"]})
            last_key = response.get("LastEvaluatedKey")
            if not last_key:
                break
            scan_kwargs["ExclusiveStartKey"] = last_key


def build_store() -> Store:
    return DynamoDBStore() if settings.use_dynamodb else SQLiteStore()
