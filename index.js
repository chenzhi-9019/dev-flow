import { existsSync, readFileSync, readdirSync } from 'node:fs'
import { dirname, join } from 'node:path'
import { fileURLToPath } from 'node:url'

export const name = 'skill-dev-flow'
export const inject = ['skills']

const ROOT = dirname(fileURLToPath(import.meta.url))
const PROVIDER = 'dev-flow'
const RANK = 120

function splitFrontmatter(text) {
  if (!text.startsWith('---')) return { meta: {}, body: text }
  const end = text.indexOf('\n---', 3)
  if (end === -1) return { meta: {}, body: text }
  const meta = {}
  for (const line of text.slice(3, end).split(/\r?\n/)) {
    const i = line.indexOf(':')
    if (i > 0) meta[line.slice(0, i).trim()] = line.slice(i + 1).trim()
  }
  return { meta, body: text.slice(end + 4).replace(/^\r?\n/, '') }
}

function skillDirs() {
  return readdirSync(ROOT, { withFileTypes: true })
    .filter((entry) => entry.isDirectory() && entry.name.startsWith('df-'))
    .map((entry) => entry.name)
    .filter((dir) => existsSync(join(ROOT, dir, 'SKILL.md')))
}

function load(dir) {
  const dirPath = join(ROOT, dir)
  const { meta, body } = splitFrontmatter(readFileSync(join(dirPath, 'SKILL.md'), 'utf8'))
  return {
    dir: dirPath,
    name: meta.name || dir,
    description: meta.description || '',
    whenToUse: meta['when-to-use'],
    invocation: {
      modelInvocable: meta['disable-model-invocation'] !== 'true',
      userInvocable: meta['user-invocable'] !== 'false',
    },
    content: body,
  }
}

function candidate(skill) {
  return {
    rank: RANK,
    name: skill.name,
    description: skill.description,
    whenToUse: skill.whenToUse,
    invocation: skill.invocation,
    source: 'bundled',
    provider: PROVIDER,
    path: join(skill.dir, 'SKILL.md'),
    resourceBase: { kind: 'directory', path: skill.dir },
    handle: skill.name,
  }
}

/** Register the dev-flow skill suite bundled with this package. */
export function apply(ctx) {
  ctx.skills.registerProvider(() => {
    const loadAll = () => skillDirs().map((dir) => load(dir))
    return {
      name: PROVIDER,
      async list() {
        return loadAll().map(candidate)
      },
      async get(selected) {
        const hit = loadAll().find((skill) => skill.name === selected.handle)
        if (!hit) return undefined
        return { ...candidate(hit), content: hit.content }
      },
    }
  })
}
