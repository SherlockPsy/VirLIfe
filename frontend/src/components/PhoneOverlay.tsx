/**
 * PhoneOverlay Component
 * 
 * Per UI_SPEC.md §8, §12:
 * - Text-only phone UI
 * - Panel overlay (not fake phone image)
 * - Apps: Messages, Calendar, Email, Notes, Banking, Social, Settings
 * - World events continue in background
 * - Urgent events show inline alert
 * 
 * Per Plan.md Phase 10.5:
 * - Open/close transitions
 * - Dimmed background
 * - Panel layout
 */

import { PhoneApp } from '../types/phone'
import PhoneAppView from './PhoneAppView'
import './PhoneOverlay.css'

interface PhoneOverlayProps {
  isOpen: boolean
  onClose: () => void
  currentApp: PhoneApp | null
  onAppChange: (app: PhoneApp) => void
  unreadCount: number
}

export default function PhoneOverlay({
  isOpen,
  onClose,
  currentApp,
  onAppChange,
  unreadCount,
}: PhoneOverlayProps) {
  const apps: { id: PhoneApp; label: string }[] = [
    { id: 'messages', label: 'Messages' },
    { id: 'calendar', label: 'Calendar' },
    { id: 'email', label: 'Email' },
    { id: 'notes', label: 'Notes' },
    { id: 'banking', label: 'Banking' },
    { id: 'social', label: 'Social' },
    { id: 'settings', label: 'Settings' },
  ]

  if (!isOpen) {
    return null
  }

  return (
    <>
      <div className="phone-overlay__backdrop" onClick={onClose} />
      <div className="phone-overlay">
        <div className="phone-overlay__header">
          <h2 className="phone-overlay__title">Phone</h2>
          <button
            className="phone-overlay__close"
            onClick={onClose}
            aria-label="Close phone"
          >
            ×
          </button>
        </div>
        
        <div className="phone-overlay__content">
          <nav className="phone-overlay__nav">
            {apps.map((app) => (
              <button
                key={app.id}
                className={`phone-overlay__nav-item ${
                  currentApp === app.id ? 'phone-overlay__nav-item--active' : ''
                }`}
                onClick={() => onAppChange(app.id)}
              >
                {app.label}
                {app.id === 'messages' && unreadCount > 0 && (
                  <span className="phone-overlay__badge">{unreadCount}</span>
                )}
              </button>
            ))}
          </nav>
          
          <div className="phone-overlay__app">
            {currentApp ? (
              <PhoneAppView app={currentApp} />
            ) : (
              <div className="phone-overlay__empty">
                Select an app from the menu
              </div>
            )}
          </div>
        </div>
      </div>
    </>
  )
}

