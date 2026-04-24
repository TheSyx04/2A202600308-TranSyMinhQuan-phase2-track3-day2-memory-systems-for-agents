from __future__ import annotations

import json
import re
from collections import defaultdict, deque
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _normalize_text(text: str) -> str:
    lowered = text.lower()
    return re.sub(r"[^\w\s]", " ", lowered)


class ShortTermMemory:
    def __init__(self, window_size: int = 8) -> None:
        self.window_size = window_size
        self._store: dict[str, deque[dict[str, str]]] = defaultdict(
            lambda: deque(maxlen=self.window_size)
        )

    def add_message(self, user_id: str, role: str, content: str) -> None:
        self._store[user_id].append({"role": role, "content": content})

    def get_recent(self, user_id: str) -> list[dict[str, str]]:
        return list(self._store[user_id])

    def clear(self, user_id: str) -> None:
        self._store[user_id].clear()


class LongTermProfileMemory:
    def __init__(self, file_path: Path) -> None:
        self.file_path = file_path
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.file_path.exists():
            self.file_path.write_text("{}", encoding="utf-8")

    def _load(self) -> dict[str, dict[str, Any]]:
        raw = self.file_path.read_text(encoding="utf-8")
        return json.loads(raw or "{}")

    def _save(self, data: dict[str, dict[str, Any]]) -> None:
        self.file_path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    def get_profile(self, user_id: str) -> dict[str, Any]:
        data = self._load()
        user_profile = data.get(user_id, {})
        return {k: v["value"] for k, v in user_profile.items() if isinstance(v, dict)}

    def update_fact(self, user_id: str, key: str, value: str) -> None:
        # Conflict policy: latest value always replaces old value for the same key.
        data = self._load()
        data.setdefault(user_id, {})
        data[user_id][key] = {"value": value, "updated_at": _utc_now_iso()}
        self._save(data)

    def bulk_update(self, user_id: str, updates: dict[str, str]) -> None:
        for key, value in updates.items():
            if value.strip():
                self.update_fact(user_id, key, value.strip())

    def reset(self) -> None:
        self._save({})


class EpisodicMemory:
    def __init__(self, file_path: Path) -> None:
        self.file_path = file_path
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.file_path.exists():
            self.file_path.write_text("[]", encoding="utf-8")

    def _load(self) -> list[dict[str, Any]]:
        raw = self.file_path.read_text(encoding="utf-8")
        return json.loads(raw or "[]")

    def _save(self, data: list[dict[str, Any]]) -> None:
        self.file_path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    def add_episode(
        self,
        user_id: str,
        summary: str,
        outcome: str,
        tags: list[str] | None = None,
    ) -> None:
        data = self._load()
        data.append(
            {
                "user_id": user_id,
                "summary": summary,
                "outcome": outcome,
                "tags": tags or [],
                "created_at": _utc_now_iso(),
            }
        )
        self._save(data)

    def get_recent(self, user_id: str, limit: int = 3) -> list[dict[str, Any]]:
        data = self._load()
        user_episodes = [item for item in data if item.get("user_id") == user_id]
        return user_episodes[-limit:]

    def reset(self) -> None:
        self._save([])


@dataclass
class SemanticHit:
    doc_id: str
    score: int
    text: str


class SemanticMemory:
    def __init__(self, corpus_path: Path) -> None:
        self.corpus_path = corpus_path
        raw = self.corpus_path.read_text(encoding="utf-8")
        self._docs: list[dict[str, Any]] = json.loads(raw)

    def retrieve(self, query: str, top_k: int = 3) -> list[str]:
        query_tokens = set(_normalize_text(query).split())
        if not query_tokens:
            return []

        hits: list[SemanticHit] = []
        for doc in self._docs:
            text = str(doc.get("text", ""))
            tags = doc.get("tags", [])
            doc_tokens = set(_normalize_text(text).split())
            for tag in tags:
                doc_tokens.update(_normalize_text(str(tag)).split())
            score = len(query_tokens.intersection(doc_tokens))
            if score > 0:
                hits.append(
                    SemanticHit(
                        doc_id=str(doc.get("id", "unknown")),
                        score=score,
                        text=text,
                    )
                )

        hits.sort(key=lambda item: item.score, reverse=True)
        return [hit.text for hit in hits[:top_k]]
