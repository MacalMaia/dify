// Aplica macal/i18n-overrides.json sobre web/i18n/<locale>/<namespace>.json.
// Se corre en el build (Cloud Build, antes de docker build). Solo Node, sin dependencias.
// Falla si una clave no existe en el archivo destino: así nos enteramos cuando Dify renombra una clave.
import { readFileSync, writeFileSync } from 'node:fs'
import { dirname, join } from 'node:path'
import { fileURLToPath } from 'node:url'

const root = join(dirname(fileURLToPath(import.meta.url)), '..')
const overrides = JSON.parse(readFileSync(join(root, 'macal', 'i18n-overrides.json'), 'utf8'))
let applied = 0
const missing = []
for (const [locale, namespaces] of Object.entries(overrides)) {
  if (locale.startsWith('_')) continue
  for (const [ns, entries] of Object.entries(namespaces)) {
    const file = join(root, 'web', 'i18n', locale, `${ns}.json`)
    const data = JSON.parse(readFileSync(file, 'utf8'))
    for (const [key, value] of Object.entries(entries)) {
      if (!(key in data)) { missing.push(`${locale}/${ns}.json: ${key}`); continue }
      data[key] = value
      applied++
    }
    writeFileSync(file, `${JSON.stringify(data, null, 2)}\n`)
  }
}
console.log(`i18n overrides Macal: ${applied} textos aplicados`)
if (missing.length) {
  console.error(`Claves inexistentes (¿Dify las renombró?):\n  ${missing.join('\n  ')}`)
  process.exit(1)
}
