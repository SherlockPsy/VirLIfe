/**
 * Calendar App
 * 
 * Per UI_SPEC.md §12.4:
 * - Shows upcoming events
 * - Allows creation of user-made events
 * - Allows viewing events involving user or agents
 * - Never generates new events on its own
 */

import { useState } from 'react'
import { PhoneCalendarEvent } from '../../types/phone'
import './PhoneApp.css'

export default function CalendarApp() {
  const [events] = useState<PhoneCalendarEvent[]>([]) // TODO: Load from backend/store

  if (events.length === 0) {
    return (
      <div className="phone-app">
        <div className="phone-app__empty">
          No upcoming events
        </div>
      </div>
    )
  }

  return (
    <div className="phone-app">
      <div className="phone-app__list">
        {events.map((event) => (
          <div key={event.id} className="phone-app__event">
            <div className="phone-app__event-title">{event.title}</div>
            {event.description && (
              <div className="phone-app__event-description">{event.description}</div>
            )}
            <div className="phone-app__event-time">
              {new Date(event.startTime).toLocaleString()}
            </div>
            {event.location && (
              <div className="phone-app__event-location">{event.location}</div>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}

