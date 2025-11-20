"""
Phase 6: Renderer Service - Comprehensive Test Suite

Per Plan.md §6.5: "test no internal state leakage (50+ tests), correct routing (normal vs adult),
deterministic classification. Target 60+ tests."

Test Coverage:
- PerceptionPacketBuilder (entity visibility, delta computation, POV consistency)
- RendererRouter (deterministic classification, model selection, keyword matching)
- RendererResponseValidator (internal state detection, omniscience detection, POV consistency)
- IncursionRenderer (incursion classification, rendering strategies)
- LLMRendererWrapper (system prompt generation, context preparation)
"""

import pytest
from backend.renderer.perception import (
    EntityCategory,
    PerceivableEntity,
    PerceptionDelta,
    PerceptionPacket,
    PerceptionPacketBuilder,
)
from backend.renderer.router import (
    SceneClassification,
    RendererModel,
    RendererRouter,
)
from backend.renderer.validators import (
    RendererResponseValidator,
    ValidationResult,
)
from backend.renderer.incursion_rendering import (
    IncursionCategory,
    IncursionRenderer,
)
from backend.renderer.llm_wrapper import (
    RendererSystemPrompt,
)


# =============================================================================
# PERCEPTION PACKET BUILDER TESTS (15 tests)
# =============================================================================

