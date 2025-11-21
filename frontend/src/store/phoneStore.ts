/**
 * Phone Store (Zustand)
 * 
 * Manages phone overlay state and phone app data
 */

import { create } from 'zustand'
import { PhoneApp, PhoneState, PhoneMessage, PhoneCalendarEvent, PhoneNotification } from '../types/phone'

interface PhoneStore extends PhoneState {
  // Actions
  openPhone: () => void
  closePhone: () => void
  setCurrentApp: (app: PhoneApp | null) => void
  addMessage: (message: PhoneMessage) => void
  addCalendarEvent: (event: PhoneCalendarEvent) => void
  addNotification: (notification: PhoneNotification) => void
  markNotificationRead: (id: string) => void
  clearNotifications: () => void
}

export const usePhoneStore = create<PhoneStore>((set) => ({
  isOpen: false,
  currentApp: null,
  messages: [],
  calendarEvents: [],
  notifications: [],
  unreadCount: 0,

  openPhone: () => {
    set({ isOpen: true })
  },

  closePhone: () => {
    set({ isOpen: false, currentApp: null })
  },

  setCurrentApp: (app: PhoneApp | null) => {
    set({ currentApp: app })
  },

  addMessage: (message: PhoneMessage) => {
    set((state) => ({
      messages: [...state.messages, message].sort((a, b) => a.timestamp - b.timestamp),
    }))
  },

  addCalendarEvent: (event: PhoneCalendarEvent) => {
    set((state) => ({
      calendarEvents: [...state.calendarEvents, event].sort((a, b) => a.startTime - b.startTime),
    }))
  },

  addNotification: (notification: PhoneNotification) => {
    set((state) => {
      const newNotifications = [...state.notifications, notification]
      const unreadCount = newNotifications.filter(n => !n.isRead).length
      return {
        notifications: newNotifications.sort((a, b) => b.timestamp - a.timestamp),
        unreadCount,
      }
    })
  },

  markNotificationRead: (id: string) => {
    set((state) => {
      const updated = state.notifications.map(n =>
        n.id === id ? { ...n, isRead: true } : n
      )
      const unreadCount = updated.filter(n => !n.isRead).length
      return {
        notifications: updated,
        unreadCount,
      }
    })
  },

  clearNotifications: () => {
    set({ notifications: [], unreadCount: 0 })
  },
}))

