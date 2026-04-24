from __future__ import annotations

import json
from pathlib import Path

from agent import MultiMemoryAgent, chat_without_memory

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
SCENARIO_FILE = DATA_DIR / "benchmark_conversations.json"
BENCHMARK_MD = ROOT / "BENCHMARK.md"


def load_scenarios() -> list[dict]:
    return json.loads(SCENARIO_FILE.read_text(encoding="utf-8"))


def evaluate_pass(with_memory_result: str, expected_keywords: list[str]) -> bool:
    result_lower = with_memory_result.lower()
    return all(keyword.lower() in result_lower for keyword in expected_keywords)


def _escape_md_cell(value: object) -> str:
    text = str(value)
    text = text.replace("|", "\\|")
    text = text.replace("\n", " ")
    return text


def run_benchmark() -> None:
    agent = MultiMemoryAgent(
        profile_path=DATA_DIR / "profile_store.json",
        episodes_path=DATA_DIR / "episodes.json",
        semantic_corpus_path=DATA_DIR / "semantic_corpus.json",
        memory_budget_chars=1000,
    )
    agent.reset_persistent_memory()

    scenarios = load_scenarios()
    rows: list[dict] = []

    for scenario in scenarios:
        user_id = f"user_{scenario['id']}"
        messages: list[dict[str, str]] = []

        for turn in scenario["turns"]:
            with_memory_turn = agent.chat_with_memory(user_id, messages, turn)
            messages.append({"role": "user", "content": turn})
            messages.append({"role": "assistant", "content": str(with_memory_turn["response"])})

        probe = scenario["probe"]
        no_memory_result = chat_without_memory(probe)
        with_memory_final = agent.chat_with_memory(user_id, messages, probe)

        with_memory_result = str(with_memory_final["response"])
        pass_flag = evaluate_pass(
            with_memory_result,
            scenario.get("expected_with_memory_contains", []),
        )

        rows.append(
            {
                "id": scenario["id"],
                "category": scenario["category"],
                "scenario": scenario["scenario"],
                "turns": len(scenario["turns"]),
                "no_memory": no_memory_result,
                "with_memory": with_memory_result,
                "prompt_chars": with_memory_final["prompt_chars"],
                "prompt_words": with_memory_final["prompt_words"],
                "pass": "Pass" if pass_flag else "Fail",
            }
        )

    pass_count = sum(1 for row in rows if row["pass"] == "Pass")

    md_lines = [
        "# BENCHMARK - Multi-Memory Agent (bản cá nhân)",
        "",
        "Mục tiêu: so sánh no-memory và with-memory trên 10 multi-turn conversations.",
        "Lưu ý: dữ liệu benchmark trong file JSON dùng câu không dấu để tiện so khớp tự động.",
        "",
        "| # | Category | Scenario | Turns | No-memory result | With-memory result | Prompt chars | Prompt words | Pass? |",
        "|---|----------|----------|------:|------------------|--------------------|-------------:|-------------:|-------|",
    ]

    for row in rows:
        md_lines.append(
            f"| {_escape_md_cell(row['id'])} | {_escape_md_cell(row['category'])} | "
            f"{_escape_md_cell(row['scenario'])} | {_escape_md_cell(row['turns'])} | "
            f"{_escape_md_cell(row['no_memory'])} | {_escape_md_cell(row['with_memory'])} | "
            f"{_escape_md_cell(row['prompt_chars'])} | {_escape_md_cell(row['prompt_words'])} | "
            f"{_escape_md_cell(row['pass'])} |"
        )

    md_lines.extend(
        [
            "",
            f"Tổng kết: {pass_count}/10 scenario đạt expectation with-memory.",
            "",
            "## Coverage check",
            "",
            "- profile_recall: scenario 1, 2, 3",
            "- conflict_update: scenario 4",
            "- episodic_recall: scenario 5, 6",
            "- semantic_retrieval: scenario 7, 8",
            "- trim_budget: scenario 9",
            "- mixed_recall: scenario 10",
        ]
    )

    BENCHMARK_MD.write_text("\n".join(md_lines), encoding="utf-8")
    print(f"Generated {BENCHMARK_MD}")
    print(f"Pass count: {pass_count}/10")


if __name__ == "__main__":
    run_benchmark()