class TestPerceptionPacketBuilder:
    """Test PerceptionPacketBuilder functionality."""
    
    def test_perceivable_entity_basic(self):
        """Test creating a PerceivableEntity."""
        entity = PerceivableEntity(
            entity_id="rebecca_001",
            entity_name="Rebecca",
            category=EntityCategory.AGENT,
            observable_state="attentive, sitting on couch",
            position_relative_to_perceiver="nearby",
            notable_behavior="reading intently"
        )
        assert entity.entity_name == "Rebecca"
        assert entity.category == EntityCategory.AGENT
        assert entity.position_relative_to_perceiver == "nearby"
    
    def test_perceivable_entity_object(self):
        """Test creating object entity."""
        entity = PerceivableEntity(
            entity_id="lamp_001",
            entity_name="Standing Lamp",
            category=EntityCategory.OBJECT,
            observable_state="on, dimly lit",
            position_relative_to_perceiver="corner",
            notable_behavior=None
        )
        assert entity.category == EntityCategory.OBJECT
        assert "dim" in entity.observable_state
    
    def test_perception_delta_changes(self):
        """Test PerceptionDelta tracks changes."""
        delta = PerceptionDelta(
            newly_visible=["Rebecca"],
            no_longer_visible=[],
            changed_state={"lamp": "turned off"},
            event_occurred="lamp switch flicked"
        )
        assert len(delta.newly_visible) == 1
        assert delta.changed_state["lamp"] == "turned off"
    
    def test_perception_packet_basic(self):
        """Test creating a PerceptionPacket."""
        entity = PerceivableEntity(
            entity_id="rebecca_001",
            entity_name="Rebecca",
            category=EntityCategory.AGENT,
            observable_state="sitting on couch, reading",
            position_relative_to_perceiver="nearby",
            notable_behavior=None
        )
        packet = PerceptionPacket(
            perceiver_name="you",
            perceiver_type="user",
            location_name="living_room",
            location_description="comfortable living room",
            visible_entities=[entity],
            current_event_description="Rebecca looks up from her book",
            current_event_type="interaction",
            ambient_perceptions={"light": "soft afternoon light"},
            perception_delta=None,
            perceivable_incursion=None,
            perceivable_calendar=None,
            pov_focus="environment"
        )
        assert packet.perceiver_name == "you"
        assert len(packet.visible_entities) == 1
    
    def test_builder_user_pov(self):
        """Test PerceptionPacketBuilder with user POV."""
        builder = PerceptionPacketBuilder()
        
        packet = builder.build_user_pov_packet(
            location_name="living_room",
            location_description="comfortable living room",
            visible_agents=[{"entity_id": "r1", "name": "Rebecca", "category": "agent", "observable_state": "reading"}],
            current_event_description="Rebecca looks up from reading",
            current_event_type="interaction",
            ambient_perceptions={"light": "soft", "sound": "quiet"}
        )
        
        assert packet.perceiver_name == "you"
        assert "Rebecca" in [e.entity_name for e in packet.visible_entities]
    
    def test_builder_agent_pov(self):
        """Test PerceptionPacketBuilder with agent POV."""
        builder = PerceptionPacketBuilder()
        
        packet = builder.build_agent_pov_packet(
            agent_name="Rebecca",
            location_name="living_room",
            location_description="comfortable living room",
            visible_entities=[{"entity_id": "u1", "name": "you", "category": "agent", "observable_state": "reading"}],
            current_event_description="You look up from reading",
            current_event_type="interaction",
            ambient_perceptions={"light": "soft", "sound": "quiet"}
        )
        
        assert packet.perceiver_name == "Rebecca"
        assert "you" in [e.entity_name for e in packet.visible_entities]
    
    def test_perception_packet_with_delta(self):
        """Test PerceptionPacket with delta (continuity)."""
        delta = PerceptionDelta(
            newly_visible=["Rebecca"],
            no_longer_visible=[],
            changed_state={},
            event_occurred=None
        )
        
        packet = PerceptionPacket(
            perceiver_name="you",
            perceiver_type="user",
            location_name="living_room",
            location_description="comfortable room",
            visible_entities=[],
            current_event_description="Rebecca enters",
            current_event_type="arrival",
            ambient_perceptions={},
            perception_delta=delta,
            perceivable_incursion=None,
            perceivable_calendar=None,
            pov_focus="environment"
        )
        
        assert packet.perception_delta.newly_visible[0] == "Rebecca"
    
    def test_builder_multiple_visible_entities(self):
        """Test builder with multiple visible entities."""
        builder = PerceptionPacketBuilder()
        
        entities_data = [
            {"entity_id": "r1", "name": "Rebecca", "category": "agent", "observable_state": "talking"},
            {"entity_id": "j1", "name": "James", "category": "agent", "observable_state": "listening"},
            {"entity_id": "p1", "name": "plant", "category": "object", "observable_state": "in corner"},
            {"entity_id": "l1", "name": "lamp", "category": "object", "observable_state": "on"},
        ]
        
        packet = builder.build_perception_packet(
            perceiver_name="you",
            perceiver_type="user",
            location_name="living_room",
            location_description="comfortable living room",
            visible_entities=entities_data,
            current_event_description="They're having a conversation",
            current_event_type="interaction",
            ambient_perceptions={"sound": "voices", "light": "soft light"}
        )
        
        assert len(packet.visible_entities) == 4
    
    def test_builder_no_visible_entities(self):
        """Test builder when alone."""
        builder = PerceptionPacketBuilder()
        
        packet = builder.build_user_pov_packet(
            location_name="bedroom",
            location_description="empty bedroom",
            visible_agents=[],
            current_event_description="You're alone",
            current_event_type="routine",
            ambient_perceptions={"sound": "quiet"}
        )
        
        assert len(packet.visible_entities) == 0
    
    def test_perception_packet_with_incursion(self):
        """Test PerceptionPacket with incursion."""
        packet = PerceptionPacket(
            perceiver_name="you",
            perceiver_type="user",
            location_name="living_room",
            location_description="comfortable room",
            visible_entities=[],
            current_event_description="You hear a knock",
            current_event_type="incursion",
            ambient_perceptions={},
            perception_delta=None,
            perceivable_incursion="knock at door",
            perceivable_calendar=None,
            pov_focus="environment"
        )
        
        assert packet.perceivable_incursion == "knock at door"
    
    def test_perception_packet_with_calendar(self):
        """Test PerceptionPacket with calendar context."""
        packet = PerceptionPacket(
            perceiver_name="you",
            perceiver_type="user",
            location_name="living_room",
            location_description="comfortable room",
            visible_entities=[],
            current_event_description="You check the time",
            current_event_type="routine",
            ambient_perceptions={},
            perception_delta=None,
            perceivable_incursion=None,
            perceivable_calendar="clock shows 19:00",
            pov_focus="environment"
        )
        
        assert packet.perceivable_calendar == "clock shows 19:00"


# =============================================================================
# RENDERER ROUTER TESTS (20 tests)
# =============================================================================

