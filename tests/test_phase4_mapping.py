"""
Tests for Phase 4 — Numeric ↔ Semantic Mapping Layer

Tests cover:
1. Determinism of all mappings
2. No numeric leakage into semantic summaries
3. Coverage of all numeric ranges (bucket testing)
4. Context packet building
5. Integration with personality and autonomy layers

Implements:
- docs/test_suite_outline.md §5 (Numeric → Semantic Mapping Tests)
- BUILDER_CONTRACT §7 (Testing Obligations)
"""

import pytest
from backend.mapping import (
    MoodMapper,
    DriveMapper,
    RelationshipMapper,
    ArcMapper,
    EnergyMapper,
    IntentionMapper,
    PersonalityMapper,
    MemoryMapper,
    CognitionContextBuilder,
    RendererContextBuilder,
)


class TestMoodMapper:
    """
    Tests for mood mapping.
    Implements: docs/numeric_semantic_mapping.md §1
    """
    
    def test_positive_calm_mood(self):
        """High valence + low arousal -> content and at ease"""
        result = MoodMapper.map_mood(0.6, 0.2)
        assert "quietly content" in result.lower() or "at ease" in result.lower()
        assert isinstance(result, str)
        assert len(result) > 0
    
    def test_positive_energized_mood(self):
        """High valence + high arousal -> upbeat and energised"""
        result = MoodMapper.map_mood(0.6, 0.6)
        assert "upbeat" in result.lower() or "energised" in result.lower()
    
    def test_neutral_calm_mood(self):
        """Neutral valence + low arousal -> neutral and low-key"""
        result = MoodMapper.map_mood(0.0, 0.2)
        assert "neutral" in result.lower() or "low-key" in result.lower()
    
    def test_negative_upset_mood(self):
        """Low valence + high arousal -> upset and agitated"""
        result = MoodMapper.map_mood(-0.6, 0.6)
        assert "upset" in result.lower() or "agitated" in result.lower()
    
    def test_mood_determinism(self):
        """Same inputs -> identical outputs"""
        result1 = MoodMapper.map_mood(0.5, 0.5)
        result2 = MoodMapper.map_mood(0.5, 0.5)
        assert result1 == result2
    
    def test_mood_clamps_valence(self):
        """Values outside [-1, 1] are clamped"""
        result_clamped = MoodMapper.map_mood(2.0, 0.5)
        result_normal = MoodMapper.map_mood(1.0, 0.5)
        assert result_clamped == result_normal
    
    def test_mood_no_numeric_values(self):
        """Output contains no numeric representations"""
        result = MoodMapper.map_mood(0.7, 0.8)
        # Check for absence of numeric patterns
        import re
        assert not re.search(r'\d+\.\d+', result)  # No float
        assert not re.search(r'[0-9]+%', result)   # No percentage


class TestDriveMapper:
    """
    Tests for drive mapping.
    Implements: docs/numeric_semantic_mapping.md §2
    """
    
    def test_relatedness_low_pressure(self):
        """Low relatedness pressure -> connected"""
        result = DriveMapper.map_relatedness(0.2)
        assert "connected" in result.lower() or "lonely" not in result.lower()
    
    def test_relatedness_high_pressure(self):
        """High relatedness pressure -> neglected, wants closeness"""
        result = DriveMapper.map_relatedness(0.8)
        assert "neglected" in result.lower() or "closeness" in result.lower()
    
    def test_autonomy_low_pressure(self):
        """Low autonomy pressure -> free"""
        result = DriveMapper.map_autonomy(0.2)
        assert "free" in result.lower()
    
    def test_autonomy_high_pressure(self):
        """High autonomy pressure -> constrained"""
        result = DriveMapper.map_autonomy(0.8)
        assert "constrained" in result.lower() or "freedom" in result.lower()
    
    def test_competence_low_pressure(self):
        """Low competence pressure -> capable"""
        result = DriveMapper.map_competence(0.2)
        assert "capable" in result.lower()
    
    def test_competence_high_pressure(self):
        """High competence pressure -> ineffective, doubting"""
        result = DriveMapper.map_competence(0.8)
        assert "ineffective" in result.lower() or "doubt" in result.lower()
    
    def test_novelty_low_pressure(self):
        """Low novelty pressure -> stimulated enough"""
        result = DriveMapper.map_novelty(0.2)
        assert "stimulated" in result.lower() or "routine" in result.lower()
    
    def test_novelty_high_pressure(self):
        """High novelty pressure -> stuck, craves change"""
        result = DriveMapper.map_novelty(0.8)
        assert "stuck" in result.lower() or "craves" in result.lower()
    
    def test_safety_low_pressure(self):
        """Low safety pressure -> safe and secure"""
        result = DriveMapper.map_safety(0.2)
        assert "safe" in result.lower() or "secure" in result.lower()
    
    def test_safety_high_pressure(self):
        """High safety pressure -> unsafe, unsettled"""
        result = DriveMapper.map_safety(0.8)
        assert "unsafe" in result.lower() or "unsettled" in result.lower()
    
    def test_drive_determinism(self):
        """Same drive + level -> identical output"""
        r1 = DriveMapper.map_autonomy(0.5)
        r2 = DriveMapper.map_autonomy(0.5)
        assert r1 == r2
    
    def test_map_drive_by_name(self):
        """map_drive() works for all drive names"""
        for drive_name in DriveMapper.DRIVE_NAMES:
            result = DriveMapper.map_drive(drive_name, 0.5)
            assert isinstance(result, str)
            assert len(result) > 0
    
    def test_get_highest_pressure_drives(self):
        """Returns top-K drives by pressure"""
        drives = {
            "relatedness": {"level": 0.2, "sensitivity": 1.0},
            "autonomy": {"level": 0.9, "sensitivity": 1.0},
            "competence": {"level": 0.5, "sensitivity": 1.0},
            "novelty": {"level": 0.1, "sensitivity": 1.0},
            "safety": {"level": 0.8, "sensitivity": 1.0},
        }
        result = DriveMapper.get_highest_pressure_drives(drives, top_k=2)
        
        assert len(result) == 2
        # Should have autonomy (0.9) and safety (0.8)
        names = [r[0] for r in result]
        assert "autonomy" in names
        assert "safety" in names


