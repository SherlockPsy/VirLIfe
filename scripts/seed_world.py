#!/usr/bin/env python3
"""
Railway-only seeding script for baseline world.

This script can ONLY be run from within Railway's private environment.
It is NOT exposed as a web endpoint and cannot be accessed over the internet.

Usage (Railway GUI):
1. Railway Dashboard → Your Service → Deployments → Run Command
2. Enter: python scripts/seed_world.py
3. Click Run
4. Wait for confirmation message

WARNING: This will WIPE and re-seed ALL data in the database.
Only run this when you want to reset the world to baseline state.
"""

import asyncio
import sys
import os
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

from sqlalchemy.ext.asyncio import create_async_engine
from backend.config.settings import settings
from backend.seeding.seed_baseline_world import seed_baseline_world


async def main():
    """Main seeding function."""
    print("=" * 80)
    print("VIRLIFE BASELINE WORLD SEEDING")
    print("=" * 80)
    print()
    print("WARNING: This will DELETE all existing data and re-seed the baseline world.")
    print("Only run this when you want to reset everything to baseline state.")
    print()
    
    # Verify we're using Postgres (Railway requirement)
    if not settings.database_url:
        print("ERROR: DATABASE_URL is not set.")
        print("This script requires Railway Postgres. DATABASE_URL must be configured.")
        sys.exit(1)
    
    if settings.database_url.startswith("sqlite"):
        print("ERROR: SQLite is not supported.")
        print("This script requires Railway Postgres. DATABASE_URL must point to Postgres.")
        sys.exit(1)
    
    print(f"Database URL: {settings.database_url[:50]}...")
    print()
    print("Starting seeding process...")
    print()
    
    try:
        # Create engine
        engine = create_async_engine(
            settings.async_database_url,
            echo=False,
            pool_size=5,
            max_overflow=5,
            pool_recycle=3600,
            pool_pre_ping=True
        )
        
        # Run seeding
        await seed_baseline_world(engine)
        
        # Cleanup
        await engine.dispose()
        
        print()
        print("=" * 80)
        print("✅ SEEDING COMPLETE")
        print("=" * 80)
        print()
        print("The baseline world has been successfully seeded with:")
        print("  - World and locations")
        print("  - Agents (George, Rebecca, Lucy, Nadine, and connections)")
        print("  - Relationships")
        print("  - Memories and arcs")
        print("  - Influence fields")
        print("  - Calendars and intentions")
        print()
        print("You can now use the application. The world is ready.")
        print()
        print("⚠️  DO NOT run this script again unless you want to reset everything.")
        print("=" * 80)
        
    except Exception as e:
        print()
        print("=" * 80)
        print("❌ SEEDING FAILED")
        print("=" * 80)
        print(f"Error: {type(e).__name__}: {str(e)}")
        print()
        import traceback
        traceback.print_exc()
        print()
        print("Check Railway logs for more details.")
        print("=" * 80)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

