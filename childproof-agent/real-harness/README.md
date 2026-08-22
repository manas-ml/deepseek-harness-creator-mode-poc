# childproof-agent, on the real DeepSeek Harness

This directory is the real-harness counterpart to `../` (the standalone
Python simulation). Everything here actually ran, verified in this session,
against a real checkout of [`deepseek-ai/deepseek-harness`](https://github.com/deepseek-ai/deepseek-harness)
— real Cordis kernel, real `ToolRuntime`/`AgentLoop`, real `@deepseek-ai/dsh-tool-bash`
+ `@deepseek-ai/dsh-bash-local` + `@deepseek-ai/dsh-subprocess-local` doing an
actual `rm -f`, and two brand-new real Cordis tool plugins written for this
demo. The only thing not real is the model: it's an in-process scripted
`LlmAdapter` subclass, which is the exact pattern this codebase's own test
suite (`packages/goal/goal-round-driver/tests/*.spec.ts`,
`packages/core/agent-loop/tests/mock-adapter.ts`, and others) uses to exercise
the agent loop without a live provider key.

**This code cannot run inside this repo.** `@deepseek-ai/dsh-*` packages only
resolve from inside the deepseek-harness pnpm workspace (each preset/plugin's
own README says as much — package names resolve relative to the *host*
composition, not wherever the file happens to sit on disk). Vendoring the
whole ~7,900-file monorepo into this repo isn't reasonable, so what's
committed here is the real source (two tool plugins + one vitest spec) plus
the three trajectories it actually produced, with exact reproduction steps
below.

## What's here

- `tests/fixtures/childproof/safe-scanner.ts` — real Cordis tool plugin.
  Registers `safe_scanner` via `ctx.tools.register(defineTool(...))`
  (`@deepseek-ai/dsh-tools`). Read-only: lists the directory with
  `node:fs/promises`, pattern-matches, never writes.
- `tests/fixtures/childproof/file-read.ts` — real Cordis tool plugin.
  Registers `file_read` (list/read), same read-only constraint.
- `tests/childproof-agent.spec.ts` — the vitest spec that actually drove all
  three runs below, real session events and all.
- `tests/fixtures/childproof/trajectories/*.json` — the real
  `agent.session.events` this spec captured, each run's exact mounted-tool
  list, and the real sha256 folder diff. Not hand-written.

## The three runs, as they actually happened

1. **`standard.json`** — `@deepseek-ai/dsh-agent-spine-demo` bundle +
   `@deepseek-ai/dsh-subprocess-local` + `@deepseek-ai/dsh-bash-local` +
   `@deepseek-ai/dsh-tool-bash` (the real `bash` tool row). The scripted
   model calls `bash` with `rm -f .DS_Store temp.log config.local.json`.
   Real subprocess, real deletion. `folderDiff.removed` is
   `[".DS_Store", "config.local.json", "temp.log"]` — the unrestricted agent
   really did delete a config file it shouldn't have, exactly like the
   Python simulation's story, this time via a real spawned `rm`.
2. **`intern.json`** — the spine bundle with `toolBash: false` (so
   `bashEnv`/`dsh-tool-bash` never mount at all — not hidden, not denied,
   *absent*) plus the two new plugins above. The scripted model calls
   `safe_scanner`, which correctly reports `config.local.json` and
   `notes_dont_delete.md` as NOT safe to remove and only `.DS_Store` /
   `temp.log` as junk. `ctx.tools.schemas()` for this run contains no `bash`
   entry at all. `folderDiff` is all-empty except `unchanged` — every file
   untouched.
3. **`intern-hallucinated-tool-call.json`** — same intern-mode composition,
   but the script has the model try to call `bash` anyway (as if it ignored
   its own tool list). The real `ToolRuntime` answers before any policy or
   dispatch runs:
   ```json
   { "error": { "name": "ToolNotFoundError", "code": "UNKNOWN_TOOL" } }
   ```
   This is the strongest proof point in the whole demo: the boundary isn't
   the model choosing to behave, it's `ctx.tools` never having heard of
   `bash` for this agent. Confirmed directly against the real registry, not
   asserted.

## Reproducing this yourself

```sh
git clone https://github.com/deepseek-ai/deepseek-harness.git
cd deepseek-harness
pnpm install
pnpm run build:lib

# Copy this demo's files into the real checkout, preserving this layout:
cp -r /path/to/childproof-agent/real-harness/tests/childproof-agent.spec.ts \
  packages/examples/agent-spine-demo/tests/
cp -r /path/to/childproof-agent/real-harness/tests/fixtures/childproof \
  packages/examples/agent-spine-demo/tests/fixtures/

pnpm exec vitest run packages/examples/agent-spine-demo/tests/childproof-agent.spec.ts
```

All three tests should pass, and re-running overwrites
`packages/examples/agent-spine-demo/tests/fixtures/childproof/trajectories/*.json`
with a fresh (behaviorally identical) capture — the committed copies here are
exactly what one such run produced.

## What would take this the rest of the way to "real end-to-end, real model"

- Swap the `MockAdapter` for `@deepseek-ai/dsh-llm-deepseek` pointed at a real
  `DEEPSEEK_API_KEY`, or at `@deepseek-ai/dsh-llm-mock-server`
  (`packages/test-support/llm-mock-server`) for a scriptable HTTP-level
  double that exercises the real wire adapter without a live key.
  `intern-mode` doesn't need to change either way — the point being proven is
  the tool composition, not the model.
- Author `intern-mode` as a real, saved **agent preset**
  (`packages/preset/agent-presets`: an `agent.cordis.yml` directory,
  authored via `ctx.agentPresets.copy()`) instead of an ad hoc test
  composition, and run it through the actual `dsh` CLI / Web UI so the
  demo-script's "Creator mode" framing (the self-referential `cordis`
  preset drafting a new one live) is literal rather than illustrative.
