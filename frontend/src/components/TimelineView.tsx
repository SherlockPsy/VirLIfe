/**
 * TimelineView Component
 * 
 * Per UI_SPEC.md §4:
 * - Primary UI surface
 * - Displays all messages
 * - Supports scrollback
 * - Auto-scroll when at bottom
 * - Pauses auto-scroll when user scrolls up
 * 
 * Per Plan.md Phase 10.2:
 * - Initially uses mock data
 * - Will connect to backend in Phase 10.3
 */

import { useEffect, useRef, useState } from 'react'
import { TimelineMessage } from '../types/timeline'
import { calculateDensity, getAutoScrollDelay } from '../utils/interactionDensity'
import MessageCard from './MessageCard'
import './TimelineView.css'

interface TimelineViewProps {
  messages: TimelineMessage[]
  isLoading?: boolean
}

export default function TimelineView({ messages, isLoading = false }: TimelineViewProps) {
  const timelineRef = useRef<HTMLDivElement>(null)
  const [isAtBottom, setIsAtBottom] = useState(true)
  const [userHasScrolled, setUserHasScrolled] = useState(false)

  // Calculate density for auto-scroll timing
  const density = calculateDensity(messages)
  const autoScrollDelay = getAutoScrollDelay(density)

  // Auto-scroll to bottom when new messages arrive (if user is at bottom)
  // Per UI_SPEC.md §6: Adjust timing based on density
  useEffect(() => {
    if (timelineRef.current && isAtBottom && !userHasScrolled) {
      // Use density-based delay for smoother experience
      const timeoutId = setTimeout(() => {
        if (timelineRef.current) {
          timelineRef.current.scrollTop = timelineRef.current.scrollHeight
        }
      }, autoScrollDelay)

      return () => clearTimeout(timeoutId)
    }
  }, [messages, isAtBottom, userHasScrolled, autoScrollDelay])

  // Check if user is at bottom of timeline
  const handleScroll = () => {
    if (!timelineRef.current) return

    const { scrollTop, scrollHeight, clientHeight } = timelineRef.current
    const distanceFromBottom = scrollHeight - scrollTop - clientHeight
    
    // Consider "at bottom" if within 50px
    const atBottom = distanceFromBottom < 50
    setIsAtBottom(atBottom)
    
    // If user scrolls up, mark as scrolled
    if (!atBottom) {
      setUserHasScrolled(true)
    } else if (atBottom && userHasScrolled) {
      // Reset when user scrolls back to bottom
      setUserHasScrolled(false)
    }
  }

  return (
    <div className="timeline-view">
      <div
        ref={timelineRef}
        className="timeline-view__container"
        onScroll={handleScroll}
      >
        {isLoading && messages.length === 0 && (
          <div className="timeline-view__loading">Loading timeline...</div>
        )}
        
        {messages.length === 0 && !isLoading && (
          <div className="timeline-view__empty">
            No messages yet. The world is quiet.
          </div>
        )}
        
        {messages.map((message) => (
          <MessageCard key={message.id} message={message} />
        ))}
        
        {!isAtBottom && (
          <div className="timeline-view__scroll-indicator">
            New messages below
          </div>
        )}
      </div>
    </div>
  )
}