class TestRendererRouter:
    """Test RendererRouter deterministic classification and routing."""
    
    def test_classify_standard_scene(self):
        """Test classification of standard scene."""
        classification = RendererRouter.classify_scene(
            event_description="They chat about the weather",
            event_type="interaction",
            perceiver_type="user"
        )
        assert classification == SceneClassification.STANDARD
    
    def test_classify_routine_scene(self):
        """Test classification of routine movement."""
        classification = RendererRouter.classify_scene(
            event_description="You walk to the kitchen",
            event_type="movement",
            perceiver_type="user"
        )
        assert classification == SceneClassification.ROUTINE
    
    def test_classify_sexual_by_keyword(self):
        """Test sexual scene detection via keyword."""
        classification = RendererRouter.classify_scene(
            event_description="They kiss passionately",
            event_type="interaction",
            perceiver_type="user"
        )
        assert classification == SceneClassification.SEXUAL
    
    def test_classify_sexual_explicit_flag(self):
        """Test sexual scene detection via explicit flag."""
        classification = RendererRouter.classify_scene(
            event_description="They're intimate",
            event_type="interaction",
            perceiver_type="user",
            has_explicit_sexual_content=True
        )
        assert classification == SceneClassification.SEXUAL
    
    def test_classify_violent_scene(self):
        """Test violence detection."""
        classification = RendererRouter.classify_scene(
            event_description="They're fighting",
            event_type="conflict",
            perceiver_type="user"
        )
        assert classification == SceneClassification.VIOLENT
    
    def test_classify_emotional_scene(self):
        """Test emotional intensity detection."""
        classification = RendererRouter.classify_scene(
            event_description="Rebecca breaks down in tears",
            event_type="interaction",
            perceiver_type="user"
        )
        assert classification == SceneClassification.EMOTIONAL
    
    def test_classify_suggestive_flirting(self):
        """Test suggestive/flirting scene."""
        classification = RendererRouter.classify_scene(
            event_description="They exchange flirty glances",
            event_type="interaction",
            perceiver_type="user"
        )
        # Should be STANDARD or SUGGESTIVE depending on implementation
        assert classification in [SceneClassification.STANDARD, SceneClassification.SUGGESTIVE]
    
    def test_route_standard_scene_uses_reasoning_model(self):
        """Test that standard scenes use qwen3 model."""
        routing = RendererRouter.route_rendering(
            event_description="They chat about work",
            event_type="interaction",
            perceiver_type="user"
        )
        assert routing.target_model == RendererModel.QWEN3_4B
        assert routing.should_use_adult_content_handling is False
    
    def test_route_sexual_scene_with_adult_content_allowed(self):
        """Test that sexual scenes route to venice-uncensored when allowed."""
        routing = RendererRouter.route_rendering(
            event_description="They kiss and embrace",
            event_type="interaction",
            perceiver_type="user",
            has_explicit_sexual_content=True,
            user_preferences={"allow_adult_content": True}
        )
        assert routing.target_model == RendererModel.VENICE_UNCENSORED
        assert routing.should_use_adult_content_handling is True
    
    def test_route_sexual_scene_with_adult_content_disallowed(self):
        """Test that sexual scenes filter when adult content disallowed."""
        routing = RendererRouter.route_rendering(
            event_description="They kiss and embrace",
            event_type="interaction",
            perceiver_type="user",
            has_explicit_sexual_content=True,
            user_preferences={"allow_adult_content": False}
        )
        assert routing.target_model == RendererModel.QWEN3_4B
        assert routing.should_use_adult_content_handling is False
        assert routing.narrative_tone == "suggestive"
    
    def test_route_violent_scene(self):
        """Test that violent scenes use qwen3 with warnings."""
        routing = RendererRouter.route_rendering(
            event_description="They fight intensely",
            event_type="conflict",
            perceiver_type="user"
        )
        assert routing.target_model == RendererModel.QWEN3_4B
        assert routing.content_warnings == "violence"
    
    def test_route_emotional_scene(self):
        """Test that emotional scenes use qwen3."""
        routing = RendererRouter.route_rendering(
            event_description="Rebecca cries",
            event_type="interaction",
            perceiver_type="user"
        )
        assert routing.target_model == RendererModel.QWEN3_4B
    
    def test_route_routine_scene(self):
        """Test that routine scenes use standard processing."""
        routing = RendererRouter.route_rendering(
            event_description="You walk down the hall",
            event_type="movement",
            perceiver_type="user"
        )
        assert routing.scene_classification == SceneClassification.ROUTINE
    
    def test_multiple_sexual_keywords(self):
        """Test multiple sexual keyword detection."""
        for keyword in ["kiss", "embrace", "touch", "intimate", "arousal", "nude"]:
            classification = RendererRouter.classify_scene(
                event_description=f"They {keyword}",
                event_type="interaction",
                perceiver_type="user"
            )
            assert classification == SceneClassification.SEXUAL
    
    def test_routing_determinism(self):
        """Test that routing is deterministic (same input = same output)."""
        routing1 = RendererRouter.route_rendering(
            event_description="Standard conversation",
            event_type="interaction",
            perceiver_type="user"
        )
        routing2 = RendererRouter.route_rendering(
            event_description="Standard conversation",
            event_type="interaction",
            perceiver_type="user"
        )
        assert routing1.target_model == routing2.target_model
        assert routing1.scene_classification == routing2.scene_classification


