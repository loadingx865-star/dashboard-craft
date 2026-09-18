# 工具链选型与持续更新机制

> 本文档不写死版本。技术栈升级快，写死版本必然过期。正确做法是：**记录角色与选型标准 + 用脚本实时拉取最新版本 + 定期复核**。

## 一、更新机制（三件事）

### 1. 实时拉取

运行 `scripts/refresh_toolchain.py`，它从 npm registry 拉取本文件登记的所有包的最新版本，并与 `toolchain-baseline.json` 对比，输出差异报告。

```bash
python scripts/refresh_toolchain.py
```

### 2. 季度复核

每季度（或在大版本发布时）执行一次复核，逐条判断：

| 判断 | 动作 |
|---|---|
| 有新稳定版 | 评估是否升级 |
| 有更好的替代品 | 记录，不在冲刺期切换 |
| 有废弃/停止维护 | 制定迁移计划 |
| 有安全公告 | 优先处理 |

### 3. 升级原则

- **先小步升级**：逐个大版本升，不要一次跨多个大版本。
- **升级必回归**：升级后必须跑阶段 5-6 的完整门禁。
- **禁止冲刺期跃迁**：交付前不做大版本迁移。
- **锁文件必须提交**：保证构建可复现。

## 二、Skill 生态现状（2026-09 调研）

以下为当前主流、可安装的 Agent Skill（按 skills.sh 安装量排序）。这些是**能力增强组件**，不是流程规范——它们增强单点能力，本 Skill 负责把它们编排进有门禁的流程。

### 设计方向

| Skill | 来源 | 安装量 | 用途 | 边界 |
|---|---|---|---|---|
| frontend-design | anthropics/skills | 约 898K | 有辨识度的视觉方向、排版、反模板感 | **主场是 landing/portfolio**，看板只能借鉴原则 |
| design-taste-frontend | leonxlnx/taste-skill | 约 491K | 反"AI 模板感"、预检清单 | 明确声明"不适用于看板、数据表格" |
| design-tokens | julianoczkowski/designer-skills | 约 5.4K | token 设计与组织 | 辅助 |

### 设计系统与组件

| Skill | 来源 | 安装量 | 用途 |
|---|---|---|---|
| shadcn | shadcn/ui | 约 272K | shadcn/ui 组件生成与规范 |
| tailwind-design-system | wshobson/agents | 约 65K | Tailwind 设计系统搭建 |
| extract-design-system | arvindrk | 约 129K | 从现有站点提取 token（用于统一既有项目） |
| responsive-design | wshobson/agents | 约 19K | 响应式设计 |
| design-system-patterns | wshobson/agents | — | 设计系统结构模式 |

### 性能

| Skill | 来源 | 安装量 | 用途 |
|---|---|---|---|
| vercel-react-best-practices | vercel-labs/agent-skills | — | React/Next 70 条性能规则（消除瀑布、包体积、重渲染等 8 类） |
| core-web-vitals | addyosmani/web-quality-skills | 约 26K | 核心网页指标优化 |
| performance-optimization | addyosmani/agent-skills | 约 40K | 通用性能优化 |

### 测试

| Skill | 来源 | 安装量 | 用途 |
|---|---|---|---|
| webapp-testing | anthropics/skills | 约 159K | Playwright 驱动的应用测试 |
| playwright-cli | microsoft/playwright-cli | 约 158K | 浏览器自动化 CLI |
| playwright-best-practices | currents-dev | 约 84K | Playwright 最佳实践 |

### 可访问性

| Skill | 来源 | 安装量 | 用途 |
|---|---|---|---|
| accessibility | addyosmani/web-quality-skills | 约 54K | a11y 审查 |
| fixing-accessibility | ibelick/ui-skills | 约 19K | 修复可访问性问题 |

### 工程流程

| Skill | 来源 | 安装量 | 用途 |
|---|---|---|---|
| frontend-ui-engineering | addyosmani/agent-skills | 约 40K | 前端 UI 工程化 |
| feature-sliced-design | feature-sliced/skills | 约 19K | FSD 架构分层 |
| spec-driven-development | addyosmani/agent-skills | — | 规格驱动开发 |
| planning-and-task-breakdown | addyosmani/agent-skills | — | 任务拆解 |

**安装方式**：
```bash
npx skills add <owner/repo@skill> --all
npx skills update          # 更新已装技能
```

**重要提醒**：Skill 的热度会变化，安装前用 `npx skills find <关键词>` 复核当前排名与安装量，不要迷信本文档快照。

## 三、技术栈选型（核心）

以下为看板类前端当前的主流选型。**推荐版本以脚本实时拉取为准**，此处只给角色定位。

### 基础框架

| 角色 | 首选 | 备选 | 选型说明 |
|---|---|---|---|
| 框架 | React + TypeScript | Vue 3 + TypeScript | 看板类两者皆可；以团队熟悉度为准 |
| 构建 | Vite | Next.js（需要 SSR/全栈时） | 纯看板通常不需要 SSR，Vite 更轻更快 |

### 样式与组件

| 角色 | 首选 | 备选 |
|---|---|---|
| CSS 方案 | Tailwind CSS | UnoCSS / CSS Modules |
| 组件库 | shadcn/ui（React） | Ant Design / Naive UI（Vue）/ Element Plus |
| 图标 | Lucide | Heroicons |

### 图表

| 角色 | 首选 | 备选 |
|---|---|---|
| 图表库 | Apache ECharts | Recharts（简单场景）/ D3（高度定制） |

**大屏推荐 ECharts**：canvas 渲染、大数据量性能好、主题系统完善、支持 SSR 与导出。

### 数据与状态

| 角色 | 首选 | 备选 |
|---|---|---|
| 服务端数据 | TanStack Query | SWR |
| 客户端状态 | Zustand | Redux Toolkit / Pinia（Vue） |
| 校验 | Zod | Yup |
| 大数据表格 | TanStack Table + TanStack Virtual | AG Grid |

### 测试与质量

| 角色 | 首选 | 备选 |
|---|---|---|
| 单元/组件测试 | Vitest | Jest |
| 端到端 / 视觉回归 | Playwright | Cypress（E2E）；pixelmatch（自定义比对） |
| 可访问性 | axe-core + @axe-core/playwright | — |
| 性能预算 | Lighthouse CI | size-limit（包体积） |

### 工程规范

| 角色 | 首选 |
|---|---|
| 类型 | TypeScript |
| Lint | ESLint（flat config） |
| 格式化 | Prettier |
| 提交钩子 | husky + lint-staged |
| 提交规范 | Commitlint |

## 四、替代方案评估清单

引入新工具前，逐条回答：

- [ ] 它解决了现有工具解决不了的什么问题？
- [ ] 维护活跃度如何（最近发布、issue 响应）？
- [ ] 生态与社区规模是否足够？
- [ ] 迁移成本多大？
- [ ] 是否与现有工具职责重叠？
- [ ] 团队是否需要重新学习？

## 五、版本登记

维护 `toolchain-baseline.json`，记录各包当前使用的版本。升级后更新该文件并记录原因。脚本 `refresh_toolchain.py` 会用它做对比基准。

## 六、本 Skill 自身的更新

本 Skill 也有生命周期：

- 版本号写在 SKILL.md 的 `metadata.version`。
- 每次实质更新，递增版本并记录变更。
- 若某阶段的方法被证明无效，**删掉它**，不要积累过时规则。
- 收集真实使用中的失败案例，针对性修订，而不是堆砌通用规则。
