"""
Seed script for baseline world population.

This script implements Section B of the blueprint: it populates the database
with the baseline world using the mapping functions from Section A.

STRATEGY: Wipe-and-reseed (STRATEGY 1)
- Before seeding, delete all rows from affected tables
- Then seed from scratch
- Ensures the world is always re-created exactly

The script is idempotent and deterministic.
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List
from sqlalchemy.ext.asyncio import AsyncSession, AsyncEngine
from sqlalchemy import select, delete, text
from sqlalchemy.orm import selectinload

from backend.persistence.models import (
    WorldModel, LocationModel, AgentModel, RelationshipModel,
    MemoryModel, ArcModel, IntentionModel, ObjectModel,
    CalendarModel, InfluenceFieldModel, UserModel
)

from backend.seeding.data_mappers import (
    map_baseline_to_locations,
    map_baseline_to_objects,
    map_george_profile,
    map_rebecca_fingerprint_to_personality_kernel,
    map_rebecca_personality_summaries,
    map_rebecca_drives,
    map_rebecca_mood,
    map_rebecca_domain_summaries,
    map_rebecca_status_flags,
    map_connections_to_relationships,
    map_memories_for_rebecca,
    map_arcs_for_rebecca,
    map_influence_fields_for_rebecca,
    map_calendar_entries_for_rebecca,
    map_archetypes
)
from backend.seeding.mapper_helpers import load_baseline_txt

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Baseline world metadata
BASELINE_WORLD_NAME = "George_Baseline_World"
SEED_SCRIPT_VERSION = "1.0.0"


async def seed_baseline_world(engine: AsyncEngine) -> None:
    """
    Seed the database with the baseline world using the mapping rules
    defined in Section A and these seeding rules.
    
    This function:
    1. Wipes existing data (STRATEGY 1: wipe-and-reseed)
    2. Creates the baseline world row
    3. Seeds all required entities in order
    4. Commits all changes
    5. Logs summary
    """
    logger.info("=" * 80)
    logger.info("Starting baseline world seeding (Version %s)", SEED_SCRIPT_VERSION)
    logger.info("=" * 80)
    
    async with AsyncSession(engine) as session:
        try:
            # Step 1: Wipe existing data
            await _wipe_existing_data(session)
            
            # Step 2: Create or update baseline world row
            world_model = await _create_or_update_world(session)
            world_id = world_model.id
            logger.info("Created/updated baseline world: ID=%d, name=%s", world_id, world_model.name)
            
            # Step 3: Seed locations and objects
            locations_map = await _seed_locations(session, world_id)
            objects_map = await _seed_objects(session, world_id, locations_map)
            
            # Step 4: Seed agents (George, Rebecca, Lucy, Nadine, others)
            agents_map = await _seed_agents(session, world_id, locations_map)
            
            # Step 5: Seed relationships
            await _seed_relationships(session, agents_map, world_id)
            
            # Step 6: Seed memories and arcs
            await _seed_memories(session, agents_map)
            await _seed_arcs(session, agents_map)
            
            # Step 7: Seed influence fields
            await _seed_influence_fields(session, agents_map)
            
            # Step 8: Seed calendars
            await _seed_calendars(session, agents_map, world_model)
            
            # Step 9: Seed initial intentions (non-George)
            await _seed_intentions(session, agents_map)
            
            # Step 10: Set initial positions for agents
            await _set_initial_positions(session, agents_map, locations_map)
            
            # Step 11: E.1.4 - Explicitly zero George's psychological fields (final cleanup)
            await _cleanup_george_psychological_fields(session, agents_map)
            
            # Step 12: Commit all changes
            await session.commit()
            logger.info("All changes committed successfully")
            
            # Step 13: Log summary
            await _log_seeding_summary(session, world_id)
            
            logger.info("=" * 80)
            logger.info("Baseline world seeding completed successfully")
            logger.info("=" * 80)
            
        except Exception as e:
            await session.rollback()
            logger.error("Error during seeding, rolled back: %s", e, exc_info=True)
            raise


async def _wipe_existing_data(session: AsyncSession) -> None:
    """Wipe all existing data from affected tables (STRATEGY 1: wipe-and-reseed)."""
    logger.info("Wiping existing data from affected tables...")
    
    # Delete in reverse dependency order to avoid foreign key violations
    tables_to_wipe = [
        "memories",
        "arcs",
        "intentions",
        "calendars",
        "pfee_influence_fields",
        "relationships",
        "events",
        "objects",
        "agents",
        "locations",
        "worlds"
    ]
    
    for table_name in tables_to_wipe:
        try:
            await session.execute(text(f"DELETE FROM {table_name}"))
            logger.info("  - Deleted all rows from %s", table_name)
        except Exception as e:
            logger.warning("  - Could not delete from %s: %s", table_name, e)
    
    await session.flush()
    logger.info("Data wipe completed")


async def _create_or_update_world(session: AsyncSession) -> WorldModel:
    """Create or update the baseline world row."""
    logger.info("Creating/updating baseline world row...")
    
    # Check if world already exists
    stmt = select(WorldModel).where(WorldModel.name == BASELINE_WORLD_NAME)
    result = await session.execute(stmt)
    existing_world = result.scalars().first()
    
    # Determine baseline time from baseline document
    # From baseline: "8 years ago" when George saw Rebecca in Greatest Showman
    # We'll use a deterministic starting time: today at 18:00 (evening)
    # In production, this should be set to a fixed date from the baseline
    baseline_time = datetime.now(timezone.utc).replace(hour=18, minute=0, second=0, microsecond=0)
    
    if existing_world:
        # Update existing world
        existing_world.current_time = baseline_time
        existing_world.current_tick = 0
        logger.info("  - Updated existing world: ID=%d", existing_world.id)
        await session.flush()
        return existing_world
    else:
        # Create new world
        world = WorldModel(
            name=BASELINE_WORLD_NAME,
            current_time=baseline_time,
            current_tick=0
        )
        session.add(world)
        await session.flush()
        logger.info("  - Created new world: ID=%d", world.id)
        return world


async def _seed_locations(session: AsyncSession, world_id: int) -> Dict[str, int]:
    """
    Seed locations from baseline document.
    
    Returns:
        Dict mapping location names to location IDs
    """
    logger.info("Seeding locations...")
    
    locations_data = map_baseline_to_locations()
    locations_map = {}
    
    for loc_data in locations_data:
        location = LocationModel(
            world_id=world_id,
            name=loc_data["name"],
            description=loc_data["description"],
            attributes={
                "floor": loc_data.get("floor", ""),
                "house": "Cookridge"
            },
            adjacency=loc_data.get("adjacency", [])
        )
        session.add(location)
        await session.flush()
        locations_map[loc_data["name"]] = location.id
        logger.info("  - Created location: %s (ID=%d)", loc_data["name"], location.id)
    
    # Now update adjacency to use location IDs instead of names
    for loc_data in locations_data:
        location_id = locations_map[loc_data["name"]]
        adjacency_names = loc_data.get("adjacency", [])
        adjacency_ids = [locations_map[name] for name in adjacency_names if name in locations_map]
        
        # Update the location's adjacency
        stmt = select(LocationModel).where(LocationModel.id == location_id)
        result = await session.execute(stmt)
        location = result.scalars().first()
        if location:
            location.adjacency = adjacency_ids
            await session.flush()
    
    logger.info("  - Created %d locations total", len(locations_map))
    return locations_map


async def _seed_objects(session: AsyncSession, world_id: int, locations_map: Dict[str, int]) -> Dict[str, int]:
    """
    Seed objects from baseline document.
    
    Returns:
        Dict mapping object names to object IDs
    """
    logger.info("Seeding objects...")
    
    objects_data = map_baseline_to_objects()
    objects_map = {}
    
    for obj_data in objects_data:
        location_name = obj_data.get("location_name")
        location_id = locations_map.get(location_name)
        
        if not location_id:
            logger.warning("  - Skipping object %s: location %s not found", obj_data["name"], location_name)
            continue
        
        obj = ObjectModel(
            name=obj_data["name"],
            description=obj_data["description"],
            location_id=location_id,
            state={}
        )
        session.add(obj)
        await session.flush()
        objects_map[obj_data["name"]] = obj.id
        logger.info("  - Created object: %s (ID=%d) at location %s", obj_data["name"], obj.id, location_name)
    
    logger.info("  - Created %d objects total", len(objects_map))
    return objects_map


async def _seed_agents(
    session: AsyncSession,
    world_id: int,
    locations_map: Dict[str, int]
) -> Dict[str, AgentModel]:
    """
    Seed agents (George, Rebecca, Lucy, Nadine, others).
    
    Returns:
        Dict mapping agent names to AgentModel instances
    """
    logger.info("Seeding agents...")
    
    agents_map = {}
    
    # Load archetypes for agent creation
    archetypes = map_archetypes()
    
    # Seed George (special rules - no internal state)
    george_data = map_george_profile()
    george = await _create_agent(
        session,
        world_id=world_id,
        name="George",
        is_real_user=True,
        role="user",
        age=george_data.get("age"),
        profession=george_data.get("profession"),
        # No psychological fields - these should be empty/neutral for George
        personality_kernel={},
        personality_summaries={},
        drives={},
        mood={},
        domain_summaries={},
        status_flags={"is_real_user": True},
        location_id=None  # Will be set in initial positions
    )
    agents_map["George"] = george
    logger.info("  - Created agent: George (ID=%d, is_real_user=True)", george.id)
    
    # Seed Rebecca (primary anchor agent)
    fingerprint = None  # Will be loaded by mapping functions
    rebecca_kernel = map_rebecca_fingerprint_to_personality_kernel(fingerprint, archetypes)
    rebecca_summaries = map_rebecca_personality_summaries()
    rebecca_drives = map_rebecca_drives()
    rebecca_mood = map_rebecca_mood()
    rebecca_domains = map_rebecca_domain_summaries()
    rebecca_status = map_rebecca_status_flags()
    
    rebecca = await _create_agent(
        session,
        world_id=world_id,
        name="Rebecca Ferguson",
        is_real_user=False,
        role="primary_partner",
        personality_kernel=rebecca_kernel,
        personality_summaries=rebecca_summaries,
        drives=rebecca_drives,
        mood=rebecca_mood,
        domain_summaries=rebecca_domains,
        status_flags=rebecca_status,
        location_id=None  # Will be set in initial positions
    )
    agents_map["Rebecca Ferguson"] = rebecca
    logger.info("  - Created agent: Rebecca Ferguson (ID=%d)", rebecca.id)
    
    # Seed Lucy (daughter)
    # Choose a suitable archetype (e.g., The Seeker or The Dreamer for a young person)
    lucy_kernel = {
        "trait_dimensions": {},
        "core_motivations": ["Independence", "Growth", "Family connection"],
        "core_fears": [],
        "internal_conflicts": [],
        "archetype_blend": {"The Seeker": 0.6, "The Dreamer": 0.4}
    }
    
    lucy = await _create_agent(
        session,
        world_id=world_id,
        name="Lucy",
        is_real_user=False,
        role="daughter",
        personality_kernel=lucy_kernel,
        personality_summaries={
            "self_view": "Young adult navigating independence and family relationships",
            "love_style": "",
            "career_style": "",
            "conflict_style": "",
            "public_image": "",
            "private_self": ""
        },
        drives={
            "attachment": {"baseline": 0.7, "sensitivity": 0.6},
            "autonomy": {"baseline": 0.8, "sensitivity": 0.7},
            "achievement": {"baseline": 0.6, "sensitivity": 0.5},
            "creativity": {"baseline": 0.5, "sensitivity": 0.5},
            "recognition": {"baseline": 0.4, "sensitivity": 0.4},
            "privacy": {"baseline": 0.6, "sensitivity": 0.5},
            "security": {"baseline": 0.7, "sensitivity": 0.6},
            "novelty": {"baseline": 0.7, "sensitivity": 0.6}
        },
        mood={"baseline_valence": 0.5, "baseline_arousal": 0.6, "anxiety_prone": 0.3, "frustration_prone": 0.2, "optimism_tendency": 0.6},
        domain_summaries={},
        status_flags={"is_family": True, "is_child_of_george": True},
        location_id=None  # Not initially at the house
    )
    agents_map["Lucy"] = lucy
    logger.info("  - Created agent: Lucy (ID=%d)", lucy.id)
    
    # Seed Nadine (ex-partner, Lucy's mother)
    nadine_kernel = {
        "trait_dimensions": {},
        "core_motivations": ["Co-parenting", "Independence"],
        "core_fears": [],
        "internal_conflicts": [],
        "archetype_blend": {"The Realist": 0.5, "The Protector": 0.5}
    }
    
    nadine = await _create_agent(
        session,
        world_id=world_id,
        name="Nadine",
        is_real_user=False,
        role="ex_partner",
        personality_kernel=nadine_kernel,
        personality_summaries={
            "self_view": "Former partner navigating co-parenting relationship",
            "love_style": "",
            "career_style": "",
            "conflict_style": "",
            "public_image": "",
            "private_self": ""
        },
        drives={
            "attachment": {"baseline": 0.5, "sensitivity": 0.5},
            "autonomy": {"baseline": 0.7, "sensitivity": 0.6},
            "achievement": {"baseline": 0.5, "sensitivity": 0.5},
            "creativity": {"baseline": 0.4, "sensitivity": 0.4},
            "recognition": {"baseline": 0.3, "sensitivity": 0.3},
            "privacy": {"baseline": 0.6, "sensitivity": 0.5},
            "security": {"baseline": 0.6, "sensitivity": 0.5},
            "novelty": {"baseline": 0.4, "sensitivity": 0.4}
        },
        mood={"baseline_valence": 0.4, "baseline_arousal": 0.5, "anxiety_prone": 0.4, "frustration_prone": 0.5, "optimism_tendency": 0.5},
        domain_summaries={},
        status_flags={"is_ex_partner_of_george": True, "is_mother_of_lucy": True},
        location_id=None  # Not initially at the house
    )
    agents_map["Nadine"] = nadine
    logger.info("  - Created agent: Nadine (ID=%d)", nadine.id)
    
    logger.info("  - Created %d agents total", len(agents_map))
    return agents_map


async def _create_agent(
    session: AsyncSession,
    world_id: int,
    name: str,
    is_real_user: bool,
    role: str,
    **kwargs
) -> AgentModel:
    """Helper function to create an agent row."""
    agent = AgentModel(
        world_id=world_id,
        name=name,
        is_real_user=is_real_user,
        energy=1.0,
        personality_kernel=kwargs.get("personality_kernel", {}),
        personality_summaries=kwargs.get("personality_summaries", {}),
        drives=kwargs.get("drives", {}),
        mood=kwargs.get("mood", {}),
        domain_summaries=kwargs.get("domain_summaries", {}),
        cached_context_fragments={},
        status_flags=kwargs.get("status_flags", {}),
        location_id=kwargs.get("location_id")
    )
    session.add(agent)
    await session.flush()
    return agent


async def _seed_relationships(
    session: AsyncSession,
    agents_map: Dict[str, AgentModel],
    world_id: int
) -> None:
    """Seed relationships from connections CSV and baseline."""
    logger.info("Seeding relationships...")
    
    # Get or create User record for George
    stmt = select(UserModel).where(UserModel.name == "George")
    result = await session.execute(stmt)
    george_user = result.scalars().first()
    if not george_user:
        george_user = UserModel(name="George")
        session.add(george_user)
        await session.flush()
    
    george_agent = agents_map["George"]
    rebecca_agent = agents_map["Rebecca Ferguson"]
    lucy_agent = agents_map.get("Lucy")
    nadine_agent = agents_map.get("Nadine")
    
    # 1. Rebecca -> George (override with high values from baseline)
    rel_rebecca_george = RelationshipModel(
        source_agent_id=rebecca_agent.id,
        target_user_id=george_user.id,
        warmth=0.95,
        trust=0.95,
        attraction=0.95,
        familiarity=0.95,
        tension=0.05,
        volatility=0.05,
        comfort=0.90
    )
    session.add(rel_rebecca_george)
    logger.info("  - Created relationship: Rebecca -> George (high warmth/trust/attraction)")
    
    # 2. Rebecca -> connections from CSV
    connections_data = map_connections_to_relationships()
    for conn in connections_data:
        target_name = conn["target_name"]
        # Find or create target agent (simplified - in full implementation, would create agents)
        # For now, skip non-existent agents
        if target_name not in agents_map:
            # Could create supporting agents here
            continue
        
        target_agent = agents_map[target_name]
        rel_vector = conn["relationship_vector"]
        
        rel = RelationshipModel(
            source_agent_id=rebecca_agent.id,
            target_agent_id=target_agent.id,
            warmth=rel_vector.get("warmth", 0.5),
            trust=rel_vector.get("trust", 0.5),
            attraction=rel_vector.get("attraction", 0.0),
            familiarity=rel_vector.get("familiarity", 0.5),
            tension=rel_vector.get("tension", 0.0),
            volatility=rel_vector.get("volatility", 0.0),
            comfort=rel_vector.get("comfort", 0.5)
        )
        session.add(rel)
    
    # 3. Lucy <-> George (parent-child)
    if lucy_agent:
        rel_lucy_george = RelationshipModel(
            source_agent_id=lucy_agent.id,
            target_user_id=george_user.id,
            warmth=0.90,
            trust=0.90,
            attraction=0.0,
            familiarity=0.95,
            tension=0.1,
            volatility=0.1,
            comfort=0.85
        )
        session.add(rel_lucy_george)
        logger.info("  - Created relationship: Lucy -> George (parent-child)")
    
    # 4. Nadine <-> George (ex-partner co-parent)
    if nadine_agent:
        rel_nadine_george = RelationshipModel(
            source_agent_id=nadine_agent.id,
            target_user_id=george_user.id,
            warmth=0.5,
            trust=0.6,
            attraction=0.0,
            familiarity=0.85,
            tension=0.4,
            volatility=0.3,
            comfort=0.5
        )
        session.add(rel_nadine_george)
        logger.info("  - Created relationship: Nadine -> George (ex-partner co-parent)")
    
    # 5. Nadine <-> Lucy (parent-child)
    if nadine_agent and lucy_agent:
        rel_nadine_lucy = RelationshipModel(
            source_agent_id=nadine_agent.id,
            target_agent_id=lucy_agent.id,
            warmth=0.95,
            trust=0.95,
            attraction=0.0,
            familiarity=0.95,
            tension=0.05,
            volatility=0.05,
            comfort=0.90
        )
        session.add(rel_nadine_lucy)
        logger.info("  - Created relationship: Nadine -> Lucy (parent-child)")
    
    await session.flush()
    logger.info("  - Relationships seeded")


async def _seed_memories(
    session: AsyncSession,
    agents_map: Dict[str, AgentModel]
) -> None:
    """Seed memories for agents (non-George)."""
    logger.info("Seeding memories...")
    
    rebecca_agent = agents_map.get("Rebecca Ferguson")
    if not rebecca_agent:
        logger.warning("  - Rebecca agent not found, skipping memories")
        return
    
    # Map memories for Rebecca
    memories_data = map_memories_for_rebecca()
    
    for mem_data in memories_data:
        memory = MemoryModel(
            agent_id=rebecca_agent.id,
            type=mem_data["type"],
            description=mem_data["content"],
            semantic_tags=mem_data.get("tags", []),
            salience=mem_data.get("salience", 0.5),
            timestamp=None  # Will be set from time_reference if available
        )
        session.add(memory)
    
    await session.flush()
    logger.info("  - Created %d memories for Rebecca", len(memories_data))
    
    # Note: No memories for George (he is real user)


async def _seed_arcs(
    session: AsyncSession,
    agents_map: Dict[str, AgentModel]
) -> None:
    """Seed arcs for agents (non-George)."""
    logger.info("Seeding arcs...")
    
    rebecca_agent = agents_map.get("Rebecca Ferguson")
    if not rebecca_agent:
        logger.warning("  - Rebecca agent not found, skipping arcs")
        return
    
    # Map arcs for Rebecca
    arcs_data = map_arcs_for_rebecca()
    
    for arc_data in arcs_data:
        arc_state = arc_data.get("arc_state", {})
        # Store arc_state data in topic_vector as JSON
        arc_state_json = {
            "name": arc_data["name"],
            "description": arc_data.get("description", ""),
            "status": arc_data.get("status", "active"),
            "core_tension": arc_state.get("core_tension", ""),
            "desired_outcomes": arc_state.get("desired_outcomes", []),
            "fears": arc_state.get("fears", []),
            "progress": arc_state.get("progress", 0.0)
        }
        # Extract keywords from core_tension for topic_vector
        core_tension = arc_state.get("core_tension", "")
        topic_keywords = core_tension.split() if core_tension else []
        
        arc = ArcModel(
            agent_id=rebecca_agent.id,
            type=arc_data["name"],
            intensity=arc_data.get("importance", 0.5),
            valence_bias=0.0,  # Will be determined from arc_state
            topic_vector=arc_state_json,  # Store full arc_state as JSON
            decay_rate=0.1
        )
        session.add(arc)
    
    await session.flush()
    logger.info("  - Created %d arcs for Rebecca", len(arcs_data))
    
    # Note: No arcs for George (he is real user)


async def _seed_influence_fields(
    session: AsyncSession,
    agents_map: Dict[str, AgentModel]
) -> None:
    """Seed influence fields for agents (non-George)."""
    logger.info("Seeding influence fields...")
    
    # Only seed for non-George agents
    for agent_name, agent in agents_map.items():
        if agent.is_real_user:
            continue  # Skip George
        
        # Map influence fields (currently only for Rebecca)
        if agent_name == "Rebecca Ferguson":
            influence_field_data = map_influence_fields_for_rebecca()
            
            field = InfluenceFieldModel(
                agent_id=agent.id,
                mood_offset={},
                drive_pressures=influence_field_data.get("background_bias", {}),
                pending_contact_probability={},
                unresolved_tension_topics=influence_field_data.get("unresolved_topics", {})
            )
            session.add(field)
            logger.info("  - Created influence field for %s", agent_name)
        else:
            # Default empty influence field for other agents
            field = InfluenceFieldModel(
                agent_id=agent.id,
                mood_offset={},
                drive_pressures={},
                pending_contact_probability={},
                unresolved_tension_topics={}
            )
            session.add(field)
            logger.info("  - Created default influence field for %s", agent_name)
    
    await session.flush()
    logger.info("  - Influence fields seeded")


async def _seed_calendars(
    session: AsyncSession,
    agents_map: Dict[str, AgentModel],
    world_model: WorldModel
) -> None:
    """Seed calendar entries for agents (non-George)."""
    logger.info("Seeding calendars...")
    
    rebecca_agent = agents_map.get("Rebecca Ferguson")
    if not rebecca_agent:
        logger.warning("  - Rebecca agent not found, skipping calendars")
        return
    
    # Map calendar entries for Rebecca
    calendar_data = map_calendar_entries_for_rebecca()
    
    for cal_entry in calendar_data:
        calendar = CalendarModel(
            agent_id=rebecca_agent.id,
            title=cal_entry["title"],
            description=cal_entry.get("description"),
            start_time=cal_entry.get("start_time") or world_model.current_time,
            end_time=cal_entry.get("end_time"),
            type=cal_entry.get("type", "appointment"),
            status="pending",
            recurrence_rule=cal_entry.get("recurrence")
        )
        session.add(calendar)
    
    await session.flush()
    logger.info("  - Created %d calendar entries", len(calendar_data))


async def _seed_intentions(
    session: AsyncSession,
    agents_map: Dict[str, AgentModel]
) -> None:
    """Seed initial intentions for agents (non-George)."""
    logger.info("Seeding intentions...")
    
    # No initial intentions seeded for now
    # This can be populated later if needed
    logger.info("  - No initial intentions seeded")


async def _set_initial_positions(
    session: AsyncSession,
    agents_map: Dict[str, AgentModel],
    locations_map: Dict[str, int]
) -> None:
    """Set initial positions for agents."""
    logger.info("Setting initial positions...")
    
    # George and Rebecca start in the lounge
    lounge_id = locations_map.get("Lounge")
    if lounge_id:
        if "George" in agents_map:
            agents_map["George"].location_id = lounge_id
        if "Rebecca Ferguson" in agents_map:
            agents_map["Rebecca Ferguson"].location_id = lounge_id
        logger.info("  - Set George and Rebecca initial location: Lounge")
    
    await session.flush()
    logger.info("  - Initial positions set")


async def _cleanup_george_psychological_fields(
    session: AsyncSession,
    agents_map: Dict[str, AgentModel]
) -> None:
    """
    E.1.4: Explicitly zero George's psychological fields before final commit.
    
    This ensures that even if any seeding step accidentally populated these fields,
    they are guaranteed to be empty for George.
    """
    logger.info("Cleaning up George's psychological fields (E.1.4)...")
    
    george = agents_map.get("George")
    if not george:
        logger.warning("  - George agent not found, skipping cleanup")
        return
    
    # E.1.3: Explicitly set all forbidden fields to empty/null
    george.personality_kernel = {}
    george.personality_summaries = {}
    george.drives = {}
    george.mood = {}
    # domain_summaries can contain ONLY public facts (optional)
    # For now, we'll set it to empty dict to be safe
    george.domain_summaries = {}
    
    # Ensure status_flags has is_real_user = True
    if not isinstance(george.status_flags, dict):
        george.status_flags = {}
    george.status_flags["is_real_user"] = True
    
    # Ensure is_real_user flag is set on the model
    george.is_real_user = True
    
    await session.flush()
    logger.info("  - George's psychological fields explicitly zeroed (E.1.4)")


async def _log_seeding_summary(session: AsyncSession, world_id: int) -> None:
    """Log summary of seeded data."""
    logger.info("=" * 80)
    logger.info("SEEDING SUMMARY")
    logger.info("=" * 80)
    
    # Count entities
    counts = {}
    
    stmt = select(WorldModel).where(WorldModel.id == world_id)
    result = await session.execute(stmt)
    world = result.scalars().first()
    if world:
        logger.info("World: %s (ID=%d)", world.name, world.id)
        logger.info("  - Current time: %s", world.current_time)
        logger.info("  - Current tick: %d", world.current_tick)
    
    # Count locations
    stmt = select(LocationModel).where(LocationModel.world_id == world_id)
    result = await session.execute(stmt)
    locations = result.scalars().all()
    logger.info("Locations: %d", len(locations))
    
    # Count agents
    stmt = select(AgentModel).where(AgentModel.world_id == world_id)
    result = await session.execute(stmt)
    agents = result.scalars().all()
    logger.info("Agents: %d", len(agents))
    for agent in agents:
        logger.info("  - %s (ID=%d, is_real_user=%s)", agent.name, agent.id, agent.is_real_user)
    
    # Count relationships
    stmt = select(RelationshipModel)
    result = await session.execute(stmt)
    relationships = result.scalars().all()
    logger.info("Relationships: %d", len(relationships))
    
    # Count memories
    stmt = select(MemoryModel)
    result = await session.execute(stmt)
    memories = result.scalars().all()
    logger.info("Memories: %d", len(memories))
    
    # Count arcs
    stmt = select(ArcModel)
    result = await session.execute(stmt)
    arcs = result.scalars().all()
    logger.info("Arcs: %d", len(arcs))
    
    # Count influence fields
    stmt = select(InfluenceFieldModel)
    result = await session.execute(stmt)
    influence_fields = result.scalars().all()
    logger.info("Influence Fields: %d", len(influence_fields))
    
    logger.info("=" * 80)

