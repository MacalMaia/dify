import { mkdir, mkdtemp, readFile, rm, stat, writeFile } from 'node:fs/promises'
import { tmpdir } from 'node:os'
import { dirname, join } from 'node:path'
import { afterEach, beforeEach, expect, it } from 'vite-plus/test'
import { ErrorCode } from '@/errors/codes'
import { installSkill } from './install'
import { embeddedSource, openDir, SKILL_FILE, SKILL_NAME } from './source'

let tmp: string
let from: string
let root: string

async function put(path: string, text: string): Promise<void> {
  const abs = join(from, path)
  await mkdir(dirname(abs), { recursive: true })
  await writeFile(abs, text)
}

beforeEach(async () => {
  tmp = await mkdtemp(join(tmpdir(), 'difyctl-skill-'))
  from = join(tmp, 'source')
  root = join(tmp, 'root')
  await put(SKILL_FILE, `---\nname: ${SKILL_NAME}\ndescription: d\n---\n`)
  await put('references/setup.md', 'setup')
})

afterEach(async () => {
  await rm(tmp, { recursive: true, force: true })
})

it('writes every file under <root>/difyctl', async () => {
  const wrote = await installSkill(root, await openDir(from))
  expect(wrote.sort()).toEqual(
    [join(root, SKILL_NAME, SKILL_FILE), join(root, SKILL_NAME, 'references/setup.md')].sort(),
  )
  expect(await readFile(join(root, SKILL_NAME, 'references/setup.md'), 'utf8')).toBe('setup')
})

it('removes files the new tree no longer has', async () => {
  await mkdir(join(root, SKILL_NAME, 'references'), { recursive: true })
  await writeFile(join(root, SKILL_NAME, 'references/old.md'), 'old')
  await installSkill(root, await openDir(from))
  await expect(stat(join(root, SKILL_NAME, 'references/old.md'))).rejects.toThrow()
})

it('maps embedded names to paths inside the skill', async () => {
  const file = Object.assign(new Blob(['setup']), { name: '../skills/difyctl/references/setup.md' })
  const source = embeddedSource([file])
  expect(source.paths).toEqual(['references/setup.md'])
  expect(new TextDecoder().decode(await source.read('references/setup.md'))).toBe('setup')
})

it('refuses a folder without SKILL.md as a usage error', async () => {
  await expect(openDir(join(tmp, 'empty'))).rejects.toMatchObject({
    code: ErrorCode.UsageInvalidFlag,
  })
})
