#!/usr/bin/env python3
"""校验 design-tokens.json 的基本规范，并抽查源码中的硬编码色值。

用法:
    python validate_tokens.py [--tokens design-system/design-tokens.json] [--src src]

退出码: 0 通过, 1 发现问题。
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
except Exception:
    pass

REQUIRED_SEMANTIC = [
    "color-bg-canvas", "color-bg-surface",
    "color-text-primary", "color-text-muted",
    "color-border",
    "color-status-ok", "color-status-warn",
    "color-status-alarm", "color-status-offline",
]
REQUIRED_FONT_SIZES = ["font-size-metric", "font-size-base"]
REQUIRED_CHART_SERIES = ["chart-series-1", "chart-series-2", "chart-series-3"]

# loose hex-color matcher
HEX_RE = re.compile(r"#[0-9a-fA-F]{3,8}\b")
SRC_EXT = {".ts", ".tsx", ".js", ".jsx", ".vue", ".css", ".scss", ".less"}


def _flatten(d: dict, prefix: str = "") -> dict:
    """扁平化 token 树。同时支持 DTCG（{"$value": ...}）与裸标量叶子两种写法。"""
    out = {}
    for k, v in d.items():
        if k.startswith("_"):
            continue
        key = f"{prefix}{k}"
        if isinstance(v, dict):
            if "$value" in v:
                out[key] = v["$value"]
            else:
                out.update(_flatten(v, f"{key}."))
        else:
            out[key] = v
    return out


def check_tokens(path: Path) -> list[str]:
    issues: list[str] = []
    if not path.exists():
        return [f"token 文件不存在: {path}"]

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        return [f"token 文件不是合法 JSON: {e}"]

    flat = _flatten(data)

    def has(name: str) -> bool:
        return any(k == name or k.endswith("." + name) for k in flat)

    for name in REQUIRED_SEMANTIC:
        if not has(name):
            issues.append(f"缺少必需的语义 token: {name}")
    for name in REQUIRED_FONT_SIZES:
        if not has(name):
            issues.append(f"缺少必需的字号 token: {name}")
    for name in REQUIRED_CHART_SERIES:
        if not has(name):
            issues.append(f"缺少必需的图表色板 token: {name}")

    # 检查引用是否存在（{a.b.c} 形式）
    for key, val in flat.items():
        if isinstance(val, str):
            for ref in re.findall(r"\{([^}]+)\}", val):
                if ref not in flat and not any(k.endswith(ref) for k in flat):
                    issues.append(f"token 引用未解析: {key} -> {{{ref}}}")

    if not data.get("primitive"):
        issues.append("缺少 primitive 层（分层要求：primitive -> semantic -> component）")
    if not data.get("semantic"):
        issues.append("缺少 semantic 层")
    return issues


def scan_sources(src: Path) -> list[str]:
    issues: list[str] = []
    if not src.exists():
        return issues
    for f in src.rglob("*"):
        if not f.is_file() or f.suffix not in SRC_EXT:
            continue
        if "node_modules" in f.parts:
            continue
        try:
            text = f.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for i, line in enumerate(text.splitlines(), 1):
            if HEX_RE.search(line):
                # 允许 token 定义文件与注释中的说明
                if "design-tokens" in f.name or "tokens" in f.name:
                    continue
                issues.append(f"疑似硬编码色值 {f}:{i}: {line.strip()[:100]}")
    return issues


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tokens", default="design-system/design-tokens.json")
    ap.add_argument("--src", default="src")
    ap.add_argument("--max-hardcoded", type=int, default=20,
                    help="最多报告多少条硬编码色值")
    args = ap.parse_args()

    token_issues = check_tokens(Path(args.tokens))
    src_issues = scan_sources(Path(args.src))

    print("=" * 60)
    print("design-tokens 校验")
    print("=" * 60)
    if token_issues:
        for i in token_issues:
            print(f"  [FAIL] {i}")
    else:
        print("  [OK] token 结构、必需项、引用关系均通过")

    print()
    print("=" * 60)
    print("源码硬编码色值抽查")
    print("=" * 60)
    if src_issues:
        for i in src_issues[: args.max_hardcoded]:
            print(f"  [WARN] {i}")
        if len(src_issues) > args.max_hardcoded:
            print(f"  ... 另有 {len(src_issues) - args.max_hardcoded} 条")
    else:
        print("  [OK] 未发现硬编码色值")

    print()
    if token_issues:
        print("结论：不通过（token 存在结构性问题）")
        return 1
    if src_issues:
        print("结论：token 通过；源码存在硬编码色值，建议整改后再交付")
        return 0
    print("结论：全部通过")
    return 0


if __name__ == "__main__":
    sys.exit(main())

