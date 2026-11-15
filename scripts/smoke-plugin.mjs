import assert from 'node:assert'
import { apply } from '../index.js'

let factory
apply({ skills: { registerProvider(fn) { factory = fn } } })
assert.ok(factory, 'apply() 没有注册 provider')

const provider = factory({ signal: undefined, invalidate() {} })
const candidates = await provider.list()
assert.ok(candidates.length >= 9, `期望 >= 9 个 skill，实际 ${candidates.length}`)

for (const c of candidates) {
  for (const field of ['name', 'description', 'invocation', 'source', 'provider', 'rank']) {
    assert.ok(c[field] !== undefined, `${c.name} 缺字段 ${field}`)
  }
  const def = await provider.get(c)
  assert.ok(def && def.content.length > 100, `${c.name} 的 content 太短`)
}

const names = candidates.map((c) => c.name).join(', ')
console.log(`provider=${provider.name} skills=${candidates.length}`)
console.log(names)
console.log('smoke ok')
