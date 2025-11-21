/**
 * Messages App
 * 
 * Per UI_SPEC.md §12.3:
 * - Text-only thread view
 * - Speaker tags and timestamps
 * - No avatars, stickers, or reaction icons
 */

import { useState } from 'react'
import { PhoneMessage } from '../../types/phone'
import './PhoneApp.css'

export default function MessagesApp() {
  const [messages] = useState<PhoneMessage[]>([]) // TODO: Load from backend/store

  if (messages.length === 0) {
    return (
      <div className="phone-app">
        <div className="phone-app__empty">
          No messages yet
        </div>
      </div>
    )
  }

  return (
    <div className="phone-app">
      <div className="phone-app__list">
        {messages.map((message) => (
          <div key={message.id} className="phone-app__message">
            <div className="phone-app__message-header">
              <span className="phone-app__sender">{message.sender}</span>
              <span className="phone-app__timestamp">
                {new Date(message.timestamp).toLocaleTimeString()}
              </span>
            </div>
            <div className="phone-app__message-content">{message.content}</div>
          </div>
        ))}
      </div>
    </div>
  )
}

