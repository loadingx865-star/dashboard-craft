# dashboard-craft

> 数据看板、运营大屏、工业控制台的前端开发规范，打包成一个可安装的 Agent Skill。

**简体中文** | [English](README.en.md)

**许可** MIT（[LICENSE](LICENSE)） · **格式** Agent Skill（`SKILL.md`、`scripts/`、`references/`、`assets/`） · **安装** `npx skills add loadingx865-star/dashboard-craft`

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
| 4 | 一个概念一处实现 | 同类组件与图表只有一个入口，不另起一套；新增看板只允许新增配置与布局，图表复用同一份实现（看板即组合） |
| 5 | 偏离必须登记 | 对设计真源的偏离写进页面级覆盖文件，并说明理由 |

### 八阶段

```
0 约束锁定 → 1 设计真源 → 2 规格拆票 → 3 骨架先行
→ 4 组件与图表 → 5 适配验证 → 6 质量门禁 → 7 交付存档
```

| 阶段 | 产出 | Gate |
|---|---|---|
| 0 约束锁定 | 环境约束卡 | 分辨率、浏览器、缩放、网络、数据频率均已明确，并声明 Browserslist 兼容目标（机器判定） |
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
# 装到自动检测到的 agent（检测到谁装给谁）
npx skills add loadingx865-star/dashboard-craft

# 指定 agent 安装
npx skills add loadingx865-star/dashboard-craft -a codex

# 装到指定的多个 agent
npx skills add loadingx865-star/dashboard-craft -a claude-code -a cursor

# 确认安装结果
npx skills list
```

Windows 上如果符号链接受限，加 `--copy`。

安装位置由 CLI 决定：全局安装在 `~/.agents/skills/dashboard-craft`，项目内安装在 `./.agents/skills/dashboard-craft`。手动安装也可行，把仓库里的 `skills/dashboard-craft/` 整目录复制到 agent 的技能目录即可。

### 适配的 agent

本 skill 是标准 Agent Skill（`SKILL.md` + 可选 `scripts/`、`references/`、`assets/`），凡支持该格式的 agent 都能用，不绑定某一家。`npx skills` v1.7 当前支持 79 个 agent，常用的有：

| 类别 | agent |
|---|---|
| 编码助手 | codex、claude-code、cursor、windsurf、gemini-cli、github-copilot、opencode、cline、roo、continue、amp、aider-desk |
| 国内团队/中文场景常用 | qwen-code、kimi-code-cli、trae、trae-cn、lingma、codebuddy、qoder、qoder-cn、iflow-cli、codearts-agent、kiro-cli |
| 终端型 | crush、goose、droid、devin、openhands、warp、zed |
| 兜底 | universal（写到通用 `.agents/skills`，供未单独适配的 agent 读取） |

> 想知道自己机器上有哪些可用，运行 `npx skills add loadingx865-star/dashboard-craft`（不加 `-y`），CLI 会列出检测到的 agent 让你选；装到全部 agent 用 `--all`。完整适配列表见 [skills.sh](https://skills.sh)。工具生态变化快，本文只保证"标准格式 + 主流 agent 可用"。

### 适配前提

Skill 本体不依赖任何运行时，但**脚本**有自己的环境要求，agent 执行到对应步骤时才会用到：

| 能力 | 前提 | 缺失时的行为 |
|---|---|---|
| token 校验 / Gate 判定 | Python 3.9+（仅标准库） | 无法机器判定，只能人工检查 |
| 工具链版本比对 | 能访问 registry.npmjs.org，或已有本地缓存 | 用 `--offline` 读缓存；都没有就跳过，不阻塞开发 |
| 多分辨率截图 | Node.js + `@playwright/test` | 阶段 5 无法自动验证 |
| 界面元数据（`agents/openai.yaml`） | 仅 Codex 读取 | 其他 agent 忽略该文件，不影响使用 |

内网、离线、无 Node 的环境也能用本 skill，只是对应阶段的自动化能力降级，规则本身仍然生效。

## 快速开始

```bash
SKILL=~/.agents/skills/dashboard-craft

# 1. 校验设计 tokens，并检测源码中的硬编码样式
python $SKILL/scripts/validate_tokens.py \
  --tokens design-system/design-tokens.json --src src,app

# 2. 校验各阶段 Gate（标准项目结构）
python $SKILL/scripts/check_gates.py --project .