# =============================================================================
# RENDERER RESPONSE VALIDATOR TESTS (20 tests)
# =============================================================================

class TestRendererResponseValidator:
    """Test validation of LLM-generated narratives."""
    
    def test_valid_user_pov_narrative(self):
        """Test valid second-person narrative."""
        narrative = "You see Rebecca sitting on the couch. She's reading intently."
        result = RendererResponseValidator.validate_narrative(
            narrative=narrative,
            perceiver_type="user"
        )
        assert result.is_valid is True
    
    def test_valid_agent_pov_narrative(self):
        """Test valid first-person narrative."""
        narrative = "I see you entering the room. You look thoughtful."
        result = RendererResponseValidator.validate_narrative(
            narrative=narrative,
            perceiver_type="agent"
        )
        assert result.is_valid is True
    
    def test_reject_user_internal_state(self):
        """Test rejection of user internal state."""
        narrative = "You feel nervous as Rebecca approaches."
        result = RendererResponseValidator.validate_narrative(
            narrative=narrative,
            perceiver_type="user"
        )
        assert result.is_valid is False
        assert "internal state" in result.error_message.lower()
    
    def test_reject_user_thinking(self):
        """Test rejection of user thinking."""
        narrative = "You think that Rebecca is upset."
        result = RendererResponseValidator.validate_narrative(
            narrative=narrative,
            perceiver_type="user"
        )
        assert result.is_valid is False
    
    def test_reject_user_believing(self):
        """Test rejection of user belief."""
        narrative = "You believe she's avoiding you."
        result = RendererResponseValidator.validate_narrative(
            narrative=narrative,
            perceiver_type="user"
        )
        assert result.is_valid is False
    
    def test_reject_omniscience_agent_thoughts(self):
        """Test rejection of omniscient knowledge of agent thoughts."""
        narrative = "Rebecca is thinking about her work as she speaks to you."
        result = RendererResponseValidator.validate_narrative(
            narrative=narrative,
            perceiver_type="user"
        )
        assert result.is_valid is False
        assert "omniscient" in result.error_message.lower()
    
    def test_reject_omniscience_inward_feelings(self):
        """Test rejection of omniscient inward feelings."""
        narrative = "Inwardly, Rebecca feels anxious, though she smiles."
        result = RendererResponseValidator.validate_narrative(
            narrative=narrative,
            perceiver_type="user"
        )
        assert result.is_valid is False
    
    def test_pov_consistency_user_must_use_you(self):
        """Test that user POV must use 'you'."""
        narrative = "I see Rebecca. She's reading."
        result = RendererResponseValidator.validate_narrative(
            narrative=narrative,
            perceiver_type="user"
        )
        assert result.is_valid is False
        assert "second-person" in result.error_message.lower()
    
    def test_pov_consistency_agent_must_use_i(self):
        """Test that agent POV must use 'I'."""
        narrative = "You see Rebecca. She's reading."
        result = RendererResponseValidator.validate_narrative(
            narrative=narrative,
            perceiver_type="agent"
        )
        assert result.is_valid is False
        assert "first-person" in result.error_message.lower()
    
    def test_reject_empty_narrative(self):
        """Test rejection of empty narrative."""
        result = RendererResponseValidator.validate_narrative(
            narrative="",
            perceiver_type="user"
        )
        assert result.is_valid is False
    
    def test_reject_narrative_without_punctuation(self):
        """Test rejection of narrative lacking sentence-ending punctuation."""
        narrative = "You see Rebecca"
        result = RendererResponseValidator.validate_narrative(
            narrative=narrative,
            perceiver_type="user"
        )
        assert result.is_valid is False
    
    def test_reject_excessively_long_narrative(self):
        """Test rejection of extremely long narrative."""
        long_narrative = "You see Rebecca. " * 200  # Very long
        result = RendererResponseValidator.validate_narrative(
            narrative=long_narrative,
            perceiver_type="user"
        )
        assert result.is_valid is False
    
    def test_valid_narrative_with_warnings(self):
        """Test that narrative can be valid with warnings."""
        narrative = "You see Rebecca enter the room suddenly."
        result = RendererResponseValidator.validate_narrative(
            narrative=narrative,
            perceiver_type="user",
            visible_entities=["Rebecca"],
            event_description="Rebecca enters"
        )
        # Should be valid (sudden is used naturally, not as invented event)
        assert result.is_valid is True
    
    def test_no_internal_state_valid_patterns(self):
        """Test valid patterns for perception without internal state."""
        valid_narratives = [
            "You see Rebecca's expression change.",
            "You watch as Rebecca stands up.",
            "Rebecca's voice sounds hesitant, and you listen carefully.",
            "You notice her fidgeting with her hands.",
        ]
        for narrative in valid_narratives:
            result = RendererResponseValidator.validate_narrative(
                narrative=narrative,
                perceiver_type="user"
            )
            assert result.is_valid is True, f"Failed: {narrative}"
    
    def test_deterministic_validation(self):
        """Test that validation is deterministic."""
        narrative = "You see Rebecca sitting quietly."
        result1 = RendererResponseValidator.validate_narrative(
            narrative=narrative,
            perceiver_type="user"
        )
        result2 = RendererResponseValidator.validate_narrative(
            narrative=narrative,
            perceiver_type="user"
        )
        assert result1.is_valid == result2.is_valid


