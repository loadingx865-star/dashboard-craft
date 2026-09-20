# dashboard-craft

> An engineering standard for dashboard, wall-display, and industrial-console frontends, packaged as an installable Agent Skill.

[简体中文](README.md) | **English**

**License** MIT ([LICENSE](LICENSE)) · **Format** Agent Skill (`SKILL.md`, `scripts/`, `references/`, `assets/`) · **Install** `npx skills add loadingx865-star/dashboard-craft`

## The problem

AI-assisted dashboard work keeps failing in the same three ways:

| Symptom | Typical cause |
|---|---|
| Looks fine on your laptop, breaks on the factory TV or control-room wall: overflowing layout, tiny fonts, blurry charts | Target resolution, OS scaling, and browser were never locked down before coding started |
| Phase 2 does not match phase 1: different colors, type scale, chart styling | Design decisions have no single source of truth and get re-invented every phase |
| Everything runs, but components are written ad hoc and get harder to change | No single entry point for shared components and charts |

None of this is a model-capability problem. It is a missing-constraints problem. This skill adds the constraint layer as 8 stages, each with a defined deliverable and a pass condition (Gate). If a Gate fails, you do not move on.

## Core mechanisms

### Five hard rules

| # | Rule | Meaning |
|---|---|---|
| 1 | No constraints, no code | Do not write UI code until the environment constraints card is complete |
| 2 | No single source, no styles | Colors, type scale, spacing, radius, and chart palettes come from design tokens. Hardcoded values and magic numbers are forbidden. Enforced by script, not by assertion |
| 3 | No matrix, no delivery | The resolution x browser matrix must pass and screenshot baselines must be committed. Verified by script |
| 4 | One concept, one implementation | Shared components and charts have exactly one entry point. No parallel implementations. A new dashboard may only add configuration and layout: charts are reused from the same implementation (a dashboard is a composition) |
| 5 | Deviations must be logged | Any deviation from the design source goes into a page-level override file with a stated reason |

### Eight stages

```
0 Lock constraints -> 1 Design source -> 2 Spec & tickets -> 3 Skeleton first
-> 4 Components & charts -> 5 Adaptation QA -> 6 Quality gates -> 7 Delivery archive
```

| Stage | Deliverable | Gate |
|---|---|---|
| 0 Lock constraints | Environment constraints card | Resolution, browser, scaling, network, data frequency all explicit, plus a declared Browserslist compatibility target (machine-checked) |
| 1 Design source | Tokens + MASTER spec | Token validation passes; scaling strategy documented |
| 2 Spec & tickets | Vertical-slice tickets | Every ticket has verifiable acceptance criteria |
| 3 Skeleton first | Layout shell | Empty shell does not break at any target resolution |
| 4 Components & charts | Restricted component layer + chart wrapper | No page-level ad-hoc styles |
| 5 Adaptation QA | Screenshot baselines | Matrix passes; no overflow or clipping |
| 6 Quality gates | Test reports | Performance, a11y, smoke, and visual diff all green |
| 7 Delivery archive | Delivery package | Baselines committed; regression assets reproducible |

Stage details live in `skills/dashboard-craft/references/01~09`.

## Install

```bash
# Install to auto-detected agents
npx skills add loadingx865-star/dashboard-craft

# Install to a specific agent
npx skills add loadingx865-star/dashboard-craft -a codex

# Install to several agents at once
npx skills add loadingx865-star/dashboard-craft -a claude-code -a cursor

# Confirm
npx skills list
```

On Windows, add `--copy` if symlinks are restricted.

The CLI chooses the install location: globally at `~/.agents/skills/dashboard-craft`, or per-project at `./.agents/skills/dashboard-craft`. Manual installation also works: copy the whole `skills/dashboard-craft/` directory into your agent's skills directory.

### Supported agents

This is a standard Agent Skill (`SKILL.md` plus optional `scripts/`, `references/`, and `assets/`), so any agent that understands the format can use it. `npx skills` v1.7 currently knows 79 agents, including:

| Category | Agents |
|---|---|
| Coding assistants | codex, claude-code, cursor, windsurf, gemini-cli, github-copilot, opencode, cline, roo, continue, amp, aider-desk |
| Popular in China | qwen-code, kimi-code-cli, trae, trae-cn, lingma, codebuddy, qoder, qoder-cn, iflow-cli, codearts-agent, kiro-cli |
| Terminal-native | crush, goose, droid, devin, openhands, warp, zed |
| Catch-all | universal (writes to the shared `.agents/skills`, readable by agents without a dedicated adapter) |

