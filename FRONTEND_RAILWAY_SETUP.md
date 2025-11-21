# FRONTEND RAILWAY SETUP INSTRUCTIONS
## For Phase 10 UI Implementation

This guide provides **step-by-step, non-technical instructions** for setting up the frontend Railway service before Phase 10 implementation begins.

---

## OVERVIEW

You need to create a **new Railway service** called `virlife-frontend` in your existing Railway project. This service will host the UI (user interface) that connects to your backend.

**Important:** This is a separate service from your backend. They work together but are deployed separately.

---

## STEP-BY-STEP INSTRUCTIONS

### Step 1: Open Your Railway Project

1. Go to [railway.app](https://railway.app) and log in
2. Find your existing project (the one that has `virlife-backend` and `virlife-db`)
3. Click on that project to open it

### Step 2: Find Your Backend Service URL

Before creating the frontend, you need to know your backend's public URL:

1. In your Railway project, click on the `virlife-backend` service
2. Go to the **"Settings"** tab
3. Scroll down to **"Networking"** or **"Domains"**
4. You should see a public URL like: `https://virlife-backend-production-xxxx.up.railway.app`
5. **Copy this URL** - you'll need it in Step 4

**Note:** If you don't see a public URL, you may need to:
- Click **"Generate Domain"** or **"Add Domain"** to create one
- This makes your backend accessible from the internet (which the frontend needs)

### Step 3: Create the Frontend Service

1. In your Railway project dashboard, click the **"+"** button or **"New"** button
2. Select **"Empty Service"** or **"Deploy from GitHub repo"**
   - If you choose "Deploy from GitHub repo", select your VirLIfe repository
   - If you choose "Empty Service", you'll configure it later
3. Railway will create a new service - **rename it to `virlife-frontend`**
   - Click on the service name and type: `virlife-frontend`

### Step 4: Configure Environment Variables

The frontend needs to know where your backend is located. You'll set this using "Environment Variables":

1. Click on the `virlife-frontend` service
2. Go to the **"Variables"** tab
3. Click **"New Variable"** or **"Add Variable"** for each of these:

#### Required Variables:

**1. VIRLIFE_ENV**
- **Name:** `VIRLIFE_ENV`
- **Value:** `production`
- **Description:** Tells the frontend it's running in production mode

**2. BACKEND_BASE_URL**
- **Name:** `BACKEND_BASE_URL`
- **Value:** The URL you copied in Step 2 (e.g., `https://virlife-backend-production-xxxx.up.railway.app`)
- **Description:** Where the frontend should send HTTP requests to the backend

**3. BACKEND_WS_URL**
- **Name:** `BACKEND_WS_URL`
- **Value:** Same as BACKEND_BASE_URL, but change `https://` to `wss://` (e.g., `wss://virlife-backend-production-xxxx.up.railway.app`)
- **Description:** WebSocket URL for real-time updates (we'll add WebSocket support during Phase 10)

**4. TTS_ENABLED**
- **Name:** `TTS_ENABLED`
- **Value:** `false` (set to `true` later if you want text-to-speech)
- **Description:** Whether to enable text-to-speech features

**5. APP_VERSION**
- **Name:** `APP_VERSION`
- **Value:** `1.0.0` (or any version number you want)
- **Description:** Version identifier for debugging

#### Optional Variables (for later):

**6. TTS_BASE_URL** (only if you have a separate TTS service)
- **Name:** `TTS_BASE_URL`
- **Value:** URL of your TTS service (if applicable)
- **Description:** Only needed if TTS is provided by a separate service

### Step 5: Configure Build Settings (Will be done during Phase 10)

**For now, you can skip this step.** During Phase 10 implementation, we'll configure:
- Build command (e.g., `npm install && npm run build`)
- Start command (e.g., `npm run preview` or `npm start`)
- Node.js version

The frontend service can exist with just the environment variables for now.

### Step 6: Generate a Public Domain (Optional but Recommended)

1. In the `virlife-frontend` service, go to **"Settings"**
2. Scroll to **"Networking"** or **"Domains"**
3. Click **"Generate Domain"** or **"Add Domain"**
4. Railway will create a URL like: `https://virlife-frontend-production-xxxx.up.railway.app`
5. **Copy this URL** - this is where users will access the UI

---

## SUMMARY CHECKLIST

Before Phase 10 implementation can begin, verify you have:

- [ ] Created `virlife-frontend` service in Railway
- [ ] Set `VIRLIFE_ENV` = `production`
- [ ] Set `BACKEND_BASE_URL` = your backend's HTTPS URL
- [ ] Set `BACKEND_WS_URL` = your backend's WSS URL (same as above but with `wss://`)
- [ ] Set `TTS_ENABLED` = `false`
- [ ] Set `APP_VERSION` = `1.0.0` (or your version)
- [ ] (Optional) Generated a public domain for the frontend service

---

## WHAT HAPPENS NEXT

Once you've completed these steps, Phase 10 implementation will:

1. Create the frontend code structure
2. Configure the build and start commands
3. Connect the frontend to your backend using the environment variables you set
4. Deploy the frontend to Railway

---

## TROUBLESHOOTING

### "I can't find my backend URL"
- Make sure your `virlife-backend` service has a public domain
- Go to backend service → Settings → Networking → Generate Domain

### "I don't see the Variables tab"
- Make sure you've clicked on the `virlife-frontend` service first
- The Variables tab should be visible in the service dashboard

### "What if I make a mistake?"
- You can edit or delete environment variables at any time
- Changes take effect on the next deployment

### "Do I need to deploy anything now?"
- No, you can leave the frontend service empty for now
- Phase 10 implementation will add the code and configure deployment

---

## REFERENCE

This setup follows:
- **Architecture.md** §FRONTEND SERVICE (RAILWAY)
- **Plan.md** Phase 10.9 - Railway Deployment for Frontend

---

**Once you've completed these steps, let me know and I'll proceed with Phase 10 implementation!**

