/**
 * PhoneAppView Component
 * 
 * Per UI_SPEC.md §12:
 * - Renders different phone apps
 * - Text-only interfaces
 * - No images, avatars, or graphical elements
 */

import { PhoneApp } from '../types/phone'
import MessagesApp from './phone/MessagesApp'
import CalendarApp from './phone/CalendarApp'
import EmailApp from './phone/EmailApp'
import NotesApp from './phone/NotesApp'
import BankingApp from './phone/BankingApp'
import SocialApp from './phone/SocialApp'
import SettingsApp from './phone/SettingsApp'

interface PhoneAppViewProps {
  app: PhoneApp
}

export default function PhoneAppView({ app }: PhoneAppViewProps) {
  switch (app) {
    case 'messages':
      return <MessagesApp />
    case 'calendar':
      return <CalendarApp />
    case 'email':
      return <EmailApp />
    case 'notes':
      return <NotesApp />
    case 'banking':
      return <BankingApp />
    case 'social':
      return <SocialApp />
    case 'settings':
      return <SettingsApp />
    default:
      return <div>Unknown app</div>
  }
}

