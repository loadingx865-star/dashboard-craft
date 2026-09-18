# 参考实现（形态参考，不是复制目标）

本目录的 `.example` 文件展示**正确形态**，用来消除"规范说到了，但 AI 现场发挥"的空白。

**它们不是真源。** 项目的真源始终是 `design-system/design-tokens.json` 与 `design-system/MASTER.md`。
落地时按项目替换类型、目录与主题来源，不要把这里的字面值当成设计决策。

| 文件 | 解决什么 |
|---|---|
| `chart-wrapper.tsx.example` | 图表唯一入口：实例生命周期、DPI、ResizeObserver、空/加载/错误态 |
| `screen-scale.ts.example` | 三种大屏缩放策略的形态（等比 / 断点 / 混合），阶段 1 只选一种 |
| `use-breakpoint.ts.example` | 看板断点档位与 JS 兜底 Hook，断点来自真实终端 |

共同约束：

- 所有颜色与尺寸取自 token，不出现字面色值与魔法数字。
- 所有 `ResizeObserver`/`resize`/定时器都在卸载时清理（7×24 长稳运行的硬要求）。
- `resize` 回调一律防抖/节流。
