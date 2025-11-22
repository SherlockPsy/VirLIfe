#!/usr/bin/env python3
"""
Test seeding against a local SQLite database to verify agent and relationship counts.
"""

import asyncio
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, func
from backend.config.settings import Settings
from backend.seeding.seed_baseline_world import seed_baseline_world
from backend.persistence.models import AgentModel, RelationshipModel
from backend.persistence.database import Base


async def main():
    """Test seeding and show counts."""
    print("=" * 80)
    print("TESTING SEEDING AGAINST LOCAL DATABASE")
    print("=" * 80)
    print()
    
    # Use SQLite for local testing
    db_url = "sqlite+aiosqlite:///./test_seeding.db"
    
    print(f"Database: {db_url}")
    print()
    print("Creating database schema...")
    
    engine = create_async_engine(db_url, echo=False)
    
    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    print("Schema created.")
    print()
    print("Running seeding process...")
    print()
    
    try:
        # Run seeding
        await seed_baseline_world(engine)
        
        # Query counts
        async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        async with async_session() as session:
            # Count agents
            agent_count_stmt = select(func.count(AgentModel.id))
            agent_result = await session.execute(agent_count_stmt)
            agent_count = agent_result.scalar()
            
            # Count relationships
            rel_count_stmt = select(func.count(RelationshipModel.id))
            rel_result = await session.execute(rel_count_stmt)
            rel_count = rel_result.scalar()
            
            # Get sample of non-core agents
            non_core_stmt = select(AgentModel).where(
                ~AgentModel.name.in_(["George", "Rebecca Ferguson", "Lucy", "Nadine"])
            ).limit(10)
            non_core_result = await session.execute(non_core_stmt)
            non_core_agents = non_core_result.scalars().all()
            
            # Get sample of relationships
            sample_rel_stmt = select(RelationshipModel).limit(10)
            sample_rel_result = await session.execute(sample_rel_stmt)
            sample_rels = sample_rel_result.scalars().all()
            
            # Get Rebecca's relationships count
            rebecca_stmt = select(AgentModel).where(AgentModel.name == "Rebecca Ferguson")
            rebecca_result = await session.execute(rebecca_stmt)
            rebecca = rebecca_result.scalar_one()
            
            rebecca_rel_stmt = select(func.count(RelationshipModel.id)).where(
                RelationshipModel.source_agent_id == rebecca.id
            )
            rebecca_rel_result = await session.execute(rebecca_rel_stmt)
            rebecca_rel_count = rebecca_rel_result.scalar()
            
            print()
            print("=" * 80)
            print("SEEDING RESULTS")
            print("=" * 80)
            print()
            print(f"Total Agents: {agent_count}")
            print(f"  - Core agents (George, Rebecca, Lucy, Nadine): 4")
            print(f"  - Supporting/background agents: {agent_count - 4}")
            print()
            print(f"Total Relationships: {rel_count}")
            print(f"  - Rebecca -> connections: {rebecca_rel_count}")
            print(f"  - Other relationships: {rel_count - rebecca_rel_count}")
            print()
            print("Sample Non-Core Agents (first 10):")
            for agent in non_core_agents:
                status = agent.status_flags or {}
                agent_type = "supporting" if status.get("is_supporting_agent") else "background"
                print(f"  - {agent.name} ({agent_type}, ID={agent.id})")
            print()
            print("Sample Relationships (first 10):")
            for rel in sample_rels:
                # Get source agent name
                source_stmt = select(AgentModel).where(AgentModel.id == rel.source_agent_id)
                source_result = await session.execute(source_stmt)
                source_agent = source_result.scalar_one()
                
                if rel.target_agent_id:
                    target_stmt = select(AgentModel).where(AgentModel.id == rel.target_agent_id)
                    target_result = await session.execute(target_stmt)
                    target_agent = target_result.scalar_one()
                    target_name = target_agent.name
                else:
                    target_name = "George (user)"
                
                print(f"  - {source_agent.name} -> {target_name} (warmth={rel.warmth:.2f}, trust={rel.trust:.2f})")
            print()
            print("=" * 80)
            print("✅ TEST COMPLETE")
            print("=" * 80)
        
        await engine.dispose()
        
    except Exception as e:
        print()
        print("=" * 80)
        print("❌ TEST FAILED")
        print("=" * 80)
        print(f"Error: {type(e).__name__}: {str(e)}")
        print()
        import traceback
        traceback.print_exc()
        print("=" * 80)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