# 3. 拉取工具链最新版本，与基线对比
python $SKILL/scripts/refresh_toolchain.py            # 联网
python $SKILL/scripts/refresh_toolchain.py --offline  # 内网，只读本地缓存
```

三个脚本的参数：

| 脚本 | 关键参数 |
|---|---|
| `validate_tokens.py` | `--tokens` 指定 token 文件；`--src a,b` 指定多个源码目录/文件（路径不存在会判失败）；`--layers base,alias,config` 自定义层名；`--fail-on-hardcode` 硬编码即失败（CI 用）；`--json` 机读输出 |
| `check_gates.py` | `--project .` 指定目标项目；`--stage 0` 只查某阶段（可重复，仅接受 0-7）；`--allow-empty-card` 只查结构不卡填写；`--json` 机读输出 |
| `refresh_toolchain.py` | `--baseline` 指定基线；`--update-baseline` 确认后写回基线；`--offline` 离线 |

Windows 下把 `~/` 换成 `%USERPROFILE%\`，或用 PowerShell 的 `$env:USERPROFILE`。

开工前的三件事：

1. 复制 `assets/templates/constraints-card.md`，填完再动手。
2. 以 `assets/templates/MASTER.md` 与 `assets/templates/design-tokens.example.json` 为起点建 `design-system/`，并选定大屏缩放策略。
3. 用 `assets/templates/playwright.viewports.ts` 配好视口矩阵。

完整方法论（面向人读）见 [docs/methodology.md](docs/methodology.md)。

## 环境要求

| 项 | 要求 |
|---|---|
| Python | 3.9 及以上；`scripts/` 下三个脚本只用标准库，无需 pip 安装 |
| 网络 | `refresh_toolchain.py` 需要访问 registry.npmjs.org；内网用 `--offline` 读本地缓存，或直接跳过 |
| Node | 仅阶段 5 的视口矩阵模板需要，配合 `@playwright/test` 使用 |
| 目标框架 | React 或 Vue，不绑定具体版本；其他框架可借鉴流程但不保证模板直接可用 |

## 仓库结构

```
dashboard-craft/
├── skills/dashboard-craft/              可安装的 Skill 本体
│   ├── SKILL.md                          入口：铁律 + 八阶段门禁
│   ├── agents/openai.yaml                界面元数据（仅 Codex 读取）
│   ├── references/01~09                  各阶段细则
│   ├── assets/templates/                 可直接复制的模板（含 MASTER.md、约束卡、视口矩阵）
│   ├── assets/examples/                  图表封装/缩放/断点 Hook 形态参考
│   ├── scripts/validate_tokens.py        token 校验 + 硬编码检测
│   ├── scripts/check_gates.py            各阶段 Gate 机器判定
│   ├── scripts/refresh_toolchain.py      工具链版本比对
│   └── toolchain-baseline.json           55 个依赖包的版本基线
├── docs/methodology.md                   面向人的完整方法论
├── README.md / README.en.md              中 / 英文说明（本文件）
├── CHANGELOG.md
├── CONTRIBUTING.md
├── LICENSE
├── .gitignore                            忽略依赖目录与运行期缓存
└── .gitattributes                        统一换行符为 LF，避免跨平台行尾漂移
```

## 设计原则

**记录角色，不记录版本。** 前端工具链升级频繁，写死版本的文档很快过期。文档里只写"图表库首选 ECharts"这类角色定位，具体版本放在 `toolchain-baseline.json`，由脚本拉取最新版本后比对。

**本 Skill 只管编排。** `frontend-design`、`shadcn`、`vercel-react-best-practices`、`playwright` 这类技能增强的是单点能力，dashboard-craft 决定什么时候用哪个、产出要满足什么标准、不达标怎么处理。

**Gate 由脚本兜底，不靠自觉。** 每个阶段的"通过"都有对应的命令与退出码；CI 里硬编码检测以 `--fail-on-hardcode` 强制失败。

## 适用范围

适用：数据看板、运营大屏、工业控制台、监控大屏。

不适用：营销官网、作品集这类表达型页面，相关需求用 [frontend-design](https://skills.sh/anthropics/skills/frontend-design)。

## 参与贡献

见 [CONTRIBUTING.md](CONTRIBUTING.md)。版本变更记录见 [CHANGELOG.md](CHANGELOG.md)。

## 许可

[MIT](LICENSE)
