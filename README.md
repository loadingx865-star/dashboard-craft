# dashboard-craft

> 数据看板、运营大屏、工业控制台的前端开发规范，打包成一个可安装的 Agent Skill。

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Agent Skill](https://img.shields.io/badge/Agent%20Skill-dashboard--craft-6E56CF)](https://skills.sh)

## 它解决什么

用 AI 做看板，反复出现的返工大致三类：

| 现象 | 通常的原因 |
|---|---|
| 本机正常，交付到工厂电视或控制室大屏后布局错乱、字太小、图表发虚 | 开工前没确认交付终端的分辨率、系统缩放和浏览器 |
| 二期看板的配色、字号、图表样式跟一期对不上 | 设计决策没有固定来源，每期重新定一遍 |
| 功能都能跑，组件却各写各的，越做越难改 | 同类组件和图表没有统一入口 |

这三件事跟模型强弱关系不大，多数出在流程缺约束。本 Skill 用 8 个阶段把约束补上：每个阶段规定产出物和通过条件（Gate），Gate 不过就不进入下一阶段。

## 核心机制

### 五条铁律

| # | 铁律 | 含义 |
|---|---|---|
| 1 | 无约束不开发 | 环境约束卡没填完，不写 UI 代码 |
| 2 | 无真源不写样式 | 颜色、字号、间距、图表配色取自 design tokens |
| 3 | 无矩阵不交付 | 跑完"分辨率 × 浏览器"矩阵，截图基线入库 |
| 4 | 一个概念一处实现 | 同类组件与图表只有一个入口，不另起一套 |
| 5 | 偏离必须登记 | 对设计真源的偏离写进页面级覆盖文件，并说明理由 |

### 八阶段

```
0 约束锁定 → 1 设计真源 → 2 规格拆票 → 3 骨架先行
→ 4 组件与图表 → 5 适配验证 → 6 质量门禁 → 7 交付存档
```

| 阶段 | 产出 | Gate |
|---|---|---|
| 0 约束锁定 | 环境约束卡 | 分辨率、浏览器、缩放、网络、数据频率均已明确 |
| 1 设计真源 | tokens + MASTER | token 校验通过，缩放策略成文 |
| 2 规格拆票 | 纵向切片任务 | 每张票有可验证的验收标准 |
| 3 骨架先行 | Layout Shell | 全部目标分辨率下不破版 |
| 4 组件与图表 | 受限组件层 + 图表封装 | 无页面级临时样式 |
| 5 适配验证 | 截图基线 | 矩阵跑通，无溢出与裁切 |
| 6 质量门禁 | 测试报告 | 性能、a11y、冒烟、视觉 diff 全绿 |
| 7 交付存档 | 交付包 | 基线入库，回归资产可复跑 |

各阶段的执行细则在 `skills/dashboard-craft/references/01~09`。

## 安装

```bash
# 装到自动检测到的 agent
npx skills add loadingx865-star/dashboard-craft

# 指定 agent 安装
npx skills add loadingx865-star/dashboard-craft -a codex

# 确认安装结果
npx skills list
```

`-a` 支持 codex、claude-code、cursor、windsurf、gemini-cli、opencode、roo、trae、qwen-code、kimi-code-cli 等 70 余个 agent，完整列表可用 `npx skills add loadingx865-star/dashboard-craft -a x` 触发查看。Windows 上如果符号链接受限，加 `--copy`。

安装位置由 CLI 决定：全局安装在 `~/.agents/skills/dashboard-craft`，项目内安装在 `./.agents/skills/dashboard-craft`。手动安装也可行，把仓库里的 `skills/dashboard-craft/` 整目录复制到 agent 的技能目录即可。

## 快速开始

```bash
# 1. 校验设计 tokens，并抽查源码中的硬编码色值
python ~/.agents/skills/dashboard-craft/scripts/validate_tokens.py \
  --tokens design-system/design-tokens.json --src src

# 2. 拉取工具链最新版本，与基线对比
python ~/.agents/skills/dashboard-craft/scripts/refresh_toolchain.py \
  --baseline ~/.agents/skills/dashboard-craft/toolchain-baseline.json
```

两条命令的路径按实际安装位置调整，Windows 下把 `~/` 换成 `%USERPROFILE%\`。

开工前的三件事：

1. 复制 `assets/templates/constraints-card.md`，填完再动手。
2. 以 `assets/templates/design-tokens.example.json` 为起点建 `design-system/`，并选定大屏缩放策略。
3. 用 `assets/templates/playwright.viewports.ts` 配好视口矩阵。

完整方法论（面向人读，约 300 行）见 [docs/methodology.md](docs/methodology.md)。

## 环境要求

| 项 | 要求 |
|---|---|
| Python | 3.9 及以上，`scripts/` 下的两个脚本只用到标准库 |
| 网络 | `refresh_toolchain.py` 需要访问 registry.npmjs.org，内网环境可跳过这一步 |
| Node | 仅视口矩阵模板需要，配合 Playwright 使用 |

## 仓库结构

```
dashboard-craft/
├── docs/methodology.md                  完整方法论
├── skills/dashboard-craft/              可安装的 Skill 本体
│   ├── SKILL.md                          入口：铁律 + 八阶段门禁
│   ├── agents/openai.yaml                界面元数据
│   ├── references/01~09                  各阶段细则
│   ├── assets/templates/                 可直接复制的模板
│   ├── scripts/                          校验与更新脚本
│   └── toolchain-baseline.json           47 个依赖包的版本基线
├── tools/check_skill.py                 仓库自检脚本
├── CHANGELOG.md
└── CONTRIBUTING.md
```

## 设计原则

**记录角色，不记录版本。** 前端工具链升级频繁，写死版本的文档很快过期。文档里只写"图表库首选 ECharts"这类角色定位，具体版本放在 `toolchain-baseline.json`，由脚本拉取最新版本后比对。

**本 Skill 只管编排。** `frontend-design`、`shadcn`、`vercel-react-best-practices`、`playwright` 这类技能增强的是单点能力，dashboard-craft 决定什么时候用哪个、产出要满足什么标准、不达标怎么处理。

## 适用范围

适用：数据看板、运营大屏、工业控制台、监控大屏。

不适用：营销官网、作品集这类表达型页面，相关需求用 [frontend-design](https://skills.sh/anthropics/skills/frontend-design)。

## 参与贡献

见 [CONTRIBUTING.md](CONTRIBUTING.md)。版本变更记录见 [CHANGELOG.md](CHANGELOG.md)。

## 许可

[MIT](LICENSE)