> To see what is available on your machine, run `npx skills add loadingx865-star/dashboard-craft` without `-y` and pick from the detected list. Use `--all` to install everywhere. Full list: [skills.sh](https://skills.sh).

### Prerequisites

The skill body needs no runtime. The scripts do, and only when a stage reaches them:

| Capability | Requirement | When missing |
|---|---|---|
| Token validation / Gate checks | Python 3.9+ (stdlib only) | Gates degrade to manual review |
| Toolchain version comparison | Access to registry.npmjs.org, or a warm local cache | Use `--offline`; otherwise skip. Does not block development |
| Multi-resolution screenshots | Node.js + `@playwright/test` | Stage 5 cannot be automated |
| UI metadata (`agents/openai.yaml`) | Read by Codex only | Other agents ignore the file; no impact |

Air-gapped, offline, and Node-less environments can still use the skill. Only the automation degrades; the rules stay in force.

## Quick start

```bash
SKILL=~/.agents/skills/dashboard-craft

# 1. Validate design tokens and detect hardcoded styles
python $SKILL/scripts/validate_tokens.py \
  --tokens design-system/design-tokens.json --src src,app

# 2. Check stage Gates against the standard project layout
python $SKILL/scripts/check_gates.py --project .

# 3. Compare the toolchain baseline with live npm versions
python $SKILL/scripts/refresh_toolchain.py            # online
python $SKILL/scripts/refresh_toolchain.py --offline  # air-gapped
```

Key flags:

| Script | Flags |
|---|---|
| `validate_tokens.py` | `--tokens` token file; `--src a,b` multiple source dirs/files (a nonexistent path fails the run); `--layers base,alias,config` custom layer names; `--fail-on-hardcode` exit non-zero on hardcoded styles (CI); `--json` |
| `check_gates.py` | `--project .` target project; `--stage 0` single stage, 0-7 only (repeatable); `--allow-empty-card` structure-only; `--json` |
| `refresh_toolchain.py` | `--baseline` baseline path; `--update-baseline` write back; `--offline` |

On Windows, replace `~/` with `%USERPROFILE%\`.

Three things to do before starting:

1. Copy `assets/templates/constraints-card.md` and fill it in.
2. Seed `design-system/` from `assets/templates/MASTER.md` and `assets/templates/design-tokens.example.json`, then pick a large-screen scaling strategy.
3. Configure the viewport matrix from `assets/templates/playwright.viewports.ts`.

The full methodology (in Chinese) is in [docs/methodology.md](docs/methodology.md).

## Repository layout

```
dashboard-craft/
|-- skills/dashboard-craft/                Installable skill
|   |-- SKILL.md                           Entry: rules + 8-stage gates
|   |-- agents/openai.yaml                 UI metadata (Codex only)
|   |-- references/01~09                   Stage-by-stage detail
|   |-- assets/templates/                  Copy-ready templates
|   |-- assets/examples/                   Chart wrapper / scaling / breakpoint hooks
|   |-- scripts/validate_tokens.py         Token validation + hardcode detection
|   |-- scripts/check_gates.py             Machine-checked stage gates
|   |-- scripts/refresh_toolchain.py       Toolchain version comparison
|   `-- toolchain-baseline.json            Version baseline for 55 packages
|-- docs/methodology.md                    Full methodology (Chinese)
|-- README.md / README.en.md               Chinese / English docs (this file)
|-- CHANGELOG.md
|-- CONTRIBUTING.md
|-- LICENSE
|-- .gitignore                          Ignores dependency and runtime-cache paths
`-- .gitattributes                      Normalizes line endings to LF
```

## Design principles

**Record roles, not versions.** Frontend tooling moves fast; docs that pin versions rot. Documents name a role ("prefer ECharts for charts"); concrete versions live in `toolchain-baseline.json` and are refreshed by script.

**This skill only orchestrates.** Skills such as `frontend-design`, `shadcn`, `vercel-react-best-practices`, and `playwright` strengthen a single capability. dashboard-craft decides when to use which, what the output must satisfy, and what happens when it does not.

**Scripts back the gates, not good intentions.** Every stage pass has a command and an exit code. CI runs hardcode detection with `--fail-on-hardcode`, so a stage cannot be waved through by assertion.

## Scope

Applies to: data dashboards, operations wall displays, industrial consoles, monitoring screens.

Does not apply to: marketing sites and portfolios. Use [frontend-design](https://skills.sh/anthropics/skills/frontend-design) for expressive pages.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Version history in [CHANGELOG.md](CHANGELOG.md).

## License

[MIT](LICENSE)
