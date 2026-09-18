# dashboard-craft

> 数据看板 / 运营大屏 / 工业控制台的**前端工程化开发规范**，打包成一个可直接安装的 Agent Skill。

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Skill](https://img.shields.io/badge/Agent%20Skill-dashboard--craft-6E56CF)](https://skills.sh)

用 AI 辅助开发看板时，你是不是反复遇到这些事？

- 在自己电脑上好好的，交付到**工厂电视 / 控制室大屏**就布局错乱、字太小、图表糊。
- 第二期看板和第一期**风格对不上** —— 配色、字号、图表样式都不一样。
- 功能能跑，但组件各写各的，**越开发越乱**，像拼出来的。

这些问题的根因不是 AI 不够强，而是**缺少约束层与门禁层**。`dashboard-craft` 用 8 个阶段把它补上：每个阶段都有明确的**产出物**和**通过条件（Gate）**，Gate 不过不进入下一阶段。

---

## 核心机制

### 五条铁律

| # | 铁律 | 拦截的问题 |
|---|---|---|
| 1 | **无约束不开发** | 环境约束卡未填完，不得写 UI 代码 |
| 2 | **无真源不写样式** | 颜色/字号/间距必须来自 design tokens |
| 3 | **无矩阵不交付** | 必须跑完"分辨率 × 浏览器"验证矩阵 |
| 4 | **一个概念一处实现** | 同类组件与图表只有一个入口 |
| 5 | **偏离必须登记** | 任何偏离都要写进页面级覆盖文件 |

### 八阶段流程

```
0 约束锁定 → 1 设计真源 → 2 规格拆票 → 3 骨架先行
                                              ↓
7 交付存档 ← 6 质量门禁 ← 5 适配验证 ← 4 组件与图表
```

| 阶段 | 产出 | Gate |
|---|---|---|
| 0 约束锁定 | 环境约束卡 | 分辨率/浏览器/缩放/网络/数据频率明确 |
| 1 设计真源 | tokens + MASTER | token 校验通过；缩放策略成文 |
| 2 规格拆票 | 纵向切片任务 | 每票有可验证验收标准 |
| 3 骨架先行 | Layout Shell | 全分辨率下不破版 |
| 4 组件图表 | 组件层 + 图表封装 | 无页面级临时样式 |
| 5 适配验证 | 截图基线 | 矩阵跑通，无溢出/裁切 |
| 6 质量门禁 | 测试报告 | 性能/a11y/冒烟/diff 全绿 |
| 7 交付存档 | 交付包 | 基线入库，可复跑 |

---

## 安装

```bash
# 从 GitHub 安装（推荐）
npx skills add loadingx865-star/dashboard-craft

# 安装后确认
npx skills list
```

手动安装（复制到 Codex skills 目录）：

```bash
git clone https://github.com/loadingx865-star/dashboard-craft.git
cp -r dashboard-craft/skills/dashboard-craft ~/.codex/skills/
```

---

## 快速开始

```bash
# 1. 校验设计 tokens（含硬编码色值抽查）
python skills/dashboard-craft/scripts/validate_tokens.py \
  --tokens design-system/design-tokens.json --src src

# 2. 拉取工具链最新版本并与基线对比
python skills/dashboard-craft/scripts/refresh_toolchain.py
```

起步三件事：

1. 复制 `assets/templates/constraints-card.md`，填完**再动手**。
2. 以 `assets/templates/design-tokens.example.json` 为起点建 `design-system/`，选定**大屏缩放策略**。
3. 用 `assets/templates/playwright.viewports.ts` 配好视口矩阵。

完整方法论见 [docs/methodology.md](docs/methodology.md)。

---

## 仓库结构

```
dashboard-craft/
├── README.md
├── LICENSE
├── CHANGELOG.md
├── CONTRIBUTING.md
├── docs/
│   └── methodology.md                    完整方法论（面向人）
├── skills/dashboard-craft/               ★ 可安装的 Skill 本体
│   ├── SKILL.md                          入口：铁律 + 八阶段门禁
│   ├── agents/openai.yaml               界面元数据
│   ├── references/01~09                  各阶段细则
│   ├── assets/templates/                 可直接复制的模板
│   ├── scripts/                          校验与更新脚本
│   └── toolchain-baseline.json           版本基线
└── tools/
    └── check_skill.py                    仓库自检脚本
```

---

## 设计原则

**记录角色，不记录版本。** 技术栈升级很快，写死版本的文档必然过期。所以本仓库的文档只写"图表库首选 ECharts"这类角色定位，版本放在 `toolchain-baseline.json`，由脚本实时拉取比对。

**Skill 是编排层，不是又一个工具。** 市面上的 `frontend-design`、`shadcn`、`vercel-react-best-practices`、`playwright` 都是单点能力增强；`dashboard-craft` 负责决定"什么时候用哪个、产出必须满足什么标准、不达标怎么办"。

---

## 适用范围

✅ 数据看板、运营大屏、工业控制台、监控大屏

❌ 营销官网、作品集等表达型页面（那类用 [`frontend-design`](https://skills.sh/anthropics/skills/frontend-design)）

---

## 许可

[MIT](LICENSE)
