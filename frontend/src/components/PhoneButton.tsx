/**
 * PhoneButton Component
 * 
 * Button to open the phone overlay
 * Shows unread notification count badge
 */

import { usePhoneStore } from '../store/phoneStore'
import './PhoneButton.css'

export default function PhoneButton() {
  const { isOpen, openPhone, unreadCount } = usePhoneStore()

  if (isOpen) {
    return null
  }

  return (
    <button
      className="phone-button"
      onClick={openPhone}
      aria-label="Open phone"
    >
      Phone
      {unreadCount > 0 && (
        <span className="phone-button__badge">{unreadCount}</span>
      )}
    </button>
  )
}

