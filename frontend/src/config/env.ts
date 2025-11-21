/**
 * Environment Configuration
 * 
 * Reads environment variables for backend URLs and settings
 * Per Architecture.md and Plan.md Phase 10.9
 */

const getEnvVar = (key: string, defaultValue?: string): string => {
  // In Vite, env vars are prefixed with VITE_ and exposed via import.meta.env
  const env = import.meta.env as Record<string, string | undefined>
  const value = env[`VITE_${key}`] || env[key] || defaultValue
  
  if (!value && !defaultValue) {
    console.warn(`Environment variable ${key} is not set`)
  }
  
  return value || ''
}

export const config = {
  env: getEnvVar('VIRLIFE_ENV', 'development'),
  backendBaseUrl: getEnvVar('BACKEND_BASE_URL', 'http://localhost:8000'),
  backendWsUrl: getEnvVar('BACKEND_WS_URL', 'ws://localhost:8000'),
  ttsEnabled: getEnvVar('TTS_ENABLED', 'false') === 'true',
  ttsBaseUrl: getEnvVar('TTS_BASE_URL', ''),
  appVersion: getEnvVar('APP_VERSION', '1.0.0'),
}

// Validate required config
if (!config.backendBaseUrl) {
  console.error('BACKEND_BASE_URL is required but not set')
}

