/**
 * Phone Types
 * 
 * Per UI_SPEC.md §12:
 * - Text-only phone overlay
 * - Apps: Messages, Calendar, Email, Notes, Banking, Social, Settings
 */

export type PhoneApp = 
  | 'messages'
  | 'calendar'
  | 'email'
  | 'notes'
  | 'banking'
  | 'social'
  | 'settings'

export interface PhoneMessage {
  id: string
  threadId: string
  sender: string
  senderId: number
  content: string
  timestamp: number
  isRead: boolean
}

export interface PhoneCalendarEvent {
  id: string
  title: string
  description?: string
  startTime: number
  endTime?: number
  location?: string
  participants?: string[]
  isUserEvent: boolean
}

export interface PhoneNotification {
  id: string
  app: PhoneApp
  title: string
  content: string
  timestamp: number
  isRead: boolean
  priority: 'low' | 'normal' | 'high'
}

export interface PhoneState {
  isOpen: boolean
  currentApp: PhoneApp | null
  messages: PhoneMessage[]
  calendarEvents: PhoneCalendarEvent[]
  notifications: PhoneNotification[]
  unreadCount: number
}

