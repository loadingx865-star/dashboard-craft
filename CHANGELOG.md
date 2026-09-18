# Changelog

本仓库遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

## [Unreleased]

### 计划
- 补充 Vue 3 技术栈的示例工程
- 增加 CI 中的视觉回归示例工作流
- 补充国产内核浏览器的兼容性适配清单

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
