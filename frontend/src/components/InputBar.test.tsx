/**
 * InputBar Component Tests
 * 
 * Per Plan.md Phase 10.4:
 * - User input sends correct payload
 * - Messages appear in timeline
 * - Failure handling
 */

import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import InputBar from './InputBar'
import { useTimelineStore } from '../store/timelineStore'

// Mock the store
vi.mock('../store/timelineStore', () => ({
  useTimelineStore: vi.fn(),
}))

describe('InputBar', () => {
  const mockSendUserAction = vi.fn()

  beforeEach(() => {
    vi.mocked(useTimelineStore).mockReturnValue({
      sendUserAction: mockSendUserAction,
    } as any)
    mockSendUserAction.mockResolvedValue(undefined)
  })

  afterEach(() => {
    vi.clearAllMocks()
  })

  it('renders input and send button', () => {
    render(<InputBar />)
    expect(screen.getByPlaceholderText(/Type your message/)).toBeInTheDocument()
    expect(screen.getByText('Send')).toBeInTheDocument()
  })

  it('sends message when send button is clicked', async () => {
    render(<InputBar />)
    const input = screen.getByPlaceholderText(/Type your message/)
    const sendButton = screen.getByText('Send')

    fireEvent.change(input, { target: { value: 'Hello, world!' } })
    fireEvent.click(sendButton)

    await waitFor(() => {
      expect(mockSendUserAction).toHaveBeenCalledWith('speak', 'Hello, world!')
    })
  })

  it('sends message when Enter is pressed', async () => {
    render(<InputBar />)
    const input = screen.getByPlaceholderText(/Type your message/)

    fireEvent.change(input, { target: { value: 'Test message' } })
    fireEvent.keyDown(input, { key: 'Enter', shiftKey: false })

    await waitFor(() => {
      expect(mockSendUserAction).toHaveBeenCalledWith('speak', 'Test message')
    })
  })

  it('does not send empty messages', () => {
    render(<InputBar />)
    const sendButton = screen.getByText('Send')

    expect(sendButton).toBeDisabled()
  })
})

