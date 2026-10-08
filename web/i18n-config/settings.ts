import type { InitOptions } from 'i18next'
import { defaultNS, namespaces } from './resources'

export function getInitOptions(): InitOptions {
  return {
    // We do not have en for fallback
    load: 'currentOnly',
    fallbackLng: {
      'es-CL': ['es-ES', 'en-US'],
      default: ['en-US'],
    },
    partialBundledLanguages: true,
    defaultNS,
    enableSelector: 'optimize',
    keySeparator: false,
    ns: namespaces,
    interpolation: {
      escapeValue: false,
    },
  }
}
