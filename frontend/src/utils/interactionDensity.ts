/**
 * Interaction Density Utilities
 * 
 * Per UI_SPEC.md §6:
 * - Tracks message rate and participant count
 * - Used to adjust UI pacing (auto-scroll, layout decisions)
 * - Density determines tempo, not tone
 */

import { TimelineMessage } from '../types/timeline'

export interface DensityMetrics {
  messageRate: number  // Messages per minute
  participantCount: number
  densityLevel: 'low' | 'medium' | 'high'
}

/**
 * Calculate interaction density from recent messages
 * Per UI_SPEC.md §6.1, §6.2
 */
export function calculateDensity(
  messages: TimelineMessage[],
  timeWindowMs: number = 60000 // 1 minute
): DensityMetrics {
  if (messages.length === 0) {
    return {
      messageRate: 0,
      participantCount: 0,
      densityLevel: 'low',
    }
  }

  const now = Date.now()
  const windowStart = now - timeWindowMs

  // Filter messages within time window
  const recentMessages = messages.filter(m => m.timestamp >= windowStart)

  // Calculate message rate (messages per minute)
  const messageRate = (recentMessages.length / timeWindowMs) * 60000

  // Count unique participants
  const participants = new Set<string>()
  recentMessages.forEach(m => {
    if (m.speaker) {
      participants.add(m.speaker)
    }
    if (m.type === 'user_dialogue') {
      participants.add('user')
    }
  })
  const participantCount = participants.size

  // Determine density level
  let densityLevel: 'low' | 'medium' | 'high'
  if (messageRate < 2 || participantCount <= 1) {
    densityLevel = 'low'
  } else if (messageRate < 10 || participantCount <= 2) {
    densityLevel = 'medium'
  } else {
    densityLevel = 'high'
  }

  return {
    messageRate,
    participantCount,
    densityLevel,
  }
}

/**
 * Get auto-scroll delay based on density
 * Higher density = faster auto-scroll
 */
export function getAutoScrollDelay(density: DensityMetrics): number {
  switch (density.densityLevel) {
    case 'low':
      return 500 // Slower for low density
    case 'medium':
      return 200
    case 'high':
      return 100 // Faster for high density
    default:
      return 300
  }
}

