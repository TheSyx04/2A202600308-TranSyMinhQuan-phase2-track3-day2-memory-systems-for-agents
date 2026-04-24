from __future__ import annotations

import re
from pathlib import Path
from typing import TypedDict

from memory_backends import (
    EpisodicMemory,
    LongTermProfileMemory,
    SemanticMemory,
    ShortTermMemory,
)


class MemoryState(TypedDict):
    messages: list[dict[str, str]]
    user_profile: dict[str, str]
    episodes: list[dict]
    semantic_hits: list[str]
    memory_budget: int
    assembled_prompt: str


class MultiMemoryAgent:
    def __init__(
        self,
        profile_path: Path,
        episodes_path: Path,
        semantic_corpus_path: Path,
        memory_budget_chars: int = 1200,
    ) -> None:
        self.short_term = ShortTermMemory(window_size=10)
        self.profile = LongTermProfileMemory(profile_path)
        self.episodic = EpisodicMemory(episodes_path)
        self.semantic = SemanticMemory(semantic_corpus_path)
        self.memory_budget_chars = memory_budget_chars

    def reset_persistent_memory(self) -> None:
        self.profile.reset()
        self.episodic.reset()

    def extract_profile_updates(self, text: str) -> dict[str, str]:
        updates: dict[str, str] = {}
        if "?" in text:
            return updates

        name_match = re.search(r"toi ten la\s+([\w\s]+)", text, re.IGNORECASE)
        if name_match:
            updates["name"] = name_match.group(1).strip(" .,!?")

        job_match = re.search(r"toi lam\s+([\w\s]+)", text, re.IGNORECASE)
        if job_match:
            updates["occupation"] = job_match.group(1).strip(" .,!?")

        pref_match = re.search(
            r"toi thich dung\s+([\w\s]+?)(?:\.|,|$)", text, re.IGNORECASE
        )
        if pref_match:
            updates["preference"] = pref_match.group(1).strip(" .,!?")

        allergy_fix = re.search(
            r"toi di ung\s+([\w\s]+?)\s+moi dung", text, re.IGNORECASE
        )
        if allergy_fix:
            updates["allergy"] = allergy_fix.group(1).strip(" .,!?")
        else:
            allergy_match = re.search(r"toi di ung\s+([\w\s]+)", text, re.IGNORECASE)
            if allergy_match:
                updates["allergy"] = allergy_match.group(1).strip(" .,!?")

        return updates

    def maybe_save_episode(self, user_id: str, text: str) -> None:
        if "?" in text:
            return

        lower = text.lower()
        markers = [
            "xong",
            "hoan thanh",
            "da xu ly",
            "da fix",
            "ket qua",
            "outcome",
            "retry",
            "timeout",
        ]
        if not any(marker in lower for marker in markers):
            return

        summary = text.strip()
        tags: list[str] = []
        for keyword in ["login", "api", "docker", "timeout", "cpu", "incident"]:
            if keyword in lower:
                tags.append(keyword)
        self.episodic.add_episode(
            user_id=user_id,
            summary=summary,
            outcome="completed_or_reported",
            tags=tags,
        )

    def _trim_by_budget(self, sections: list[str], budget: int) -> str:
        assembled = "\n\n".join(sections)
        if len(assembled) <= budget:
            return assembled
        return assembled[-budget:]

    def retrieve_memory(self, state: MemoryState, user_id: str, query: str) -> MemoryState:
        user_profile = self.profile.get_profile(user_id)
        episodes = self.episodic.get_recent(user_id=user_id, limit=3)
        semantic_hits = self.semantic.retrieve(query=query, top_k=3)
        recent = self.short_term.get_recent(user_id)

        profile_section = f"[PROFILE]\n{user_profile}" if user_profile else "[PROFILE]\n{}"
        episodic_section = f"[EPISODIC]\n{episodes}" if episodes else "[EPISODIC]\n[]"
        semantic_section = (
            f"[SEMANTIC]\n{semantic_hits}" if semantic_hits else "[SEMANTIC]\n[]"
        )
        recent_section = f"[RECENT]\n{recent}" if recent else "[RECENT]\n[]"

        assembled_prompt = self._trim_by_budget(
            [profile_section, episodic_section, semantic_section, recent_section],
            budget=state["memory_budget"],
        )

        state["user_profile"] = user_profile
        state["episodes"] = episodes
        state["semantic_hits"] = semantic_hits
        state["assembled_prompt"] = assembled_prompt
        return state

    def _respond_with_memory(self, state: MemoryState, query: str) -> str:
        q = query.lower()
        profile = state["user_profile"]
        episodes = state["episodes"]
        semantic_hits = state["semantic_hits"]

        def _episode_pack() -> str:
            if not episodes:
                return "chua co"
            summaries = [ep.get("summary", "") for ep in episodes[-3:] if ep.get("summary")]
            return " | ".join(summaries)

        def _timeout_hint() -> str:
            for item in semantic_hits:
                low = item.lower()
                if "timeout" in low or "backoff" in low or "retry" in low:
                    return item
            return semantic_hits[0] if semantic_hits else "uu tien retry co gioi han va exponential backoff"

        if "toi la ai" in q or ("tom tat" in q and "guideline" in q):
            name = profile.get("name", "chua ro")
            latest_episode = _episode_pack()
            timeout_hint = _timeout_hint()
            return (
                f"Ban la {name}. Episode gan day: {latest_episode}. "
                f"Guideline timeout: {timeout_hint}"
            )

        if "ten" in q and ("toi" in q or "moi" in q):
            name = profile.get("name")
            return f"Ban ten la {name}." if name else "Minh chua thay ten cua ban trong profile."

        if "nghe" in q or "lam gi" in q:
            job = profile.get("occupation")
            return f"Ban dang lam {job}." if job else "Minh chua luu nghe nghiep cua ban."

        if "di ung" in q:
            allergy = profile.get("allergy")
            return (
                f"Thong tin moi nhat: ban di ung {allergy}."
                if allergy
                else "Minh chua co thong tin di ung trong profile."
            )

        if "so thich" in q or "cong cu" in q:
            pref = profile.get("preference")
            return f"So thich da luu: {pref}." if pref else "Minh chua luu preference cua ban."

        if "task" in q or "on-call" in q or "tom tat" in q:
            if episodes:
                return (
                    "Episode gan day: "
                    f"{_episode_pack()} "
                    "(outcome=completed_or_reported)."
                )

        if "docker compose" in q or "localhost" in q:
            if semantic_hits:
                return semantic_hits[0]

        if "timeout" in q or "retry" in q or "backoff" in q:
            if semantic_hits:
                return semantic_hits[0]

        if "trim" in q or "ngan sach context" in q:
            return (
                "Uu tien trim theo thu tu: profile quan trong, episodic moi nhat, "
                "semantic lien quan, roi den recent conversation."
            )

        if semantic_hits:
            return f"Goi y tu semantic memory: {semantic_hits[0]}"

        return "Minh da luu memory va se tiep tuc ho tro theo ngu canh gan day."

    def chat_with_memory(
        self,
        user_id: str,
        messages: list[dict[str, str]],
        user_input: str,
    ) -> dict[str, str | int]:
        self.short_term.add_message(user_id, "user", user_input)

        updates = self.extract_profile_updates(user_input)
        if updates:
            self.profile.bulk_update(user_id, updates)

        self.maybe_save_episode(user_id, user_input)

        state: MemoryState = {
            "messages": messages,
            "user_profile": {},
            "episodes": [],
            "semantic_hits": [],
            "memory_budget": self.memory_budget_chars,
            "assembled_prompt": "",
        }

        state = self.retrieve_memory(state, user_id=user_id, query=user_input)
        answer = self._respond_with_memory(state, user_input)

        self.short_term.add_message(user_id, "assistant", answer)

        return {
            "response": answer,
            "prompt_chars": len(state["assembled_prompt"]),
            "prompt_words": len(state["assembled_prompt"].split()),
        }


def chat_without_memory(query: str) -> str:
    q = query.lower()
    if "docker compose" in q or "localhost" in q:
        return "Co the can xem lai cau hinh ket noi DB."
    if "di ung" in q:
        return "Minh khong chac vi khong co memory profile."
    if "ten" in q or "nghe" in q or "so thich" in q:
        return "Minh khong co du lieu lich su de tra loi chinh xac."
    if "task" in q or "on-call" in q:
        return "Minh khong nho duoc su kien truoc do khi khong bat memory."
    if "trim" in q:
        return "Can co co che quan ly context budget."
    return "No-memory mode: tra loi dua tren cau hoi hien tai."