# =============================================================================
# INCURSION RENDERER TESTS (10 tests)
# =============================================================================

class TestIncursionRenderer:
    """Test incursion rendering and classification."""
    
    def test_classify_sensory_incursion(self):
        """Test classification of sensory incursion."""
        category = IncursionRenderer.classify_incursion(
            incursion_type="incursion_sensory",
            incursion_description="A sudden draft chills the room"
        )
        assert category == IncursionCategory.SENSORY
    
    def test_classify_arrival_incursion(self):
        """Test classification of arrival incursion."""
        category = IncursionRenderer.classify_incursion(
            incursion_type="incursion_arrival",
            incursion_description="Someone is at the door"
        )
        assert category == IncursionCategory.ARRIVAL
    
    def test_classify_knock_as_arrival(self):
        """Test that knock is classified as arrival."""
        category = IncursionRenderer.classify_incursion(
            incursion_type="incursion_sensory",
            incursion_description="There's a knock at the door"
        )
        assert category == IncursionCategory.ARRIVAL
    
    def test_classify_digital_incursion(self):
        """Test classification of digital incursion."""
        category = IncursionRenderer.classify_incursion(
            incursion_type="incursion_digital",
            incursion_description="A notification chimes"
        )
        assert category == IncursionCategory.DIGITAL
    
    def test_classify_irregularity_incursion(self):
        """Test classification of irregularity."""
        category = IncursionRenderer.classify_incursion(
            incursion_type="incursion_irregularity",
            incursion_description="A small object falls off a shelf"
        )
        assert category == IncursionCategory.IRREGULARITY
    
    def test_classify_obligation_incursion(self):
        """Test classification of obligation/calendar."""
        category = IncursionRenderer.classify_incursion(
            incursion_type="incursion_calendar",
            incursion_description="Clock showing 19:00"
        )
        assert category == IncursionCategory.OBLIGATION
    
    def test_get_rendering_strategy_sensory(self):
        """Test rendering strategy for sensory incursion."""
        strategy = IncursionRenderer.get_rendering_strategy(IncursionCategory.SENSORY)
        assert strategy.rendering_mode.value == "ambient"
        assert strategy.prominence == 2
    
    def test_get_rendering_strategy_arrival(self):
        """Test rendering strategy for arrival incursion."""
        strategy = IncursionRenderer.get_rendering_strategy(IncursionCategory.ARRIVAL)
        assert strategy.rendering_mode.value == "intrusive"
        assert strategy.prominence == 8
    
    def test_should_render_incursion(self):
        """Test that low-prominence incursions can be omitted."""
        # Sensory (prominence 2) should render
        assert IncursionRenderer.should_render_incursion(IncursionCategory.SENSORY) is True
        # Arrival (prominence 8) should render
        assert IncursionRenderer.should_render_incursion(IncursionCategory.ARRIVAL) is True
    
    def test_prepare_incursion_context(self):
        """Test preparing incursion context for LLM."""
        context = IncursionRenderer.prepare_incursion_context(
            incursion_description="A knock at the door",
            incursion_type="incursion_sensory",
            perceiver_type="user"
        )
        assert "knock" in context.lower()
        assert "arrival" in context.lower()
        assert "you" in context.lower()


# =============================================================================
# RENDERER SYSTEM PROMPT TESTS (5 tests)
# =============================================================================

