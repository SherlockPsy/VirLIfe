/**
 * Accessibility Utilities
 * 
 * Per UI_SPEC.md §17:
 * - Font scaling
 * - Contrast options
 * - Screen reader support
 * - Keyboard navigation
 * - Respect "reduce motion"
 */

/**
 * Get font scale multiplier from user preference or system
 */
export function getFontScale(): number {
  // Check localStorage for user preference
  const stored = localStorage.getItem('fontScale')
  if (stored) {
    const scale = parseFloat(stored)
    if (scale >= 0.75 && scale <= 2.0) {
      return scale
    }
  }
  return 1.0
}

/**
 * Set font scale
 */
export function setFontScale(scale: number): void {
  const clamped = Math.max(0.75, Math.min(2.0, scale))
  localStorage.setItem('fontScale', clamped.toString())
  document.documentElement.style.setProperty('--font-scale', clamped.toString())
}

/**
 * Get contrast preference
 */
export function getContrastMode(): 'normal' | 'high' {
  const stored = localStorage.getItem('contrastMode')
  return (stored === 'high' ? 'high' : 'normal') as 'normal' | 'high'
}

/**
 * Set contrast mode
 */
export function setContrastMode(mode: 'normal' | 'high'): void {
  localStorage.setItem('contrastMode', mode)
  document.documentElement.setAttribute('data-contrast', mode)
}

/**
 * Check if user prefers reduced motion
 */
export function prefersReducedMotion(): boolean {
  return window.matchMedia('(prefers-reduced-motion: reduce)').matches
}

/**
 * Initialize accessibility features
 */
export function initAccessibility(): void {
  // Apply font scale
  const fontScale = getFontScale()
  document.documentElement.style.setProperty('--font-scale', fontScale.toString())
  
  // Apply contrast mode
  const contrastMode = getContrastMode()
  document.documentElement.setAttribute('data-contrast', contrastMode)
  
  // Respect reduce motion (handled by CSS)
}

