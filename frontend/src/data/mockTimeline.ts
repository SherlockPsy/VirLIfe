/**
 * Mock Timeline Data
 * 
 * Per Plan.md Phase 10.2:
 * - Static mock data for initial development
 * - Tests multi-character scenes
 * - Tests interleaved perception and dialogue
 * - Tests long sequences
 */

import { TimelineMessage } from '../types/timeline'

export const mockTimelineMessages: TimelineMessage[] = [
  {
    id: '1',
    type: 'perception',
    timestamp: Date.now() - 300000,
    content: 'You step into the living room. The afternoon light filters through the windows, casting long shadows across the floor.',
  },
  {
    id: '2',
    type: 'dialogue',
    timestamp: Date.now() - 280000,
    speaker: 'Rebecca',
    speakerId: 1,
    content: 'Hey, you\'re back. How was your day?',
  },
  {
    id: '3',
    type: 'user_dialogue',
    timestamp: Date.now() - 270000,
    content: 'It was good, thanks. Just a regular day at work.',
  },
  {
    id: '4',
    type: 'perception',
    timestamp: Date.now() - 260000,
    content: 'Rebecca nods and moves to the kitchen. You hear the sound of water running.',
  },
  {
    id: '5',
    type: 'dialogue',
    timestamp: Date.now() - 250000,
    speaker: 'Rebecca',
    speakerId: 1,
    content: 'I was thinking we could order Thai tonight. Sound good?',
  },
  {
    id: '6',
    type: 'system',
    timestamp: Date.now() - 240000,
    content: 'A notification appears on your phone.',
    metadata: {
      isIncursion: true,
    },
  },
  {
    id: '7',
    type: 'phone_echo',
    timestamp: Date.now() - 235000,
    content: 'New message from Lucy',
    metadata: {
      phoneApp: 'Messages',
    },
  },
  {
    id: '8',
    type: 'user_dialogue',
    timestamp: Date.now() - 230000,
    content: 'Thai sounds perfect. Let me check this message first.',
  },
  {
    id: '9',
    type: 'perception',
    timestamp: Date.now() - 220000,
    content: 'Rebecca smiles and continues preparing something in the kitchen. The room feels calm, comfortable.',
  },
  {
    id: '10',
    type: 'dialogue',
    timestamp: Date.now() - 210000,
    speaker: 'Rebecca',
    speakerId: 1,
    content: 'Take your time. I\'ll be here when you\'re ready.',
  },
]

