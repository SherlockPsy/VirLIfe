#!/usr/bin/env python3
"""
Get full database schema from PostgreSQL database.

Usage:
    # Option 1: Set DATABASE_URL environment variable
    export DATABASE_URL="postgresql://user:password@host:port/database"
    python3 scripts/get_schema.py

    # Option 2: Use Railway CLI to get DATABASE_URL
    railway link
    railway variables
    python3 scripts/get_schema.py

    # Option 3: Pass DATABASE_URL as argument
    python3 scripts/get_schema.py "postgresql://user:password@host:port/database"
"""

import asyncio
import sys
import os
from sqlalchemy import text, inspect
from sqlalchemy.ext.asyncio import create_async_engine

async def get_schema(database_url: str):
    """Get full database schema."""
    # Convert postgresql:// to postgresql+asyncpg:// if needed
    if database_url.startswith("postgresql://") and "+asyncpg" not in database_url:
        database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    
    engine = create_async_engine(database_url, echo=False)
    
    try:
        async with engine.begin() as conn:
            # Get all table names
            result = await conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                ORDER BY table_name
            """))
            tables = [row[0] for row in result.fetchall()]
            
            print(f"\n{'='*80}")
            print(f"Database Schema - Found {len(tables)} tables")
            print(f"{'='*80}\n")
            
            for table in tables:
                print(f"\n{'─'*80}")
                print(f"TABLE: {table.upper()}")
                print(f"{'─'*80}")
                
                # Get columns
                result = await conn.execute(text(f"""
                    SELECT 
                        column_name,
                        data_type,
                        character_maximum_length,
                        numeric_precision,
                        numeric_scale,
                        is_nullable,
                        column_default
                    FROM information_schema.columns
                    WHERE table_name = '{table}'
                    ORDER BY ordinal_position
                """))
                columns = result.fetchall()
                
                print("\nColumns:")
                for col in columns:
                    col_name, data_type, max_length, precision, scale, is_nullable, default_val = col
                    
                    # Build type string
                    if max_length:
                        type_str = f"{data_type}({max_length})"
                    elif precision and scale:
                        type_str = f"{data_type}({precision},{scale})"
                    elif precision:
                        type_str = f"{data_type}({precision})"
                    else:
                        type_str = data_type
                    
                    nullable_str = "NULL" if is_nullable == "YES" else "NOT NULL"
                    default_str = f" DEFAULT {default_val}" if default_val else ""
                    
                    print(f"  • {col_name:30} {type_str:25} {nullable_str:10}{default_str}")
                
                # Get primary keys
                result = await conn.execute(text(f"""
                    SELECT column_name
                    FROM information_schema.table_constraints tc
                    JOIN information_schema.key_column_usage kcu
                      ON tc.constraint_name = kcu.constraint_name
                    WHERE tc.table_name = '{table}'
                      AND tc.constraint_type = 'PRIMARY KEY'
                    ORDER BY kcu.ordinal_position
                """))
                pk_columns = [row[0] for row in result.fetchall()]
                if pk_columns:
                    print(f"\n  Primary Key: {', '.join(pk_columns)}")
                
                # Get foreign keys
                result = await conn.execute(text(f"""
                    SELECT
                        kcu.column_name,
                        ccu.table_name AS foreign_table_name,
                        ccu.column_name AS foreign_column_name,
                        tc.constraint_name
                    FROM information_schema.table_constraints AS tc
                    JOIN information_schema.key_column_usage AS kcu
                      ON tc.constraint_name = kcu.constraint_name
                    JOIN information_schema.constraint_column_usage AS ccu
                      ON ccu.constraint_name = tc.constraint_name
                    WHERE tc.constraint_type = 'FOREIGN KEY'
                      AND tc.table_name = '{table}'
                """))
                fks = result.fetchall()
                if fks:
                    print(f"\n  Foreign Keys:")
                    for fk in fks:
                        print(f"    • {fk[0]} → {fk[1]}.{fk[2]}")
                
                # Get indexes
                result = await conn.execute(text(f"""
                    SELECT 
                        indexname,
                        indexdef
                    FROM pg_indexes
                    WHERE tablename = '{table}'
                      AND schemaname = 'public'
                    ORDER BY indexname
                """))
                indexes = result.fetchall()
                if indexes:
                    print(f"\n  Indexes:")
                    for idx in indexes:
                        # Simplify index definition for readability
                        idx_def = idx[1].replace(f"CREATE {idx[0].split('_')[0].upper()} INDEX", "").strip()
                        print(f"    • {idx[0]}: {idx_def}")
                
                # Get row count
                try:
                    result = await conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
                    count = result.scalar()
                    print(f"\n  Row Count: {count}")
                except Exception as e:
                    print(f"\n  Row Count: (error: {e})")
            
            print(f"\n{'='*80}\n")
            
    finally:
        await engine.dispose()


def main():
    # Get DATABASE_URL from:
    # 1. Command line argument
    # 2. Environment variable
    # 3. Railway CLI (if available)
    
    database_url = None
    
    # Check command line argument
    if len(sys.argv) > 1:
        database_url = sys.argv[1]
    # Check environment variable
    elif os.environ.get("DATABASE_URL"):
        database_url = os.environ.get("DATABASE_URL")
    # Try Railway CLI - try multiple approaches
    else:
        try:
            import subprocess
            # Try getting from project level (might work without service linked)
            result = subprocess.run(
                ["railway", "variables", "--output", "json"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0 and result.stdout.strip():
                import json
                try:
                    vars_data = json.loads(result.stdout)
                    if isinstance(vars_data, list):
                        for var in vars_data:
                            if var.get("name") == "DATABASE_URL":
                                database_url = var.get("value")
                                break
                    elif isinstance(vars_data, dict):
                        database_url = vars_data.get("DATABASE_URL")
                except json.JSONDecodeError:
                    # Try parsing as plain text
                    for line in result.stdout.split('\n'):
                        if 'DATABASE_URL' in line:
                            parts = line.split('=', 1)
                            if len(parts) == 2:
                                database_url = parts[1].strip()
                                break
        except Exception as e:
            # Try alternative: check common service names
            try:
                common_services = ["virlife-db", "postgres", "database", "db"]
                for service_name in common_services:
                    result = subprocess.run(
                        ["railway", "variables", "--service", service_name, "--output", "json"],
                        capture_output=True,
                        text=True,
                        timeout=5
                    )
                    if result.returncode == 0 and result.stdout.strip():
                        import json
                        vars_data = json.loads(result.stdout)
                        if isinstance(vars_data, list):
                            for var in vars_data:
                                if var.get("name") == "DATABASE_URL":
                                    database_url = var.get("value")
                                    break
                        if database_url:
                            break
            except Exception:
                pass
    
    if not database_url:
        print("ERROR: DATABASE_URL not found.")
        print("\nPlease provide DATABASE_URL in one of these ways:")
        print("  1. Set environment variable: export DATABASE_URL='postgresql://...'")
        print("  2. Pass as argument: python3 scripts/get_schema.py 'postgresql://...'")
        print("  3. Use Railway CLI: railway link && railway variables")
        print("\nTo get DATABASE_URL from Railway:")
        print("  - Go to Railway dashboard → Your project → Postgres service → Variables")
        print("  - Copy the DATABASE_URL value")
        sys.exit(1)
    
    # Mask password in output
    if "@" in database_url:
        parts = database_url.split("@")
        if len(parts) == 2:
            masked_url = parts[0].split(":")[0] + ":***@" + parts[1]
            print(f"Connecting to: {masked_url}")
    
    asyncio.run(get_schema(database_url))


if __name__ == "__main__":
    main()

