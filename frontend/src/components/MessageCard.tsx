/**
 * MessageCard Component
 * 
 * Per UI_SPEC.md §4.2, §11:
 * - Renders a single timeline message
 * - Supports all message types
 * - Emotionally neutral styling
 * - Clear speaker attribution
 */

import { TimelineMessage, MessageType } from '../types/timeline'
import './MessageCard.css'

interface MessageCardProps {
  message: TimelineMessage
}

export default function MessageCard({ message }: MessageCardProps) {
  const getCardClassName = (type: MessageType): string => {
    const base = 'message-card'
    return `${base} ${base}--${type}`
  }

  const renderContent = () => {
    switch (message.type) {
      case 'perception':
        return (
          <div className="message-card__content message-card__content--perception">
            {message.content}
          </div>
        )
      
      case 'dialogue':
        return (
          <div className="message-card__content message-card__content--dialogue">
            {message.speaker && (
              <div className="message-card__speaker">{message.speaker}:</div>
            )}
            <div className="message-card__text">"{message.content}"</div>
          </div>
        )
      
      case 'user_dialogue':
        return (
          <div className="message-card__content message-card__content--user">
            <div className="message-card__text">"{message.content}"</div>
          </div>
        )
      
      case 'system':
        return (
          <div className="message-card__content message-card__content--system">
            {message.content}
          </div>
        )
      
      case 'phone_echo':
        return (
          <div className="message-card__content message-card__content--phone">
            {message.metadata?.phoneApp && (
              <span className="message-card__phone-label">
                {message.metadata.phoneApp}:
              </span>
            )}
            {message.content}
          </div>
        )
      
      default:
        return <div className="message-card__content">{message.content}</div>
    }
  }

  return (
    <div className={getCardClassName(message.type)}>
      {renderContent()}
      <div className="message-card__timestamp">
        {new Date(message.timestamp).toLocaleTimeString()}
      </div>
    </div>
  )
}

