/**
 * TTS Service
 * 
 * Per UI_SPEC.md §10:
 * - Optional text-to-speech
 * - Reads perception blocks and dialogue exactly as written
 * - No summarization, rephrasing, or emotional biasing
 * - Queue model with interruption rules
 * - User controls (mute, replay, speed, toggles)
 */

import { TimelineMessage, MessageType } from '../types/timeline'
import { config } from '../config/env'

export type TTSQueueItem = {
  id: string
  text: string
  type: MessageType
  timestamp: number
  priority: 'high' | 'normal'
  interrupted?: boolean
}

class TTSService {
  private queue: TTSQueueItem[] = []
  private isEnabled: boolean = false
  private isMuted: boolean = false
  private isSpeaking: boolean = false
  private currentUtterance: SpeechSynthesisUtterance | null = null
  private speed: number = 1.0
  private readUserMessages: boolean = false
  private readPhoneMessages: boolean = false

  constructor() {
    this.isEnabled = config.ttsEnabled && 'speechSynthesis' in window
    
    if (this.isEnabled) {
      // Handle speech synthesis events
      if (window.speechSynthesis) {
        // Note: onend is not a standard property, we'll handle it via utterance events
        // This is handled in the speak() method via utterance.onend
      }
    }
  }

  /**
   * Enable TTS
   */
  enable(): void {
    if (!('speechSynthesis' in window)) {
      console.warn('Speech synthesis not available')
      return
    }
    this.isEnabled = true
  }

  /**
   * Disable TTS
   */
  disable(): void {
    this.isEnabled = false
    this.stop()
    this.clearQueue()
  }

  /**
   * Mute TTS (pause without clearing queue)
   */
  mute(): void {
    this.isMuted = true
    this.stop()
  }

  /**
   * Unmute TTS
   */
  unmute(): void {
    this.isMuted = false
    this.processQueue()
  }

  /**
   * Set TTS speed (0.5 to 2.0)
   */
  setSpeed(speed: number): void {
    this.speed = Math.max(0.5, Math.min(2.0, speed))
    if (this.currentUtterance) {
      this.currentUtterance.rate = this.speed
    }
  }

  /**
   * Toggle reading user messages
   */
  setReadUserMessages(enabled: boolean): void {
    this.readUserMessages = enabled
  }

  /**
   * Toggle reading phone messages
   */
  setReadPhoneMessages(enabled: boolean): void {
    this.readPhoneMessages = enabled
  }

  /**
   * Add message to TTS queue
   * Per UI_SPEC.md §10.1, §10.3
   */
  enqueue(message: TimelineMessage): void {
    if (!this.isEnabled || this.isMuted) {
      return
    }

    // Filter based on user preferences
    if (message.type === 'user_dialogue' && !this.readUserMessages) {
      return
    }

    if (message.type === 'phone_echo' && !this.readPhoneMessages) {
      return
    }

    // Determine priority
    const priority: 'high' | 'normal' = 
      message.type === 'system' && message.metadata?.isIncursion
        ? 'high'
        : message.type === 'dialogue'
        ? 'high' // Character dialogue is high priority
        : 'normal'

    const item: TTSQueueItem = {
      id: message.id,
      text: message.content,
      type: message.type,
      timestamp: message.timestamp,
      priority,
    }

    // High priority interrupts
    if (priority === 'high' && this.isSpeaking) {
      this.stop()
      // Mark current item as interrupted
      if (this.queue.length > 0) {
        this.queue[0].interrupted = true
      }
      this.queue.unshift(item) // Add to front
      this.processQueue()
    } else {
      // Normal priority queues
      this.queue.push(item)
      if (!this.isSpeaking) {
        this.processQueue()
      }
    }
  }

  /**
   * Process TTS queue
   */
  private processQueue(): void {
    if (!this.isEnabled || this.isMuted || this.isSpeaking || this.queue.length === 0) {
      return
    }

    const item = this.queue.shift()
    if (!item) {
      return
    }

    this.speak(item.text)
  }

  /**
   * Speak text
   */
  private speak(text: string): void {
    if (!('speechSynthesis' in window)) {
      return
    }

    const utterance = new SpeechSynthesisUtterance(text)
    utterance.rate = this.speed
    utterance.pitch = 1.0
    utterance.volume = 1.0

    utterance.onend = () => {
      this.isSpeaking = false
      this.currentUtterance = null
      this.processQueue()
    }

    utterance.onerror = (error) => {
      console.error('TTS error:', error)
      this.isSpeaking = false
      this.currentUtterance = null
      this.processQueue()
    }

    this.currentUtterance = utterance
    this.isSpeaking = true
    window.speechSynthesis.speak(utterance)
  }

  /**
   * Stop current speech
   */
  stop(): void {
    if (window.speechSynthesis) {
      window.speechSynthesis.cancel()
    }
    this.isSpeaking = false
    this.currentUtterance = null
  }

  /**
   * Clear queue
   */
  clearQueue(): void {
    this.queue = []
    this.stop()
  }

  /**
   * Replay last line (if available)
   */
  replayLast(): void {
    // This would require storing the last spoken item
    // For now, just process queue if available
    if (this.queue.length > 0 && !this.isSpeaking) {
      this.processQueue()
    }
  }

  /**
   * Get current state
   */
  getState() {
    return {
      isEnabled: this.isEnabled,
      isMuted: this.isMuted,
      isSpeaking: this.isSpeaking,
      queueLength: this.queue.length,
      speed: this.speed,
      readUserMessages: this.readUserMessages,
      readPhoneMessages: this.readPhoneMessages,
    }
  }
}

// Export singleton
export const ttsService = new TTSService()

