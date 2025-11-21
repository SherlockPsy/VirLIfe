/**
 * ConnectionStatus Component
 * 
 * Per Plan.md Phase 10.3:
 * - Shows WebSocket connection status
 * - Displays reconnection banner when disconnected
 * - Neutral, unobtrusive styling
 */

import './ConnectionStatus.css'

interface ConnectionStatusProps {
  isConnected: boolean
  error: string | null
}

export default function ConnectionStatus({ isConnected, error }: ConnectionStatusProps) {
  if (error) {
    return (
      <div className="connection-status connection-status--error">
        Error: {error}
      </div>
    )
  }

  if (!isConnected) {
    return (
      <div className="connection-status connection-status--disconnected">
        Reconnecting...
      </div>
    )
  }

  return null
}

