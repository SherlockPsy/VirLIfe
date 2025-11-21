/**
 * Settings App
 * 
 * Per UI_SPEC.md §12:
 * - TTS settings
 * - Notification settings
 * - UI preferences
 */

import { useState } from 'react'
import { config } from '../../config/env'
import './PhoneApp.css'

export default function SettingsApp() {
  const [ttsEnabled, setTtsEnabled] = useState(config.ttsEnabled)

  return (
    <div className="phone-app">
      <div className="phone-app__settings">
        <div className="phone-app__setting">
          <label className="phone-app__setting-label">
            Enable Text-to-Speech
          </label>
          <input
            type="checkbox"
            checked={ttsEnabled}
            onChange={(e) => setTtsEnabled(e.target.checked)}
            className="phone-app__setting-input"
          />
        </div>
        
        <div className="phone-app__setting">
          <label className="phone-app__setting-label">
            App Version
          </label>
          <div className="phone-app__setting-value">{config.appVersion}</div>
        </div>
      </div>
    </div>
  )
}

