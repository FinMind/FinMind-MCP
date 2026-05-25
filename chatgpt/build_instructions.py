#!/usr/bin/env python3
"""Compile knowledge pack into a ChatGPT Custom GPT instructions file.

Produces two outputs:
- ``instructions.txt``: inline GPT instructions, < 8000 chars
  (full instructions + errors + compact dataset cheatsheet + token pointer)
- ``knowledge_bundle.md``: rich content for GPT Knowledge file upload, no size cap
  (full datasets + examples + token-guide)

If ``instructions.txt`` exceeds the budget, abort.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
KNOWLEDGE = ROOT / "knowledge"
OUT_DIR = Path(__file__).resolve().parent
INSTRUCTIONS_OUT = OUT_DIR / "instructions.txt"
BUNDLE_OUT = OUT_DIR / "knowledge_bundle.md"
MAX_INSTRUCTIONS_CHARS = 8000

TOKEN_POINTER = """\
# Token 設定

未設定或無效時，引導用戶至 https://finmindtrade.com/analysis/#/account/user
取得 Token（未登入會自動導向登入 / 註冊頁）。ChatGPT Action 首次呼叫時會
自動彈窗請填 Token。完整流程請參考已上傳的 knowledge_bundle.md。
"""


def parse_datasets(content: str) -> list[dict]:
    """Parse datasets.md into structured records (name, desc, required, tier, category)."""
    records: list[dict] = []
    current: dict | None = None
    current_category: str | None = None
    for line in content.splitlines():
        if line.startswith("### "):
            if current and "desc" in current:
                records.append(current)
            current = {"name": line[4:].strip(), "category": current_category}
            continue
        if line.startswith("## ") and not line.startswith("### "):
            if current and "desc" in current:
                records.append(current)
                current = None
            current_category = line[3:].strip()
            continue
        if current is not None:
            m = re.match(r"- \*\*Tier:\*\*\s*(.+)", line)
            if m:
                current["tier"] = m.group(1).strip()
                continue
            m = re.match(r"- \*\*Required:\*\*\s*(.+)", line)
            if m:
                current["required"] = m.group(1).strip()
                continue
            m = re.match(r"- \*\*描述:\*\*\s*(.+)", line)
            if m:
                current["desc"] = m.group(1).strip()
                continue
    if current and "desc" in current:
        records.append(current)
    return records


def compact_datasets(content: str) -> str:
    """Produce a category-only summary; full dataset list lives in bundle.

    Keeps instructions.txt under the 8000 char hard cap. GPT can lookup the
    full list (~90 datasets) via Knowledge retrieval on knowledge_bundle.md.
    """
    records = parse_datasets(content)
    seen_cat: list[str] = []
    by_cat: dict[str, int] = {}
    for r in records:
        cat = r.get("category") or "Other"
        if cat not in by_cat:
            seen_cat.append(cat)
            by_cat[cat] = 0
        by_cat[cat] += 1

    lines = [
        "# Dataset 分類摘要",
        "",
        f"FinMind 共支援 {len(records)} 個 dataset，按分類：",
        "",
    ]
    for cat in seen_cat:
        lines.append(f"- **{cat}**：{by_cat[cat]} 個")
    lines.append("")
    lines.append(
        "完整 dataset 名稱 / 必要參數 / Tier / 欄位請查已上傳的 "
        "`knowledge_bundle.md`。常用 dataset 對照請看本檔上方"
        "「Intent → Dataset 對照」表。"
    )
    return "\n".join(lines)


def build_instructions() -> str:
    instructions = (KNOWLEDGE / "instructions.md").read_text(encoding="utf-8").strip()
    errors = (KNOWLEDGE / "errors.md").read_text(encoding="utf-8").strip()
    datasets_raw = (KNOWLEDGE / "datasets.md").read_text(encoding="utf-8")
    cheatsheet = compact_datasets(datasets_raw)
    return "\n\n---\n\n".join([
        "# 角色與規則\n\n" + instructions,
        cheatsheet,
        "# 錯誤處理腳本\n\n" + errors,
        TOKEN_POINTER.strip(),
    ])


def build_bundle() -> str:
    datasets = (KNOWLEDGE / "datasets.md").read_text(encoding="utf-8").strip()
    examples = (KNOWLEDGE / "examples.md").read_text(encoding="utf-8").strip()
    token_guide = (KNOWLEDGE / "token-guide.md").read_text(encoding="utf-8").strip()
    return "\n\n---\n\n".join([
        "# FinMind Custom GPT — 完整 Dataset 參考\n\n" + datasets,
        "# 範例問答\n\n" + examples,
        "# Token 取得與設定\n\n" + token_guide,
    ])


def main() -> int:
    instructions = build_instructions()
    total = len(instructions)
    if total > MAX_INSTRUCTIONS_CHARS:
        print(
            f"ERROR: instructions exceed {MAX_INSTRUCTIONS_CHARS} chars (got {total})",
            file=sys.stderr,
        )
        print("Trim knowledge/instructions.md or knowledge/errors.md.", file=sys.stderr)
        return 1

    INSTRUCTIONS_OUT.write_text(instructions, encoding="utf-8")
    print(f"OK: wrote {INSTRUCTIONS_OUT.name} ({total}/{MAX_INSTRUCTIONS_CHARS} chars)")

    bundle = build_bundle()
    BUNDLE_OUT.write_text(bundle, encoding="utf-8")
    print(f"OK: wrote {BUNDLE_OUT.name} ({len(bundle)} chars, upload to GPT Knowledge)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
