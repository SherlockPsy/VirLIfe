#!/usr/bin/env python3
"""
Add missing is_real_user column to agents table.
"""

import asyncio
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from backend.config.settings import settings


async def main():
    """Add missing column."""
    print("=" * 80)
    print("ADDING MISSING COLUMN: is_real_user")
    print("=" * 80)
    print()
    
    if not settings.database_url:
        print("ERROR: DATABASE_URL is not set.")
        sys.exit(1)
    
    print(f"Database URL: {settings.database_url[:50]}...")
    print()
    print("Adding is_real_user column to agents table...")
    print()
    
    try:
        engine = create_async_engine(
            settings.async_database_url,
            echo=False
        )
        
        async with engine.begin() as conn:
            # Check if column exists
            check_sql = text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='agents' AND column_name='is_real_user'
            """)
            result = await conn.execute(check_sql)
            exists = result.fetchone() is not None
            
            if exists:
                print("Column 'is_real_user' already exists. Skipping.")
            else:
                # Add the column
                alter_sql = text("""
                    ALTER TABLE agents 
                    ADD COLUMN is_real_user BOOLEAN NOT NULL DEFAULT FALSE
                """)
                await conn.execute(alter_sql)
                print("✅ Column 'is_real_user' added successfully.")
        
        await engine.dispose()
        
        print()
        print("=" * 80)
        print("✅ COLUMN ADDED")
        print("=" * 80)
        print()
        print("You can now run the seeding script.")
        print("=" * 80)
        
    except Exception as e:
        print()
        print("=" * 80)
        print("❌ FAILED")
        print("=" * 80)
        print(f"Error: {type(e).__name__}: {str(e)}")
        print()
        import traceback
        traceback.print_exc()
        print("=" * 80)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

