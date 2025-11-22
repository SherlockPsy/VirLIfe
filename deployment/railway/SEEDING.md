# Database Seeding on Railway

## Overview

The baseline world data (agents, relationships, memories, arcs, etc.) must be seeded after initial deployment. This is done using Railway's **"Run Command"** feature, which executes scripts inside Railway's private environment.

## ⚠️ Current Status

**The database is currently NOT seeded.** You need to run the seeding script once after deployment.

## How to Seed (One-Click via Railway GUI)

### Step 1: Open Railway Dashboard

1. Go to [Railway Dashboard](https://railway.app)
2. Select your **VirLIfe project**
3. Click on your **backend service** (e.g., `virlife-backend`)

### Step 2: Run the Seeding Command

1. Click on the **"Deployments"** tab
2. Click the **"Run Command"** button
3. In the command field, type:
   ```
   python scripts/seed_world.py
   ```
4. Click **"Run"**

### Step 3: Wait for Completion

The script will:
- Print progress messages
- Show what's being seeded
- Display a confirmation when complete: `✅ SEEDING COMPLETE`

### Step 4: Verify

Check the output for:
- ✅ "SEEDING COMPLETE" message
- ✅ List of seeded entities (agents, relationships, memories, etc.)
- ✅ No error messages

## What Gets Seeded

The seed script creates:

- ✅ **World**: Baseline world with initial time
- ✅ **Locations**: All Cookridge house rooms and areas (Kitchen, Lounge, Our Bedroom, Studio, etc.)
- ✅ **Objects**: Key objects (guitars, furniture, etc.)
- ✅ **Agents**: 
  - George (real user, no internal state)
  - Rebecca Ferguson (full personality, drives, mood, memories, arcs)
  - Lucy (daughter)
  - Nadine (ex-partner)
  - Other connections from CSV
- ✅ **Relationships**: All relationship vectors (especially Rebecca → George override)
- ✅ **Memories**: Rebecca's episodic and biographical memories (>10 memories)
- ✅ **Arcs**: Rebecca's active life arcs (fame/private balance, relationship secrecy, etc.)
- ✅ **Influence Fields**: Unresolved topics and background biases
- ✅ **Calendars**: Agent schedules and obligations
- ✅ **Intentions**: Initial intentions for non-George agents

## ⚠️ Important Warnings

### This Script WIPES All Data

The seeding script uses **STRATEGY 1: Wipe-and-Reseed**:
- **It will DELETE ALL EXISTING DATA** before seeding
- This ensures a clean, deterministic baseline world
- **DO NOT run this on a production database with user data unless you intend to reset everything**

### When to Run

✅ **Run ONCE** after initial deployment  
✅ **Run** when you intentionally want to reset to baseline  
❌ **NEVER run** if you have user data you want to keep  
❌ **NEVER run** unless you understand it will delete everything

## Security

The seeding script is:
- ✅ **Private**: Only runs inside Railway's private environment
- ✅ **Not exposed**: No web endpoint exists
- ✅ **Safe**: Cannot be accessed over the internet
- ✅ **Simple**: No secrets, API keys, or CLI knowledge required

## Troubleshooting

### Script fails with "DATABASE_URL is not set"
- Check that Railway Postgres service is running
- Verify `DATABASE_URL` environment variable exists (Railway sets this automatically)

### Script fails with "SQLite is not supported"
- Ensure you're using Railway Postgres, not SQLite
- Check that `DATABASE_URL` points to Postgres

### Seeding appears to hang
- Check Railway logs for detailed progress
- The seeding process can take 30-60 seconds
- Wait for the completion message

### Data not appearing after seeding
- Check Railway logs for any errors
- Verify the script completed successfully
- Re-run the script if needed (remember: it will wipe existing data)

## Verification Checklist

After seeding, verify:

- [ ] Script output shows "✅ SEEDING COMPLETE"
- [ ] No error messages in output
- [ ] World row exists with name "George_Baseline_World"
- [ ] George agent exists with `is_real_user = True` and **NO** internal psychological fields
- [ ] Rebecca agent exists with full personality_kernel, drives, mood, memories, arcs
- [ ] Relationships exist (especially Rebecca → George with high warmth/trust)
- [ ] Memories exist for Rebecca (check count > 10)
- [ ] Arcs exist for Rebecca (check count >= 2)
- [ ] Locations exist (Kitchen, Lounge, Our Bedroom, Studio, etc.)

## Next Steps

Once seeding is complete:
1. ✅ Database is ready for production use
2. ✅ All baseline world data is in place
3. ✅ System can start processing user actions
4. ✅ PFEE cycles can run with seeded agent data

## Technical Details

The seeding script (`scripts/seed_world.py`):
- Uses the same `seed_baseline_world()` function as the test suite
- Runs inside Railway's container with access to `DATABASE_URL`
- Cannot be accessed from outside Railway's environment
- Implements Section B of `SIMULATION_IMPLEMENTATION_BLUEPRINT_v1.md`
