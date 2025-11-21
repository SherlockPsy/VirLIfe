/**
 * Accessibility Settings Component
 * 
 * Per UI_SPEC.md §17:
 * - Font scaling controls
 * - Contrast options
 * - Keyboard navigation info
 */

import { useState, useEffect } from 'react'
import { getFontScale, setFontScale, getContrastMode, setContrastMode } from '../utils/accessibility'
import './AccessibilitySettings.css'

export default function AccessibilitySettings() {
  const [fontScale, setFontScaleState] = useState(1.0)
  const [contrastMode, setContrastModeState] = useState<'normal' | 'high'>('normal')
  const [isOpen, setIsOpen] = useState(false)

  useEffect(() => {
    setFontScaleState(getFontScale())
    setContrastModeState(getContrastMode())
  }, [])

  const handleFontScaleChange = (scale: number) => {
    setFontScaleState(scale)
    setFontScale(scale)
  }

  const handleContrastChange = (mode: 'normal' | 'high') => {
    setContrastModeState(mode)
    setContrastMode(mode)
  }

  if (!isOpen) {
    return (
      <button
        className="accessibility-settings__toggle"
        onClick={() => setIsOpen(true)}
        aria-label="Open accessibility settings"
      >
        ♿
      </button>
    )
  }

  return (
    <div className="accessibility-settings">
      <div className="accessibility-settings__header">
        <h3>Accessibility Settings</h3>
        <button
          className="accessibility-settings__close"
          onClick={() => setIsOpen(false)}
          aria-label="Close accessibility settings"
        >
          ×
        </button>
      </div>
      
      <div className="accessibility-settings__content">
        <div className="accessibility-settings__group">
          <label className="accessibility-settings__label">
            Font Size: {fontScale.toFixed(2)}x
            <input
              type="range"
              min="0.75"
              max="2.0"
              step="0.25"
              value={fontScale}
              onChange={(e) => handleFontScaleChange(parseFloat(e.target.value))}
              className="accessibility-settings__slider"
            />
          </label>
        </div>
        
        <div className="accessibility-settings__group">
          <label className="accessibility-settings__label">
            Contrast Mode
            <select
              value={contrastMode}
              onChange={(e) => handleContrastChange(e.target.value as 'normal' | 'high')}
              className="accessibility-settings__select"
            >
              <option value="normal">Normal</option>
              <option value="high">High</option>
            </select>
          </label>
        </div>
        
        <div className="accessibility-settings__info">
          <p>Keyboard Navigation:</p>
          <ul>
            <li>Tab: Navigate between elements</li>
            <li>Enter: Activate buttons/links</li>
            <li>Escape: Close dialogs</li>
          </ul>
        </div>
      </div>
    </div>
  )
}

