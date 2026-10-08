export const loadResource = (fileNamespace: string) =>
  import(`../../i18n/es-CL/${fileNamespace}.json`)
