# Testing Your Production Railway Backend

This guide will help you test your production VirLIfe backend to make sure everything is working correctly.

## Step 1: Find Your Railway Backend URL

1. Go to [railway.app](https://railway.app) and log in
2. Click on your VirLIfe project
3. Click on the `virlife-backend` service
4. Go to the **"Settings"** tab
5. Scroll down to **"Networking"** or **"Domains"** section
6. You should see a URL like: `https://virlife-backend-production-xxxx.up.railway.app`
7. **Copy this URL** - you'll need it for testing

## Step 2: Run the Test Script

I've created a simple test script that will check all the important endpoints.

### Option A: Using the Test Script (Easiest)

1. Open a terminal/command prompt
2. Navigate to your VirLIfe project folder
3. Set your backend URL as an environment variable and run:

```bash
BACKEND_URL="https://your-actual-url.up.railway.app" ./test_production.sh
```

**Or** edit the script first:
1. Open `test_production.sh` in a text editor
2. Find the line: `BACKEND_URL="${BACKEND_URL:-https://virlife-backend-production-xxxx.up.railway.app}"`
3. Replace `https://virlife-backend-production-xxxx.up.railway.app` with your actual URL
4. Save the file
5. Run: `./test_production.sh`

### Option B: Manual Testing with curl

If you prefer to test manually, here are the commands:

#### Test 1: Root Endpoint
```bash
curl https://your-backend-url.up.railway.app/
```

**Expected:** Should return `{"app": "VirLife Backend", "environment": "production", "status": "running"}`

#### Test 2: Basic Health Check
```bash
curl https://your-backend-url.up.railway.app/health
```

**Expected:** Should return `{"status": "ok", "environment": "production", "database": "ok"}`

#### Test 3: Full Health Check
```bash
curl https://your-backend-url.up.railway.app/health/full
```

**Expected:** Should return detailed health status including database, Redis (if configured), Qdrant (if configured), and Venice API

#### Test 4: Gateway Status
```bash
curl https://your-backend-url.up.railway.app/api/v1/status
```

**Expected:** Should return system status with world tick, time, and counts

#### Test 5: World Advance
```bash
curl -X POST https://your-backend-url.up.railway.app/api/v1/world/advance \
  -H "Content-Type: application/json" \
  -d '{"ticks": 1}'
```

**Expected:** Should return `{"ticks_advanced": 1, "world_tick": X, "world_time": "...", "events_generated": X}`

#### Test 6: Render Endpoint
```bash
curl "https://your-backend-url.up.railway.app/api/v1/render?user_id=1&pov=second_person"
```

**Expected:** Should return rendered narrative with visible agents and objects

## What to Look For

### ✅ Good Signs:
- HTTP status codes are **200** (success)
- `/health` shows `"database": "ok"`
- `/health/full` shows all services as "ok" or "not_configured" (if optional)
- No errors about SQLite or local databases
- Responses are valid JSON

### ❌ Problems to Watch For:
- **503 Service Unavailable**: Database might not be connected
- **Connection refused**: Backend might not be deployed or URL is wrong
- **404 Not Found**: Endpoint might not exist
- **500 Internal Server Error**: There might be a code issue
- **Database error messages**: Railway Postgres might not be configured

## Troubleshooting

### "Connection refused" or "DNS resolution failed"
- Make sure your Railway backend service is running
- Check that the URL is correct (copy-paste it directly from Railway)
- Verify you've generated a public domain in Railway settings

### Database errors in `/health`
- Make sure `DATABASE_URL` is set in Railway environment variables
- Verify the Postgres service is linked to your backend service
- Check Railway logs for connection errors

### "VirLife only supports Railway Postgres" error
- This means the Railway-only infrastructure enforcement is working! ✅
- Make sure `DATABASE_URL` is set correctly in Railway

## Testing Railway-Only Infrastructure

The tests should confirm:
1. ✅ No SQLite fallback is being used
2. ✅ Database connection uses Railway Postgres
3. ✅ All services require Railway-provided environment variables

If you see any SQLite-related errors, that means the Railway-only enforcement is working correctly (it's rejecting SQLite).

## Need Help?

If tests fail, check:
1. Railway dashboard → Backend service → Logs (for error messages)
2. Railway dashboard → Backend service → Variables (to verify environment variables)
3. Railway dashboard → Backend service → Settings → Networking (to verify public URL)

