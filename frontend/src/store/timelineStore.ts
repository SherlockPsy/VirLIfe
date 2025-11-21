/**
 * Timeline Store (Zustand)
 * 
 * Per Plan.md Phase 10.3:
 * - Central store for timeline state
 * - Appends incoming events
 * - Paginates older messages on demand
 */

import { create } from 'zustand'
import { TimelineMessage } from '../types/timeline'
import { apiClient, wsClient } from '../api/client'

interface TimelineStore {
  messages: TimelineMessage[]
  isLoading: boolean
  isConnected: boolean
  error: string | null
  userId: number | null
  
  // Actions
  setUserId: (userId: number) => void
  addMessage: (message: TimelineMessage) => void
  addMessages: (messages: TimelineMessage[]) => void
  setLoading: (loading: boolean) => void
  setConnected: (connected: boolean) => void
  setError: (error: string | null) => void
  clearMessages: () => void
  
  // Async actions
  loadInitialSnapshot: () => Promise<void>
  sendUserAction: (action: string, utterance?: string) => Promise<void>
  connectWebSocket: () => void
  disconnectWebSocket: () => void
}

export const useTimelineStore = create<TimelineStore>((set, get) => ({
  messages: [],
  isLoading: false,
  isConnected: false,
  error: null,
  userId: null,

  setUserId: (userId: number) => {
    set({ userId })
  },

  addMessage: (message: TimelineMessage) => {
    set((state) => {
      // Avoid duplicates
      if (state.messages.some(m => m.id === message.id)) {
        return state
      }
      
      // Insert in chronological order
      const newMessages = [...state.messages, message].sort(
        (a, b) => a.timestamp - b.timestamp
      )
      
      return { messages: newMessages }
    })
  },

  addMessages: (messages: TimelineMessage[]) => {
    set((state) => {
      const existingIds = new Set(state.messages.map(m => m.id))
      const newMessages = messages.filter(m => !existingIds.has(m.id))
      
      if (newMessages.length === 0) {
        return state
      }
      
      const allMessages = [...state.messages, ...newMessages].sort(
        (a, b) => a.timestamp - b.timestamp
      )
      
      return { messages: allMessages }
    })
  },

  setLoading: (loading: boolean) => {
    set({ isLoading: loading })
  },

  setConnected: (connected: boolean) => {
    set({ isConnected: connected })
  },

  setError: (error: string | null) => {
    set({ error })
  },

  clearMessages: () => {
    set({ messages: [] })
  },

  loadInitialSnapshot: async () => {
    const { userId } = get()
    if (!userId) {
      set({ error: 'User ID not set' })
      return
    }

    set({ isLoading: true, error: null })
    
    try {
      const snapshot = await apiClient.getWorldSnapshot(userId)
      
      const messages: TimelineMessage[] = snapshot.recentMessages.map(
        (msg, index) => ({
          id: `snapshot-${snapshot.timestamp}-${index}`,
          type: msg.type === 'dialogue' ? 'dialogue' :
                msg.type === 'system' ? 'system' : 'perception',
          timestamp: msg.timestamp,
          content: msg.content,
          speaker: msg.speaker,
          speakerId: msg.speakerId,
          metadata: msg.metadata,
        })
      )
      
      set({ messages, isLoading: false })
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to load snapshot'
      set({ error: errorMessage, isLoading: false })
    }
  },

  sendUserAction: async (action: string, utterance?: string) => {
    const { userId } = get()
    if (!userId) {
      set({ error: 'User ID not set' })
      return
    }

    try {
      const response = await apiClient.sendUserAction({
        userId,
        action,
        utterance,
      })
      
      // Add user message to timeline immediately (optimistic update)
      if (utterance) {
        get().addMessage({
          id: `user-${response.timestamp}`,
          type: 'user_dialogue',
          timestamp: response.timestamp,
          content: utterance,
        })
      }
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to send action'
      set({ error: errorMessage })
    }
  },

  connectWebSocket: () => {
    // Subscribe to WebSocket messages
    wsClient.onMessage((message) => {
      get().addMessage(message)
    })
    
    // Subscribe to connection status
    wsClient.onConnectionChange((connected) => {
      get().setConnected(connected)
    })
    
    // Connect
    wsClient.connect()
  },

  disconnectWebSocket: () => {
    wsClient.disconnect()
    set({ isConnected: false })
  },
}))

