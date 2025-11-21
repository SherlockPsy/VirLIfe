/**
 * App Component Tests
 * 
 * Per Plan.md Phase 10.1:
 * - Basic render test for root app component
 * - CI command wired into existing CI
 */

import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import App from './App'

describe('App', () => {
  it('renders without crashing', () => {
    render(<App />)
    expect(screen.getByText('VirLIfe')).toBeInTheDocument()
  })
  
  it('displays the app subtitle', () => {
    render(<App />)
    expect(screen.getByText('Virtual World')).toBeInTheDocument()
  })
})

