# VirLIfe Frontend

Virtual World UI - Text-only, visually rich, emotionally neutral interface.

## Overview

This is the frontend client for the Virtual World system. It provides a text-only, visually rich interface that:

- Displays a continuous timeline of world events
- Supports real-time updates via WebSocket
- Maintains emotional neutrality (no biasing, no modes)
- Treats all interactions (intimate, conflict, mundane) equally
- Never simulates user internal state
- Never exposes numeric psychology

## Tech Stack

- **React 18** - UI framework
- **TypeScript** - Type safety
- **Vite** - Build tool and dev server
- **Zustand** - State management
- **Vitest** - Testing framework

## Development

### Prerequisites

- Node.js 18+ 
- npm or pnpm

### Setup

```bash
cd frontend
npm install
```

### Development Server

```bash
npm run dev
```

Opens at `http://localhost:3000`

### Build

```bash
npm run build
```

Outputs to `dist/` directory.

### Preview Production Build

```bash
npm run preview
```

### Tests

```bash
npm test
```

## Environment Variables

The frontend reads these environment variables at build time:

- `VITE_BACKEND_BASE_URL` - Backend HTTP API URL
- `VITE_BACKEND_WS_URL` - Backend WebSocket URL
- `VITE_TTS_ENABLED` - Enable/disable TTS (true/false)
- `VITE_APP_VERSION` - App version string

For Railway deployment, these are set via Railway environment variables (without the `VITE_` prefix).

## Architecture

Per UI_SPEC.md and Plan.md Phase 10:

- **Timeline View** - Primary UI surface showing all events
- **Input Bar** - User action/utterance input
- **Phone Overlay** - In-world phone apps (messages, calendar, etc.)
- **TTS Integration** - Optional text-to-speech
- **State Management** - Zustand store for timeline and UI state

## Compliance

This frontend strictly adheres to:

- **UI_SPEC.md** - Complete UI specification
- **MASTER_SPEC.md** - World model and constraints
- **Architecture.md** - Deployment and integration rules
- **Plan.md Phase 10** - Implementation order

## License

Same as main project.

