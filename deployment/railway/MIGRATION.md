# Railway Migration Instructions

Per CompleteWork.md Phase 8.

This document covers migrating the VirLIfe backend to Railway deployment.

## Pre-Migration Checklist

- [ ] Code is committed to GitHub
- [ ] All tests pass locally
- [ ] `requirements.txt` is up to date
- [ ] `Procfile` exists and is correct
- [ ] `runtime.txt` specifies Python version (if needed)
- [ ] Environment variables documented

## Migration Steps

### Step 1: Initial Setup

1. Create Railway account
2. Connect GitHub repository
3. Create new Railway project

### Step 2: Database Setup

1. Add Postgres service to Railway project
2. Railway will automatically:
   - Create database
   - Set environment variables
   - Provide connection string

3. Verify database connection:
   ```bash
   # Use Railway CLI or dashboard to check DATABASE_URL
   ```

### Step 3: Environment Configuration

1. Add required environment variables (see `.env.example`)
2. Set `VENICE_API_KEY` and related LLM config
3. Verify all variables are set correctly

### Step 4: Deploy

1. Railway will auto-deploy on push to main
2. Or trigger manual deployment
3. Monitor deployment logs

### Step 5: Database Initialization

The application will automatically:
- Create database tables on startup (via `startup_event` in `main.py`)
- Initialize world state if needed

### Step 6: Verification

1. Test health endpoint:
   ```bash
   curl https://your-app.railway.app/health
   ```

2. Test full health check:
   ```bash
   curl https://your-app.railway.app/health/full
   ```

3. Test API endpoints:
   ```bash
   curl -X POST https://your-app.railway.app/api/v1/world/advance \
     -H "Content-Type: application/json" \
     -d '{"ticks": 1}'
   ```

## Post-Migration

### Monitoring

- Check Railway dashboard for:
  - Service health
  - Resource usage
  - Logs

### Database Backups

Railway Postgres includes automatic backups. Configure backup retention in Railway dashboard.

### Scaling

Railway allows horizontal scaling:
1. Go to service settings
2. Adjust instance count
3. Railway handles load balancing

## Troubleshooting

### Database Connection Errors

**Problem:** Cannot connect to database

**Solutions:**
1. Verify `DATABASE_URL` is set
2. Check Postgres service is running
3. Verify network connectivity
4. Check connection string format

### LLM API Errors

**Problem:** Venice API calls failing

**Solutions:**
1. Verify `VENICE_API_KEY` is correct
2. Check `VENICE_BASE_URL` is correct
3. Verify API key permissions
4. Check API rate limits

### Build Failures

**Problem:** Deployment fails during build

**Solutions:**
1. Check `requirements.txt` for errors
2. Verify Python version in `runtime.txt`
3. Check build logs for specific errors
4. Ensure all dependencies are available

### Runtime Errors

**Problem:** Service crashes after deployment

**Solutions:**
1. Check application logs in Railway dashboard
2. Verify all environment variables are set
3. Check database schema initialization
4. Review error messages in logs

## Rollback Procedure

If deployment fails:

1. Go to Railway dashboard
2. Select previous successful deployment
3. Click "Redeploy"
4. Or revert code changes in GitHub

## Phase 8 Specific Notes

**IMPORTANT:** Per Plan.md Phase 8:

- **NO Redis** - Do not add Redis service yet
- **NO Qdrant** - Do not add Qdrant service yet
- **Postgres ONLY** - Single authoritative data store

These services will be added in Phase 9.

## Next Steps

After successful Phase 8 deployment:

1. Run smoke tests (see `tests/test_phase9_railway_smoke.py`)
2. Verify all endpoints work
3. Test world advancement
4. Test rendering
5. Proceed to Phase 9 (Redis & Qdrant integration)

## Support

- Railway Documentation: https://docs.railway.app
- Railway Discord: https://discord.gg/railway
- Project Issues: GitHub Issues

