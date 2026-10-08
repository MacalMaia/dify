import { readdir, readFile } from 'node:fs/promises'
import { dirname, join, normalize, relative, sep } from 'node:path'
import { fileURLToPath } from 'node:url'
import { describe, expect, it } from 'vite-plus/test'
import { commandTree } from '@/commands/tree.generated'

const SKILL_DIR = fileURLToPath(new URL('../../../skills/difyctl/', import.meta.url))
const CATALOG = fileURLToPath(new URL('../fixtures/catalog.json', import.meta.url))
const ROOT_DOC = 'SKILL.md'
const MAX_HOPS = 2
const MAP_MAX_LINES = 60
const TOC_AFTER_LINES = 100
const TOC_HEADING = /^## Contents$/m
const LINK = /\]\(([^)#\s]+\.md)\)/g
const COMMAND = /`difyctl ([^`]+)`/g
const BUILTIN_ROOTS = new Set(['help'])
const WORD = /^[a-z_]+$/

async function docs(): Promise<string[]> {
  const out: string[] = []
  for (const entry of await readdir(SKILL_DIR, { recursive: true, withFileTypes: true })) {
    if (entry.isFile() && entry.name.endsWith('.md'))
      out.push(relative(SKILL_DIR, join(entry.parentPath, entry.name)).split(sep).join('/'))
  }
  return out
}

function links(doc: string, text: string): string[] {
  return [...text.matchAll(LINK)].map((m) =>
    normalize(join(dirname(doc), m[1] as string))
      .split(sep)
      .join('/'),
  )
}

function commandWords(span: string): string[] {
  const words: string[] = []
  for (const word of span.split(' ')) {
    if (!WORD.test(word)) break
    words.push(word)
  }
  return words
}

function isLocal(words: readonly string[]): boolean {
  if (BUILTIN_ROOTS.has(words[0] as string)) return true
  let node: { subcommands?: Record<string, unknown> } | undefined = { subcommands: commandTree }
  for (const word of words) {
    node = node?.subcommands?.[word] as typeof node
    if (node === undefined) return false
  }
  return true
}

function isOpOrNamespace(words: readonly string[], ops: readonly string[]): boolean {
  const full = words.join('.')
  if (ops.some((op) => op.startsWith(`${full}.`))) return true
  for (let end = words.length; end > 0; end--) {
    if (ops.includes(words.slice(0, end).join('.'))) return true
  }
  return false
}

describe('skills/difyctl tree', async () => {
  const all = await docs()
  const text = new Map(
    await Promise.all(
      all.map(async (d) => [d, await readFile(join(SKILL_DIR, d), 'utf8')] as const),
    ),
  )
  const ops = Object.keys(
    (JSON.parse(await readFile(CATALOG, 'utf8')) as { ops: Record<string, unknown> }).ops,
  )

  it('every relative link resolves', () => {
    for (const [doc, body] of text)
      for (const target of links(doc, body)) expect(all, `${doc} → ${target}`).toContain(target)
  })

  it('every doc is reachable within two hops of SKILL.md', () => {
    const depth = new Map([[ROOT_DOC, 0]])
    const queue = [ROOT_DOC]
    while (queue.length > 0) {
      const doc = queue.shift() as string
      for (const next of links(doc, text.get(doc) ?? '')) {
        if (depth.has(next)) continue
        depth.set(next, (depth.get(doc) as number) + 1)
        queue.push(next)
      }
    }
    for (const doc of all) {
      expect(depth.has(doc), `${doc} unreachable`).toBe(true)
      expect(depth.get(doc) as number, doc).toBeLessThanOrEqual(MAX_HOPS)
    }
  })

  it('maps stay short and long leaves have contents', () => {
    for (const [doc, body] of text) {
      const lines = body.split('\n').length
      const isMap = links(doc, body).length > 0
      if (isMap) expect(lines, doc).toBeLessThan(MAP_MAX_LINES)
      else if (lines > TOC_AFTER_LINES) expect(body, doc).toMatch(TOC_HEADING)
    }
  })

  it('every difyctl command exists locally or in the catalog', () => {
    for (const [doc, body] of text) {
      for (const m of body.matchAll(COMMAND)) {
        const words = commandWords(m[1] as string)
        if (words.length === 0) continue
        expect(isLocal(words) || isOpOrNamespace(words, ops), `${doc}: difyctl ${m[1]}`).toBe(true)
      }
    }
  })
})
