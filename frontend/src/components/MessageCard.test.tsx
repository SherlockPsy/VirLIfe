/**
 * MessageCard Component Tests
 * 
 * Per Plan.md Phase 10.2:
 * - Speaker attribution correctness
 * - Type-based styling
 * - All message types render correctly
 */

import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import MessageCard from './MessageCard'
import { TimelineMessage } from '../types/timeline'

describe('MessageCard', () => {
  it('renders perception messages correctly', () => {
    const message: TimelineMessage = {
      id: '1',
      type: 'perception',
      timestamp: Date.now(),
      content: 'You see Rebecca walking through the doorway.',
    }
    
    render(<MessageCard message={message} />)
    expect(screen.getByText(/You see Rebecca walking/)).toBeInTheDocument()
  })

  it('renders dialogue with speaker label', () => {
    const message: TimelineMessage = {
      id: '2',
      type: 'dialogue',
      timestamp: Date.now(),
      speaker: 'Rebecca',
      speakerId: 1,
      content: 'Hello, how are you?',
    }
    
    render(<MessageCard message={message} />)
    expect(screen.getByText('Rebecca:')).toBeInTheDocument()
    expect(screen.getByText(/"Hello, how are you\?"/)).toBeInTheDocument()
  })

  it('renders user dialogue correctly', () => {
    const message: TimelineMessage = {
      id: '3',
      type: 'user_dialogue',
      timestamp: Date.now(),
      content: 'I am doing well, thanks.',
    }
    
    render(<MessageCard message={message} />)
    expect(screen.getByText(/"I am doing well, thanks\."/)).toBeInTheDocument()
  })

  it('renders system messages correctly', () => {
    const message: TimelineMessage = {
      id: '4',
      type: 'system',
      timestamp: Date.now(),
      content: 'A notification appears on your phone.',
    }
    
    render(<MessageCard message={message} />)
    expect(screen.getByText(/A notification appears/)).toBeInTheDocument()
  })

  it('renders phone echo messages correctly', () => {
    const message: TimelineMessage = {
      id: '5',
      type: 'phone_echo',
      timestamp: Date.now(),
      content: 'New message from Lucy',
      metadata: {
        phoneApp: 'Messages',
      },
    }
    
    render(<MessageCard message={message} />)
    expect(screen.getByText('Messages:')).toBeInTheDocument()
    expect(screen.getByText(/New message from Lucy/)).toBeInTheDocument()
  })
})

