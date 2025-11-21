/**
 * Main App Component
 * 
 * Per Plan.md Phase 10.3, 10.4:
 * - Connects to backend via HTTP and WebSocket
 * - Uses timeline store for state management
 * - Includes InputBar for user actions
 * - Handles reconnection logic
 * 
 * Per UI_SPEC.md:
 * - No user simulation
 * - No numeric psychology exposure
 * - Neutral, continuous, real-time UI
 */

import { useEffect } from 'react'
import TimelineView from './components/TimelineView'
import InputBar from './components/InputBar'
import ConnectionStatus from './components/ConnectionStatus'
import PhoneOverlay from './components/PhoneOverlay'
import PhoneButton from './components/PhoneButton'
import TTSControls from './components/TTSControls'
import AccessibilitySettings from './components/AccessibilitySettings'
import { useTimelineStore } from './store/timelineStore'
import { usePhoneStore } from './store/phoneStore'
import { ttsService } from './services/tts'
import './App.css'

function App() {
  const {
    messages,
    isLoading,
    isConnected,
    error,
    userId,
    setUserId,
    loadInitialSnapshot,
    connectWebSocket,
    disconnectWebSocket,
  } = useTimelineStore()

  // Initialize: Set user ID (for now, hardcoded to 1; will be from auth later)
  useEffect(() => {
    if (!userId) {
      setUserId(1) // TODO: Get from authentication
    }
  }, [userId, setUserId])

  // Load initial snapshot when user ID is set
  useEffect(() => {
    if (userId) {
      loadInitialSnapshot()
    }
  }, [userId, loadInitialSnapshot])

  // Connect WebSocket when component mounts
  useEffect(() => {
    connectWebSocket()
    
    return () => {
      disconnectWebSocket()
    }
  }, [connectWebSocket, disconnectWebSocket])

  // Subscribe to timeline messages for TTS
  useEffect(() => {
    const unsubscribe = useTimelineStore.subscribe(
      (state) => state.messages,
      (messages) => {
        // Enqueue latest message for TTS
        if (messages.length > 0) {
          const latestMessage = messages[messages.length - 1]
          ttsService.enqueue(latestMessage)
        }
      }
    )
    
    return unsubscribe
  }, [])

  const {
    isOpen: isPhoneOpen,
    currentApp,
    unreadCount,
    openPhone,
    closePhone,
    setCurrentApp,
  } = usePhoneStore()

  return (
    <div className="app">
      <header className="app-header">
        <h1>VirLIfe</h1>
        <p className="app-subtitle">Virtual World</p>
        <ConnectionStatus isConnected={isConnected} error={error} />
      </header>
      <main className="app-main">
        <TimelineView messages={messages} isLoading={isLoading} />
        <TTSControls />
        <InputBar />
      </main>
      <PhoneButton />
      <AccessibilitySettings />
      <PhoneOverlay
        isOpen={isPhoneOpen}
        onClose={closePhone}
        currentApp={currentApp}
        onAppChange={setCurrentApp}
        unreadCount={unreadCount}
      />
    </div>
  )
}

export default App
