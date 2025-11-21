# VirLIfe Frontend - Production README

## Overview

This is the frontend client for the Virtual World system. It provides a text-only, visually rich, emotionally neutral interface that connects to the backend via HTTP and WebSocket.

## Railway Deployment

### Prerequisites

- Railway account
- `virlife-frontend` service created in Railway
- Backend service URL (`virlife-backend-production.up.railway.app`)

### Environment Variables

Set these in your Railway frontend service:

- `VIRLIFE_ENV` = `production`
- `BACKEND_BASE_URL` = `https://virlife-backend-production-xxxx.up.railway.app` (your backend URL)
- `BACKEND_WS_URL` = `wss://virlife-backend-production-xxxx.up.railway.app` (same as above but with `wss://`)
- `TTS_ENABLED` = `false` (or `true` if you want TTS)
- `APP_VERSION` = `1.0.0` (or your version)

**Note:** Vite requires environment variables to be prefixed with `VITE_` at build time. Railway will automatically handle this if you set them without the prefix in the Railway dashboard.

### Build Configuration

Railway will automatically detect:
- **Build Command:** `npm install && npm run build`
- **Start Command:** `npm run preview`
- **Node Version:** 18+ (specified in `.nvmrc`)

### Deployment Steps

1. Connect your GitHub repository to Railway
2. Select the `frontend/` directory as the root (or configure Railway to use it)
3. Set all environment variables
4. Railway will automatically build and deploy

### Verification

After deployment, verify:
- Frontend loads at `https://virlife-frontend-production.up.railway.app`
- Timeline connects to backend
- WebSocket connection establishes
- Input bar sends messages
- Phone overlay opens/closes

## Local Development

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

### Environment Variables (Local)

Create `.env.local`:

```
VITE_BACKEND_BASE_URL=http://localhost:8000
VITE_BACKEND_WS_URL=ws://localhost:8000
VITE_TTS_ENABLED=false
VITE_APP_VERSION=1.0.0
```

### Build

```bash
npm run build
```

Outputs to `dist/` directory.

### Preview Production Build

```bash
npm run preview
```

## Architecture

### Components

- **TimelineView** - Main timeline display
- **MessageCard** - Individual message rendering
- **InputBar** - User input
- **PhoneOverlay** - Phone apps overlay
- **TTSControls** - Text-to-speech controls
- **AccessibilitySettings** - Accessibility options

### State Management

- **Zustand** stores:
  - `timelineStore` - Timeline messages and connection state
  - `phoneStore` - Phone overlay state and app data

### Services

- **ApiClient** - HTTP API communication
- **WebSocketClient** - Real-time event streaming
- **TTSService** - Text-to-speech queue management

## Features

### Core Features

- ✅ Real-time timeline with WebSocket updates
- ✅ User input and actions
- ✅ Phone overlay with apps (Messages, Calendar, Email, Notes, Banking, Social, Settings)
- ✅ Text-to-speech (optional)
- ✅ Accessibility features (font scaling, contrast, keyboard navigation)
- ✅ Scene flow and interaction density handling
- ✅ Connection status and reconnection logic

### Compliance

- ✅ **UI_SPEC.md** - Text-only, neutral, continuous timeline
- ✅ **MASTER_SPEC.md** - No user simulation, no numeric psychology
- ✅ **Architecture.md** - Frontend service structure
- ✅ **Plan.md Phase 10** - All subphases implemented

## Testing

```bash
npm test
```

Tests cover:
- Component rendering
- User interactions
- State management
- API client behavior

## Troubleshooting

### WebSocket Connection Issues

- Verify `BACKEND_WS_URL` is correct (must use `wss://` for HTTPS)
- Check backend WebSocket endpoint is accessible
- Review browser console for connection errors

### Build Failures

- Ensure Node.js 18+ is installed
- Check all dependencies are installed (`npm install`)
- Verify environment variables are set correctly

### Runtime Errors

- Check browser console for errors
- Verify backend is running and accessible
- Check environment variables are loaded correctly

## Support

- **Documentation:** See `UI_SPEC.md`, `MASTER_SPEC.md`, `Architecture.md`
- **Issues:** GitHub Issues
- **Railway Docs:** https://docs.railway.app

