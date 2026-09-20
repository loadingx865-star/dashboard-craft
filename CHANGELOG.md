# Changelog

本仓库遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

## [Unreleased]

### 计划
- 补充 Vue 3 技术栈的示例工程
- 增加 CI 中的视觉回归示例工作流
- 补充国产内核浏览器的兼容性适配清单

## [2.2.0] - 2026-09-20

把三条一线开发经验纳入规范：两条部分采纳，一条完全采纳，并纠正其中一条的内部矛盾。

### 新增
- **兼容目标与降级清单**（部分采纳）：约束卡新增第 7 类“兼容目标”（Browserslist / 是否支持原生 ESM / 构建目标 / 语言 polyfill / DOM polyfill 清单 / 降级形态）。明确拒绝“客户设备老就全线写 ES5”，改为“显式声明目标 + 按需降级”：ES5 与 ES6+ 各有优劣，由目标浏览器与构建链能力决定
- **跨看板复用：看板即组合**（完全采纳）：组件与图表跨看板只有一份实现，新增看板只允许新增配置与布局，改一处全部看板生效。标注为**人工确认项**，不做机器判定
- **scale 与 px 的路线选择**（部分采纳 + 纠错）：指出“避免写死 px”与“把写死的 px 整体缩放”是互斥的两条路线，只能选一条。允许 scale 路线写设计稿 px，但 **px 必须来自 token 刻度**；补非 16:9 拼接、超宽、DPR 补偿、字号下限等代价与验证项

### 机器判定
- `check_gates.py` 阶段 0 新增判定：环境约束卡必须包含兼容目标声明（`browserslist` / 兼容目标 / 构建目标 / 无需降级 / `legacy` / `ES5`），否则阶段 0 不通过；“客户设备老”不算声明

### 模板与清单
- 验收矩阵模板补 scale 边界验证项（非设计稿比例的黑边/裁切、超宽拼接、缩放后字号下限、DPR 补偿），属人工确认项
- 环境约束卡、MASTER、组件清单同步补兼容目标、scale 边界、跨看板复用说明

### 工具链基线
- `toolchain-baseline.json` 新增“兼容与降级”分组（browserslist、caniuse-lite、core-js、@babel/preset-env、@vitejs/plugin-legacy、postcss-preset-env、autoprefixer、terser），总包数 47 → 55

### 测试
- 回归用例 33 → 36，新增：约束卡未声明兼容目标 → 阶段 0 失败；存在 `__pycache__` 时自检不误报；自检文件总数不含缓存

### 修复
- `tools/check_skill.py` 此前把 `__pycache__/` 等运行期产物也算作仓库文件：先跑一次 skill 脚本、再跑自检，会因 `.pyc` 非 UTF-8 而误报失败。现统一跳过 `.git` / `__pycache__` / 虚拟环境 / 依赖目录，文件总数与编码检查不再受本地运行痕迹影响

### 说明
- 本次不改变任何现有命令调用方式；新增判定只作用于阶段 0，旧项目补一行兼容目标即可通过

## [2.1.1] - 2026-09-18

2.1.0 发布后的对抗性复核发现若干"假通过"路径：校验器在参数错误或漏扫时仍返回成功。本次全部堵住，并补入回归用例。

### 修复
- `check_gates.py` 的 `--stage` 此前接受任意整数，`--stage 9` 因未命中任何阶段而输出"全部通过"；现限定为 0-7，非法值由 argparse 直接报错退出
- `validate_tokens.py` 的 `--src` 此前指向不存在的路径时只提示一句警告并返回成功；现区分配置错误与真实告警，路径全部不存在时判失败（默认值 `src` 缺失仍只提示，不算配置错误）
- 硬编码检测此前只抓到 CSS 里的 `#hex`，JSX 属性与内联样式里的同色值字面量漏报；现统一抓取
- 锚点豁免据此收紧：仅对 JSX 属性上下文中的 `href/to/route` 生效，`const href = "#ffffff"` 这类变量赋值不再被放过
- 阶段 5 此前只检查"未测"标记，矩阵里明确写"失败/不通过"也算通过；现此类结果直接判失败
- 阶段 0 此前约束卡只有正文、没有表格时也算通过；现要求存在表格数据行

### 测试
- 回归用例从 25 个增至 33 个，新增非法参数、配置错误、hex 漏报、锚点豁免边界、矩阵失败态、空约束卡六类反例

### 说明
- 本次只收紧判定边界，未改动任何 `--tokens/--src/--stage` 的既有调用方式；按 2.1.0 用法调用的项目行为不变