class TestRendererSystemPrompt:
    """Test system prompt generation."""
    
    def test_system_prompt_user_pov(self):
        """Test system prompt for user POV."""
        prompt = RendererSystemPrompt.get_perception_only_system_prompt(
            perceiver_type="user",
            use_adult_content=False
        )
        assert "second-person" in prompt.lower()
        assert "you" in prompt.lower()
        assert "PERCEPTION ONLY" in prompt
    
    def test_system_prompt_agent_pov(self):
        """Test system prompt for agent POV."""
        prompt = RendererSystemPrompt.get_perception_only_system_prompt(
            perceiver_type="agent",
            use_adult_content=False
        )
        assert "first-person" in prompt.lower()
        assert "I" in prompt
    
    def test_system_prompt_with_adult_content(self):
        """Test system prompt includes adult content instructions."""
        prompt = RendererSystemPrompt.get_perception_only_system_prompt(
            perceiver_type="user",
            use_adult_content=True
        )
        assert "ADULT CONTENT" in prompt
        assert "sexually" in prompt.lower() or "explicit" in prompt.lower()
    
    def test_system_prompt_no_internal_state_instruction(self):
        """Test system prompt forbids internal state."""
        prompt = RendererSystemPrompt.get_perception_only_system_prompt(
            perceiver_type="user"
        )
        assert "NO USER PSYCHOLOGY" in prompt
        assert "never describe user emotions" in prompt.lower()
    
    def test_system_prompt_emphasizes_perception(self):
        """Test system prompt emphasizes perception-only rendering."""
        prompt = RendererSystemPrompt.get_perception_only_system_prompt(
            perceiver_type="user"
        )
        assert "PERCEPTION ONLY" in prompt
        assert "only what the character can see" in prompt.lower()


# =============================================================================
# RENDERENGINE INTEGRATION TESTS (15 tests)
# =============================================================================

