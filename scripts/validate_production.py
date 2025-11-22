#!/usr/bin/env python3
"""
Production Validation Script - READ-ONLY

This script performs comprehensive validation of the production Railway database
without modifying any data. All queries are SELECT-only.
"""

import asyncio
import sys
import os
from pathlib import Path
from typing import Dict, Any, List

# Add backend to path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, func, text
from backend.config.settings import Settings
from backend.persistence.models import (
    WorldModel, LocationModel, ObjectModel, AgentModel,
    RelationshipModel, MemoryModel, ArcModel,
    InfluenceFieldModel, CalendarModel, IntentionModel
)
from backend.persistence.database import Base


# PRODUCTION DATABASE URL (from user's earlier message)
PRODUCTION_DB_URL = "postgresql://postgres:rUaCGawjVEoluMBJZzZgAerZfKPmTbQu@interchange.proxy.rlwy.net:50418/railway"


def redact_url(url: str) -> str:
    """Redact credentials from database URL."""
    if "@" in url:
        parts = url.split("@")
        if "://" in parts[0]:
            protocol_user = parts[0].split("://")
            if ":" in protocol_user[1]:
                user_pass = protocol_user[1].split(":")
                redacted = f"{protocol_user[0]}://{user_pass[0]}:****@{parts[1]}"
            else:
                redacted = f"{protocol_user[0]}://****@{parts[1]}"
        else:
            redacted = f"****@{parts[1]}"
    else:
        redacted = url
    return redacted


async def phase_1_environment_identification():
    """PHASE 1: Identify production environment."""
    print("=" * 80)
    print("PHASE 1: ENVIRONMENT & DB IDENTIFICATION")
    print("=" * 80)
    print()
    print("Production Configuration:")
    print(f"  - Railway Project: Virtual Life")
    print(f"  - Environment: production")
    print(f"  - Database URL: {redact_url(PRODUCTION_DB_URL)}")
    print(f"  - Database Type: PostgreSQL (Railway)")
    print()
    print("Validation Mode:")
    print("  - READ-ONLY SQL queries only (SELECT)")
    print("  - Normal API calls via /api/v1/user/action endpoint")
    print("  - NO writes, NO schema changes, NO data modifications")
    print()
    print("=" * 80)
    print()


