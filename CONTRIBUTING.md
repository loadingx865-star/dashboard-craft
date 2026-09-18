# Contributing

感谢你有兴趣改进 `dashboard-craft`。

## 提交前自检

```bash
python tools/check_skill.py    # 仓库结构与 SKILL.md 体积预算
python tests/run_tests.py      # 校验器正反用例
```

`check_skill.py` 校验：frontmatter 字段合法性（官方白名单）、名称与目录一致、description 长度、SKILL.md 行数/token 预算、`references/` 编号连续性、文档内相对路径、`assets/examples/` 登记、文件编码、脚本语法。

`run_tests.py` 是防"假绿灯"的关键：它用正反用例证明校验器真的能抓到硬编码、也真的不误伤 `var()`、token 类、1px 发丝线这类合法写法。**改了 `scripts/` 下的任何脚本，都必须同时补/改对应用例。**

改了 SKILL.md frontmatter 后，建议再跑一次官方规范校验（需要 `pip install skills-ref==0.1.1`）：

```bash
python -m skills_ref.cli validate ./skills/dashboard-craft
```

CI（`.github/workflows/skill-check.yml`）会在 Ubuntu 与 Windows 上跑 Python 3.9/3.11/3.13 三档矩阵，外加 `skills-ref validate`，本地过不代表 CI 一定过。

## 改进原则

本 Skill 的目标是**改变 AI 的决策**，而不是堆砌通用建议。提交前请自问：

- 这条规则是否**改变某个具体决策**？如果只是"要写好代码"这类通识，不要加。
- 是否针对**真实发生过的失败案例**？请说明案例来源。
- 是否与现有规则**冲突或重复**？冲突时优先修订而非追加。

## 修改内容的约定

| 改动位置 | 要求 |
|---|---|
| `SKILL.md` | 保持简洁，细则放 `references/`；改动实质内容须递增 `metadata.version`。行数不超 500、token 估算不超 5000（`tools/check_skill.py` 会拦） |
| `tests/` | 新增或修改校验规则时，必须补正反用例；只改脚本不补用例的 PR 不予合并 |
| `references/*.md` | 保持文件名编号顺序；新增须在 SKILL.md 索引中登记 |
| `assets/templates/` | 模板要能直接复制使用，不留占位符错误 |
| `scripts/` | 必须实际运行验证，不能只做静态检查；只用标准库，保持 Python 3.9 兼容 |
| 版本号 | 遵循语义化版本；破坏性改动升 major |

## 新增 skill 相关规则时的边界

- **不要写死工具版本**。版本属于 `toolchain-baseline.json`，由脚本维护。
- **不要引入与看板场景无关的规则**。本 Skill 限定在数据看板 / 大屏 / 控制台；表达型页面（官网、作品集）不适用。
- **不要复制其他 skill 的完整内容**。引用即可，避免规则打架。
- **不要把单点能力塞进来**。前端设计、组件生成、性能优化由对应 skill 负责；本 skill 只做编排、约束与门禁。
- **新增 frontmatter 字段前先查官方 spec**。顶层字段只允许 `allowed-tools`、`compatibility`、`description`、`license`、`metadata`、`name`，其他会被官方校验器拒绝。

## 提交流程

1. Fork 并创建分支：`git checkout -b feat/your-change`
2. 完成改动并跑通自检
3. 提交（建议遵循 Conventional Commits，如 `feat:` / `fix:` / `docs:`）；改动交付行为时同步更新 `CHANGELOG.md`
4. 发起 Pull Request，说明**改动动机**与**验证方式**

## 报告问题

提 Issue 时请附上：使用场景（终端/分辨率/浏览器）、期望行为、实际行为、复现步骤。若能附截图更佳。
