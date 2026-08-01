"""Loads markdown files in the repo `knowledge/` and exposes them as MCP resources.

URI scheme:
    finmind://datasets    → knowledge/datasets.md
    finmind://examples    → knowledge/examples.md
    finmind://errors      → knowledge/errors.md
    finmind://instructions → knowledge/instructions.md
    finmind://token-guide → knowledge/token-guide.md
    finmind://regression  → knowledge/regression.md
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from mcp.types import Resource


def _find_knowledge_dir() -> Path:
    # editable / dev install：repo root 下的 knowledge/
    dev = Path(__file__).resolve().parents[2] / "knowledge"
    if dev.is_dir():
        return dev
    # 從 wheel 安裝後 knowledge/ 透過 hatch force-include 被搬到 package 旁
    bundled = Path(__file__).resolve().parent / "_knowledge"
    if bundled.is_dir():
        return bundled
    # 都找不到時回 dev 路徑；下游 is_file() 會 False，走 fallback templates
    return dev


# Module level so it can be monkey-patched in tests if needed.
KNOWLEDGE_DIR: Path = _find_knowledge_dir()

# Maps URI suffix → file under KNOWLEDGE_DIR.
_RESOURCE_MAP: dict[str, str] = {
    "datasets": "datasets.md",
    "examples": "examples.md",
    "errors": "errors.md",
    "instructions": "instructions.md",
    "token-guide": "token-guide.md",
    "regression": "regression.md",
}


def _path_for(suffix: str) -> Path:
    return KNOWLEDGE_DIR / _RESOURCE_MAP[suffix]


def resource_definitions() -> list[Resource]:
    """Return MCP resource definitions for every present knowledge file."""
    resources: list[Resource] = []
    for suffix, filename in _RESOURCE_MAP.items():
        if (KNOWLEDGE_DIR / filename).is_file():
            resources.append(
                Resource(
                    uri=f"finmind://{suffix}",
                    name=suffix,
                    description=f"FinMind knowledge pack: {filename}",
                    mime_type="text/markdown",
                )
            )
    return resources


def read(uri: str) -> str:
    """Return the raw markdown for the given finmind:// URI."""
    if not uri.startswith("finmind://"):
        raise ValueError(f"unknown URI scheme: {uri}")
    suffix = uri.removeprefix("finmind://")
    if suffix not in _RESOURCE_MAP:
        raise ValueError(f"unknown finmind resource: {suffix}")
    path = _path_for(suffix)
    if not path.is_file():
        raise FileNotFoundError(f"knowledge file missing: {path}")
    return path.read_text(encoding="utf-8")


def dataset_catalog() -> list[dict[str, str]]:
    """Parse datasets.md into ordered {name, category, tier, desc} records.

    FinMind exposes no API endpoint that enumerates all datasets — `/datalist`
    only lists the data_id values *within* a single dataset. So datasets.md is
    the single source of truth for "what datasets exist", shared with the
    Custom GPT knowledge bundle. Returns [] when datasets.md is absent (e.g. CI
    without the knowledge/ tree), letting callers fall back gracefully.
    """
    try:
        content = read("finmind://datasets")
    except FileNotFoundError:
        return []
    records: list[dict[str, str]] = []
    category = ""
    current: Optional[dict[str, str]] = None
    for line in content.splitlines():
        if line.startswith("## "):
            # Section header (e.g. "台股 - 技術面"); "Tier 說明" legend has no
            # dataset entries so it never produces a record.
            category = line[3:].strip()
            current = None
        elif line.startswith("### "):
            current = {
                "name": line[4:].strip(),
                "category": category,
                "tier": "",
                "desc": "",
            }
            records.append(current)
        elif current is not None:
            stripped = line.strip()
            if stripped.startswith("- **Tier:**"):
                current["tier"] = stripped.split("**Tier:**", 1)[1].strip()
            elif stripped.startswith("- **描述:**"):
                current["desc"] = stripped.split("**描述:**", 1)[1].strip()
    return records


def load_errors() -> str:
    """Return errors.md contents for tools.py to format user-facing messages."""
    try:
        return read("finmind://errors")
    except FileNotFoundError:
        return ""


def get_error_template(kind: str) -> Optional[str]:
    """Extract a section from errors.md by error kind.

    kind ∈ {"auth", "payment", "empty", "upstream", "rate_limit"}

    Returns the section's full markdown (header + body) including the
    繁中 response template block. Falls back to a generic 繁中 string
    if errors.md is not present.
    """
    content = load_errors()
    if not content:
        return _FALLBACK_TEMPLATES.get(kind)
    headers = {
        "auth": "401 Unauthorized",
        "payment": "402 Payment Required",
        "empty": "空資料",
        "upstream": "HTTP Timeout / 5xx",
        "rate_limit": "Rate Limit",
    }
    needle = headers.get(kind)
    if not needle:
        return None
    # Sections start with `## ` headers.
    lines = content.splitlines()
    out: list[str] = []
    capturing = False
    for line in lines:
        if line.startswith("## "):
            if capturing:
                break
            if needle in line:
                capturing = True
                out.append(line)
                continue
        if capturing:
            out.append(line)
    section = "\n".join(out).strip()
    return section or _FALLBACK_TEMPLATES.get(kind)


# Minimal 繁中 fallbacks so tests pass even when knowledge/ is missing in CI.
_FALLBACK_TEMPLATES: dict[str, str] = {
    "auth": (
        "您的 FinMind Token 無法驗證，請確認 Token 是否正確。"
        "取得 Token：https://finmindtrade.com/analysis/#/account/user"
    ),
    "payment": (
        "您查詢的資料集需要 Sponsor 會員權限才能存取。"
        "升級 Sponsor 方案：https://finmindtrade.com/analysis/#/account/pricing"
    ),
    "empty": "在指定條件下查無資料，請確認股票代號與日期區間。",
    "upstream": (
        "FinMind 服務目前回應較慢或暫時無法連線，請稍候再試。"
    ),
    "rate_limit": (
        "您目前的請求數已達 FinMind 方案上限。"
        "升級方案：https://finmindtrade.com/analysis/#/account/pricing"
    ),
}
