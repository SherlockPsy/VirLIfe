/**
 * InputBar Component
 * 
 * Per Plan.md Phase 10.4:
 * - Text entry for user actions/utterances
 * - Send button
 * - Keyboard shortcuts (Enter to send)
 * - Wired to backend
 * 
 * Per UI_SPEC.md:
 * - No rewriting of text
 * - Immediate optimistic echo or conservative echo after backend confirmation
 */

import { useState, KeyboardEvent } from 'react'
import { useTimelineStore } from '../store/timelineStore'
import './InputBar.css'

export default function InputBar() {
  const [input, setInput] = useState('')
  const [isSending, setIsSending] = useState(false)
  const sendUserAction = useTimelineStore((state) => state.sendUserAction)

  const handleSend = async () => {
    if (!input.trim() || isSending) {
      return
    }

    const message = input.trim()
    setInput('')
    setIsSending(true)

    try {
      // Send as utterance (action will be parsed by backend)
      await sendUserAction('speak', message)
      // Success - input already cleared
    } catch (error) {
      console.error('Failed to send message:', error)
      // Restore input on error and show user feedback
      setInput(message)
      
      // Show error to user (could be enhanced with toast notification)
      const errorMessage = error instanceof Error ? error.message : 'Failed to send message'
      alert(`Error: ${errorMessage}`) // TODO: Replace with proper error UI component
    } finally {
      setIsSending(false)
    }
  }

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <div className="input-bar">
      <div className="input-bar__container">
        <textarea
          className="input-bar__input"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Type your message or action..."
          rows={1}
          disabled={isSending}
        />
        <button
          className="input-bar__send"
          onClick={handleSend}
          disabled={!input.trim() || isSending}
          aria-label="Send message"
        >
          {isSending ? '...' : 'Send'}
        </button>
      </div>
      <div className="input-bar__hint">
        Press Enter to send, Shift+Enter for new line
      </div>
    </div>
  )
}

