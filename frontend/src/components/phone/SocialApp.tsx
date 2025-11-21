/**
 * Social App
 * 
 * Per UI_SPEC.md §12.6:
 * - Text-only social feed
 * - Deterministic (backend-driven)
 * - Never shows images
 * - Never attempts to model real social media visuals
 */

import { useState } from 'react'
import './PhoneApp.css'

interface SocialPost {
  id: string
  author: string
  content: string
  timestamp: number
}

export default function SocialApp() {
  const [posts] = useState<SocialPost[]>([]) // TODO: Load from backend/store

  if (posts.length === 0) {
    return (
      <div className="phone-app">
        <div className="phone-app__empty">
          No posts
        </div>
      </div>
    )
  }

  return (
    <div className="phone-app">
      <div className="phone-app__list">
        {posts.map((post) => (
          <div key={post.id} className="phone-app__post">
            <div className="phone-app__post-author">{post.author}</div>
            <div className="phone-app__post-content">{post.content}</div>
            <div className="phone-app__post-time">
              {new Date(post.timestamp).toLocaleString()}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

