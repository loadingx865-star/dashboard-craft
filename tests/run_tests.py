#!/usr/bin/env python3
"""dashboard-craft 回归测试。

覆盖正反两类用例：合法 token 写法必须通过，硬编码样式必须被抓到。
这是"校验器真的有在工作"的证据 —— 没有这些用例，CI 绿灯只是假象。

用法:
    python tests/run_tests.py
退出码: 0 全部通过, 1 有用例失败。
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

REPO = Path(__file__).resolve().parent.parent
SKILL = REPO / "skills" / "dashboard-craft"
SCRIPTS = SKILL / "scripts"
VALIDATE = SCRIPTS / "validate_tokens.py"
GATES = SCRIPTS / "check_gates.py"
FIX = REPO / "tests" / "fixtures"
DEMO = FIX / "demo-project"
EXAMPLE_TOKENS = SKILL / "assets" / "templates" / "design-tokens.example.json"
# 变体夹具在临时目录里从 demo-project 派生，避免仓库堆积重复文件
TMP = Path(tempfile.mkdtemp(prefix="dashboard-craft-tests-"))


def variant(name: str, *, drop=(), rewrite=None) -> Path:
    """复制 demo-project 并按需删目录/改文件，返回变体路径。"""
    dst = TMP / name
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(DEMO, dst)
    for rel in drop:
        victim = dst / rel
        if victim.is_dir():
            shutil.rmtree(victim)
        elif victim.exists():
            victim.unlink()
    for rel, content in (rewrite or {}).items():
        target = dst / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
    return dst

failures: list[str] = []
passed = 0


def run(args, expect: int, label: str, expect_in: str | None = None):
    global passed
    r = subprocess.run(
        [sys.executable] + [str(a) for a in args],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    out = (r.stdout or "") + (r.stderr or "")
    ok = r.returncode == expect
    if ok and expect_in is not None:
        ok = expect_in in out
    if ok:
        passed += 1
        print(f"  [OK]   {label}")
    else:
        failures.append(f"{label}（期望 exit={expect}，实际 exit={r.returncode}）\n{out[-600:]}")
        print(f"  [FAIL] {label} 实际 exit={r.returncode}")
    return out


def main() -> int:
    print("=" * 60)
    print("dashboard-craft 回归测试")
    print("=" * 60)
    print("\n--- token 结构：合法写法必须通过 ---")
    run([VALIDATE, "--tokens", EXAMPLE_TOKENS, "--src", FIX / "src_ok"],
        0, "示例 token + 干净源码 → 通过")
    run([VALIDATE, "--tokens", FIX / "tokens.multi-theme.json", "--src", FIX / "src_ok"],
        0, "多主题 themes{} + DTCG 嵌套 → 通过")
    run([VALIDATE, "--tokens", FIX / "tokens.custom-layers.json",
         "--layers", "base,alias,config", "--src", FIX / "src_ok"],
        0, "自定义层名 base/alias/config → 通过")

    print("\n--- token 结构：非法写法必须失败 ---")
    run([VALIDATE, "--tokens", FIX / "tokens.broken-ref.json", "--src", FIX / "src_ok"],
        1, "悬空引用 {primitive.notexist} → 失败", "引用未解析")

    print("\n--- 硬编码检测：必须抓到（上轮漏报的正是这些） ---")
    r = subprocess.run(
        [sys.executable, str(VALIDATE), "--tokens", str(EXAMPLE_TOKENS),
         "--src", str(FIX / "src"), "--json"],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    data = json.loads(r.stdout)
    found = "\n".join(data["hardcoded_issues"])
    for needle, label in (
        ("bg-slate-900", "Tailwind 调色板原子类"),
        ("text-red-500", "Tailwind 调色板原子类（文字）"),
        ("text-white", "Tailwind 颜色关键字类"),
        ("rgb(", "颜色函数 rgb()"),
        ("fontSize", "内联样式魔法数字"),
        ("padding: 16px", "CSS 魔法数字"),
    ):
        if needle in found:
            globals()["passed"] += 1
            print(f"  [OK]   抓到 {label}: {needle}")
        else:
            failures.append(f"漏报 {label}: {needle}")
            print(f"  [FAIL] 漏报 {label}: {needle}")

    print("\n--- 误报控制：正常写法不得被误判 ---")
    run([VALIDATE, "--tokens", EXAMPLE_TOKENS, "--src", FIX / "src_ok"],
        0, "var()/token 类/1px 发丝线/锚点 #section → 无告警",
        "未发现硬编码样式")

    print("\n--- 硬编码门禁开关 ---")
    run([VALIDATE, "--tokens", EXAMPLE_TOKENS, "--src", FIX / "src"],
        0, "默认模式：只告警，不失败")
    run([VALIDATE, "--tokens", EXAMPLE_TOKENS, "--src", FIX / "src", "--fail-on-hardcode"],
        1, "--fail-on-hardcode：存在硬编码即失败")

    print("\n--- Gate 校验：空项目必须失败 ---")
    empty = TMP / "empty-project"
    empty.mkdir(parents=True, exist_ok=True)
    run([GATES, "--project", empty],
        1, "空项目 → Gate 未通过", "不通过")

    print("\n--- Gate 校验：合规项目必须通过（防误伤） ---")
    run([GATES, "--project", DEMO],
        0, "标准项目结构 → 八阶段全过", "全部通过")

    custom = variant(
        "custom-layout-project",
        drop=("src",),
        rewrite={
            "design-system/MASTER.md": (
                "# MASTER\n\n## 缩放策略\n断点重排。\n\n## 图表规范\n"
                "ECharts 唯一封装。\n\n## 7. 目录结构（非标准约定必填）\n"
                "- `app/views/` 布局与页面骨架\n- `lib/ui/` 共享组件\n"
                "- `lib/charts/` 图表封装\n"
            )
        },
    )
    for d in ("app/views", "lib/ui", "lib/charts"):
        (custom / d).mkdir(parents=True, exist_ok=True)
    run([GATES, "--project", custom],
        0, "非标准目录 + MASTER 登记 → 全过", "全部通过")

    print("\n--- 端到端：合规项目阶段 1 也必须过 ---")
    run([VALIDATE, "--tokens", DEMO / "design-system" / "design-tokens.json",
         "--src", FIX / "src_ok"],
        0, "合规项目 token + 干净源码 → 阶段 1 通过")

    print("\n--- Gate 校验：结构缺失必须失败（防静默放行） ---")
    no_skel = variant("no-skeleton-project", drop=("src",))
    run([GATES, "--project", no_skel, "--stage", "3"],
        1, "缺布局骨架 → 阶段 3 失败", "阶段 3 未通过")

    no_charts = variant("no-charts-project", drop=("src/charts",))
    run([GATES, "--project", no_charts, "--stage", "4"],
        1, "缺图表封装目录 → 阶段 4 失败", "阶段 4 未通过")

    # 只登记了骨架目录时，不得顺带放行图表封装目录
    partial = variant(
        "partial-mapping-project",
        drop=("src",),
        rewrite={
            "design-system/MASTER.md": (
                "# MASTER\n\n## 缩放策略\n断点重排。\n\n## 图表规范\n"
                "ECharts 唯一封装。\n\n## 目录结构\n- `app/views/` 布局骨架\n"
            )
        },
    )
    (partial / "app/views").mkdir(parents=True, exist_ok=True)
    run([GATES, "--project", partial, "--stage", "4"],
        1, "仅登记骨架目录 → 阶段 4 仍失败", "阶段 4 未通过")

    thin = variant(
        "thin-report-project",
        rewrite={"reports/quality-report.md": "# 质量门禁报告\n\n- 性能：1.2s\n"},
    )
    run([GATES, "--project", thin, "--stage", "6"],
        1, "报告缺少 a11y/冒烟/视觉结论 → 阶段 6 失败", "阶段 6 未通过")

    print("\n--- 假通过防线：参数/配置错误不得算作通过 ---")
    run([GATES, "--project", DEMO, "--stage", "9"],
        2, "非法阶段号 → argparse 报错退出（不再静默全过）")
    run([GATES, "--project", DEMO, "--stage", "-1"],
        2, "负阶段号 → argparse 报错退出")
    run([VALIDATE, "--tokens", EXAMPLE_TOKENS, "--src", TMP / "no-such-src",
         "--fail-on-hardcode"],
        1, "--src 指向不存在的目录 → 配置错误判失败", "配置错误")

    print("\n--- 硬编码检测：hex 色值漏报回归（上轮只报 CSS 里的） ---")
    hexprobe = variant("hex-probe") / "src" / "probe"
    hexprobe.mkdir(parents=True, exist_ok=True)
    (hexprobe / "probe.tsx").write_text(
        'const c = "#1e293b";\n'
        'export const B = () => <div style={{ background: "#1e293b" }} />;\n',
        encoding="utf-8",
    )
    r = subprocess.run(
        [sys.executable, str(VALIDATE), "--tokens", str(EXAMPLE_TOKENS),
         "--src", str(hexprobe), "--json"],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    data = json.loads(r.stdout)
    hit = "\n".join(data["hardcoded_issues"])
    if hit.count("#1e293b") >= 2:
        globals()["passed"] += 1
        print("  [OK]   JSX 变量与内联样式里的 hex 色值均被抓到")
    else:
        failures.append("hex 漏报：JSX/内联样式里的 #1e293b 未被抓到")
        print("  [FAIL] hex 漏报：JSX/内联样式里的 #1e293b 未被抓到")

    print("\n--- 锚点豁免：只认 JSX 属性，不得放过同名变量 ---")
    anchor_probe = variant("anchor-probe") / "src" / "probe"
    anchor_probe.mkdir(parents=True, exist_ok=True)
    (anchor_probe / "probe.tsx").write_text(
        'const href = "#ffffff";\n'
        'export const A = () => <a href="#section">ok</a>;\n'
        'export const B = () => <Link to="/detail#face">ok</Link>;\n',
        encoding="utf-8",
    )
    out = run([VALIDATE, "--tokens", EXAMPLE_TOKENS, "--src", anchor_probe,
               "--fail-on-hardcode"],
              1, 'const href="#ffffff" → 判硬编码；真锚点不误报', "#ffffff")
    if "section" in out or "face" in out:
        failures.append("锚点误报：真锚点 #section / /detail#face 被当成色值")
        print("  [FAIL] 锚点误报：真锚点被当成色值")
    else:
        globals()["passed"] += 1
        print("  [OK]   真锚点 #section 与 /detail#face 未误报")

    print("\n--- Gate 反例：矩阵失败态与空约束卡不得算通过 ---")
    bad_matrix = variant(
        "matrix-failed-project",
        rewrite={"acceptance-matrix.md": (
            "# 验收矩阵\n\n"
            "| 视口 | 宽度 | 高度 | 浏览器 | 结果 |\n"
            "|---|---|---|---|---|\n"
            "| laptop | 1920 | 1080 | Chrome | 失败 |\n"
            "| tv-4k | 3840 | 2160 | Chrome | 不通过 |\n\n"
            "截图基线位置：`__screenshots__/`\n"
        )},
    )
    run([GATES, "--project", bad_matrix, "--stage", "5"],
        1, "矩阵结果为失败/不通过 → 阶段 5 失败", "阶段 5 未通过")

    no_compat = variant(
        "card-no-compat-project",
        rewrite={"design-system/constraints-card.md": (
            "# 环境约束卡\n\n"
            "| 项目 | 内容 |\n|---|---|\n"
            "| 显示终端 | 工厂电视 |\n"
            "| 物理分辨率 | 1920x1080 |\n"
            "| 系统缩放 | 100% |\n"
            "| 浏览器 | Chrome 120 |\n"
            "| 观看距离 | 3 米 |\n"
            "| 数据频率 | 5 秒 |\n"
            "| 网络环境 | 内网 |\n"
        )},
    )
    run([GATES, "--project", no_compat, "--stage", "0"],
        1, "约束卡未声明兼容目标 → 阶段 0 失败",
        "未声明兼容目标")

    no_table = variant(
        "card-no-table-project",
        rewrite={"design-system/constraints-card.md": (
            "# 环境约束卡\n\n目标 1920x1080，Chrome。\n"
        )},
    )
    run([GATES, "--project", no_table, "--stage", "0"],
        1, "约束卡只有正文没有表格 → 阶段 0 失败", "没有任何表格数据行")

    print("\n--- 工具链脚本：缺失基线必须报错（不得假装全部更新） ---")
    run([SCRIPTS / "refresh_toolchain.py", "--offline",
         "--baseline", TMP / "no-such-baseline.json"],
        1, "基线不存在 → 明确失败", "无法做版本对比")

    print("\n--- 脚本可运行性 ---")
    for s in (VALIDATE, GATES, SCRIPTS / "refresh_toolchain.py"):
        run([s, "--help"], 0, f"{s.name} --help 正常退出")

    shutil.rmtree(TMP, ignore_errors=True)

    print()
    print("=" * 60)
    if failures:
        print(f"结论：{len(failures)} 个用例失败（通过 {passed} 个）")
        for f in failures:
            print(f"  - {f}")
        return 1
    print(f"结论：全部通过（{passed} 个用例）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
