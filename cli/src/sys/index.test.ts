import { homedir } from 'node:os'
import { join } from 'node:path'
import { afterEach, describe, expect, it, vi } from 'vite-plus/test'
import { isCompiledBinary, resolvePlatform, SUBDIR } from './index'

describe('resolvePlatform', () => {
  it('id matches process.platform', () => {
    expect(resolvePlatform().id()).toBe(process.platform)
  })

  it('configDir ends with the difyctl subdir', () => {
    const p = resolvePlatform()
    if (p.id() === 'win32') {
      expect(p.configDir()).toMatch(/difyctl$/)
    } else {
      expect(p.configDir()).toBe(join(homedir(), '.config', SUBDIR))
    }
  })

  it('cacheDir ends with the difyctl subdir', () => {
    const p = resolvePlatform()
    if (p.id() === 'win32') {
      expect(p.cacheDir()).toMatch(/difyctl$/)
    } else if (p.id() === 'darwin') {
      expect(p.cacheDir()).toBe(join(homedir(), 'Library', 'Caches', SUBDIR))
    } else {
      expect(p.cacheDir()).toBe(join(homedir(), '.cache', SUBDIR))
    }
  })

  it('atomicReplace is a function', () => {
    expect(resolvePlatform().atomicReplace).toBeTypeOf('function')
  })
})

describe('isCompiledBinary', () => {
  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it.each([
    ['/$bunfs/root/difyctl', true],
    ['B:\\~BUN\\root\\difyctl.exe', true],
    ['/repo/cli/bin/run.ts', false],
  ])('Bun.main %s -> %s', (main, compiled) => {
    vi.stubGlobal('Bun', { main })
    expect(isCompiledBinary()).toBe(compiled)
  })

  it('is false without Bun', () => {
    expect(isCompiledBinary()).toBe(false)
  })
})