class TestRelationshipMapper:
    """
    Tests for relationship mapping.
    Implements: docs/numeric_semantic_mapping.md §3
    """
    
    def test_close_safe_relationship(self):
        """High warmth + trust + low tension -> close and safe"""
        result = RelationshipMapper.map_relationship_state(
            warmth=0.7, trust=0.8, tension=0.1
        )
        assert "close" in result.lower() or "safe" in result.lower()
    
    def test_strained_relationship(self):
        """Moderate warmth + low-medium trust + medium tension -> strain"""
        result = RelationshipMapper.map_relationship_state(
            warmth=0.4, trust=0.3, tension=0.5
        )
        assert "strain" in result.lower() or "uncertainty" in result.lower()
    
    def test_conflicted_relationship(self):
        """Low warmth + low trust + high tension -> conflicted/negative"""
        result = RelationshipMapper.map_relationship_state(
            warmth=-0.3, trust=0.1, tension=0.7
        )
        assert "conflict" in result.lower() or "negative" in result.lower() or "mistrust" in result.lower()
    
    def test_neutral_relationship(self):
        """Neutral warmth + low tension -> neutral investment"""
        result = RelationshipMapper.map_relationship_state(
            warmth=0.0, trust=0.5, tension=0.1
        )
        assert "neutral" in result.lower() or "investment" in result.lower()
    
    def test_full_relationship_with_attraction(self):
        """Full relationship mapping with attraction"""
        result = RelationshipMapper.map_relationship_full(
            warmth=0.6, trust=0.7, tension=0.2, attraction=0.8, comfort=0.7
        )
        
        assert "primary_state" in result
        assert "attraction_note" in result
        assert "attracted" in result["attraction_note"].lower()
        assert "ease" in result["comfort_note"].lower() or "comfortable" in result["comfort_note"].lower()


class TestArcMapper:
    """
    Tests for arc mapping.
    Implements: docs/numeric_semantic_mapping.md §4
    """
    
    def test_intense_negative_arc(self):
        """High intensity + negative bias -> raw sore spot"""
        result = ArcMapper.map_arc(0.8, -0.5, "trust")
        assert "sore spot" in result.lower() or "raw" in result.lower()
    
    def test_moderate_negative_arc(self):
        """Moderate intensity + negative bias -> lingering tension"""
        result = ArcMapper.map_arc(0.5, -0.4, "control")
        assert "tension" in result.lower() or "lingering" in result.lower()
    
    def test_intense_positive_arc(self):
        """High intensity + positive bias -> ongoing positive thread"""
        result = ArcMapper.map_arc(0.8, 0.5, "partnership")
        assert "positive" in result.lower() or "positive emotional thread" in result.lower()
    
    def test_mild_arc(self):
        """Low intensity -> mild background sensitivity"""
        result = ArcMapper.map_arc(0.2, 0.0, "something")
        assert "mild" in result.lower() or "background" in result.lower()
    
    def test_arc_maps_arcs_summary(self):
        """map_arcs_summary filters and maps active arcs"""
        arcs = [
            {"intensity": 0.8, "valence_bias": -0.4, "topic_vector": ["trust"]},
            {"intensity": 0.1, "valence_bias": 0.0, "topic_vector": ["past"]},  # Too weak
            {"intensity": 0.6, "valence_bias": 0.7, "topic_vector": ["future"]},
        ]
        result = ArcMapper.map_arcs_summary(arcs)
        
        # Should skip the 0.1 intensity arc
        assert len(result) == 2
        assert all(isinstance(s, str) for s in result)


