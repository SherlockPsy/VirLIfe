/**
 * API Type Definitions
 * 
 * Defines interfaces matching backend payloads
 * Per Plan.md Phase 10.3
 */

/**
 * Backend API Response Types
 */
export interface BackendHealthResponse {
  status: string
  environment: string
  database?: string
}

export interface RenderResponse {
  content: string
  timestamp: number
  type: 'perception' | 'dialogue' | 'system'
  speaker?: string
  speakerId?: number
  metadata?: {
    location?: string
    isIncursion?: boolean
  }
}

export interface UserActionRequest {
  userId: number
  action: string
  utterance?: string
}

export interface UserActionResponse {
  success: boolean
  message?: string
  timestamp: number
}

export interface WorldSnapshot {
  userId: number
  currentLocation: string
  recentMessages: RenderResponse[]
  timestamp: number
}

/**
 * WebSocket Message Types
 */
export type WebSocketMessageType =
  | 'timeline_event'
  | 'incursion'
  | 'notification'
  | 'heartbeat'

export interface WebSocketMessage {
  type: WebSocketMessageType
  data: RenderResponse | any
  timestamp: number
}

