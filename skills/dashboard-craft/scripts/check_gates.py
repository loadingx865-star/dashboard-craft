#!/usr/bin/env python3
"""校验看板项目是否满足 dashboard-craft 各阶段 Gate。

用途：把"AI 声称 Gate 已通过"变成"脚本判定 Gate 是否通过"。

约定：本脚本检查的是**目标项目**目录（默认当前目录）下的标准结构：
    design-system/constraints-card.md     阶段 0 环境约束卡（必填项不留空）
    design-system/design-tokens.json      阶段 1 设计真源
    design-system/MASTER.md               阶段 1 人读规范（含缩放策略与图表规范）
    specs/*.md                            阶段 2 规格与拆票（含验收标准）
    src/layouts|views|app                阶段 3 布局骨架入口
    src/components + src/charts           阶段 4 组件与图表统一入口
    acceptance-matrix.md                  阶段 5 验收矩阵（或 design-system/ 下）
    *report*.md                           阶段 6 性能/a11y/冒烟/视觉报告
    README.md                             阶段 7 部署与回滚说明
    assets/templates 目录结构可参考 skill 自带的 templates/

用法:
    python check_gates.py --project .
    python check_gates.py --project . --stage 3
    python check_gates.py --project . --json
    python check_gates.py --project . --allow-empty-card   # 只做结构检查，不卡填写完整度

退出码: 0 通过, 1 未通过。
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

# 模板里的空占位写法，出现即视为"未填"
EMPTY_CELL_RE = re.compile(r"\|\s*\|")
PLACEHOLDER_RE = re.compile(r"<(?:待填|TODO|TBD|请填写)[^>]*>|待填|TODO|TBD|xxx|XXX|＿＿", re.I)
CHECKBOX_EMPTY_RE = re.compile(r"^\s*-\s*\[\s\]", re.M)

CARD_CANDIDATES = (
    "design-system/constraints-card.md",
    "docs/constraints-card.md",
    "constraints-card.md",
    "环境约束卡.md",
)
TOKENS_CANDIDATES = (
    "design-system/design-tokens.json",
    "design-tokens.json",
    "src/design-tokens.json",
)
MASTER_CANDIDATES = (
    "design-system/MASTER.md",
    "design-system/master.md",
    "MASTER.md",
)
MATRIX_CANDIDATES = (
    "acceptance-matrix.md",
    "design-system/acceptance-matrix.md",
    "docs/acceptance-matrix.md",
    "验收矩阵.md",
)

# 阶段 3/4 的入口目录候选（覆盖 React 与 Vue 常见约定）
SKELETON_CANDIDATES = (
    "src/layouts", "src/layout", "src/shell", "src/app", "src/views", "src/pages",
)
COMPONENT_CANDIDATES = (
    "src/components", "src/ui", "src/lib/components", "src/shared/components",
)
CHART_CANDIDATES = (
    "src/charts", "src/components/charts", "src/lib/charts",
    "src/plugins/charts", "src/shared/charts",
)
DIR_MAPPING_HEADING_RE = re.compile(r"^#{2,4}\s*.*(目录|结构|directory|layout)", re.M)
# 目录登记必须与类别语义匹配，避免登记一个无关目录就放行整个结构 Gate
SKELETON_HINTS = ("layout", "shell", "views", "pages", "app", "骨架", "布局", "视图")
COMPONENT_HINTS = ("component", "ui", "shared", "widget", "组件")
CHART_HINTS = ("chart", "graph", "echart", "图表", "可视化")
PATH_TOKEN_RE = re.compile(r"`([A-Za-z0-9_@./-]+/[A-Za-z0-9_@./-]*)`")

STAGE_NAMES = {
    0: "约束锁定",
    1: "设计单一真源",
    2: "规格与拆票",
    3: "骨架先行",
    4: "组件与图表",
    5: "适配验证",
    6: "质量门禁",
    7: "交付存档",
}


def _first_existing(root: Path, candidates) -> Path | None:
    for rel in candidates:
        p = root / rel
        if p.is_file():
            return p
    return None


def _table_rows(text: str) -> list[str]:
    """取出 markdown 表格的数据行（排除表头与分隔行）。"""
    rows = []
    for line in text.splitlines():
        s = line.strip()
        if not s.startswith("|"):
            continue
        cells = [c.strip() for c in s.strip("|").split("|")]
        if not cells:
            continue
        if all(set(c) <= set("-: ") for c in cells):
            continue
        rows.append(cells)
    return rows


def check_constraints_card(path: Path | None, allow_empty: bool):
    issues, notes = [], []
    if path is None:
        issues.append(
            "阶段 0 未通过：找不到环境约束卡。"
            f"请从 skill 的 assets/templates/constraints-card.md 复制到 {CARD_CANDIDATES[0]}"
        )
        return issues, notes
    text = path.read_text(encoding="utf-8")
    rows = _table_rows(text)
    data_rows = [r for r in rows if len(r) >= 2]

    if not data_rows:
        issues.append(
            "阶段 0 未通过：约束卡没有任何表格数据行。"
            "请从 skill 的 assets/templates/constraints-card.md 复制结构后填写"
        )

    empty_rows = [r for r in data_rows if any(c == "" for c in r[1:])]
    if empty_rows and not allow_empty:
        issues.append(
            f"阶段 0 未通过：约束卡有 {len(empty_rows)} 行未填完整，"
            f"例如 “{empty_rows[0][0]}”"
        )

    hits = PLACEHOLDER_RE.findall(text)
    if hits and not allow_empty:
        issues.append(f"阶段 0 未通过：约束卡残留占位内容 {len(hits)} 处（如 {hits[0]}）")

    unchecked = len(CHECKBOX_EMPTY_RE.findall(text))
    if unchecked and not allow_empty:
        notes.append(f"约束卡仍有 {unchecked} 个未勾选项（国产内核/缩放/适配策略等确认项）")

    if not re.search(r"分辨率|视口|1920|3840|2560", text):
        issues.append("阶段 0 未通过：约束卡未记录任何真实分辨率/视口")
    return issues, notes


def check_design_source(root: Path, tokens: Path | None, master: Path | None):
    issues, notes = [], []
    if tokens is None:
        issues.append(
            "阶段 1 未通过：找不到 design-tokens.json"
            f"（候选位置: {', '.join(TOKENS_CANDIDATES[:2])}）"
        )
    if master is None:
        issues.append(
            f"阶段 1 未通过：找不到 MASTER 规范（候选: {', '.join(MASTER_CANDIDATES[:2])}）"
        )
    if master is not None:
        text = master.read_text(encoding="utf-8")
        if not re.search(r"缩放|scale|断点", text):
            issues.append("阶段 1 未通过：MASTER 未写明大屏字号缩放策略（等比/断点/混合）")
        if not re.search(r"图表", text):
            issues.append("阶段 1 未通过：MASTER 未写明图表规范")
        pages = root / "design-system" / "pages"
        if pages.is_dir() and any(pages.glob("*.md")):
            notes.append(f"已登记 {len(list(pages.glob('*.md')))} 个页面级偏离文件")
    if tokens is not None:
        notes.append("token 结构校验请单独运行 scripts/validate_tokens.py（本脚本不重复实现）")
    return issues, notes


def check_specs(root: Path):
    issues, notes = [], []
    spec_dirs = [root / "specs", root / "docs" / "specs", root / "tickets"]
    files: list[Path] = []
    for d in spec_dirs:
        if d.is_dir():
            files.extend(sorted(d.glob("*.md")))
    if not files:
        issues.append(
            "阶段 2 未通过：找不到规格/任务文件（specs/*.md 或 tickets/*.md）"
        )
        return issues, notes
    weak = []
    for f in files:
        text = f.read_text(encoding="utf-8")
        has_acceptance = bool(re.search(r"验收|acceptance|Given|When|Then", text, re.I))
        if not has_acceptance:
            weak.append(f.name)
    if weak:
        issues.append(
            f"阶段 2 未通过：{len(weak)} 个任务文件没有可验证的验收标准（如 {weak[0]}）"
        )
    notes.append(f"已检查 {len(files)} 个任务文件")
    return issues, notes


def check_matrix(root: Path, matrix: Path | None, tokens_present: bool):
    issues, notes = [], []
    if matrix is None:
        issues.append(
            f"阶段 5 未通过：找不到验收矩阵（候选: {', '.join(MATRIX_CANDIDATES[:2])}）"
        )
        return issues, notes
    text = matrix.read_text(encoding="utf-8")
    rows = _table_rows(text)
    viewport_rows = [r for r in rows if len(r) >= 4 and re.search(r"\d{3,4}", " ".join(r))]
    if not viewport_rows:
        issues.append("阶段 5 未通过：验收矩阵里没有可识别的视口行（宽×高）")
    pending = [r for r in viewport_rows if any(re.search(r"☐|\[ \]|未测|待测", c) for c in r)]
    if pending:
        issues.append(
            f"阶段 5 未通过：验收矩阵仍有 {len(pending)} 个视口未标记通过"
            f"（如 {pending[0][1] if len(pending[0]) > 1 else pending[0][0]}）"
        )
    failed_rows = [
        r for r in viewport_rows
        if any(re.search(r"失败|不通过|未通过|fail", c, re.I) for c in r)
    ]
    if failed_rows:
        issues.append(
            f"阶段 5 未通过：验收矩阵有 {len(failed_rows)} 个视口结果为失败/不通过"
            f"（如 {failed_rows[0][1] if len(failed_rows[0]) > 1 else failed_rows[0][0]}）"
        )
    if not re.search(r"基线|baseline|__screenshots__", text, re.I):
        issues.append("阶段 5 未通过：验收矩阵未登记截图基线位置")
    notes.append(f"矩阵视口行 {len(viewport_rows)} 条")
    return issues, notes


def _documented_dir_mapping(root: Path, master: Path | None) -> list[str]:
    """MASTER 里用「目录结构」小节登记过的、且真实存在的目录。

    非标准目录约定是被允许的（铁律 5：偏离必须登记），但登记之后
    路径必须真实存在，避免用一句空话绕过结构 Gate。
    """
    if master is None or not master.is_file():
        return []
    text = master.read_text(encoding="utf-8")
    m = DIR_MAPPING_HEADING_RE.search(text)
    if not m:
        return []
    tail = text[m.end():]
    nxt = re.search(r"^##\s", tail, re.M)
    section = tail[: nxt.start()] if nxt else tail
    found = []
    for token in PATH_TOKEN_RE.findall(section):
        token = token.rstrip("/")
        if token and (root / token).exists():
            found.append(token)
    return found


def _documented_for(documented: list[str], hints) -> list[str]:
    """从已登记的目录里挑出与当前类别语义匹配的路径。"""
    out = []
    for path in documented:
        low = path.lower()
        if any(h in low for h in hints):
            out.append(path)
    return out


def check_skeleton(root: Path, master: Path | None, stage: int):
    """阶段 3 要求能定位到布局骨架；阶段 4 要求组件与图表各有统一入口。

    不猜测代码内容，只校验入口存在。非标准目录约定需在 MASTER 的
    「目录结构」小节登记，且登记的路径必须真实存在。
    """
    issues, notes = [], []
    skeleton = [h for h in SKELETON_CANDIDATES if (root / h).is_dir()]
    components = [h for h in COMPONENT_CANDIDATES if (root / h).is_dir()]
    charts = [h for h in CHART_CANDIDATES if (root / h).is_dir()]
    documented = _documented_dir_mapping(root, master)

    documented_skeleton = _documented_for(documented, SKELETON_HINTS)
    documented_components = _documented_for(documented, COMPONENT_HINTS)
    documented_charts = _documented_for(documented, CHART_HINTS)

    if stage == 3:
        if skeleton:
            notes.append(f"已发现布局骨架目录: {', '.join(skeleton)}")
        elif documented_skeleton:
            notes.append(
                "未使用默认骨架目录，已按 MASTER 目录登记确认: "
                + ", ".join(documented_skeleton)
            )
        else:
            issues.append(
                "阶段 3 未通过：找不到布局骨架入口"
                f"（候选: {', '.join(SKELETON_CANDIDATES)}）。"
                "若项目使用其他目录约定，请在 design-system/MASTER.md 的"
                "「目录结构」小节登记该路径"
            )
        return issues, notes

    # stage 4
    if components:
        notes.append(f"已发现共享组件目录: {', '.join(components)}")
    elif documented_components:
        notes.append(
            "共享组件目录按 MASTER 目录登记确认: " + ", ".join(documented_components)
        )
    else:
        issues.append(
            "阶段 4 未通过：找不到共享组件目录"
            f"（候选: {', '.join(COMPONENT_CANDIDATES)}）"
        )
    if charts:
        notes.append(f"已发现图表封装目录: {', '.join(charts)}")
    elif documented_charts:
        notes.append(
            "图表封装目录按 MASTER 目录登记确认: " + ", ".join(documented_charts)
        )
    else:
        issues.append(
            "阶段 4 未通过：找不到图表统一封装目录"
            f"（候选: {', '.join(CHART_CANDIDATES)}）。"
            "页面内直接实例化图表库属于违规"
        )
    return issues, notes


def check_delivery(root: Path):
    issues, notes = [], []
    readme = root / "README.md"
    if not readme.is_file():
        issues.append("阶段 7 未通过：交付包缺少 README.md（部署/回滚说明入口）")
    else:
        text = readme.read_text(encoding="utf-8")
        if not re.search(r"回滚|rollback", text, re.I):
            issues.append("阶段 7 未通过：README 未包含回滚说明")
        if not re.search(r"部署|deploy|构建", text, re.I):
            issues.append("阶段 7 未通过：README 未包含部署/构建说明")
    return issues, notes


def main() -> int:
    ap = argparse.ArgumentParser(description="dashboard-craft Gate 校验")
    ap.add_argument("--project", default=".", help="目标项目根目录")
    ap.add_argument("--stage", type=int, action="append", choices=sorted(STAGE_NAMES),
                    help="只校验指定阶段 0-7（可重复，如 --stage 0 --stage 1）")
    ap.add_argument("--allow-empty-card", action="store_true",
                    help="只检查文件是否存在与结构，不卡填写完整度")
    ap.add_argument("--json", action="store_true", help="以 JSON 输出")
    args = ap.parse_args()

    root = Path(args.project).expanduser().resolve()
    wanted = set(args.stage) if args.stage else set(STAGE_NAMES)

    card = _first_existing(root, CARD_CANDIDATES)
    tokens = _first_existing(root, TOKENS_CANDIDATES)
    master = _first_existing(root, MASTER_CANDIDATES)
    matrix = _first_existing(root, MATRIX_CANDIDATES)

    results: dict[int, dict] = {}

    def run(stage: int, fn):
        if stage not in wanted:
            return
        issues, notes = fn()
        results[stage] = {"issues": issues, "notes": notes}

    run(0, lambda: check_constraints_card(card, args.allow_empty_card))
    run(1, lambda: check_design_source(root, tokens, master))
    run(2, lambda: check_specs(root))
    run(3, lambda: check_skeleton(root, master, 3))
    run(4, lambda: check_skeleton(root, master, 4))
    run(5, lambda: check_matrix(root, matrix, tokens is not None))
    def check_reports():
        reports = [
            p for p in root.rglob("*.md")
            if re.search(r"report|报告", p.name, re.I) and "node_modules" not in p.parts
        ]
        if not reports:
            return (["阶段 6 未通过：未找到验证报告（文件名含 report/报告）"], [])
        issues, notes = [], []
        blob = "\n".join(p.read_text(encoding="utf-8", errors="replace") for p in reports)
        checks = (
            (r"性能|performance|lighthouse|包体积|bundle", "性能预算"),
            (r"a11y|可访问性|accessibility|axe", "可访问性"),
            (r"冒烟|smoke", "冒烟测试"),
            (r"视觉|visual|diff|截图", "视觉回归"),
        )
        missing = [label for pattern, label in checks if not re.search(pattern, blob, re.I)]
        if missing:
            issues.append(
                "阶段 6 未通过：验证报告缺少以下门禁结论: " + "、".join(missing)
            )
        notes.append(f"已检查 {len(reports)} 个报告文件")
        return issues, notes

    run(6, check_reports)
    run(7, lambda: check_delivery(root))

    all_issues = [i for r in results.values() for i in r["issues"]]
    all_notes = [n for r in results.values() for n in r["notes"]]

    if args.json:
        print(json.dumps({
            "ok": not all_issues,
            "project": str(root),
            "checked_stages": sorted(results),
            "issues": all_issues,
            "notes": all_notes,
        }, ensure_ascii=False, indent=2))
        return 1 if all_issues else 0

    print("=" * 60)
    print("dashboard-craft Gate 校验")
    print("=" * 60)
    print(f"项目目录: {root}")
    print(f"检查阶段: {', '.join(str(s) for s in sorted(results))}")
    print(f"约束卡: {card if card else '未找到'}")
    print(f"token : {tokens if tokens else '未找到'}")
    print(f"矩阵  : {matrix if matrix else '未找到'}")
    print()

    for stage in sorted(results):
        r = results[stage]
        status = "通过" if not r["issues"] else "未通过"
        print(f"阶段 {stage} {STAGE_NAMES[stage]} —— {status}")
        for i in r["issues"]:
            print(f"    [FAIL] {i}")
        for n in r["notes"]:
            print(f"    [INFO] {n}")
    print()

    if all_issues:
        print(f"结论：不通过（{len(all_issues)} 项）。Gate 未通过不得进入下一阶段。")
        return 1
    print("结论：所选阶段的 Gate 全部通过")
    return 0


if __name__ == "__main__":
    sys.exit(main())
