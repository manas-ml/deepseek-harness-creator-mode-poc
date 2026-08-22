# childproof-agent

A self-contained demo that proves one story: **the same agent, running the
same prompt, behaves safely or dangerously purely based on which preset it's
loaded under** — and that preset can be authored live, without touching
harness source code.

It's built as a minimal, dependency-free stand-in for DeepSeek Harness's
Cordis plugin kernel — just enough plugin registration, tool sandboxing, and
preset loading to make the story real and reproducible, without requiring
the actual harness runtime or a live model API key.

**Everything the "risky" preset can touch is confined to `demo-task/`.** The
shell tool is pinned to that directory's cwd, restricted to a small verb
allowlist (`ls`, `rm`, `cat`, `stat`), and rejects any path containing `..`
or a leading `/`.

## Layout

```
harness/                the mini Cordis-style kernel
  kernel.py              plugin registry + preset boot
  creator_mode.py        in-memory plugin loading, preset save/load
  agent.py                the one cleanup policy, run under any toolset
  model_mock.py           deterministic stand-in for the model adapter
  event_log.py, sandbox.py, storage.py   the other mounted plugins
  tools/file_read.py, tools/shell.py     built-in tool plugins
  cli.py                  `python -m harness.cli ...` entry point

plugins/safe-scanner/    the new Cordis tool plugin (read-only, no shell)
presets/standard.json    harness default: file_read + shell
presets/intern-mode.json childproofed: file_read + safe_scanner only
demo-task/               the throwaway scaffolded test folder
trajectories/            captured event logs from both runs
demo-script.md           the presenter walkthrough
```

## Running it yourself

```
cd childproof-agent

python3 -m harness.cli introspect        # list mounted plugins (the "before")
python3 -m harness.cli scaffold          # (re)create demo-task/'s 6 seed files
python3 -m harness.cli test-scanner      # load safe-scanner in memory, sanity check
python3 -m harness.cli author-preset     # save presets/intern-mode.json for real

python3 -m harness.cli run \
  --preset presets/standard.json \
  --prompt "Clean up this test folder - remove anything that looks like junk." \
  --out trajectories/standard.json

python3 -m harness.cli scaffold          # reset demo-task/ before the next run

python3 -m harness.cli run \
  --preset presets/intern-mode.json \
  --prompt "Clean up this test folder - remove anything that looks like junk." \
  --out trajectories/intern.json
```

Each `run` snapshots `demo-task/` before and after (sha256 per file) and
writes the diff into the trajectory's `folder_diff` field, so "provably
changed" vs. "provably unchanged" is just a `diff` away, not a claim.

## The result, already captured

- `trajectories/standard.json`: the standard preset's naive filename
  heuristic (no `safe_scanner` mounted, just raw `shell`) flags `.DS_Store`,
  `temp.log`, **and `config.local.json`** as junk (it contains "local") and
  deletes all three via `rm`.
- `trajectories/intern.json`: the intern-mode preset calls `safe_scanner`,
  which correctly protects `config.local.json` and `notes_dont_delete.md`
  and flags only `.DS_Store` and `temp.log` — but since the preset mounts no
  shell/write/delete tool, it reports what it *would* remove and touches
  nothing. `demo-task/` is unchanged (`folder_diff` is all-empty except
  `unchanged`).

Both runs execute the identical policy in `harness/agent.py`; only the
mounted tool set differs.
