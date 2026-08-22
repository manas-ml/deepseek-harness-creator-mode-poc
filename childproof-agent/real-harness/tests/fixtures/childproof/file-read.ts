/**
 * Real Cordis tool plugin: file_read.
 *
 * Read-only file access scoped to one directory. Registers `file_read` via
 * `ctx.tools.register(defineTool(...))`. No write, no delete, no shell.
 */
import { readdir, readFile } from 'node:fs/promises'
import { resolve } from 'node:path'
import type { Context } from '@deepseek-ai/cordis'
import { defineTool } from '@deepseek-ai/dsh-tools'

export const name = 'childproof-file-read'
export const inject = ['tools']

export interface Config {
  root: string
}

export function apply(ctx: Context, config: Config): void {
  const root = resolve(config.root)

  ctx.tools.register(defineTool({
    name: 'file_read',
    description: 'List files in the sandbox root, or read one file inside it. Read-only.',
    parameters: {
      action: { type: 'string', enum: ['list', 'read'], required: true },
      path: { type: 'string' },
    },
    output: {
      schema: { type: 'json' },
      render: (_args, value) => [{ type: 'text', text: JSON.stringify(value, null, 2) }],
    },
    async execute(args, exec) {
      if (args.action === 'list') {
        const entries = await readdir(root, { withFileTypes: true, signal: exec.signal })
        return { files: entries.filter(entry => entry.isFile()).map(entry => entry.name).sort() }
      }
      if (args.action === 'read') {
        if (!args.path) throw new Error("action=read requires 'path'")
        const target = resolve(root, args.path)
        if (target !== root && !target.startsWith(root + '/')) {
          throw new Error(`'${args.path}' escapes the sandbox root`)
        }
        return { content: await readFile(target, 'utf8') }
      }
      throw new Error(`unsupported action '${args.action as string}'`)
    },
  }))
}
