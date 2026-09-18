#!/usr/bin/env python3
"""实时拉取工具链最新版本并与基线对比，输出差异报告。

用法:
    python refresh_toolchain.py                    # 使用内置默认包清单
    python refresh_toolchain.py --baseline toolchain-baseline.json
    python refresh_toolchain.py --update-baseline  # 把当前最新版本写入基线

依赖: 标准库（urllib）。无需 pip 安装。
"""
from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
except Exception:
    pass

# 按角色登记。新增工具时在此追加。
TRACKED = {
    "框架与构建": [
        "react", "vue", "next", "vite",
        "@vitejs/plugin-react", "@vitejs/plugin-vue", "typescript",
    ],
    "样式与组件": [
        "tailwindcss", "unocss", "shadcn", "antd", "naive-ui", "element-plus",
        "radix-ui", "lucide-react", "clsx", "tailwind-merge",
        "class-variance-authority",
    ],
    "图表": [
        "echarts", "echarts-for-react", "recharts", "d3",
    ],
    "数据与状态": [
        "@tanstack/react-query", "@tanstack/vue-query", "@tanstack/react-table",
        "@tanstack/react-virtual", "zustand", "pinia", "swr", "zod", "axios",
    ],
    "测试与质量": [
        "@playwright/test", "playwright", "vitest", "@testing-library/react",
        "axe-core", "@axe-core/playwright", "@lhci/cli", "size-limit",
        "pixelmatch", "msw",
    ],
    "工程规范": [
        "eslint", "prettier", "husky", "lint-staged", "typescript-eslint",
        "eslint-plugin-react-hooks",
    ],
}

REGISTRY = "https://registry.npmjs.org/{name}"


def latest_version(name: str, timeout: int = 20, retries: int = 3) -> str:
    """拉取单个包的最新版本。遇到限流/网络抖动时重试。"""
    url = REGISTRY.format(name=name.replace("/", "%2F"))
    last = "ERR"
    for attempt in range(retries):
        req = urllib.request.Request(url, headers={"User-Agent": "toolchain-refresh"})
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            return data.get("dist-tags", {}).get("latest", "?")
        except Exception as e:
            last = type(e).__name__
            # 退避后重试，缓解 registry 限流
            time.sleep(1.5 * (attempt + 1))
    return f"ERR({last})"


def collect() -> dict[str, dict[str, str]]:
    result: dict[str, dict[str, str]] = {}
    with ThreadPoolExecutor(max_workers=6) as pool:
        for role, pkgs in TRACKED.items():
            versions = dict(zip(pkgs, pool.map(latest_version, pkgs)))
            result[role] = versions
    return result


def _strip_errors(data: dict[str, dict[str, str]]) -> dict[str, dict[str, str]]:
    """写入基线时丢弃拉取失败的项，避免把 ERR 固化成基准。"""
    return {
        role: {k: v for k, v in pkgs.items() if not v.startswith("ERR")}
        for role, pkgs in data.items()
    }


def load_baseline(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


SKILL_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_BASELINE = SKILL_ROOT / "toolchain-baseline.json"
CACHE_FILE = SKILL_ROOT / ".toolchain-cache.json"


def load_cache() -> dict:
    if not CACHE_FILE.exists():
        return {}
    try:
        return json.loads(CACHE_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def save_cache(data: dict) -> None:
    try:
        CACHE_FILE.write_text(
            json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8"
        )
    except OSError:
        pass


def main() -> int:
    ap = argparse.ArgumentParser(
        description="实时拉取工具链最新版本并与基线对比",
        epilog="离线/内网环境请使用 --offline，只与本地基线对比，不访问网络。",
    )
    ap.add_argument("--baseline", default=str(DEFAULT_BASELINE),
                    help=f"基线文件路径，默认 {DEFAULT_BASELINE.name}（脚本同级目录）")
    ap.add_argument("--update-baseline", action="store_true",
                    help="把当前最新版本写入基线文件")
    ap.add_argument("--offline", action="store_true",
                    help="不访问网络，只读取本地缓存/基线并输出对照表（内网可用）")
    args = ap.parse_args()

    if args.offline:
        cached = load_cache()
        print("离线模式：不访问网络，仅输出本地缓存/基线的版本对照。\n")
        if not cached:
            print("[WARN] 本地缓存为空，没有可对照的数据。")
            print("       联网环境下先跑一次不带 --offline 的命令，即可生成缓存。")
            print(f"       缓存路径：{CACHE_FILE}")
            print("       本次没有做任何版本比对，不代表依赖是最新版。")
            return 1
        current = cached
    else:
        print("正在从 npm registry 拉取最新版本 ...\n")
        current = collect()
        save_cache(_strip_errors(current))
    baseline = load_baseline(Path(args.baseline))
    changed = 0

    for role, pkgs in current.items():
        print(f"## {role}")
        for name, ver in pkgs.items():
            old = baseline.get(role, {}).get(name)
            if old is None:
                mark = "NEW"
            elif old != ver:
                mark = f"UPDATE ({old} -> {ver})"
                changed += 1
            else:
                mark = "ok"
            print(f"  {name:<32} {ver:<14} {mark}")
        print()

    print("=" * 60)
    if baseline:
        print(f"与基线相比有 {changed} 项版本变化。")
        if changed:
            print("升级前请评估迁移成本，升级后必须重跑阶段 5-6 全部门禁。")
        print(f"基线文件：{args.baseline}")
    else:
        print(f"[WARN] 未找到基线文件 {args.baseline} —— 无法做版本对比。")
        print("       上面每一行都标为 NEW 只是因为缺少基线，并不代表版本变化。")
        print(f"       默认基线在脚本同级目录：{DEFAULT_BASELINE}")
        return 1

    if args.update_baseline:
        if args.offline:
            print("离线模式下不更新基线（数据非实时）。")
            return 1
        Path(args.baseline).parent.mkdir(parents=True, exist_ok=True)
        Path(args.baseline).write_text(
            json.dumps(_strip_errors(current), indent=2, ensure_ascii=False), encoding="utf-8"
        )
        print(f"已写入基线: {args.baseline}")
    return 0


if __name__ == "__main__":
    sys.exit(main())