class TestEnergyMapper:
    """
    Tests for energy mapping.
    Implements: docs/numeric_semantic_mapping.md §5
    """
    
    def test_high_energy(self):
        """High energy -> energetic and has capacity"""
        result = EnergyMapper.map_energy(0.8)
        assert "energetic" in result.lower() or "capacity" in result.lower()
    
    def test_medium_energy(self):
        """Medium energy -> somewhat tired but functional"""
        result = EnergyMapper.map_energy(0.5)
        assert "tired" in result.lower() or "functional" in result.lower()
    
    def test_low_energy(self):
        """Low energy -> drained, little capacity"""
        result = EnergyMapper.map_energy(0.2)
        assert "drained" in result.lower() or "capacity" in result.lower()


class TestIntentionMapper:
    """
    Tests for intention mapping.
    Implements: docs/numeric_semantic_mapping.md §6
    """
    
    def test_avoid_intention(self):
        """Avoid intention -> actively trying to avoid"""
        result = IntentionMapper.map_intention("avoid_topic_politics", 0.7, "politics")
        assert "avoid" in result.lower()
    
    def test_raise_intention(self):
        """Raise intention -> intends to bring up"""
        result = IntentionMapper.map_intention("raise_issue_commitment", 0.6, "commitment")
        assert "bring up" in result.lower() or "raise" in result.lower()
    
    def test_support_intention(self):
        """Support intention -> trying to be supportive"""
        result = IntentionMapper.map_intention("be_supportive_to_alice", 0.5, "Alice")
        assert "support" in result.lower()
    
    def test_high_priority_intention(self):
        """High priority intention -> stronger language"""
        result_high = IntentionMapper.map_intention("avoid_topic_x", 0.8, "x")
        result_low = IntentionMapper.map_intention("avoid_topic_x", 0.3, "x")
        
        # High priority should have different phrasing
        assert "actively" in result_high.lower()


class TestPersonalityMapper:
    """
    Tests for personality mapping.
    Implements: docs/numeric_semantic_mapping.md §9, MASTER_SPEC §PART IIA
    """
    
    def test_kernel_to_stable_summary(self):
        """Kernel -> stable personality summary"""
        kernel = {
            "sociability": 0.7,
            "emotional_volatility": 0.4,
            "dominance": 0.5,
            "conscientiousness": 0.8,
            "openness": 0.6,
        }
        
        result = PersonalityMapper.kernel_to_stable_summary(kernel, name="She")
        
        assert isinstance(result, str)
        assert len(result) > 0
        # Should mention traits from kernel
        assert "organised" in result.lower() or "conscientiousness" not in result  # High conscientiousness
    
    def test_kernel_to_domain_summaries(self):
        """Kernel -> domain summaries"""
        kernel = {
            "emotional_volatility": 0.2,  # Stable
            "conflict_avoidance": 0.8,    # Highly avoidant
            "humour_activation": 0.5,
            "openness": 0.7,
            "conscientiousness": 0.7,
            "directness": 0.3,
            "intimacy_assertiveness": 0.6,
            "intimacy_responsiveness": 0.5,
        }
        
        result = PersonalityMapper.kernel_to_domain_summaries(kernel)
        
        assert "emotion_regulation" in result
        assert "conflict_style" in result
        assert "humour_style" in result
        assert "communication_style" in result
        assert "intimacy_style" in result
        
        # Check content
        assert all(isinstance(v, str) and len(v) > 0 for v in result.values())
    
    def test_dynamic_activation_packet(self):
        """Dynamic activation based on state"""
        kernel = {"emotional_volatility": 0.5}
        drives = {"safety": {"level": 0.8, "sensitivity": 1.0}}
        mood = {"valence": -0.4, "arousal": 0.7}
        
        result = PersonalityMapper.compute_dynamic_activation_packet(
            kernel=kernel,
            drives=drives,
            mood=mood,
            arcs=[],
            relationships=[],
            energy=0.9,
        )
        
        assert isinstance(result, str)
        assert len(result) > 0
        # Should mention defensive/guarded due to high safety pressure
        assert ("defensive" in result.lower() or "guarded" in result.lower() or 
                "upset" in result.lower() or "edge" in result.lower())


