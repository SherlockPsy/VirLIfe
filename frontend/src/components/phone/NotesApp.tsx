/**
 * Notes App
 * 
 * Simple text-only notes interface
 */

import { useState } from 'react'
import './PhoneApp.css'

interface Note {
  id: string
  title: string
  content: string
  timestamp: number
}

export default function NotesApp() {
  const [notes] = useState<Note[]>([]) // TODO: Load from backend/store

  if (notes.length === 0) {
    return (
      <div className="phone-app">
        <div className="phone-app__empty">
          No notes
        </div>
      </div>
    )
  }

  return (
    <div className="phone-app">
      <div className="phone-app__list">
        {notes.map((note) => (
          <div key={note.id} className="phone-app__note">
            <div className="phone-app__note-title">{note.title}</div>
            <div className="phone-app__note-content">{note.content}</div>
            <div className="phone-app__note-time">
              {new Date(note.timestamp).toLocaleString()}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

