/**
 * Real Cordis tool plugin: safe_scanner.
 *
 * Read-only. Scans one directory and reports, per file, whether it looks
 * safe to remove, with a one-line reason. Registers exactly one tool via
 * `ctx.tools.register(defineTool(...))` — no write, no delete, no shell
 * capability anywhere in this file.
 */
import { readdir } from 'node:fs/promises'
import type { Context } from '@deepseek-ai/cordis'
import { defineTool } from '@deepseek-ai/dsh-tools'

export const name = 'childproof-safe-scanner'
export const inject = ['tools']

export interface Config {
  root: string
  extraExclude?: string[]
}

interface ScanRow {
  file: string
  looksSafeToRemove: boolean
  reason: string
}

const JUNK_PATTERNS = [/\.log$/, /^\.DS_Store$/, /\.tmp$/, /^temp/, /__pycache__/]
const EXCLUDE_ALWAYS = [/dont_delete/, /\.md$/]

function classify(fileName: string, extraExclude: RegExp[]): ScanRow {
  for (const pattern of [...EXCLUDE_ALWAYS, ...extraExclude]) {
    if (pattern.test(fileName)) {
      return { file: fileName, looksSafeToRemove: false, reason: `protected: matches ${pattern}` }
    }
  }
  for (const pattern of JUNK_PATTERNS) {
    if (pattern.test(fileName)) {
      return { file: fileName, looksSafeToRemove: true, reason: `junk: matches ${pattern}` }
    }
  }
  return { file: fileName, looksSafeToRemove: false, reason: 'no junk pattern matched; treated as content' }
}

export function apply(ctx: Context, config: Config): void {
  const extraExclude = (config.extraExclude ?? []).map(source => new RegExp(source))

  ctx.tools.register(defineTool({
    name: 'safe_scanner',
    description: 'Read-only scan of the sandbox directory that flags files that look safe to remove, with a reason. Never writes or deletes.',
    parameters: {},
    output: {
      schema: { type: 'json' },
      render: (_args, value) => [{ type: 'text', text: JSON.stringify(value, null, 2) }],
    },
    async execute(_args, exec) {
      const entries = await readdir(config.root, { withFileTypes: true, signal: exec.signal })
      const report = entries
        .filter(entry => entry.isFile())
        .map(entry => classify(entry.name, extraExclude))
        .sort((a, b) => a.file.localeCompare(b.file))
      return { report }
    },
  }))
}