async def phase_2_raw_data_integrity(session: AsyncSession):
    """PHASE 2: Raw data integrity checks (read-only)."""
    print("=" * 80)
    print("PHASE 2: RAW DATA INTEGRITY (READ-ONLY)")
    print("=" * 80)
    print()
    
    # 2.1 Counts
    print("2.1 TABLE COUNTS:")
    print("-" * 80)
    
    counts = {}
    
    # Worlds
    stmt = select(func.count(WorldModel.id))
    result = await session.execute(stmt)
    counts["worlds"] = result.scalar()
    print(f"  worlds: {counts['worlds']} (expected: 1)")
    
    # Locations
    stmt = select(func.count(LocationModel.id))
    result = await session.execute(stmt)
    counts["locations"] = result.scalar()
    print(f"  locations: {counts['locations']} (expected: ~17 from baseline)")
    
    # Objects
    stmt = select(func.count(ObjectModel.id))
    result = await session.execute(stmt)
    counts["objects"] = result.scalar()
    print(f"  objects: {counts['objects']} (expected: ~4 from baseline)")
    
    # Agents
    stmt = select(func.count(AgentModel.id))
    result = await session.execute(stmt)
    counts["agents"] = result.scalar()
    print(f"  agents: {counts['agents']} (expected: 4 core + supporting from CSV)")
    
    # Relationships
    stmt = select(func.count(RelationshipModel.id))
    result = await session.execute(stmt)
    counts["relationships"] = result.scalar()
    print(f"  relationships: {counts['relationships']} (expected: 4+ from baseline + CSV)")
    
    # Memories
    stmt = select(func.count(MemoryModel.id))
    result = await session.execute(stmt)
    counts["memories"] = result.scalar()
    print(f"  memories: {counts['memories']} (expected: >500 for Rebecca, 0 for George)")
    
    # Arcs
    stmt = select(func.count(ArcModel.id))
    result = await session.execute(stmt)
    counts["arcs"] = result.scalar()
    print(f"  arcs: {counts['arcs']} (expected: ~4 for Rebecca, 0 for George)")
    
    # Influence Fields
    stmt = select(func.count(InfluenceFieldModel.id))
    result = await session.execute(stmt)
    counts["influence_fields"] = result.scalar()
    print(f"  pfee_influence_fields: {counts['influence_fields']} (expected: >0 for non-George agents)")
    
    # Calendars
    stmt = select(func.count(CalendarModel.id))
    result = await session.execute(stmt)
    counts["calendars"] = result.scalar()
    print(f"  calendars: {counts['calendars']} (expected: >=1)")
    
    # Intentions
    stmt = select(func.count(IntentionModel.id))
    result = await session.execute(stmt)
    counts["intentions"] = result.scalar()
    print(f"  intentions: {counts['intentions']} (expected: >=0, 0 for George)")
    
    print()
    
    # 2.2 Key sanity checks on agents
    print("2.2 AGENT SANITY CHECKS:")
    print("-" * 80)
    
    # George
    stmt = select(AgentModel).where(AgentModel.name == "George")
    result = await session.execute(stmt)
    george = result.scalars().first()
    
    if george:
        print(f"  George (ID={george.id}):")
        print(f"    - is_real_user: {george.is_real_user} (expected: True)")
        print(f"    - personality_kernel: {len(str(george.personality_kernel or {}))} chars (expected: empty/0)")
        print(f"    - drives: {len(str(george.drives or {}))} chars (expected: empty/0)")
        print(f"    - mood: {len(str(george.mood or {}))} chars (expected: empty/0)")
        print(f"    - status_flags: {george.status_flags}")
        
        # Check for memories/arcs/intentions
        mem_stmt = select(func.count(MemoryModel.id)).where(MemoryModel.agent_id == george.id)
        mem_result = await session.execute(mem_stmt)
        george_memories = mem_result.scalar()
        
        arc_stmt = select(func.count(ArcModel.id)).where(ArcModel.agent_id == george.id)
        arc_result = await session.execute(arc_stmt)
        george_arcs = arc_result.scalar()
        
        int_stmt = select(func.count(IntentionModel.id)).where(IntentionModel.agent_id == george.id)
        int_result = await session.execute(int_stmt)
        george_intentions = int_result.scalar()
        
        print(f"    - memories: {george_memories} (expected: 0)")
        print(f"    - arcs: {george_arcs} (expected: 0)")
        print(f"    - intentions: {george_intentions} (expected: 0)")
    else:
        print("  George: NOT FOUND (ERROR)")
    
    print()
    
    # Rebecca
    stmt = select(AgentModel).where(AgentModel.name == "Rebecca Ferguson")
    result = await session.execute(stmt)
    rebecca = result.scalars().first()
    
    if rebecca:
        print(f"  Rebecca Ferguson (ID={rebecca.id}):")
        print(f"    - is_real_user: {rebecca.is_real_user} (expected: False)")
        print(f"    - personality_kernel: {len(str(rebecca.personality_kernel or {}))} chars (expected: >0)")
        print(f"    - drives: {len(str(rebecca.drives or {}))} chars (expected: >0)")
        print(f"    - mood: {len(str(rebecca.mood or {}))} chars (expected: >0)")
        print(f"    - status_flags: {rebecca.status_flags}")
    else:
        print("  Rebecca Ferguson: NOT FOUND (ERROR)")
    
    print()
    
    # Lucy
    stmt = select(AgentModel).where(AgentModel.name == "Lucy")
    result = await session.execute(stmt)
    lucy = result.scalars().first()
    
    if lucy:
        print(f"  Lucy (ID={lucy.id}):")
        print(f"    - is_real_user: {lucy.is_real_user} (expected: False)")
        print(f"    - personality_kernel: {len(str(lucy.personality_kernel or {}))} chars")
        print(f"    - status_flags: {lucy.status_flags}")
    else:
        print("  Lucy: NOT FOUND")
    
    print()
    
    # Nadine
    stmt = select(AgentModel).where(AgentModel.name == "Nadine")
    result = await session.execute(stmt)
    nadine = result.scalars().first()
    
    if nadine:
        print(f"  Nadine (ID={nadine.id}):")
        print(f"    - is_real_user: {nadine.is_real_user} (expected: False)")
        print(f"    - personality_kernel: {len(str(nadine.personality_kernel or {}))} chars")
        print(f"    - status_flags: {nadine.status_flags}")
    else:
        print("  Nadine: NOT FOUND")
    
    print()
    
    # 2.3 Relationships
    print("2.3 RELATIONSHIPS:")
    print("-" * 80)
    print(f"  Total relationships: {counts['relationships']}")
    print()
    print("  Key relationships:")
    
    if george and rebecca:
        # Rebecca -> George
        stmt = select(RelationshipModel).where(
            RelationshipModel.source_agent_id == rebecca.id,
            RelationshipModel.target_user_id.isnot(None)
        )
        result = await session.execute(stmt)
        rel_rebecca_george = result.scalars().first()
        if rel_rebecca_george:
            print(f"    Rebecca -> George: warmth={rel_rebecca_george.warmth:.2f}, trust={rel_rebecca_george.trust:.2f}, attraction={rel_rebecca_george.attraction:.2f}")
        else:
            print("    Rebecca -> George: NOT FOUND")
    
    if george and lucy:
        # Lucy -> George
        stmt = select(RelationshipModel).where(
            RelationshipModel.source_agent_id == lucy.id,
            RelationshipModel.target_user_id.isnot(None)
        )
        result = await session.execute(stmt)
        rel_lucy_george = result.scalars().first()
        if rel_lucy_george:
            print(f"    Lucy -> George: warmth={rel_lucy_george.warmth:.2f}, trust={rel_lucy_george.trust:.2f}")
        else:
            print("    Lucy -> George: NOT FOUND")
    
    if george and nadine:
        # Nadine -> George
        stmt = select(RelationshipModel).where(
            RelationshipModel.source_agent_id == nadine.id,
            RelationshipModel.target_user_id.isnot(None)
        )
        result = await session.execute(stmt)
        rel_nadine_george = result.scalars().first()
        if rel_nadine_george:
            print(f"    Nadine -> George: warmth={rel_nadine_george.warmth:.2f}, trust={rel_nadine_george.trust:.2f}")
        else:
            print("    Nadine -> George: NOT FOUND")
    
    if lucy and nadine:
        # Nadine -> Lucy
        stmt = select(RelationshipModel).where(
            RelationshipModel.source_agent_id == nadine.id,
            RelationshipModel.target_agent_id == lucy.id
        )
        result = await session.execute(stmt)
        rel_nadine_lucy = result.scalars().first()
        if rel_nadine_lucy:
            print(f"    Nadine -> Lucy: warmth={rel_nadine_lucy.warmth:.2f}, trust={rel_nadine_lucy.trust:.2f}")
        else:
            print("    Nadine -> Lucy: NOT FOUND")
    
    # Count Rebecca's relationships
    if rebecca:
        stmt = select(func.count(RelationshipModel.id)).where(
            RelationshipModel.source_agent_id == rebecca.id
        )
        result = await session.execute(stmt)
        rebecca_rel_count = result.scalar()
        print(f"    Rebecca total relationships: {rebecca_rel_count}")
    
    print()
    
    # 2.4 Memories & Arcs
    print("2.4 MEMORIES & ARCS:")
    print("-" * 80)
    
    # Memories per agent
    if george:
        stmt = select(func.count(MemoryModel.id)).where(MemoryModel.agent_id == george.id)
        result = await session.execute(stmt)
        george_mem = result.scalar()
        print(f"  George memories: {george_mem} (expected: 0)")
    
    if rebecca:
        stmt = select(func.count(MemoryModel.id)).where(MemoryModel.agent_id == rebecca.id)
        result = await session.execute(stmt)
        rebecca_mem = result.scalar()
        print(f"  Rebecca memories: {rebecca_mem} (expected: >500)")
    
    if lucy:
        stmt = select(func.count(MemoryModel.id)).where(MemoryModel.agent_id == lucy.id)
        result = await session.execute(stmt)
        lucy_mem = result.scalar()
        print(f"  Lucy memories: {lucy_mem}")
    
    if nadine:
        stmt = select(func.count(MemoryModel.id)).where(MemoryModel.agent_id == nadine.id)
        result = await session.execute(stmt)
        nadine_mem = result.scalar()
        print(f"  Nadine memories: {nadine_mem}")
    
    print()
    
    # Arcs per agent
    if george:
        stmt = select(func.count(ArcModel.id)).where(ArcModel.agent_id == george.id)
        result = await session.execute(stmt)
        george_arcs = result.scalar()
        print(f"  George arcs: {george_arcs} (expected: 0)")
    
    if rebecca:
        stmt = select(func.count(ArcModel.id)).where(ArcModel.agent_id == rebecca.id)
        result = await session.execute(stmt)
        rebecca_arcs = result.scalar()
        print(f"  Rebecca arcs: {rebecca_arcs} (expected: ~4)")
    
    print()
    print("=" * 80)
    print()
    
    return {
        "counts": counts,
        "george": george,
        "rebecca": rebecca,
        "lucy": lucy,
        "nadine": nadine
    }


async def main():
    """Main validation function."""
    await phase_1_environment_identification()
    
    # Connect to production database
    print("Connecting to production database...")
    print()
    
    # Convert postgres:// to postgresql+asyncpg://
    db_url = PRODUCTION_DB_URL
    if db_url.startswith("postgresql://"):
        db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    elif db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql+asyncpg://", 1)
    
    engine = create_async_engine(db_url, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    try:
        async with async_session() as session:
            data = await phase_2_raw_data_integrity(session)
        
        print("=" * 80)
        print("PHASE 2 COMPLETE - READ-ONLY VALIDATION")
        print("=" * 80)
        print()
        print("Next: Run PFEE pipeline tests via API endpoints")
        print("=" * 80)
        
    except Exception as e:
        print()
        print("=" * 80)
        print("❌ VALIDATION FAILED")
        print("=" * 80)
        print(f"Error: {type(e).__name__}: {str(e)}")
        print()
        import traceback
        traceback.print_exc()
        print("=" * 80)
        sys.exit(1)
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())