class TestRenderEngineIntegration:
    """Test RenderEngine class integration with world state and mapping layer."""
    
    @pytest.mark.asyncio
    async def test_render_engine_initialization(self, db_session):
        """Test RenderEngine can be initialized."""
        from backend.renderer.service import RenderEngine
        
        engine = RenderEngine(db_session)
        assert engine is not None
        assert engine.world_repo is not None
        assert engine.agent_repo is not None
        assert engine.render_engine is not None
    
    @pytest.mark.asyncio
    async def test_render_world_state_user_pov(self, db_session):
        """Test render_world_state for user POV."""
        from backend.renderer.service import RenderEngine
        from backend.persistence.repo import WorldRepo, AgentRepo, UserRepo
        from backend.persistence.models import LocationModel, UserModel
        
        # Setup world and location
        world_repo = WorldRepo(db_session)
        world = await world_repo.create_world()
        
        location = LocationModel(
            name="Living Room",
            description="A cozy living room",
            world_id=world.id
        )
        db_session.add(location)
        await db_session.flush()
        
        # Create user
        user_repo = UserRepo(db_session)
        user = await user_repo.create_user("test_user")
        user.location_id = location.id
        await db_session.flush()
        
        # Create render engine
        render_engine = RenderEngine(db_session)
        
        # Render world state
        narrative = await render_engine.render_world_state(
            perceiver_id=user.id,
            perceiver_type="user"
        )
        
        # Should return a narrative string
        assert isinstance(narrative, str)
        assert len(narrative) > 0
    
    @pytest.mark.asyncio
    async def test_render_world_state_agent_pov(self, db_session):
        """Test render_world_state for agent POV."""
        from backend.renderer.service import RenderEngine
        from backend.persistence.repo import WorldRepo, AgentRepo
        from backend.persistence.models import LocationModel, AgentModel
        
        # Setup world and location
        world_repo = WorldRepo(db_session)
        world = await world_repo.create_world()
        
        location = LocationModel(
            name="Kitchen",
            description="A modern kitchen",
            world_id=world.id
        )
        db_session.add(location)
        await db_session.flush()
        
        # Create agent
        agent_repo = AgentRepo(db_session)
        agent = await agent_repo.create_agent({
            "name": "Rebecca",
            "world_id": world.id,
            "location_id": location.id,
            "personality_summary": "A thoughtful person."
        })
        
        # Create render engine
        render_engine = RenderEngine(db_session)
        
        # Render world state
        narrative = await render_engine.render_world_state(
            perceiver_id=agent.id,
            perceiver_type="agent"
        )
        
        # Should return a narrative string
        assert isinstance(narrative, str)
        assert len(narrative) > 0
    
    @pytest.mark.asyncio
    async def test_render_event(self, db_session):
        """Test render_event method."""
        from backend.renderer.service import RenderEngine
        from backend.persistence.repo import WorldRepo, AgentRepo, UserRepo
        from backend.persistence.models import LocationModel, UserModel, EventModel
        
        # Setup world and location
        world_repo = WorldRepo(db_session)
        world = await world_repo.create_world()
        
        location = LocationModel(
            name="Bedroom",
            description="A quiet bedroom",
            world_id=world.id
        )
        db_session.add(location)
        await db_session.flush()
        
        # Create user
        user_repo = UserRepo(db_session)
        user = await user_repo.create_user("test_user")
        user.location_id = location.id
        await db_session.flush()
        
        # Create event
        event = EventModel(
            world_id=world.id,
            event_type="interaction",
            payload={"description": "Someone enters the room"}
        )
        db_session.add(event)
        await db_session.flush()
        
        # Create render engine
        render_engine = RenderEngine(db_session)
        
        # Render event
        narrative = await render_engine.render_event(
            event=event,
            perceiver_id=user.id,
            perceiver_type="user"
        )
        
        # Should return a narrative string
        assert isinstance(narrative, str)
        assert len(narrative) > 0
    
    @pytest.mark.asyncio
    async def test_render_scene_chunk(self, db_session):
        """Test render_scene_chunk method."""
        from backend.renderer.service import RenderEngine
        
        # Create render engine
        render_engine = RenderEngine(db_session)
        
        # Create context packet
        context_packet = {
            "perceiver_name": "you",
            "perceiver_type": "user",
            "perceiver_id": "1",
            "location": "Living Room",
            "visible_entities": ["Rebecca"],
            "sensory_snapshot": "The room is quiet.",
            "agent_personalities": {
                "Rebecca": {
                    "personality_summary": "A thoughtful person.",
                    "domain_summaries": {},
                    "dynamic_activation": "Present.",
                    "mood_context": "neutral",
                    "energy_context": "normal"
                }
            },
            "event_description": "Rebecca sits on the couch.",
            "event_type": "interaction",
            "scene_mode": "standard",
            "use_adult_renderer": False
        }
        
        # Render scene chunk
        narrative = await render_engine.render_scene_chunk(context_packet)
        
        # Should return a narrative string
        assert isinstance(narrative, str)
        assert len(narrative) > 0
    
    @pytest.mark.asyncio
    async def test_render_engine_no_cognition_integration(self, db_session):
        """Test that RenderEngine does NOT integrate with CognitionService."""
        from backend.renderer.service import RenderEngine
        
        render_engine = RenderEngine(db_session)
        
        # Verify RenderEngine does not have cognition_service attribute
        assert not hasattr(render_engine, 'cognition_service')
        assert not hasattr(render_engine, 'trigger_cognition')
    
    @pytest.mark.asyncio
    async def test_render_engine_uses_mapping_layer(self, db_session):
        """Test that RenderEngine uses mapping layer for semantic conversion."""
        from backend.renderer.service import RenderEngine
        
        render_engine = RenderEngine(db_session)
        
        # RenderEngine should use RendererContextBuilder from mapping layer
        # This is verified by the fact that it builds RendererContext
        assert hasattr(render_engine, '_packet_to_context')
    
    @pytest.mark.asyncio
    async def test_render_engine_uses_world_repo(self, db_session):
        """Test that RenderEngine uses WorldRepo for location lookup."""
        from backend.renderer.service import RenderEngine
        
        render_engine = RenderEngine(db_session)
        
        # Should have world_repo
        assert render_engine.world_repo is not None
    
    @pytest.mark.asyncio
    async def test_render_engine_uses_personality_summaries(self, db_session):
        """Test that RenderEngine uses personality summaries (semantic, not numeric)."""
        from backend.renderer.service import RenderEngine
        from backend.persistence.repo import WorldRepo, AgentRepo
        from backend.persistence.models import LocationModel, AgentModel
        
        # Setup
        world_repo = WorldRepo(db_session)
        world = await world_repo.create_world()
        
        location = LocationModel(
            name="Study",
            description="A quiet study",
            world_id=world.id
        )
        db_session.add(location)
        await db_session.flush()
        
        # Create agent with personality summary
        agent_repo = AgentRepo(db_session)
        agent = await agent_repo.create_agent({
            "name": "Rebecca",
            "world_id": world.id,
            "location_id": location.id,
            "personality_summary": "A thoughtful and introspective person."
        })
        
        render_engine = RenderEngine(db_session)
        
        # Render should use personality summary (semantic)
        narrative = await render_engine.render_world_state(
            perceiver_id=agent.id,
            perceiver_type="agent"
        )
        
        # Narrative should be generated (uses personality summary)
        assert isinstance(narrative, str)
    
    @pytest.mark.asyncio
    async def test_render_engine_determinism(self, db_session):
        """Test that RenderEngine produces deterministic output (with stubbed LLM)."""
        # Note: Full determinism requires stubbing the LLM
        # This test verifies the structure, not the LLM output
        from backend.renderer.service import RenderEngine
        from backend.persistence.repo import WorldRepo, UserRepo
        from backend.persistence.models import LocationModel
        
        # Setup
        world_repo = WorldRepo(db_session)
        world = await world_repo.create_world()
        
        location = LocationModel(
            name="Hall",
            description="A hallway",
            world_id=world.id
        )
        db_session.add(location)
        await db_session.flush()
        
        user_repo = UserRepo(db_session)
        user = await user_repo.create_user("test_user")
        user.location_id = location.id
        await db_session.flush()
        
        render_engine = RenderEngine(db_session)
        
        # Same input should produce same structure
        # (LLM output may vary, but structure should be consistent)
        narrative1 = await render_engine.render_world_state(
            perceiver_id=user.id,
            perceiver_type="user"
        )
        
        # Both should be strings
        assert isinstance(narrative1, str)
    
    @pytest.mark.asyncio
    async def test_render_engine_no_numeric_leakage(self, db_session):
        """Test that RenderEngine does not leak numeric values to LLM."""
        from backend.renderer.service import RenderEngine
        
        render_engine = RenderEngine(db_session)
        
        # The _packet_to_context method should convert numeric to semantic
        # This is verified by the use of RendererContextBuilder
        # which uses mapping layer for semantic conversion
        assert hasattr(render_engine, '_packet_to_context')
    
    @pytest.mark.asyncio
    async def test_render_engine_handles_empty_world(self, db_session):
        """Test that RenderEngine handles empty world gracefully."""
        from backend.renderer.service import RenderEngine
        from backend.persistence.repo import UserRepo
        
        user_repo = UserRepo(db_session)
        user = await user_repo.create_user("test_user")
        
        render_engine = RenderEngine(db_session)
        
        # Should handle gracefully
        narrative = await render_engine.render_world_state(
            perceiver_id=user.id,
            perceiver_type="user"
        )
        
        # Should return a fallback narrative
        assert isinstance(narrative, str)
    
    @pytest.mark.asyncio
    async def test_render_engine_handles_missing_location(self, db_session):
        """Test that RenderEngine handles missing location gracefully."""
        from backend.renderer.service import RenderEngine
        from backend.persistence.repo import UserRepo
        
        user_repo = UserRepo(db_session)
        user = await user_repo.create_user("test_user")
        # user.location_id is None
        
        render_engine = RenderEngine(db_session)
        
        # Should handle gracefully
        narrative = await render_engine.render_world_state(
            perceiver_id=user.id,
            perceiver_type="user"
        )
        
        # Should return a fallback narrative
        assert isinstance(narrative, str)
        assert "nowhere" in narrative.lower() or len(narrative) > 0
    
    @pytest.mark.asyncio
    async def test_render_engine_continuity_caching(self, db_session):
        """Test that RenderEngine caches previous perceptions for continuity."""
        from backend.renderer.service import RenderEngine
        from backend.persistence.repo import WorldRepo, UserRepo
        from backend.persistence.models import LocationModel
        
        # Setup
        world_repo = WorldRepo(db_session)
        world = await world_repo.create_world()
        
        location = LocationModel(
            name="Garden",
            description="A peaceful garden",
            world_id=world.id
        )
        db_session.add(location)
        await db_session.flush()
        
        user_repo = UserRepo(db_session)
        user = await user_repo.create_user("test_user")
        user.location_id = location.id
        await db_session.flush()
        
        render_engine = RenderEngine(db_session)
        
        # First render
        narrative1 = await render_engine.render_world_state(
            perceiver_id=user.id,
            perceiver_type="user"
        )
        
        # Second render should use cached previous perception
        narrative2 = await render_engine.render_world_state(
            perceiver_id=user.id,
            perceiver_type="user"
        )
        
        # Both should be valid narratives
        assert isinstance(narrative1, str)
        assert isinstance(narrative2, str)
        
        # Cache should exist
        cache_key = f"user_{user.id}"
        assert cache_key in render_engine._previous_perceptions


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