## [2.1.0] - 2026-09-18

### 新增
- `scripts/check_gates.py`：八阶段 Gate 机器判定，检查标准项目结构、约束卡空项、任务票验收标准、验收矩阵未测视口与基线登记。退出码非 0 即 Gate 未通过
- `assets/templates/MASTER.md`：设计真源模板，含缩放策略、图表规范、**目录结构登记**三节（此前 Gate 要求 MASTER 却没有模板可复制）
- `assets/examples/`：图表封装、大屏缩放、断点 Hook 三个精简形态参考
- `tests/run_tests.py` + `tests/fixtures/`：22 个正反用例，覆盖硬编码抓取、误报控制、Gate 正反判定
- `README.en.md`：英文版说明
- `compatibility` frontmatter 字段，明确 Python / 网络 / Node 前提
- CI 增加 Windows 与 Python 3.9/3.11/3.13 矩阵、回归测试、官方 `skills-ref validate`

### 变更
- `validate_tokens.py` 重写：支持扁平命名、DTCG 分组嵌套、多主题 `themes{}` 三种 token 组织；层名可用 `--layers` 配置并内置同义词表
- 硬编码检测扩展：Tailwind 调色板原子类与颜色关键字类、任意值尺寸、`rgb()/hsl()/oklch()`、内联样式与 CSS 魔法数字；默认只告警，`--fail-on-hardcode` 才失败
- `refresh_toolchain.py`：基线默认路径改为脚本同级目录，不再依赖当前工作目录；新增 `--offline` 读本地缓存；基线缺失时明确报错，不再把全部依赖误标为"新包"
- 容差按视口分档：4K 视口改用 `maxDiffPixels` 绝对值，默认比例阈值从 0.01 收紧到 0.002；视口矩阵新增 `dpr: 2` 的 4K HiDPI 档
- `SKILL.md` description 改为中英混排，覆盖 dashboard / KPI screen / control room / large display 等检索词，并支持审计已有看板
- `tools/check_skill.py`：新增官方 frontmatter 字段白名单、description 长度、SKILL.md 行数/token 预算、`assets/examples/` 登记检查
- 方法论文档补充 Gate 机器判定、多主题 token、容差分档与 DPR、离线模式

### 修复
- 阶段 3/4 的 Gate 此前只输出 INFO、无论结构如何都返回通过，属于"静默放行"；现改为找不到骨架/组件/图表入口即失败
- 非标准目录约定改为按类别校验：MASTER「目录结构」小节登记的路径必须语义匹配且真实存在，登记骨架目录不能顺带放行图表封装目录
- 阶段 6 此前只按文件名判断报告是否存在；现要求报告正文覆盖性能、可访问性、冒烟、视觉回归四类结论
- 回归测试补入"合规项目必须通过"的正向夹具，避免把校验器修成一律报错

### 说明
- 1.x 到 2.0 是同版本内的重构与改名（`dashboard-engineering` → `dashboard-craft`），无迁移成本；2.1 起对外接口以脚本参数为准，向后兼容 2.0 的调用方式

## [2.0.0] - 2026-09-18

### 变更
- **重命名为 `dashboard-craft`**（原 `dashboard-engineering`），更简短易记并突出功能性
- 仓库重构为标准 Skill 分发结构，`skills/dashboard-craft/` 为可安装本体
- 新增 `docs/methodology.md`（面向人的完整方法论）
- 新增 `tools/check_skill.py` 仓库自检脚本
- 新增 `LICENSE`、`CHANGELOG.md`、`CONTRIBUTING.md`
- SKILL.md 补充 `license` 与 `metadata.author`

### 修复
- 修复 `validate_tokens.py` 无法解析 DTCG 裸标量叶子（primitive 层裸字符串）导致 token 引用误报的问题
- 修复脚本在 Windows 控制台的中文输出编码问题
- 修复 `refresh_toolchain.py` 并发过高触发 npm registry 限流的问题，并避免把拉取失败项写入基线
- 统一配置文件的名称与作用域描述

## [1.0.0] - 2026-09-18

### 新增
- 首个版本：8 阶段流程 + 5 条铁律 + 各阶段 Gate
- `references/01~09` 阶段细则，含工具链持续更新机制
- 模板：环境约束卡、验收矩阵、Playwright 视口配置、design tokens 示例、组件清单
- 脚本：`validate_tokens.py`（token 校验 + 硬编码色值抽查）、`refresh_toolchain.py`（版本实时拉取）
