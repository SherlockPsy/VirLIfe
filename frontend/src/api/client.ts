/**
 * API Client
 * 
 * Per Plan.md Phase 10.3:
 * - Fetches initial snapshot and recent timeline (HTTP)
 * - Opens WebSocket connection for live events
 * - Handles reconnection logic
 */

import { config } from '../config/env'
import { WorldSnapshot, RenderResponse, UserActionRequest, UserActionResponse } from '../types/api'
import { TimelineMessage } from '../types/timeline'

/**
 * Convert backend RenderResponse to TimelineMessage
 */
function renderResponseToMessage(response: RenderResponse, id: string): TimelineMessage {
  return {
    id,
    type: response.type === 'dialogue' ? 'dialogue' : 
          response.type === 'system' ? 'system' : 'perception',
    timestamp: response.timestamp,
    content: response.content,
    speaker: response.speaker,
    speakerId: response.speakerId,
    metadata: response.metadata,
  }
}

/**
 * HTTP API Client
 */
export class ApiClient {
  private baseUrl: string

  constructor(baseUrl: string = config.backendBaseUrl) {
    this.baseUrl = baseUrl.replace(/\/$/, '') // Remove trailing slash
  }

  /**
   * Fetch world snapshot and recent timeline
   */
  async getWorldSnapshot(userId: number): Promise<WorldSnapshot> {
    const response = await fetch(`${this.baseUrl}/api/v1/render?user_id=${userId}&pov=second_person`)
    
    if (!response.ok) {
      const errorText = await response.text()
      throw new Error(`Failed to fetch world snapshot: ${response.status} ${errorText}`)
    }
    
    const backendData = await response.json()
    
    // Convert backend RenderResponse to frontend format
    // Backend returns: { narrative, visible_agents, visible_objects, current_location_id, world_tick }
    const data: RenderResponse = {
      content: backendData.narrative || 'No narrative available',
      timestamp: Date.now(),
      type: 'perception',
      metadata: {
        location: `location_${backendData.current_location_id}`,
      },
    }
    
    // For now, return a snapshot with a single message
    // TODO: Backend should provide full snapshot endpoint
    return {
      userId,
      currentLocation: `location_${backendData.current_location_id || 'unknown'}`,
      recentMessages: [data],
      timestamp: Date.now(),
    }
  }

  /**
   * Send user action
   */
  async sendUserAction(request: UserActionRequest): Promise<UserActionResponse> {
    // Convert frontend camelCase to backend snake_case
    const backendRequest = {
      user_id: request.userId,
      action_type: request.action,
      text: request.utterance || null,
      target_id: null,
      destination_location_id: null,
    }
    
    const response = await fetch(`${this.baseUrl}/api/v1/user/action`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(backendRequest),
    })
    
    if (!response.ok) {
      const errorText = await response.text()
      throw new Error(`Failed to send user action: ${response.status} ${errorText}`)
    }
    
    const data = await response.json()
    // Convert backend response to frontend format
    return {
      success: data.success,
      message: data.message,
      timestamp: Date.now(), // Backend doesn't return timestamp, use current time
    }
  }

  /**
   * Check backend health
   */
  async healthCheck(): Promise<boolean> {
    try {
      const response = await fetch(`${this.baseUrl}/health`)
      return response.ok
    } catch {
      return false
    }
  }
}

/**
 * WebSocket Client
 * 
 * Per Plan.md Phase 10.3:
 * - Opens WebSocket connection for live events
 * - Handles reconnection logic
 * - Merges missed events on reconnect
 */
export class WebSocketClient {
  private wsUrl: string
  private ws: WebSocket | null = null
  private reconnectAttempts = 0
  private maxReconnectAttempts = 10
  private reconnectDelay = 1000
  private messageHandlers: Set<(message: TimelineMessage) => void> = new Set()
  private connectionHandlers: Set<(connected: boolean) => void> = new Set()
  private isConnecting = false

  constructor(wsUrl: string = config.backendWsUrl) {
    this.wsUrl = wsUrl.replace(/^http/, 'ws').replace(/\/$/, '')
  }

  /**
   * Connect to WebSocket
   */
  connect(): void {
    if (this.ws?.readyState === WebSocket.OPEN || this.isConnecting) {
      return
    }

    this.isConnecting = true
    
    try {
      // For now, connect to /ws endpoint (will be implemented in backend)
      const url = `${this.wsUrl}/ws`
      this.ws = new WebSocket(url)

      this.ws.onopen = () => {
        console.log('WebSocket connected')
        this.reconnectAttempts = 0
        this.isConnecting = false
        this.notifyConnectionHandlers(true)
      }

      this.ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          const message = renderResponseToMessage(data, `ws-${Date.now()}-${Math.random()}`)
          this.notifyMessageHandlers(message)
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error)
        }
      }

      this.ws.onerror = (error) => {
        console.error('WebSocket error:', error)
        this.isConnecting = false
      }

      this.ws.onclose = () => {
        console.log('WebSocket disconnected')
        this.isConnecting = false
        this.notifyConnectionHandlers(false)
        this.attemptReconnect()
      }
    } catch (error) {
      console.error('Failed to create WebSocket connection:', error)
      this.isConnecting = false
      this.attemptReconnect()
    }
  }

  /**
   * Attempt to reconnect
   */
  private attemptReconnect(): void {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error('Max reconnection attempts reached')
      return
    }

    this.reconnectAttempts++
    const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1) // Exponential backoff
    
    console.log(`Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts})...`)
    
    setTimeout(() => {
      this.connect()
    }, delay)
  }

  /**
   * Disconnect WebSocket
   */
  disconnect(): void {
    if (this.ws) {
      this.ws.close()
      this.ws = null
    }
    this.reconnectAttempts = 0
  }

  /**
   * Subscribe to incoming messages
   */
  onMessage(handler: (message: TimelineMessage) => void): () => void {
    this.messageHandlers.add(handler)
    return () => {
      this.messageHandlers.delete(handler)
    }
  }

  /**
   * Subscribe to connection status changes
   */
  onConnectionChange(handler: (connected: boolean) => void): () => void {
    this.connectionHandlers.add(handler)
    return () => {
      this.connectionHandlers.delete(handler)
    }
  }

  /**
   * Notify all message handlers
   */
  private notifyMessageHandlers(message: TimelineMessage): void {
    this.messageHandlers.forEach(handler => {
      try {
        handler(message)
      } catch (error) {
        console.error('Error in message handler:', error)
      }
    })
  }

  /**
   * Notify all connection handlers
   */
  private notifyConnectionHandlers(connected: boolean): void {
    this.connectionHandlers.forEach(handler => {
      try {
        handler(connected)
      } catch (error) {
        console.error('Error in connection handler:', error)
      }
    })
  }

  /**
   * Get current connection status
   */
  isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN
  }
}

// Export singleton instances
export const apiClient = new ApiClient()
export const wsClient = new WebSocketClient()