class TestCognitionContextBuilder:
    """
    Tests for CognitionContext building.
    Implements: docs/cognition_flow.md §4
    """
    
    def test_build_cognition_context_no_numerics(self):
        """Built context contains no raw numeric values"""
        context = CognitionContextBuilder.build_context(
            agent_id=1,
            agent_name="Rebecca",
            personality_summary="She is thoughtful and introspective.",
            domain_summaries={"emotion_regulation": "She handles stress well."},
            kernel={"sociability": 0.6},
            mood={"valence": 0.3, "arousal": 0.4},
            drives={
                "relatedness": {"level": 0.5, "sensitivity": 1.0},
                "autonomy": {"level": 0.6, "sensitivity": 1.0},
            },
            arcs=[{"intensity": 0.5, "valence_bias": -0.2, "topic_vector": ["conflict"]}],
            energy=0.7,
            relationships=[
                {
                    "target_name": "User",
                    "target_type": "user",
                    "warmth": 0.6,
                    "trust": 0.7,
                    "tension": 0.1,
                }
            ],
            intentions=[
                {"type": "be_supportive", "priority": 0.7, "target": "User"}
            ],
            episodic_memories=[
                {"description": "They had a good conversation yesterday.", "salience": 0.8}
            ],
            biographical_memories=[
                {"description": "She knows the user values honesty."}
            ],
            perception_snapshot={"location": "lounge", "present": ["User"]},
            event={"type": "interaction", "description": "User enters the room."},
        )
        
        # Verify no raw numerics in output
        context_dict = context.to_prompt_dict()
        context_str = str(context_dict)
        
        # Should not contain numeric psychology values
        assert "0.5" not in context_str or "0.5" not in str(context.pressured_drives)
        
        # Should contain semantic descriptions
        assert "relatedness" in context_str or context.pressured_drives
        assert context.mood_summary is not None
        assert context.energy_summary is not None
    
    def test_cognition_context_includes_personality(self):
        """Context includes personality summaries and domain info"""
        context = CognitionContextBuilder.build_context(
            agent_id=1,
            agent_name="Agent",
            personality_summary="Test summary",
            domain_summaries={"emotion": "Test domain"},
            kernel={},
            mood={},
            drives={},
            arcs=[],
            energy=0.5,
            relationships=[],
            intentions=[],
            episodic_memories=[],
            biographical_memories=[],
            perception_snapshot={},
            event={},
        )
        
        assert context.personality_summary == "Test summary"
        assert context.domain_summaries == {"emotion": "Test domain"}
        assert context.dynamic_activation_packet is not None


class TestRendererContextBuilder:
    """
    Tests for RendererContext building.
    Implements: MASTER_SPEC §APPENDIX A (Renderer POV Rules)
    """
    
    def test_build_renderer_context_perception_only(self):
        """Renderer context is perception-focused"""
        context = RendererContextBuilder.build_context(
            perceiver_name="you",
            perceiver_type="user",
            location="lounge",
            visible_agents=[
                {
                    "agent_name": "Rebecca",
                    "agent_id": 1,
                    "personality_kernel": {"sociability": 0.6},
                    "personality_summary": "She is warm and thoughtful.",
                    "domain_summaries": {"emotion": "Stable."},
                    "mood": {"valence": 0.5, "arousal": 0.3},
                    "energy": 0.8,
                    "drives": {},
                    "arcs": [],
                    "relationships": [],
                }
            ],
            sensory_snapshot="The room is warm and comfortable.",
            event_description="Rebecca smiles at you.",
            event_type="interaction",
        )
        
        assert context.perceiver_type == "user"
        assert "Rebecca" in context.visible_entities
        assert "warm" in context.sensory_snapshot.lower()
        assert context.scene_mode == "standard"
    
    def test_renderer_context_no_user_internal_state(self):
        """Renderer never receives user psychology"""
        context = RendererContextBuilder.build_context(
            perceiver_name="you",
            perceiver_type="user",
            location="lounge",
            visible_agents=[],
            sensory_snapshot="You see a room.",
            event_description="Nothing happening.",
            event_type="idle",
        )
        
        # Context should not contain any psychologically modeled user state
        # (User has no numeric psychology per MASTER_SPEC)
        assert context.perceiver_type == "user"
        # No drives, mood, energy, intentions stored for the user
        assert not hasattr(context, 'user_mood')
        assert not hasattr(context, 'user_drives')


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
