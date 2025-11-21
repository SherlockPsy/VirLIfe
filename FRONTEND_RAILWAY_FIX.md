# Frontend Railway Service Fix

## Problem

The frontend service is crashing because Railway is trying to run the backend Python code instead of the frontend Node.js code. This happens because Railway detects the root `Procfile` which contains the backend command.

## Solution

You need to configure the frontend service to use the `frontend/` directory as its root directory.

## Step-by-Step Fix

### Option 1: Set Root Directory in Railway (RECOMMENDED)

1. Go to your Railway project dashboard
2. Click on the `virlife-frontend` service
3. Go to **"Settings"** tab
4. Scroll down to **"Root Directory"** or **"Source"** section
5. Set the root directory to: `frontend`
6. Save the changes
7. Railway will redeploy automatically

This tells Railway to:
- Use `frontend/` as the working directory
- Look for `package.json` in `frontend/`
- Use the `frontend/Procfile` (which we just created)
- Ignore the root `Procfile`

### Option 2: Use Railway Service Settings

If you don't see a "Root Directory" option:

1. Go to `virlife-frontend` service → **"Settings"**
2. Look for **"Build Command"** and set it to:
   ```
   cd frontend && npm install && npm run build
   ```
3. Look for **"Start Command"** and set it to:
   ```
   cd frontend && npm run preview
   ```
4. Save and redeploy

### Option 3: Create a Separate GitHub Branch/Path (Advanced)

If the above don't work, you can:
1. Create a separate service that points to a specific path
2. Or use Railway's monorepo support if available

## Verification

After applying the fix, check the deployment logs. You should see:
- ✅ `npm install` running (not `pip install`)
- ✅ `npm run build` running
- ✅ `npm run preview` starting the server
- ❌ NO Python/uvicorn errors
- ❌ NO `DATABASE_URL` errors (those are backend-only)

## Expected Logs (Success)

```
[inf] Installing dependencies...
[inf] npm install
[inf] Building frontend...
[inf] npm run build
[inf] Starting preview server...
[inf] npm run preview
[inf] VITE v5.x.x  ready in xxx ms
[inf] ➜  Local:   http://localhost:3000/
```

## If It Still Fails

1. **Check Root Directory**: Make sure it's set to `frontend` (not `/frontend` or `./frontend`)
2. **Check Build Command**: Should be `npm install && npm run build` (or Railway auto-detects from package.json)
3. **Check Start Command**: Should be `npm run preview`
4. **Check Node Version**: Railway should auto-detect from `.nvmrc` (Node 18)
5. **Remove Procfile Detection**: If Railway still uses root Procfile, you may need to explicitly set build/start commands in Railway settings

## Environment Variables

Make sure these are set in the `virlife-frontend` service (NOT the backend service):

- `VIRLIFE_ENV` = `production`
- `BACKEND_BASE_URL` = `https://your-backend-url.up.railway.app`
- `BACKEND_WS_URL` = `wss://your-backend-url.up.railway.app`
- `TTS_ENABLED` = `false`
- `APP_VERSION` = `1.0.0`

**Note:** Vite requires these to be prefixed with `VITE_` at build time, but Railway handles this automatically if you set them without the prefix in the Railway dashboard.

## Quick Checklist

- [ ] Root directory set to `frontend`
- [ ] Build command: `npm install && npm run build` (or auto-detected)
- [ ] Start command: `npm run preview` (or uses frontend/Procfile)
- [ ] Environment variables set in frontend service
- [ ] No Python/backend errors in logs
- [ ] Frontend builds successfully
- [ ] Frontend starts on port 3000

