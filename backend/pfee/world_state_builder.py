"""
PFEE World State Builder

Helper module to build world state snapshots for PFEE.
"""

from typing import Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from backend.persistence.models import WorldModel, AgentModel, LocationModel
from backend.persistence.repo import WorldRepo, AgentRepo
from sqlalchemy import select


async def build_world_state_for_pfee(
    session: AsyncSession,
    world: WorldModel,
    user_id: int
) -> Dict[str, Any]:
    """
    Build a world state snapshot for PFEE.
    
    Returns a dictionary containing:
    - current_time
    - current_tick
    - current_location_id
    - persistent_agents_present_with_user
    - user_id
    - other relevant world state
    """
    # Get user's location (default to location 1 if not tracked)
    location_id = 1
    
    # Get agents in same location as user
    stmt = select(AgentModel).where(AgentModel.location_id == location_id)
    result = await session.execute(stmt)
    agents_in_location = result.scalars().all()
    
    # Build agent data
    persistent_agents_present = []
    for agent in agents_in_location:
        agent_data = {
            "id": agent.id,
            "name": agent.name,
            "location_id": agent.location_id,
            "mood": agent.mood or {"valence": 0.0, "arousal": 0.0},
            "drives": agent.drives or {},
            "energy": agent.energy or 1.0,
            "arcs": {},  # Will be loaded if needed
            "intentions": {},  # Will be loaded if needed
            "relationships": {}  # Will be loaded if needed
        }
        persistent_agents_present.append(agent_data)
    
    # Build world state
    world_state = {
        "current_time": world.current_time,
        "current_tick": world.current_tick,
        "current_location_id": location_id,
        "persistent_agents_present_with_user": persistent_agents_present,
        "user_id": user_id,
        "world_id": world.id,
        "current_location_type": "general",  # Default, can be enhanced
        "salience": 0.5,  # Default salience
        "active_arcs": [],  # Can be populated from agent arcs
        "user_routine_locations": ["Bedroom", "Kitchen", "Living Room"]  # Default
    }
    
    return world_state

