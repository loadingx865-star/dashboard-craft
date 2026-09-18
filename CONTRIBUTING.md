# Contributing

感谢你有兴趣改进 `dashboard-craft`。

## 提交前自检

```bash
python tools/check_skill.py
```

该脚本会校验：frontmatter 完整性、`references/` 编号连续性、文档内相对路径是否存在、文件编码、以及脚本语法。

## 改进原则

本 Skill 的目标是**改变 AI 的决策**，而不是堆砌通用建议。提交前请自问：

- 这条规则是否**改变某个具体决策**？如果只是"要写好代码"这类通识，不要加。
- 是否针对**真实发生过的失败案例**？请说明案例来源。
- 是否与现有规则**冲突或重复**？冲突时优先修订而非追加。

## 修改内容的约定

| 改动位置 | 要求 |
|---|---|
| `SKILL.md` | 保持简洁，细则放 `references/`；改动实质内容须递增 `metadata.version` |
| `references/*.md` | 保持文件名编号顺序；新增须在 SKILL.md 索引中登记 |
| `assets/templates/` | 模板要能直接复制使用，不留占位符错误 |
| `scripts/` | 必须实际运行验证，不能只做静态检查 |
| 版本号 | 遵循语义化版本；破坏性改动升 major |

## 新增 skill 相关规则时的边界

- **不要写死工具版本**。版本属于 `toolchain-baseline.json`，由脚本维护。
- **不要引入与看板场景无关的规则**。本 Skill 限定在数据看板 / 大屏 / 控制台；表达型页面（官网、作品集）不适用。
- **不要复制其他 skill 的完整内容**。引用即可，避免规则打架。

## 提交流程

1. Fork 并创建分支：`git checkout -b feat/your-change`
2. 完成改动并跑通自检
3. 提交（建议遵循 Conventional Commits，如 `feat:` / `fix:` / `docs:`）
4. 发起 Pull Request，说明**改动动机**与**验证方式**

## 报告问题

提 Issue 时请附上：使用场景（终端/分辨率/浏览器）、期望行为、实际行为、复现步骤。若能附截图更佳。
