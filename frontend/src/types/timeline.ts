/**
 * Timeline Type Definitions
 * 
 * Per UI_SPEC.md §4:
 * - Timeline is the primary UI surface
 * - Each entry belongs to exactly one type
 * - No numeric psychology exposed
 * - All content from backend renderer
 */

/**
 * Timeline Message Types
 * Per UI_SPEC.md §4.2
 */
export type MessageType =
  | 'perception'      // Renderer descriptions (second-person)
  | 'dialogue'        // Character dialogue
  | 'user_dialogue'   // User's own messages
  | 'system'          // System lines (incursions, notifications)
  | 'phone_echo'      // Phone overlay echo lines

/**
 * Timeline Message
 * Represents a single entry on the timeline
 */
export interface TimelineMessage {
  id: string
  type: MessageType
  timestamp: number  // Unix timestamp in milliseconds
  content: string    // Text content (never modified by UI)
  
  // Optional fields based on type
  speaker?: string   // Character name (for dialogue)
  speakerId?: number // Character ID (for dialogue)
  
  // Metadata (never exposed as numeric psychology)
  metadata?: {
    location?: string
    isIncursion?: boolean
    phoneApp?: string  // For phone_echo type
  }
}

/**
 * Timeline State
 * Manages the complete timeline and UI state
 */
export interface TimelineState {
  messages: TimelineMessage[]
  isLoading: boolean
  isConnected: boolean
  lastMessageId: string | null
  hasMore: boolean  // For pagination
}

/**
 * Scene Flow (Internal, Non-Visible)
 * Per UI_SPEC.md §5
 */
export interface SceneFlow {
  id: string
  startTime: number
  endTime: number | null
  messageIds: string[]
}

