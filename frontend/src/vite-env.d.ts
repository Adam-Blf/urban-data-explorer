/// <reference types="vite/client" />

interface ImportMetaEnv {
  /** Base URL de l'API backend. Vide = même origine (exe local-first). */
  readonly VITE_API_BASE?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
