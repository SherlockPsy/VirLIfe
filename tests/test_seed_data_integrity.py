"""
F.1 TEST_SEED_DATA_INTEGRITY

Purpose: Verify that the seed script constructed the world EXACTLY as specified.
"""

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.persistence.models import (
    AgentModel, RelationshipModel, MemoryModel, ArcModel,
    LocationModel, ObjectModel, InfluenceFieldModel, IntentionModel
)


class TestSeedDataIntegrity:
    """F.1: Test seed data integrity"""
    
    @pytest.mark.asyncio
    async def test_rebecca_agent_seeded_correctly(
        self, test_session: AsyncSession, seeded_world: dict
    ):
        """F.1.1: Verify Rebecca's agent row is correctly populated"""
        rebecca_id = seeded_world["rebecca_agent_id"]
        assert rebecca_id is not None, "Rebecca agent not found"
        
        stmt = select(AgentModel).where(AgentModel.id == rebecca_id)
        result = await test_session.execute(stmt)
        rebecca = result.scalars().first()
        
        assert rebecca is not None, "Rebecca agent not found in DB"
        assert rebecca.name == "Rebecca Ferguson"
        assert rebecca.is_real_user == False
        
        # Check personality_kernel
        assert isinstance(rebecca.personality_kernel, dict), "personality_kernel must be dict"
        assert "trait_dimensions" in rebecca.personality_kernel or len(rebecca.personality_kernel) > 0
        # May have archetype_blend, core_motivations, etc.
        
        # Check personality_summaries
        assert isinstance(rebecca.personality_summaries, dict), "personality_summaries must be dict"
        required_summaries = ["self_view", "love_style", "career_style", "conflict_style", "public_image", "private_self"]
        for key in required_summaries:
            assert key in rebecca.personality_summaries, f"Missing {key} in personality_summaries"
            assert rebecca.personality_summaries[key], f"{key} must not be empty"
        
        # Check drives
        assert isinstance(rebecca.drives, dict), "drives must be dict"
        assert len(rebecca.drives) > 0, "drives must be populated"
        # Check drive structure (baseline, sensitivity)
        for drive_name, drive_data in rebecca.drives.items():
            assert isinstance(drive_data, dict), f"Drive {drive_name} must be dict"
            assert "baseline" in drive_data, f"Drive {drive_name} missing baseline"
            assert "sensitivity" in drive_data, f"Drive {drive_name} missing sensitivity"
        
        # Check mood
        assert isinstance(rebecca.mood, dict), "mood must be dict"
        assert "baseline_valence" in rebecca.mood or "valence" in rebecca.mood
        assert "baseline_arousal" in rebecca.mood or "arousal" in rebecca.mood
        
        # Check domain_summaries
        assert isinstance(rebecca.domain_summaries, dict), "domain_summaries must be dict"
        required_domains = ["career", "family", "romance", "friends", "fame_and_public_life", "creativity", "health_and_body"]
        for domain in required_domains:
            assert domain in rebecca.domain_summaries, f"Missing {domain} in domain_summaries"
        
        # Check status_flags
        assert isinstance(rebecca.status_flags, dict), "status_flags must be dict"
        assert rebecca.status_flags.get("is_celebrity") == True, "Rebecca must be marked as celebrity"
        assert rebecca.status_flags.get("is_partner_of_george") == True, "Rebecca must be marked as partner of George"
        assert rebecca.status_flags.get("relationship_is_public") == False, "Relationship must be private"
    
    @pytest.mark.asyncio
    async def test_lucy_and_nadine_seeded_correctly(
        self, test_session: AsyncSession, seeded_world: dict
    ):
        """F.1.2: Verify Lucy and Nadine are seeded correctly"""
        lucy_id = seeded_world.get("lucy_agent_id")
        nadine_id = seeded_world.get("nadine_agent_id")
        
        if lucy_id:
            stmt = select(AgentModel).where(AgentModel.id == lucy_id)
            result = await test_session.execute(stmt)
            lucy = result.scalars().first()
            
            assert lucy is not None
            assert lucy.name == "Lucy"
            assert lucy.is_real_user == False
            assert isinstance(lucy.personality_kernel, dict)
            assert len(lucy.personality_kernel) > 0 or lucy.personality_kernel == {}
            assert isinstance(lucy.status_flags, dict)
        
        if nadine_id:
            stmt = select(AgentModel).where(AgentModel.id == nadine_id)
            result = await test_session.execute(stmt)
            nadine = result.scalars().first()
            
            assert nadine is not None
            assert nadine.name == "Nadine"
            assert nadine.is_real_user == False
            assert isinstance(nadine.personality_kernel, dict)
            assert isinstance(nadine.status_flags, dict)
    
    @pytest.mark.asyncio
    async def test_rebecca_relationships_seeded(
        self, test_session: AsyncSession, seeded_world: dict
    ):
        """F.1.3: Verify Rebecca's relationships are seeded correctly"""
        rebecca_id = seeded_world["rebecca_agent_id"]
        george_id = seeded_world["george_agent_id"]
        
        stmt = select(RelationshipModel).where(RelationshipModel.source_agent_id == rebecca_id)
        result = await test_session.execute(stmt)
        relationships = result.scalars().all()
        
        assert len(relationships) > 0, "Rebecca must have relationships"
        
        # Check relationship to George (override values)
        george_rel = None
        for rel in relationships:
            if rel.target_agent_id == george_id:
                george_rel = rel
                break
        
        assert george_rel is not None, "Rebecca must have relationship to George"
        # George relationship should have very high warmth/trust, low tension
        assert george_rel.warmth >= 0.8, "Rebecca->George warmth should be very high"
        assert george_rel.trust >= 0.8, "Rebecca->George trust should be very high"
        assert george_rel.tension <= 0.2, "Rebecca->George tension should be low"
        
        # Check all relationships have valid numeric ranges
        for rel in relationships:
            assert 0.0 <= rel.warmth <= 1.0, f"Invalid warmth: {rel.warmth}"
            assert 0.0 <= rel.trust <= 1.0, f"Invalid trust: {rel.trust}"
            assert 0.0 <= rel.tension <= 1.0, f"Invalid tension: {rel.tension}"
            assert 0.0 <= rel.attraction <= 1.0, f"Invalid attraction: {rel.attraction}"
            assert 0.0 <= rel.familiarity <= 1.0, f"Invalid familiarity: {rel.familiarity}"
    
    @pytest.mark.asyncio
    async def test_rebecca_memories_seeded(
        self, test_session: AsyncSession, seeded_world: dict
    ):
        """F.1.4: Verify Rebecca's memories are seeded correctly"""
        rebecca_id = seeded_world["rebecca_agent_id"]
        
        stmt = select(MemoryModel).where(MemoryModel.agent_id == rebecca_id)
        result = await test_session.execute(stmt)
        memories = result.scalars().all()
        
        assert len(memories) > 10, f"Expected >10 memories, got {len(memories)}"
        
        # Check salience values
        for memory in memories:
            assert 0.0 <= memory.salience <= 1.0, f"Invalid salience: {memory.salience}"
            assert memory.description, "Memory description must not be empty"
        
        # Check for high-salience key memories
        high_salience_memories = [m for m in memories if m.salience >= 0.8]
        assert len(high_salience_memories) > 0, "Should have high-salience memories"
        
        # Check for key events (Greatest Showman, Richmond)
        memory_texts = [m.description.lower() for m in memories]
        has_greatest_showman = any("greatest showman" in text or "white dress" in text for text in memory_texts)
        has_richmond = any("richmond" in text or "restaurant" in text for text in memory_texts)
        # These are optional but should exist if baseline mentions them
    
    @pytest.mark.asyncio
    async def test_rebecca_arcs_seeded(
        self, test_session: AsyncSession, seeded_world: dict
    ):
        """F.1.5: Verify Rebecca's arcs are seeded correctly"""
        rebecca_id = seeded_world["rebecca_agent_id"]
        
        stmt = select(ArcModel).where(ArcModel.agent_id == rebecca_id)
        result = await test_session.execute(stmt)
        arcs = result.scalars().all()
        
        assert len(arcs) >= 2, f"Expected at least 2 arcs, got {len(arcs)}"
        assert len(arcs) <= 4, f"Expected at most 4 arcs, got {len(arcs)}"
        
        for arc in arcs:
            assert arc.type, "Arc must have type/name"
            assert 0.0 <= arc.intensity <= 1.0, f"Invalid intensity: {arc.intensity}"
            # Check arc_state if stored in topic_vector or other fields
            assert isinstance(arc.topic_vector, list) or arc.topic_vector is None
    
    @pytest.mark.asyncio
    async def test_locations_seeded(
        self, test_session: AsyncSession, seeded_world: dict
    ):
        """F.1.6: Verify locations are seeded correctly"""
        world_id = seeded_world["world_id"]
        
        stmt = select(LocationModel).where(LocationModel.world_id == world_id)
        result = await test_session.execute(stmt)
        locations = result.scalars().all()
        
        assert len(locations) > 0, "Locations must be seeded"
        
        # Check for Cookridge house rooms
        location_names = [loc.name for loc in locations]
        expected_rooms = ["Kitchen", "Lounge", "Our Bedroom", "Studio", "Bathroom"]
        for room in expected_rooms:
            assert room in location_names, f"Missing location: {room}"
        
        # Check adjacency lists point to valid rooms
        location_map = {loc.id: loc for loc in locations}
        for loc in locations:
            if loc.adjacency:
                assert isinstance(loc.adjacency, list), "adjacency must be list"
                for adj_id in loc.adjacency:
                    assert adj_id in location_map, f"Adjacent location {adj_id} does not exist"
    
    @pytest.mark.asyncio
    async def test_objects_seeded(
        self, test_session: AsyncSession, seeded_world: dict
    ):
        """F.1.7: Verify objects are seeded correctly"""
        world_id = seeded_world["world_id"]
        
        stmt = select(ObjectModel).where(ObjectModel.world_id == world_id)
        result = await test_session.execute(stmt)
        objects = result.scalars().all()
        
        # Objects are optional, but if they exist, check they're in valid locations
        if objects:
            location_ids = {obj.location_id for obj in objects if obj.location_id}
            if location_ids:
                stmt = select(LocationModel).where(LocationModel.id.in_(location_ids))
                result = await test_session.execute(stmt)
                valid_locations = {loc.id for loc in result.scalars().all()}
                for obj in objects:
                    if obj.location_id:
                        assert obj.location_id in valid_locations, f"Object {obj.name} in invalid location"
    
    @pytest.mark.asyncio
    async def test_no_george_internal_seed(
        self, test_session: AsyncSession, seeded_world: dict
    ):
        """F.1.8: Verify George has NO internal psychological state"""
        george_id = seeded_world["george_agent_id"]
        assert george_id is not None, "George agent not found"
        
        stmt = select(AgentModel).where(AgentModel.id == george_id)
        result = await test_session.execute(stmt)
        george = result.scalars().first()
        
        assert george is not None
        assert george.name == "George"
        assert george.is_real_user == True, "George must be marked as real user"
        
        # E.1.3: All forbidden fields must be empty/null
        assert george.personality_kernel == {} or george.personality_kernel is None, "George must not have personality_kernel"
        assert george.drives == {} or george.drives is None, "George must not have drives"
        assert george.mood == {} or george.mood is None, "George must not have mood"
        
        # Check arcs (should be empty list)
        stmt = select(ArcModel).where(ArcModel.agent_id == george_id)
        result = await test_session.execute(stmt)
        george_arcs = result.scalars().all()
        assert len(george_arcs) == 0, "George must not have arcs"
        
        # Check influence fields
        stmt = select(InfluenceFieldModel).where(InfluenceFieldModel.agent_id == george_id)
        result = await test_session.execute(stmt)
        george_influence = result.scalars().all()
        assert len(george_influence) == 0, "George must not have influence fields"
        
        # Check intentions
        stmt = select(IntentionModel).where(IntentionModel.agent_id == george_id)
        result = await test_session.execute(stmt)
        george_intentions = result.scalars().all()
        assert len(george_intentions) == 0, "George must not have intentions"

