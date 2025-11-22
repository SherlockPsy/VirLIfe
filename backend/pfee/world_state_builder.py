"""
PFEE World State Builder

Implements Section C.3 of the blueprint:
- Builds comprehensive world state from all seeded data
- Enforces George protection (no internal state for George)
- Loads relationships, memories, arcs, influence fields, intentions, calendars
"""

from typing import Dict, Any, Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from sqlalchemy.orm import selectinload

from backend.persistence.models import (
    WorldModel, AgentModel, LocationModel, RelationshipModel,
    MemoryModel, ArcModel, IntentionModel, InfluenceFieldModel,
    CalendarModel, UserModel
)


async def build_world_state(
    session: AsyncSession,
    *,
    world_id: int,
    user_id: Optional[int] = None,
    trigger: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Build a full snapshot of the world relevant to the current trigger.
    
    Implements Section C.3:
    - Uses all seeded data (agents, relationships, arcs, memories, influence fields)
    - Enforces George protection (no internal state for George)
    - Loads physical context, agent internal state, relationships, memories, arcs
    
    Args:
        session: Async database session
        world_id: World ID
        user_id: Optional user ID (for resolving George)
        trigger: Optional trigger dict with trigger_type, actor_agent_id, etc.
    
    Returns:
        WorldState dict with all required fields
    """
    # C.3.1 Determine Physical Context
    world_state = await _build_physical_context(session, world_id, user_id)
    
    # C.3.2 Load Agent Internal State (Non-George Only)
    agents_in_scene = await _load_agents_in_scene(session, world_state, world_id)
    world_state["agents_in_scene"] = agents_in_scene
    
    # Load relationships for all agents in scene
    relationships = await _load_relationships(session, world_state, agents_in_scene)
    world_state["relationships"] = relationships
    
    # C.3.3 WorldState Structure is now complete
    return world_state


async def _build_physical_context(
    session: AsyncSession,
    world_id: int,
    user_id: Optional[int]
) -> Dict[str, Any]:
    """
    C.3.1 Determine Physical Context
    
    Resolves George's location, loads world time, determines agents present.
    """
    # Load world
    stmt = select(WorldModel).where(WorldModel.id == world_id)
    result = await session.execute(stmt)
    world = result.scalars().first()
    if not world:
        raise ValueError(f"World {world_id} not found")
    
    # Resolve user_agent_id from user_id (George's agent)
    george_agent = None
    if user_id:
        # Try to find George agent by name
        stmt = select(AgentModel).where(
            and_(
                AgentModel.world_id == world_id,
                AgentModel.name == "George",
                AgentModel.is_real_user == True
            )
        )
        result = await session.execute(stmt)
        george_agent = result.scalars().first()
    
    # If no user_id provided or not found, try to find George agent directly
    if not george_agent:
        stmt = select(AgentModel).where(
            and_(
                AgentModel.world_id == world_id,
                AgentModel.is_real_user == True
            )
        )
        result = await session.execute(stmt)
        george_agent = result.scalars().first()
    
    if not george_agent:
        raise ValueError("George agent not found in world")
    
    # Determine George's current location
    location_id = george_agent.location_id
    if not location_id:
        # Default to Lounge if not set
        stmt = select(LocationModel).where(
            and_(
                LocationModel.world_id == world_id,
                LocationModel.name == "Lounge"
            )
        )
        result = await session.execute(stmt)
        location = result.scalars().first()
        if location:
            location_id = location.id
            george_agent.location_id = location_id
            await session.flush()
        else:
            # Fallback to any location
            stmt = select(LocationModel).where(LocationModel.world_id == world_id).limit(1)
            result = await session.execute(stmt)
            location = result.scalars().first()
            if location:
                location_id = location.id
    
    # Load location with adjacency
    location = None
    if location_id:
        stmt = select(LocationModel).where(LocationModel.id == location_id)
        result = await session.execute(stmt)
        location = result.scalars().first()
    
    # Identify agents present in the same location (and optionally adjacent)
    agents_in_location_ids = set()
    if location_id:
        # Same location
        stmt = select(AgentModel).where(AgentModel.location_id == location_id)
        result = await session.execute(stmt)
        for agent in result.scalars().all():
            agents_in_location_ids.add(agent.id)
        
        # Optionally: adjacent locations (within earshot)
        # For now, only same location
    
    world_state = {
        "world_id": world_id,
        "current_time": world.current_time,
        "current_tick": world.current_tick,
        "location": {
            "location_id": location_id,
            "name": location.name if location else None,
            "description": location.description if location else None,
            "attributes": location.attributes if location else {},
            "adjacency": location.adjacency if location else []
        },
        "george_in_scene": True,
        "george_agent_id": george_agent.id,
        "agents_in_location_ids": list(agents_in_location_ids)
    }
    
    return world_state


async def _load_agents_in_scene(
    session: AsyncSession,
    world_state: Dict[str, Any],
    world_id: int
) -> List[Dict[str, Any]]:
    """
    C.3.2 Load Agent Internal State (Non-George Only)
    
    Loads full internal state for non-George agents, external-only for George.
    """
    agents_in_scene = []
    agents_in_location_ids = world_state.get("agents_in_location_ids", [])
    george_agent_id = world_state.get("george_agent_id")
    
    if not agents_in_location_ids:
        return agents_in_scene
    
    # Load all agents in location
    stmt = select(AgentModel).where(AgentModel.id.in_(agents_in_location_ids)).options(
        selectinload(AgentModel.memories),
        selectinload(AgentModel.arcs),
        selectinload(AgentModel.intentions),
        selectinload(AgentModel.location)
    )
    result = await session.execute(stmt)
    agents = result.scalars().all()
    
    for agent in agents:
        if agent.is_real_user:
            # George: external-only data
            agent_data = {
                "id": agent.id,
                "name": agent.name,
                "is_real_user": True,
                "location_id": agent.location_id,
                "public_profile": {
                    "profession": agent.status_flags.get("profession") if isinstance(agent.status_flags, dict) else None,
                    "hobbies": agent.status_flags.get("hobbies") if isinstance(agent.status_flags, dict) else None
                },
                # NO internal psychological state
                # NO drives, mood, personality_kernel, etc.
            }
        else:
            # Non-George: full internal state
            # Load influence fields
            stmt = select(InfluenceFieldModel).where(InfluenceFieldModel.agent_id == agent.id)
            result = await session.execute(stmt)
            influence_field = result.scalars().first()
            
            # Load relevant memories (filtered by tags, sorted by salience, limited)
            memories = await _load_relevant_memories(
                session, agent.id, world_state, limit=7
            )
            
            # Load active arcs
            active_arcs = [arc for arc in agent.arcs if arc.intensity > 0.1]
            
            # Load active intentions
            active_intentions = [intent for intent in agent.intentions]
            
            agent_data = {
                "id": agent.id,
                "name": agent.name,
                "is_real_user": False,
                "location_id": agent.location_id,
                # Full internal state
                "drives": agent.drives if isinstance(agent.drives, dict) else {},
                "mood": agent.mood if isinstance(agent.mood, dict) else {},
                "personality_kernel": agent.personality_kernel if isinstance(agent.personality_kernel, dict) else {},
                "personality_summaries": agent.personality_summaries if isinstance(agent.personality_summaries, dict) else {},
                "domain_summaries": agent.domain_summaries if isinstance(agent.domain_summaries, dict) else {},
                "status_flags": agent.status_flags if isinstance(agent.status_flags, dict) else {},
                "influence_fields": _serialize_influence_field(influence_field) if influence_field else {},
                "arcs": [_serialize_arc(arc) for arc in active_arcs],
                "intentions": [_serialize_intention(intent) for intent in active_intentions],
                "memories": [_serialize_memory(mem) for mem in memories],
                "energy": agent.energy or 1.0
            }
        
        agents_in_scene.append(agent_data)
    
    return agents_in_scene


async def _load_relevant_memories(
    session: AsyncSession,
    agent_id: int,
    world_state: Dict[str, Any],
    limit: int = 7
) -> List[MemoryModel]:
    """
    Load relevant memories filtered by tags related to:
    - George's identity
    - Current location
    - Active arcs
    """
    # Build filter criteria
    george_agent_id = world_state.get("george_agent_id")
    location_id = world_state.get("location", {}).get("location_id")
    
    # Get active arcs for tag matching
    stmt = select(ArcModel).where(ArcModel.agent_id == agent_id)
    result = await session.execute(stmt)
    arcs = result.scalars().all()
    arc_topics = []
    for arc in arcs:
        if isinstance(arc.topic_vector, dict):
            topic = arc.topic_vector.get("core_tension", "")
            if topic:
                arc_topics.extend(topic.lower().split())
    
    # Query memories
    stmt = select(MemoryModel).where(MemoryModel.agent_id == agent_id)
    result = await session.execute(stmt)
    all_memories = result.scalars().all()
    
    # Filter and score memories
    scored_memories = []
    for mem in all_memories:
        score = mem.salience or 0.0
        tags = mem.semantic_tags if isinstance(mem.semantic_tags, list) else []
        
        # Boost score for relevant tags
        for tag in tags:
            tag_lower = str(tag).lower()
            if george_agent_id and "george" in tag_lower:
                score += 0.2
            if location_id and "location" in tag_lower:
                score += 0.1
            if any(topic in tag_lower for topic in arc_topics):
                score += 0.1
        
        scored_memories.append((score, mem))
    
    # Sort by score descending and limit
    scored_memories.sort(key=lambda x: x[0], reverse=True)
    return [mem for _, mem in scored_memories[:limit]]


async def _load_relationships(
    session: AsyncSession,
    world_state: Dict[str, Any],
    agents_in_scene: List[Dict[str, Any]]
) -> Dict[str, Dict[str, Any]]:
    """
    C.3.2 Relationships
    
    Load relationships for every pair (A, B) among:
    - present agents
    - plus George always included as a reference
    """
    relationships = {}
    
    # Get all agent IDs in scene (including George)
    agent_ids_in_scene = {agent["id"] for agent in agents_in_scene}
    george_agent_id = world_state.get("george_agent_id")
    
    # Also get George's UserModel ID if relationships use target_user_id
    george_user_id = None
    if george_agent_id:
        stmt = select(UserModel).where(UserModel.name == "George")
        result = await session.execute(stmt)
        george_user = result.scalars().first()
        if george_user:
            george_user_id = george_user.id
    
    # Load all relationships where source is an agent in scene
    for agent_data in agents_in_scene:
        source_agent_id = agent_data["id"]
        
        # Query relationships from this agent
        stmt = select(RelationshipModel).where(
            RelationshipModel.source_agent_id == source_agent_id
        )
        result = await session.execute(stmt)
        agent_relationships = result.scalars().all()
        
        for rel in agent_relationships:
            # Determine target
            target_key = None
            if rel.target_agent_id and rel.target_agent_id in agent_ids_in_scene:
                target_key = f"agent_{rel.target_agent_id}"
            elif rel.target_user_id == george_user_id:
                target_key = f"george_user_{rel.target_user_id}"
            elif rel.target_agent_id:
                target_key = f"agent_{rel.target_agent_id}"
            
            if target_key:
                rel_key = f"{source_agent_id}_to_{target_key}"
                relationships[rel_key] = {
                    "source_agent_id": source_agent_id,
                    "target_agent_id": rel.target_agent_id,
                    "target_user_id": rel.target_user_id,
                    "warmth": rel.warmth or 0.0,
                    "trust": rel.trust or 0.0,
                    "attraction": rel.attraction or 0.0,
                    "familiarity": rel.familiarity or 0.0,
                    "tension": rel.tension or 0.0,
                    "volatility": rel.volatility or 0.0,
                    "comfort": rel.comfort or 0.0
                }
    
    return relationships


def _serialize_influence_field(influence_field: InfluenceFieldModel) -> Dict[str, Any]:
    """Serialize influence field model to dict."""
    return {
        "mood_offset": influence_field.mood_offset if isinstance(influence_field.mood_offset, dict) else {},
        "drive_pressures": influence_field.drive_pressures if isinstance(influence_field.drive_pressures, dict) else {},
        "pending_contact_probability": influence_field.pending_contact_probability if isinstance(influence_field.pending_contact_probability, dict) else {},
        "unresolved_tension_topics": influence_field.unresolved_tension_topics if isinstance(influence_field.unresolved_tension_topics, dict) else {}
    }


def _serialize_arc(arc: ArcModel) -> Dict[str, Any]:
    """Serialize arc model to dict."""
    return {
        "id": arc.id,
        "type": arc.type,
        "intensity": arc.intensity or 0.0,
        "valence_bias": arc.valence_bias or 0.0,
        "topic_vector": arc.topic_vector if isinstance(arc.topic_vector, dict) else {},
        "decay_rate": arc.decay_rate or 0.1
    }


def _serialize_intention(intention: IntentionModel) -> Dict[str, Any]:
    """Serialize intention model to dict."""
    return {
        "id": intention.id,
        "description": intention.description,
        "priority": intention.priority or 0.0,
        "horizon": intention.horizon or "short",
        "type": intention.type or "action",
        "stability": intention.stability or 0.5
    }


def _serialize_memory(memory: MemoryModel) -> Dict[str, Any]:
    """Serialize memory model to dict."""
    return {
        "id": memory.id,
        "type": memory.type,
        "description": memory.description,
        "semantic_tags": memory.semantic_tags if isinstance(memory.semantic_tags, list) else [],
        "salience": memory.salience or 0.0,
        "timestamp": memory.timestamp.isoformat() if memory.timestamp else None
    }


# Legacy function for backward compatibility
async def build_world_state_for_pfee(
    session: AsyncSession,
    world: WorldModel,
    user_id: int
) -> Dict[str, Any]:
    """
    Legacy wrapper for backward compatibility.
    """
    return await build_world_state(
        session,
        world_id=world.id,
        user_id=user_id,
        trigger=None
    )
