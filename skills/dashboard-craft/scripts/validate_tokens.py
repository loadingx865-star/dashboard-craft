#!/usr/bin/env python3
"""校验 design tokens 结构，并检测源码中的硬编码样式。

用法:
    python validate_tokens.py --tokens design-system/design-tokens.json --src src
    python validate_tokens.py --src src,app --fail-on-hardcode
    python validate_tokens.py --layers base,alias,config
    python validate_tokens.py --json

退出码:
    0 通过
    1 token 结构有问题，或（在 --fail-on-hardcode 下）源码存在硬编码样式

支持的 token 组织方式（三种都合法，脚本不做形状绑架）:
    1. 扁平命名 + 三层顶层键:   {"primitive": {...}, "semantic": {...}, "component": {...}}
    2. 分组嵌套（DTCG 风格）:   {"semantic": {"color": {"bg": {"canvas": {"$value": ...}}}}}
    3. 多主题:                  {"primitive": {...}, "themes": {"dark": {...}, "light": {...}}}

层名可配置（顺序固定为 基础值 / 语义值 / 组件值）:
    python validate_tokens.py --layers base,alias,config
默认层名 primitive / semantic / component，并内置常见同义词（base、alias、config 等）。

豁免硬编码告警：在对应行加注释 ``hardcode-ok: 原因``。
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

REQUIRED_SEMANTIC = [
    "color-bg-canvas", "color-bg-surface",
    "color-text-primary", "color-text-muted",
    "color-border",
    "color-status-ok", "color-status-warn",
    "color-status-alarm", "color-status-offline",
]
REQUIRED_FONT_SIZES = ["font-size-metric", "font-size-base"]
REQUIRED_CHART_SERIES = ["chart-series-1", "chart-series-2", "chart-series-3"]

LAYER_ROLES = ("primitive", "semantic", "component")
LAYER_LABEL = {
    "primitive": "基础值层",
    "semantic": "语义值层",
    "component": "组件值层",
}
LAYER_ALIASES = {
    "primitive": {"primitive", "primitives", "base", "raw", "foundation", "global", "palette"},
    "semantic": {"semantic", "semantics", "alias", "aliases", "theme", "themes", "mapping"},
    "component": {"component", "components", "config", "spec", "ui", "application", "app"},
}
THEME_KEYS = ("themes", "$themes", "modes", "colorSchemes", "theme")

SRC_EXT = {".ts", ".tsx", ".js", ".jsx", ".vue", ".css", ".scss", ".less"}
TOKENS_FILE_HINT = "tokens"

# --- 硬编码检测规则 -------------------------------------------------------
HEX_RE = re.compile(r"#[0-9a-fA-F]{3,8}\b")
COLOR_FUNC_RE = re.compile(
    r"(?<![\w-])(?:rgba?|hsla?|hsva?|oklch|oklab|lab|lch|color-mix)\s*\(", re.I
)
TW_PALETTE = (
    "slate|gray|zinc|neutral|stone|red|orange|amber|yellow|lime|green|emerald|"
    "teal|cyan|sky|blue|indigo|violet|purple|fuchsia|pink|rose"
)
TW_COLOR_RE = re.compile(
    r"(?<![\w-])(?:bg|text|border|ring|inset-ring|fill|stroke|from|via|to|divide|"
    r"placeholder|caret|accent|decoration|outline|shadow)-(?:" + TW_PALETTE + r")"
    r"(?:-\d{2,3})?(?:/\d{1,3})?(?![\w-])",
    re.I,
)
TW_KEYWORD_COLOR_RE = re.compile(
    r"(?<![\w-])(?:bg|text|border|ring|inset-ring|fill|stroke|divide|placeholder|"
    r"caret|accent|decoration|outline|shadow)-(?:white|black|transparent|current)"
    r"(?:/\d{1,3})?(?![\w-])",
    re.I,
)

# Tailwind 任意值写法里的硬编码尺寸：text-[13px] / p-[13px] / gap-[7px]
# var(--x) 与 calc() 形式不算（它们引用了真源或真源派生值）
TW_ARBITRARY_RE = re.compile(
    r"(?<![\w-])(?:text|p|px|py|pt|pb|pl|pr|m|mx|my|mt|mb|ml|mr|gap|gap-x|gap-y|"
    r"w|h|min-w|min-h|max-w|max-h|top|bottom|left|right|inset|space-x|space-y|"
    r"rounded|leading|tracking|z|border)-\[(\d+(?:\.\d+)?)(px|rem|em|pt)\]",
    re.I,
)

NUMERIC_STYLE_PROPS = (
    "fontSize", "lineHeight", "letterSpacing", "fontWeight",
    "padding", "paddingTop", "paddingBottom", "paddingLeft", "paddingRight",
    "paddingX", "paddingY", "margin", "marginTop", "marginBottom",
    "marginLeft", "marginRight", "marginX", "marginY",
    "width", "height", "minWidth", "maxWidth", "minHeight", "maxHeight",
    "gap", "rowGap", "columnGap", "top", "left", "right", "bottom",
    "borderRadius", "borderWidth", "borderTopWidth", "borderBottomWidth",
    "borderLeftWidth", "borderRightWidth", "zIndex",
)
INLINE_NUM_RE = re.compile(
    r"(?<![\w.])(" + "|".join(NUMERIC_STYLE_PROPS) + r")\s*[:=]\s*(\d+(?:\.\d+)?)(?![\w.%])"
)
CSS_NUM_RE = re.compile(
    r"(?<![\w-])(font-size|line-height|letter-spacing|padding(?:-top|-bottom|-left|-right)?|"
    r"margin(?:-top|-bottom|-left|-right)?|width|height|min-width|max-width|min-height|"
    r"max-height|gap|row-gap|column-gap|top|left|right|bottom|border-radius|z-index)"
    r"\s*:\s*(\d+(?:\.\d+)?)(px|rem|em|pt)?(?![\w.%-])",
    re.I,
)
# 允许的极小值：0 与 1px 发丝线，避免把 border: 1px 这类正常写法判成问题
NUMERIC_ALLOW = {"0", "1"}

HARDCODE_OK_RE = re.compile(r"hardcode-ok\s*[:：]\s*(\S.*)")
ROUTE_HINT_RE = re.compile(r"\b(?:href|to|path|url|route|id)\s*[:=]|location\.hash|useNavigate|router\.", re.I)


# --- token 结构 ----------------------------------------------------------
def _normalize_key(key: str) -> str:
    """把嵌套路径归一成连字符形式：semantic.color.bg.canvas -> semantic-color-bg-canvas"""
    return re.sub(r"[.\s/]+", "-", str(key)).strip("-").lower()


def _flatten(node: dict, prefix: str = "") -> dict:
    """扁平化 token 树。兼容 DTCG（{"$value": ...}）与裸标量叶子两种写法。"""
    out = {}
    for k, v in node.items():
        if str(k).startswith("_") or str(k).startswith("$"):
            # $schema / $description 等元数据；$value 由父级分支处理
            if not (str(k) == "$value"):
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


def _layer_names(arg: str) -> tuple:
    parts = [p.strip() for p in str(arg).split(",") if p.strip()]
    if len(parts) != 3:
        raise ValueError("--layers 需要 3 个逗号分隔的名称，例如 primitive,semantic,component")
    return tuple(parts)


def _roles_in(*trees) -> dict:
    """在若干棵树里做顶层别名匹配，判定三层是否存在。

    只看"分支键"（值为 dict 且自身不是 token 叶子），避免把名为 base 的
    颜色叶子误判成基础值层。
    """
    found = {role: [] for role in LAYER_ROLES}
    for tree in trees:
        if not isinstance(tree, dict):
            continue
        for key, val in tree.items():
            if not isinstance(val, dict) or "$value" in val:
                continue
            norm = _normalize_key(key)
            for idx, role in enumerate(LAYER_ROLES):
                if norm == _normalize_key(LAYER_NAMES[0][idx]) or norm in LAYER_ALIASES[role]:
                    found[role].append(key)
    return found


def _direct_leaf_tokens(tree) -> int:
    """统计主题分支里直接声明的 token 叶子数量（未包在层里的写法）。"""
    if not isinstance(tree, dict):
        return 0
    n = 0
    for key, val in tree.items():
        if str(key).startswith("_") or str(key).startswith("$"):
            continue
        if isinstance(val, dict):
            if "$value" in val:
                n += 1
        else:
            n += 1
    return n


def _theme_branches(data: dict) -> dict:
    for key in THEME_KEYS:
        val = data.get(key)
        if isinstance(val, dict) and val:
            branches = {k: v for k, v in val.items() if isinstance(v, dict)}
            if branches:
                return branches
    return {}


LAYER_NAMES = [("primitive", "semantic", "component")]


def _scopes(data: dict):
    """返回 [(主题名, 归一化 token 字典, 层角色表, 主题直接声明的叶子数)].

    多主题时把主题外的共享层（如 primitive）合并进每个主题分支用于查找，
    但层识别分别在共享树与主题树各自的顶层进行，以兼容
    {"primitive": ..., "themes": {"dark": {"semantic": ..., "component": ...}}}。
    """
    branches = _theme_branches(data)
    if branches:
        shared = {k: v for k, v in data.items() if k not in THEME_KEYS}
        pairs = []
        for name, tree in branches.items():
            merged = dict(shared)
            merged.update(tree)
            pairs.append((name, merged, (shared, tree), tree))
    else:
        pairs = [("default", data, (data,), None)]

    out = []
    for name, tree, role_trees, theme_tree in pairs:
        flat = _flatten(tree)
        norm = {_normalize_key(k): v for k, v in flat.items()}
        roles = _roles_in(*role_trees)
        leaves = _direct_leaf_tokens(theme_tree) if theme_tree is not None else 0
        out.append((name, norm, roles, leaves))
    return out


def _present(name: str, norm: dict) -> bool:
    target = _normalize_key(name)
    return any(k == target or k.endswith("-" + target) for k in norm)


def check_tokens(path: Path):
    """返回 (issues, notes)。"""
    issues: list[str] = []
    notes: list[str] = []

    if not path.exists():
        return [f"token 文件不存在: {path}"], notes

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        return [f"token 文件不是合法 JSON: {e}"], notes

    if not isinstance(data, dict):
        return ["token 文件顶层必须是对象（JSON object）"], notes

    scopes = _scopes(data)
    theme_names = [s[0] for s in scopes if s[0] != "default"]
    if theme_names:
        notes.append(f"检测到多主题: {', '.join(theme_names)}（必需 token 按全部主题的并集判定）")

    union: dict = {}
    for _, norm, _roles, _leaves in scopes:
        union.update(norm)

    required = (
        [("语义 token", n) for n in REQUIRED_SEMANTIC]
        + [("字号 token", n) for n in REQUIRED_FONT_SIZES]
        + [("图表色板 token", n) for n in REQUIRED_CHART_SERIES]
    )
    for label, name in required:
        if not _present(name, union):
            issues.append(f"缺少必需的{label}: {name}")

    # 每个主题单独缺项只提示，不判失败（允许主题只覆盖差异部分）
    if theme_names:
        for scope_name, norm, _roles, _leaves in scopes:
            missing = [n for _, n in required if not _present(n, norm)]
            if missing:
                notes.append(
                    f"主题 {scope_name} 未在本分支重复声明 {len(missing)} 项（若依赖其他主题继承可忽略）"
                )

    # 层结构校验
    for scope_name, _norm, roles, leaves in scopes:
        for role in LAYER_ROLES:
            if roles[role]:
                continue
            if scope_name == "default" or leaves > 3:
                issues.append(
                    f"缺少{LAYER_LABEL[role]}（当前作用域: {scope_name}）。"
                    f"可用 --layers 指定实际层名，也接受同义词 "
                    f"{'、'.join(sorted(LAYER_ALIASES[role]))}"
                )
            else:
                notes.append(
                    f"作用域 {scope_name} 未声明{LAYER_LABEL[role]}，"
                    f"按继承处理（若该主题为独立完整定义，请补上该层）"
                )

    # 引用解析
    for scope_name, norm, _roles, _leaves in scopes:
        for key, val in norm.items():
            if not isinstance(val, str):
                continue
            for ref in re.findall(r"\{([^}]+)\}", val):
                target = _normalize_key(ref)
                if not _present(target, norm) and not _present(target, union):
                    issues.append(f"token 引用未解析: {key} -> {{{ref}}}")

    return issues, notes


# --- 源码硬编码扫描 -------------------------------------------------------
def _line_issue(line: str, f: Path, lineno: int) -> list[str]:
    kinds: list[str] = []

    for m in HEX_RE.finditer(line):
        prev = line[m.start() - 1] if m.start() > 0 else ""
        # 路径/锚点/URL 片段：/detail#face、/x#face、url(/a#b)
        # 真正的颜色字面量前面不会是字母、数字或连字符
        if prev and (prev.isalnum() or prev in "_/&-"):
            continue
        # 纯锚点字面量：'#face'、"#section"（后方紧跟引号或收尾）
        if prev in "\"'`" and m.end() < len(line) and line[m.end()] in "\"'`":
            continue
        if prev in "\"'`" and m.end() == len(line):
            continue
        # CSS ID 选择器：#face { 或 #face,
        if prev == "" and re.match(r"\s*[,{]", line[m.end():]):
            continue
        kinds.append(f"hex 色值 {m.group(0)}")
        break

    if COLOR_FUNC_RE.search(line):
        kinds.append("颜色函数 rgb()/hsl() 等")
    for rex, label in ((TW_COLOR_RE, "Tailwind 调色板原子类"), (TW_KEYWORD_COLOR_RE, "Tailwind 颜色关键字类")):
        m = rex.search(line)
        if m:
            kinds.append(f"{label} {m.group(0)}")
            break

    m_tw = TW_ARBITRARY_RE.search(line)
    if m_tw and m_tw.group(1) not in NUMERIC_ALLOW:
        kinds.append(f"Tailwind 任意值尺寸 {m_tw.group(0)}")

    m = INLINE_NUM_RE.search(line)
    if m and m.group(2) not in NUMERIC_ALLOW:
        kinds.append(f"内联样式魔法数字 {m.group(1)}: {m.group(2)}")
    else:
        m2 = CSS_NUM_RE.search(line)
        if m2 and m2.group(2) not in NUMERIC_ALLOW:
            kinds.append(f"CSS 魔法数字 {m2.group(1)}: {m2.group(0).split(':', 1)[1].strip()}")

    if not kinds:
        return []
    # rgb(239 68 68) 里的分量为纯数字，不会命中 hex；这里只做同义去重
    seen = []
    for k in kinds:
        if k not in seen:
            seen.append(k)
    return [f"硬编码样式 {f}:{lineno}（{'、'.join(seen)}）: {line.strip()[:100]}"]


def scan_sources(paths) -> tuple:
    issues: list[str] = []
    notes: list[str] = []
    existing = [p for p in paths if p.exists()]
    for p in paths:
        if not p.exists():
            continue
        for f in sorted(p.rglob("*")):
            if not f.is_file() or f.suffix not in SRC_EXT:
                continue
            if "node_modules" in f.parts or "dist" in f.parts:
                continue
            if TOKENS_FILE_HINT in f.name:
                continue
            try:
                text = f.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            for i, line in enumerate(text.splitlines(), 1):
                if HARDCODE_OK_RE.search(line):
                    continue
                issues.extend(_line_issue(line, f, i))
    if not existing:
        notes.append(
            "未找到任何源码目录（已检查: " + ", ".join(str(p) for p in paths) + "），硬编码扫描未生效"
        )
    return issues, notes


# --- 主流程 --------------------------------------------------------------
def main() -> int:
    ap = argparse.ArgumentParser(description="design tokens 校验 + 硬编码样式检测")
    ap.add_argument("--tokens", default="design-system/design-tokens.json")
    ap.add_argument("--src", default="src",
                    help="源码目录，多个用逗号分隔（如 src,app）")
    ap.add_argument("--layers", default="primitive,semantic,component",
                    help="按 基础值/语义值/组件值 顺序指定实际层名")
    ap.add_argument("--max-hardcoded", type=int, default=50,
                    help="最多列出多少条硬编码样式")
    ap.add_argument("--fail-on-hardcode", action="store_true",
                    help="存在硬编码样式时以非零码退出（CI 用）")
    ap.add_argument("--json", action="store_true", help="以 JSON 输出结果")
    args = ap.parse_args()

    try:
        LAYER_NAMES[0] = _layer_names(args.layers)
    except ValueError as e:
        print(f"[FAIL] {e}")
        return 1

    src_paths = [Path(p.strip()) for p in args.src.split(",") if p.strip()]
    token_issues, token_notes = check_tokens(Path(args.tokens))
    src_issues, src_notes = scan_sources(src_paths)
    notes = token_notes + src_notes

    failed = bool(token_issues) or (args.fail_on_hardcode and bool(src_issues))

    if args.json:
        print(json.dumps({
            "ok": not failed,
            "token_file": str(args.tokens),
            "token_issues": token_issues,
            "hardcoded_issues": src_issues,
            "notes": notes,
            "hardcoded_count": len(src_issues),
            "fail_on_hardcode": args.fail_on_hardcode,
        }, ensure_ascii=False, indent=2))
        return 1 if failed else 0

    print("=" * 60)
    print("design-tokens 校验")
    print("=" * 60)
    if token_issues:
        for i in token_issues:
            print(f"  [FAIL] {i}")
    else:
        print("  [OK] token 结构、必需项、引用关系均通过")
    for n in token_notes:
        print(f"  [INFO] {n}")

    print()
    print("=" * 60)
    print("源码硬编码样式扫描")
    print("=" * 60)
    if src_issues:
        for i in src_issues[: args.max_hardcoded]:
            print(f"  [WARN] {i}")
        if len(src_issues) > args.max_hardcoded:
            print(f"  ... 另有 {len(src_issues) - args.max_hardcoded} 条")
    else:
        print("  [OK] 未发现硬编码样式")
    for n in src_notes:
        print(f"  [WARN] {n}")

    print()
    if token_issues:
        print("结论：不通过（token 存在结构性问题）")
        return 1
    if src_issues:
        if args.fail_on_hardcode:
            print(f"结论：不通过（{len(src_issues)} 处硬编码样式，--fail-on-hardcode 已开启）")
            return 1
        print(f"结论：token 通过；源码存在 {len(src_issues)} 处硬编码样式，建议整改后再交付"
              f"（加 --fail-on-hardcode 可让 CI 直接失败）")
        return 0
    print("结论：全部通过")
    return 0


if __name__ == "__main__":
    sys.exit(main())
