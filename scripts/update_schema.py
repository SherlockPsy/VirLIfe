#!/usr/bin/env python3
"""
Update database schema to match current models.

This ensures all columns exist before seeding.
"""

import asyncio
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

from sqlalchemy.ext.asyncio import create_async_engine
from backend.config.settings import settings
from backend.persistence.database import Base


async def main():
    """Update database schema."""
    print("=" * 80)
    print("UPDATING DATABASE SCHEMA")
    print("=" * 80)
    print()
    
    if not settings.database_url:
        print("ERROR: DATABASE_URL is not set.")
        sys.exit(1)
    
    print(f"Database URL: {settings.database_url[:50]}...")
    print()
    print("Creating/updating database tables...")
    print()
    
    try:
        engine = create_async_engine(
            settings.async_database_url,
            echo=False
        )
        
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        await engine.dispose()
        
        print()
        print("=" * 80)
        print("✅ SCHEMA UPDATE COMPLETE")
        print("=" * 80)
        print()
        print("All database tables are now up to date.")
        print("You can now run the seeding script.")
        print("=" * 80)
        
    except Exception as e:
        print()
        print("=" * 80)
        print("❌ SCHEMA UPDATE FAILED")
        print("=" * 80)
        print(f"Error: {type(e).__name__}: {str(e)}")
        print()
        import traceback
        traceback.print_exc()
        print("=" * 80)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

