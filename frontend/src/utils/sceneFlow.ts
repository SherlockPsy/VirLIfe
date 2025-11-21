/**
 * Scene Flow Utilities
 * 
 * Per UI_SPEC.md §5:
 * - Internal, non-visible construct for continuity and pacing
 * - Used for auto-scroll and grouping
 * - Never labeled visibly
 * - Never imposes themes
 */

import { TimelineMessage } from '../types/timeline'

export interface SceneFlow {
  id: string
  startTime: number
  endTime: number | null
  messageIds: string[]
  location?: string
}

/**
 * Detect scene flow boundaries
 * Per UI_SPEC.md §5.1
 */
export function detectSceneFlow(messages: TimelineMessage[]): SceneFlow[] {
  if (messages.length === 0) {
    return []
  }

  const flows: SceneFlow[] = []
  let currentFlow: SceneFlow | null = null

  for (const message of messages) {
    const isNewScene = 
      // Location change
      (currentFlow?.location && message.metadata?.location && 
       currentFlow.location !== message.metadata.location) ||
      // Major incursion
      (message.type === 'system' && message.metadata?.isIncursion) ||
      // Extended interaction start (heuristic: long dialogue sequence)
      (message.type === 'dialogue' && currentFlow && 
       currentFlow.messageIds.length > 10)

    if (isNewScene && currentFlow) {
      // End current flow
      currentFlow.endTime = message.timestamp
      flows.push(currentFlow)
      currentFlow = null
    }

    if (!currentFlow || isNewScene) {
      // Start new flow
      currentFlow = {
        id: `scene-${message.timestamp}`,
        startTime: message.timestamp,
        endTime: null,
        messageIds: [message.id],
        location: message.metadata?.location,
      }
    } else {
      // Continue current flow
      currentFlow.messageIds.push(message.id)
      if (message.metadata?.location) {
        currentFlow.location = message.metadata.location
      }
    }
  }

  // Add final flow if exists
  if (currentFlow) {
    flows.push(currentFlow)
  }

  return flows
}

/**
 * Get current active scene flow
 */
export function getCurrentSceneFlow(flows: SceneFlow[]): SceneFlow | null {
  return flows.find(flow => flow.endTime === null) || flows[flows.length - 1] || null
}

