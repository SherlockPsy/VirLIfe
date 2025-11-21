/**
 * TTS Controls Component
 * 
 * Per UI_SPEC.md §10.4:
 * - Mute/Unmute
 * - Replay last line
 * - Clear queue
 * - TTS speed slider
 * - Toggle "read my own messages"
 * - Toggle "read phone messages"
 */

import { useState, useEffect } from 'react'
import { ttsService } from '../services/tts'
import './TTSControls.css'

export default function TTSControls() {
  const [isEnabled, setIsEnabled] = useState(false)
  const [isMuted, setIsMuted] = useState(false)
  const [speed, setSpeed] = useState(1.0)
  const [readUserMessages, setReadUserMessages] = useState(false)
  const [readPhoneMessages, setReadPhoneMessages] = useState(false)

  useEffect(() => {
    const state = ttsService.getState()
    setIsEnabled(state.isEnabled)
    setIsMuted(state.isMuted)
    setSpeed(state.speed)
    setReadUserMessages(state.readUserMessages)
    setReadPhoneMessages(state.readPhoneMessages)
  }, [])

  const handleToggleEnabled = () => {
    if (isEnabled) {
      ttsService.disable()
      setIsEnabled(false)
    } else {
      ttsService.enable()
      setIsEnabled(true)
    }
  }

  const handleToggleMute = () => {
    if (isMuted) {
      ttsService.unmute()
      setIsMuted(false)
    } else {
      ttsService.mute()
      setIsMuted(true)
    }
  }

  const handleSpeedChange = (newSpeed: number) => {
    setSpeed(newSpeed)
    ttsService.setSpeed(newSpeed)
  }

  const handleReplay = () => {
    ttsService.replayLast()
  }

  const handleClearQueue = () => {
    ttsService.clearQueue()
  }

  if (!isEnabled) {
    return (
      <div className="tts-controls">
        <button
          className="tts-controls__enable"
          onClick={handleToggleEnabled}
        >
          Enable TTS
        </button>
      </div>
    )
  }

  return (
    <div className="tts-controls">
      <div className="tts-controls__row">
        <button
          className="tts-controls__button"
          onClick={handleToggleMute}
          aria-label={isMuted ? 'Unmute TTS' : 'Mute TTS'}
        >
          {isMuted ? '🔇 Unmute' : '🔊 Mute'}
        </button>
        <button
          className="tts-controls__button"
          onClick={handleReplay}
          aria-label="Replay last line"
        >
          ↻ Replay
        </button>
        <button
          className="tts-controls__button"
          onClick={handleClearQueue}
          aria-label="Clear TTS queue"
        >
          ✕ Clear
        </button>
      </div>
      
      <div className="tts-controls__row">
        <label className="tts-controls__label">
          Speed: {speed.toFixed(1)}x
          <input
            type="range"
            min="0.5"
            max="2.0"
            step="0.1"
            value={speed}
            onChange={(e) => handleSpeedChange(parseFloat(e.target.value))}
            className="tts-controls__slider"
          />
        </label>
      </div>
      
      <div className="tts-controls__row">
        <label className="tts-controls__checkbox">
          <input
            type="checkbox"
            checked={readUserMessages}
            onChange={(e) => {
              setReadUserMessages(e.target.checked)
              ttsService.setReadUserMessages(e.target.checked)
            }}
          />
          Read my own messages
        </label>
        <label className="tts-controls__checkbox">
          <input
            type="checkbox"
            checked={readPhoneMessages}
            onChange={(e) => {
              setReadPhoneMessages(e.target.checked)
              ttsService.setReadPhoneMessages(e.target.checked)
            }}
          />
          Read phone messages
        </label>
      </div>
    </div>
  )
}

