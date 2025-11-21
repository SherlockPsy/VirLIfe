/**
 * Email App
 * 
 * Per UI_SPEC.md §12.5:
 * - Text-only email list
 * - Subject, sender, time, plain-text body
 */

import { useState } from 'react'
import './PhoneApp.css'

interface Email {
  id: string
  subject: string
  sender: string
  timestamp: number
  body: string
}

export default function EmailApp() {
  const [emails] = useState<Email[]>([]) // TODO: Load from backend/store

  if (emails.length === 0) {
    return (
      <div className="phone-app">
        <div className="phone-app__empty">
          No emails
        </div>
      </div>
    )
  }

  return (
    <div className="phone-app">
      <div className="phone-app__list">
        {emails.map((email) => (
          <div key={email.id} className="phone-app__email">
            <div className="phone-app__email-header">
              <div className="phone-app__email-subject">{email.subject}</div>
              <div className="phone-app__email-meta">
                <span>{email.sender}</span>
                <span>{new Date(email.timestamp).toLocaleString()}</span>
              </div>
            </div>
            <div className="phone-app__email-body">{email.body}</div>
          </div>
        ))}
      </div>
    </div>
  )
}

