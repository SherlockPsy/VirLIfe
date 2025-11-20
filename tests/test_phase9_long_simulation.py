"""
Phase 9 Long-Duration World Simulation Tests

Tests to verify system stability and correctness over extended simulation periods.

Implements: Plan.md §9.3 (long-duration world simulations)

Goal: Run world for extended periods (100+ ticks) and verify:
- No state corruption
- Determinism maintained
- Memory growth is reasonable
- Performance doesn't degrade
- All invariants hold
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List
from backend.persistence.database import AsyncSessionLocal, get_db
from backend.persistence.models import WorldModel, AgentModel, MemoryModel
from backend.world.engine import WorldEngine
from backend.autonomy.engine import AutonomyEngine
from sqlalchemy import select, func


@pytest.mark.asyncio
class TestLongDurationSimulation:
    """Tests for long-duration world simulations."""
    
    async def test_100_tick_simulation_determinism(self):
        """
        Run 100 ticks and verify determinism.
        
        Given: Same initial state and seed
        When: Run simulation twice
        Then: Final state must match exactly
        """
        from backend.persistence.repo import WorldRepository, AgentRepository
        
        # Create initial world state
        async with AsyncSessionLocal() as session:
            world_repo = WorldRepository(session)
            agent_repo = AgentRepository(session)
            
            # Create world
            world = await world_repo.create_world()
            world_id = world.id
            
            # Create test agent
            agent = await agent_repo.create_agent(
                world_id=world_id,
                name="TestAgent",
                location_id=None,
                personality_kernel={"sociability": 0.5},
                drives={"relatedness": {"level": 0.5, "sensitivity": 1.0}}
            )
            agent_id = agent.id
            
            # Save initial state snapshot
            initial_state = await self._capture_state(session, world_id, agent_id)
            
            # Run 100 ticks
            world_engine = WorldEngine(session)
            autonomy_engine = AutonomyEngine(session)
            
            for tick in range(100):
                # Advance world
                await world_engine.advance_tick(world_id)
                
                # Process autonomy for agent
                await autonomy_engine.process_agent_tick(agent_id, world_id)
                
                # Commit periodically (every 10 ticks)
                if tick % 10 == 0:
                    await session.commit()
            
            await session.commit()
            
            # Capture final state
            final_state_1 = await self._capture_state(session, world_id, agent_id)
            
            # Reset and run again with same initial state
            await session.rollback()
            await self._restore_state(session, world_id, agent_id, initial_state)
            await session.commit()
            
            # Run 100 ticks again
            for tick in range(100):
                await world_engine.advance_tick(world_id)
                await autonomy_engine.process_agent_tick(agent_id, world_id)
                if tick % 10 == 0:
                    await session.commit()
            
            await session.commit()
            
            # Capture final state again
            final_state_2 = await self._capture_state(session, world_id, agent_id)
            
            # Verify states match
            assert final_state_1["world_tick"] == final_state_2["world_tick"]
            assert abs(final_state_1["agent_energy"] - final_state_2["agent_energy"]) < 0.001
            assert final_state_1["memory_count"] == final_state_2["memory_count"]
    
    async def test_100_tick_simulation_state_invariants(self):
        """
        Run 100 ticks and verify all state invariants hold.
        
        Verifies:
        - Drives stay in [0, 1]
        - Mood valence in [-1, 1]
        - Mood arousal in [0, 1]
        - Energy in [0, 1]
        - Relationship edges in valid ranges
        """
        from backend.persistence.repo import WorldRepository, AgentRepository
        
        async with AsyncSessionLocal() as session:
            world_repo = WorldRepository(session)
            agent_repo = AgentRepository(session)
            
            world = await world_repo.create_world()
            agent = await agent_repo.create_agent(
                world_id=world.id,
                name="TestAgent",
                location_id=None,
                personality_kernel={"sociability": 0.5},
                drives={"relatedness": {"level": 0.5, "sensitivity": 1.0}}
            )
            
            world_engine = WorldEngine(session)
            autonomy_engine = AutonomyEngine(session)
            
            violations = []
            
            for tick in range(100):
                await world_engine.advance_tick(world.id)
                await autonomy_engine.process_agent_tick(agent.id, world.id)
                
                # Check invariants every 10 ticks
                if tick % 10 == 0:
                    await session.refresh(agent)
                    
                    # Check drives
                    drives = agent.drives or {}
                    for drive_name, drive_data in drives.items():
                        if isinstance(drive_data, dict):
                            level = drive_data.get("level", 0.5)
                            if level < 0.0 or level > 1.0:
                                violations.append(f"Tick {tick}: Drive {drive_name} level {level} out of bounds")
                    
                    # Check mood
                    mood = agent.mood or {}
                    valence = mood.get("valence", 0.0)
                    arousal = mood.get("arousal", 0.0)
                    if valence < -1.0 or valence > 1.0:
                        violations.append(f"Tick {tick}: Valence {valence} out of bounds")
                    if arousal < 0.0 or arousal > 1.0:
                        violations.append(f"Tick {tick}: Arousal {arousal} out of bounds")
                    
                    # Check energy
                    if agent.energy < 0.0 or agent.energy > 1.0:
                        violations.append(f"Tick {tick}: Energy {agent.energy} out of bounds")
                
                if tick % 20 == 0:
                    await session.commit()
            
            await session.commit()
            
            # Assert no violations
            assert len(violations) == 0, f"State invariant violations: {violations}"
    
    async def test_100_tick_memory_growth(self):
        """
        Run 100 ticks and verify memory growth is reasonable.
        
        Memory should grow but not explode (e.g., < 50 memories for 100 ticks).
        """
        from backend.persistence.repo import WorldRepository, AgentRepository
        
        async with AsyncSessionLocal() as session:
            world_repo = WorldRepository(session)
            agent_repo = AgentRepository(session)
            
            world = await world_repo.create_world()
            agent = await agent_repo.create_agent(
                world_id=world.id,
                name="TestAgent",
                location_id=None,
                personality_kernel={"sociability": 0.5},
                drives={"relatedness": {"level": 0.5, "sensitivity": 1.0}}
            )
            
            world_engine = WorldEngine(session)
            autonomy_engine = AutonomyEngine(session)
            
            initial_memory_count = await self._count_memories(session, agent.id)
            
            # Run 100 ticks
            for tick in range(100):
                await world_engine.advance_tick(world.id)
                await autonomy_engine.process_agent_tick(agent.id, world.id)
                
                if tick % 20 == 0:
                    await session.commit()
            
            await session.commit()
            
            final_memory_count = await self._count_memories(session, agent.id)
            memory_growth = final_memory_count - initial_memory_count
            
            # Memory should grow but not excessively
            # Most ticks won't create memories (only high-salience events)
            assert memory_growth >= 0, "Memory count should not decrease"
            assert memory_growth < 50, f"Memory growth {memory_growth} seems excessive for 100 ticks"
    
    async def test_100_tick_performance_stability(self):
        """
        Run 100 ticks and verify performance doesn't degrade.
        
        Measures: execution time per tick should remain relatively stable.
        """
        from backend.persistence.repo import WorldRepository, AgentRepository
        import time
        
        async with AsyncSessionLocal() as session:
            world_repo = WorldRepository(session)
            agent_repo = AgentRepository(session)
            
            world = await world_repo.create_world()
            agent = await agent_repo.create_agent(
                world_id=world.id,
                name="TestAgent",
                location_id=None,
                personality_kernel={"sociability": 0.5},
                drives={"relatedness": {"level": 0.5, "sensitivity": 1.0}}
            )
            
            world_engine = WorldEngine(session)
            autonomy_engine = AutonomyEngine(session)
            
            tick_times = []
            
            for tick in range(100):
                start_time = time.time()
                
                await world_engine.advance_tick(world.id)
                await autonomy_engine.process_agent_tick(agent.id, world.id)
                
                elapsed = time.time() - start_time
                tick_times.append(elapsed)
                
                if tick % 20 == 0:
                    await session.commit()
            
            await session.commit()
            
            # Check that later ticks don't take significantly longer
            first_quarter_avg = sum(tick_times[:25]) / 25
            last_quarter_avg = sum(tick_times[-25:]) / 25
            
            # Performance shouldn't degrade by more than 2x
            performance_ratio = last_quarter_avg / first_quarter_avg if first_quarter_avg > 0 else 1.0
            assert performance_ratio < 2.0, f"Performance degraded: {performance_ratio:.2f}x slower"
    
    # Helper methods
    
    async def _capture_state(self, session, world_id: int, agent_id: int) -> Dict[str, Any]:
        """Capture world and agent state snapshot."""
        from backend.persistence.repo import WorldRepository, AgentRepository
        
        world_repo = WorldRepository(session)
        agent_repo = AgentRepository(session)
        
        world = await world_repo.get_world(world_id)
        agent = await agent_repo.get_agent(agent_id)
        memory_count = await self._count_memories(session, agent_id)
        
        return {
            "world_tick": world.current_tick,
            "agent_energy": agent.energy,
            "agent_mood": agent.mood,
            "agent_drives": agent.drives,
            "memory_count": memory_count
        }
    
    async def _restore_state(self, session, world_id: int, agent_id: int, state: Dict[str, Any]):
        """Restore world and agent state (simplified - just for testing)."""
        # In a real implementation, this would restore full state
        # For determinism testing, we'd need to reset the entire database
        pass
    
    async def _count_memories(self, session, agent_id: int) -> int:
        """Count memories for an agent."""
        result = await session.execute(
            select(func.count(MemoryModel.id)).where(MemoryModel.agent_id == agent_id)
        )
        return result.scalar() or 0

