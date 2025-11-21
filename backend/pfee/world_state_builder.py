"""
PFEE World State Builder

Builds world_state dict from WorldModel and related entities for PFEE orchestrator.
"""

from typing import Dict, Any, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from backend.persistence.models import WorldModel, AgentModel, LocationModel, UserModel
from backend.persistence.repo import WorldRepo, AgentRepo, UserRepo
from sqlalchemy import select


class WorldStateBuilder:
    """Builder for world state dicts for PFEE."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def build(
        self,
        world: WorldModel,
        user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Build world state dict from WorldModel."""
        return await self._build_world_state(world, user_id)
    
    async def _build_world_state(
        self,
        world: WorldModel,
        user_id: Optional[int] = None
    ) -> Dict[str, Any]:
    """
    Build world_state dict from WorldModel for PFEE orchestrator.
    
    Args:
        session: Database session
        world: WorldModel instance
        user_id: Optional user ID for user context
    
    Returns:
        Dict with world state for PFEE
    """
    world_repo = WorldRepo(session)
    agent_repo = AgentRepo(session)
    user_repo = UserRepo(session)
    
    # Get user location (default to location 1)
    user_location_id = 1
    if user_id:
        user = await user_repo.get_user_by_name(f"user_{user_id}")
        # UserModel doesn't have location_id, so we default to 1
        # In future, this could be tracked separately
    
    # Get agents in user's location
    agents_in_location = await agent_repo.list_agents_in_location(user_location_id)
    
    # Get location details
    location = None
    if user_location_id:
        stmt = select(LocationModel).where(LocationModel.id == user_location_id)
        result = await session.execute(stmt)
        location = result.scalars().first()
    
    # Build persistent agents list
    persistent_agents = []
    persistent_agents_present_with_user = []
    
    for agent in agents_in_location:
        agent_dict = {
            "id": agent.id,
            "name": agent.name,
            "location_id": agent.location_id,
            "mood": agent.mood or {"valence": 0.0, "arousal": 0.0},
            "drives": agent.drives or {},
            "energy": agent.energy or 1.0,
            "intentions": [
                {
                    "id": intent.id,
                    "description": intent.description,
                    "priority": intent.priority,
                    "horizon": intent.horizon,
                    "type": intent.type
                }
                for intent in (agent.intentions or [])
            ],
            "relationships": [
                {
                    "target_agent_id": rel.target_agent_id,
                    "target_user_id": rel.target_user_id,
                    "warmth": rel.warmth,
                    "trust": rel.trust,
                    "tension": rel.tension,
                    "attraction": rel.attraction,
                    "familiarity": rel.familiarity,
                    "comfort": rel.comfort
                }
                for rel in (agent.relationships or [])
            ]
        }
        persistent_agents.append(agent_dict)
        persistent_agents_present_with_user.append(agent_dict)
    
    # Build world state
    world_state = {
        "world_id": world.id,
        "current_tick": world.current_tick,
        "current_time": world.current_time,
        "current_location_id": user_location_id,
        "current_location_type": location.attributes.get("type", "general") if location else "general",
        "current_location": location.name if location else "unknown",
        "persistent_agents": persistent_agents,
        "persistent_agents_present_with_user": persistent_agents_present_with_user,
        "agents_present": [a["name"] for a in persistent_agents_present_with_user],
        "user_id": user_id,
        "salience": self._compute_world_salience(agents_in_location, world.current_time),  # Computed from current state
        "agents": persistent_agents  # Alias for compatibility
    }
    
        return world_state
    
    def _compute_world_salience(
        self,
        agents_present: List[Any],
        current_time: datetime
    ) -> float:
        """Compute overall salience for current world state."""
        salience = 0.0
        
        # Base salience from number of agents present
        if agents_present:
            salience += min(0.3, len(agents_present) * 0.1)
        
        # Salience from time of day (evening/night can be more atmospheric)
        if current_time:
            hour = current_time.hour
            if hour in [18, 19, 20, 21, 22, 23, 0, 1, 2, 3, 4, 5, 6]:  # Evening/night/dawn
                salience += 0.1
        
        return min(1.0, salience)


# Convenience function for backward compatibility
async def build_world_state_for_pfee(
    session: AsyncSession,
    world: WorldModel,
    user_id: Optional[int] = None
) -> Dict[str, Any]:
    """Build world state dict from WorldModel (convenience function)."""
    builder = WorldStateBuilder(session)
    return await builder.build(world, user_id)

