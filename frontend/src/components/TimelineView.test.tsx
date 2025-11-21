/**
 * TimelineView Component Tests
 * 
 * Per Plan.md Phase 10.2:
 * - Scroll behavior (auto-scroll only when at bottom)
 * - Message rendering
 * - Empty state handling
 */

import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import TimelineView from './TimelineView'
import { TimelineMessage } from '../types/timeline'

describe('TimelineView', () => {
  it('renders empty state when no messages', () => {
    render(<TimelineView messages={[]} />)
    expect(screen.getByText(/No messages yet/)).toBeInTheDocument()
  })

  it('renders loading state', () => {
    render(<TimelineView messages={[]} isLoading={true} />)
    expect(screen.getByText(/Loading timeline/)).toBeInTheDocument()
  })

  it('renders messages correctly', () => {
    const messages: TimelineMessage[] = [
      {
        id: '1',
        type: 'perception',
        timestamp: Date.now(),
        content: 'Test perception message',
      },
      {
        id: '2',
        type: 'dialogue',
        timestamp: Date.now(),
        speaker: 'Rebecca',
        speakerId: 1,
        content: 'Test dialogue',
      },
    ]
    
    render(<TimelineView messages={messages} />)
    expect(screen.getByText(/Test perception message/)).toBeInTheDocument()
    expect(screen.getByText(/Test dialogue/)).toBeInTheDocument()
  })
})

