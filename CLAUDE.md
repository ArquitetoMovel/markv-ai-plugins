# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

`markv-ai-plugins` is a **multi-platform AI plugin marketplace**. Every plugin in this repo must work across three hosts: **Claude Code**, **GitHub Copilot CLI**, and **Cursor**. The repo has no application code, build step, or test suite — it ships Markdown (agents/skills) and JSON (manifests).

Spec of record: `spec-modular-plugins.md`. Platform docs are mirrored locally as `claude-plugins-ref.md`, `claude-plugins-market-place.md`, `copilot-plugins-ref.md`, `copilot-plugins-market-place.md`, `cursor-plugins-ref.md` — prefer these over fetching upstream docs.

Content language is Portuguese (pt-BR). Keep user-facing strings, agent prompts, and docs in pt-BR.

## Marketplace + manifest layout (critical)

Each of the three host platforms expects plugin/marketplace manifests in a **different location**. To stay installable from all three from the same Git repo, the same content is duplicated across well-known paths. When you change a manifest, update **all copies in lockstep** — drift here breaks installs silently on the platform you didn't touch.

Repo-level marketplace manifests (all identical content):

- `marketplace.json` — root (generic)
- `.claude-plugin/marketplace.json` — Claude Code
- `.cursor-plugin/marketplace.json` — Cursor
- `.github/plugin/marketplace.json` — Copilot CLI (note `name` is `arquiteto-movel-plugins` here; the other three use `markv-ai-plugins` — both kebab-case as required by the Claude Code schema; match the existing per-host convention when editing)

Per-plugin manifests inside a plugin directory (see `dotnet-unity-tests/`):

- `.claude-plugin/plugin.json` — Claude Code manifest (points `agents` → `./agents/`, `skills` → `./skills/`)
- `.cursor-plugin/plugin.json` — Cursor manifest (minimal — no agents/skills fields)
- `plugin.json` at the plugin root — Copilot CLI manifest (points `agents` → `copilot-agents/`, `skills` → `["skills/"]`)

The Copilot manifest points to `copilot-agents/`, not `agents/`, because Copilot agents use a **different file extension and frontmatter schema** than Claude/Cursor (see below). The `skills/` directory is shared by all three.

## Plugin internal structure

Pattern established by `dotnet-unity-tests/` (the only plugin so far — follow this layout for new plugins):

```
<plugin-name>/
├── .claude-plugin/plugin.json   # Claude Code manifest
├── .cursor-plugin/plugin.json   # Cursor manifest
├── plugin.json                  # Copilot CLI manifest (plugin root)
├── agents/                      # Claude + Cursor agents (*.md)
├── copilot-agents/              # Copilot CLI agents (*.agent.md)
├── skills/                      # Shared skills across all 3 platforms
│   └── <skill-name>/SKILL.md
├── docs/                        # Design docs, specs
└── README.md
```

### Agent file format differs per host

- **Claude/Cursor agents** (`agents/*.md`): rich YAML frontmatter with `name`, `description`, `model`, `tools` (list of tool names like `Read`, `Glob`, `Bash`), `skills` (list of `<plugin>:<skill>` refs). The skills reference uses the `<plugin-name>:<skill-name>` form, e.g. `dotnet-unity-tests-plugin:dotnet-xunit`.
- **Copilot CLI agents** (`copilot-agents/*.agent.md`): different frontmatter — `name`, `description`, `tools` as a lowercase JSON array (e.g. `["bash", "edit", "view"]`). No `model`, no `skills` field.

When porting an agent across hosts: keep the body (pt-BR prose) identical; only rewrite the frontmatter to match the target host's schema. The two copies in `agents/` and `copilot-agents/` should stay semantically aligned.

### Skills are the one thing that's truly shared

`skills/<name>/SKILL.md` works identically for all three hosts. Put canonical knowledge here and reference it from agents on every platform.

## How plugins in this repo work (dotnet-unity-tests)

The plugin ships two cooperating agents plus supporting skills:

1. `dotnet-tester-reviewer` analyzes a .NET solution and writes `test-plan.md` (analysis only — no test code).
2. `dotnet-tester-creator` reads `test-plan.md` and implements the tests (`dotnet build`, `dotnet test`, ≥80% coverage goal).
3. The plan's **Section 4** marks projects as parallelizable; the creator may be invoked in parallel over independent projects.

Framework selection rule (hardcoded in the skills): `net472` → MSTest v3 (`skills/dotnet-mstest`); `net8.0+` → xUnit (`skills/dotnet-xunit`). Agent prompts reference this decision rule — don't invert it without also updating the skills.

## Commands

There is no build, lint, or test for this repo itself. Useful end-user install commands (document these when shipping a new plugin):

```bash
# Claude Code
/plugin marketplace add ArquitetoMovel/markv-ai-plugins
/plugin install <plugin-name>@markv-ai-plugins

# GitHub Copilot CLI
copilot plugin marketplace add ArquitetoMovel/markv-ai-plugins
copilot plugin install <plugin-name>

# Cursor — imported as Team Marketplace via Dashboard → Settings → Plugins
```

## Adding a new plugin

1. Create `<plugin-name>/` at the repo root following the layout above.
2. Write the three per-plugin manifests (Claude, Cursor, Copilot root) — keep `name`, `version`, `description`, `keywords` consistent across all three.
3. Author agents in **both** `agents/` (Claude/Cursor schema) and `copilot-agents/` (Copilot schema). Keep bodies in sync.
4. Put shared knowledge in `skills/<skill>/SKILL.md`.
5. Add a matching entry to **all four** marketplace manifests (`marketplace.json`, `.claude-plugin/marketplace.json`, `.cursor-plugin/marketplace.json`, `.github/plugin/marketplace.json`) with identical `name`, `source`, `version`, `description`, `category`, `keywords`.
