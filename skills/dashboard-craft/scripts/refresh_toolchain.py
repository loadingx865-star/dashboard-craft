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


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--baseline", default="toolchain-baseline.json")
    ap.add_argument("--update-baseline", action="store_true",
                    help="把当前最新版本写入基线文件")
    args = ap.parse_args()

    print("正在从 npm registry 拉取最新版本 ...\n")
    current = collect()
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
    else:
        print(f"未找到基线文件 {args.baseline}，以上为当前最新版本。")

    if args.update_baseline:
        Path(args.baseline).write_text(
            json.dumps(_strip_errors(current), indent=2, ensure_ascii=False), encoding="utf-8"
        )
        print(f"已写入基线: {args.baseline}")
    return 0


if __name__ == "__main__":
    sys.exit(main())


