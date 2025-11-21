/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_VIRLIFE_ENV?: string
  readonly VITE_BACKEND_BASE_URL?: string
  readonly VITE_BACKEND_WS_URL?: string
  readonly VITE_TTS_ENABLED?: string
  readonly VITE_TTS_BASE_URL?: string
  readonly VITE_APP_VERSION?: string
  // Also support non-prefixed versions for Railway
  readonly VIRLIFE_ENV?: string
  readonly BACKEND_BASE_URL?: string
  readonly BACKEND_WS_URL?: string
  readonly TTS_ENABLED?: string
  readonly TTS_BASE_URL?: string
  readonly APP_VERSION?: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}

