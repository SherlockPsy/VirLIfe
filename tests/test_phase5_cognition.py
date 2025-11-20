"""
Phase 5 Tests: Cognition Service Wrapper

Comprehensive test suite for the cognition pipeline including:
- Salience calculation (determinism, all categories)
- Meaningfulness scoring (formula correctness, weighting)
- Cognition eligibility checking (4-factor logic)
- LLM response validation (schema, forbidden patterns)
- Numeric update mapping (stance shifts, intentions)
- CognitionService orchestration (end-to-end)

Per Plan.md 5.7 and docs/test_suite_outline.md §7.
"""

import pytest
from datetime import datetime, timedelta
from typing import Dict, List

from backend.cognition.salience import (
    SalienceCalculator, AgentSalienceContext, SalienceCategory
)
from backend.cognition.meaningfulness import (
    MeaningfulnessCalculator, MeaningfulnessScore, MEANINGFULNESS_WEIGHTS,
    DEFAULT_COGNITION_THRESHOLD
)
from backend.cognition.eligibility import (
    CognitionEligibilityChecker, CognitionEligibilityResult,
    EventTrivialityClassification, BehavioralChoice, BehavioralChoiceType
)
from backend.cognition.llm_wrapper import (
    LLMCognitionWrapper, LLMResponseValidator, CognitionLLMResponse,
    StanceShiftOutput, IntentionUpdateOutput
)
from backend.cognition.numeric_updates import (
    StanceShiftMapper, IntentionUpdateMapper,
    IntentionOperationType, IntentionType, IntentionHorizon
)
from backend.cognition.service import CognitionService, CognitionInput, CognitionOutput


class TestSalienceCalculator:
    """Tests for salience computation (all entity types)."""
    
    def test_drive_level_to_salience_zero(self):
        """Low drive level → low salience."""
        salience = SalienceCalculator.drive_level_to_salience(0.1)
        assert 0.0 <= salience <= 0.5
    
    def test_drive_level_to_salience_high(self):
        """High drive level → high salience."""
        salience = SalienceCalculator.drive_level_to_salience(0.9)
        assert 0.7 <= salience <= 1.0
    
    def test_drive_level_to_salience_mid(self):
        """Mid drive level → mid salience."""
        salience = SalienceCalculator.drive_level_to_salience(0.5)
        assert 0.2 <= salience <= 0.8
    
    def test_arc_intensity_to_salience_low(self):
        """Low arc intensity → low salience."""
        salience = SalienceCalculator.arc_intensity_to_salience(0.05)
        assert 0.0 <= salience <= 0.3
    
    def test_arc_intensity_to_salience_high(self):
        """High arc intensity → high salience."""
        salience = SalienceCalculator.arc_intensity_to_salience(0.95)
        assert 0.8 <= salience <= 1.0
    
    def test_compute_people_salience_physically_present(self):
        """Physically present people have high base salience."""
        people = {
            "alice": {"name": "Alice", "proximity_type": "physically_present"}
        }
        result = SalienceCalculator.compute_people_salience(people, {})
        assert result["alice"] == 1.0
    
    def test_compute_people_salience_recently_interacted(self):
        """Recently interacted people have moderate salience."""
        people = {
            "bob": {"name": "Bob", "proximity_type": "recently_interacted"}
        }
        result = SalienceCalculator.compute_people_salience(people, {})
        assert 0.5 <= result["bob"] <= 0.8
    
    def test_compute_people_salience_background(self):
        """Background people have low salience."""
        people = {
            "charlie": {"name": "Charlie", "proximity_type": "background"}
        }
        result = SalienceCalculator.compute_people_salience(people, {})
        assert result["charlie"] < 0.5
    
    def test_compute_people_salience_relationship_stakes_boost(self):
        """High relationship stakes boost salience."""
        people = {
            "alice": {"name": "Alice", "proximity_type": "mentioned"}
        }
        relationships = {
            "alice": {"warmth": 0.8, "trust": 0.7, "tension": 0.2}
        }
        result = SalienceCalculator.compute_people_salience(people, relationships)
        # Mentioned base is 0.5, relationship stakes boost it
        assert result["alice"] > 0.5
    
    def test_compute_topic_salience_no_arc(self):
        """Topics without arcs have base salience."""
        topics = ["work"]
        result = SalienceCalculator.compute_topic_salience(topics, {}, {})
        assert "work" in result
        assert 0.4 <= result["work"] <= 0.6
    
    def test_compute_topic_salience_with_hot_arc(self):
        """Topics with hot arcs have boosted salience."""
        topics = ["conflict"]
        arcs = {"conflict": {"intensity": 0.8, "valence_bias": -0.9}}
        result = SalienceCalculator.compute_topic_salience(topics, arcs, {})
        assert result["conflict"] > 0.6
    
    def test_compute_object_salience_critical(self):
        """Critical objects have high salience."""
        objects = {
            "ring": {"name": "ring", "relevance_type": "critical"}
        }
        result = SalienceCalculator.compute_object_salience(objects)
        assert result["ring"] == 0.9
    
    def test_compute_object_salience_background(self):
        """Background objects have low salience."""
        objects = {
            "table": {"name": "table", "relevance_type": "background"}
        }
        result = SalienceCalculator.compute_object_salience(objects)
        assert result["table"] == 0.2
    
    def test_compute_drive_salience_all_drives(self):
        """Drive salience computed for all drives."""
        drives = {
            "autonomy": 0.1,
            "competence": 0.5,
            "relatedness": 0.9,
            "novelty": 0.3,
            "safety": 0.2
        }
        result = SalienceCalculator.compute_drive_salience(drives)
        assert len(result) == 5
        assert result["relatedness"] > result["autonomy"]
    
    def test_compute_arc_salience_multiple_arcs(self):
        """Arc salience computed for all arcs."""
        arcs = {
            "conflict": {"intensity": 0.1},
            "intimacy": {"intensity": 0.8},
            "work": {"intensity": 0.5}
        }
        result = SalienceCalculator.compute_arc_salience(arcs)
        assert len(result) == 3
        assert result["intimacy"] > result["conflict"]
    
    def test_build_salience_context_complete(self):
        """Build complete salience context."""
        context = SalienceCalculator.build_salience_context(
            agent_id="rebecca",
            people={"alice": {"name": "Alice", "proximity_type": "physically_present"}},
            topics=["conflict"],
            objects={},
            drive_levels={"autonomy": 0.7},
            arcs={"conflict": {"intensity": 0.6}},
            agent_relationships={"alice": {"warmth": 0.5, "trust": 0.5, "tension": 0.3}},
            agent_intentions={}
        )
        assert context.agent_id == "rebecca"
        assert len(context.people_salience) == 1
        assert context.max_salience > 0


class TestMeaningfulnessCalculator:
    """Tests for meaningfulness (M) score computation."""
    
    def test_m_score_basic_computation(self):
        """M score computed correctly from components."""
        salience_context = AgentSalienceContext(
            agent_id="rebecca",
            people_salience={"alice": 0.8},
            topic_salience={"conflict": 0.6},
            object_salience={},
            drive_salience={"autonomy": 0.5},
            arc_salience={"conflict": 0.7}
        )
        drives = {"autonomy": 0.5, "competence": 0.2, "relatedness": 0.3, "novelty": 0.1, "safety": 0.6}
        arcs = {"conflict": {"intensity": 0.7}}
        rels = {"alice": {"warmth": 0.5, "trust": 0.3, "tension": 0.4}}
        
        m = MeaningfulnessCalculator.compute_m_score(
            salience_context=salience_context,
            drive_levels=drives,
            arcs=arcs,
            relationships=rels,
            energy=0.8
        )
        
        assert 0.0 <= m.total_m <= 1.0
        assert m.salience_max == 0.8
        assert m.drive_pressure_max == 0.6
        assert m.arc_hot == 0.7
        assert m.is_above_threshold == (m.total_m >= m.threshold)
    
    def test_m_score_low_energy_penalty(self):
        """Low energy reduces M score."""
        salience_context = AgentSalienceContext(
            agent_id="rebecca",
            people_salience={"alice": 0.5},
            topic_salience={},
            object_salience={},
            drive_salience={},
            arc_salience={}
        )
        m_high_energy = MeaningfulnessCalculator.compute_m_score(
            salience_context=salience_context,
            drive_levels={},
            arcs={},
            relationships={},
            energy=0.9
        )
        m_low_energy = MeaningfulnessCalculator.compute_m_score(
            salience_context=salience_context,
            drive_levels={},
            arcs={},
            relationships={},
            energy=0.1
        )
        assert m_low_energy.total_m < m_high_energy.total_m
    
    def test_m_score_above_threshold(self):
        """High M score marked as above threshold."""
        salience_context = AgentSalienceContext(
            agent_id="rebecca",
            people_salience={"alice": 1.0},
            topic_salience={"conflict": 1.0},
            object_salience={},
            drive_salience={"autonomy": 1.0},
            arc_salience={"conflict": 1.0}
        )
        m = MeaningfulnessCalculator.compute_m_score(
            salience_context=salience_context,
            drive_levels={"autonomy": 1.0, "safety": 0},
            arcs={"conflict": {"intensity": 1.0}},
            relationships={"alice": {"warmth": 1.0, "trust": 1.0, "tension": 1.0}},
            energy=1.0
        )
        assert m.is_above_threshold
    
    def test_m_score_below_threshold(self):
        """Low M score marked as below threshold."""
        salience_context = AgentSalienceContext(
            agent_id="rebecca",
            people_salience={},
            topic_salience={},
            object_salience={},
            drive_salience={},
            arc_salience={}
        )
        m = MeaningfulnessCalculator.compute_m_score(
            salience_context=salience_context,
            drive_levels={},
            arcs={},
            relationships={},
            energy=0.1
        )
        assert not m.is_above_threshold


class TestCognitionEligibilityChecker:
    """Tests for cognition eligibility (4-factor check)."""
    
    def test_factor_1_m_score_sufficient(self):
        """Factor 1: M >= threshold."""
        assert CognitionEligibilityChecker.check_factor_1_m_score(0.5, 0.4)
        assert not CognitionEligibilityChecker.check_factor_1_m_score(0.3, 0.4)
    
    def test_factor_2_event_not_trivial(self):
        """Factor 2: Event is not trivial."""
        assert CognitionEligibilityChecker.check_factor_2_event_triviality(
            EventTrivialityClassification.SIGNIFICANT
        )
        assert not CognitionEligibilityChecker.check_factor_2_event_triviality(
            EventTrivialityClassification.TRIVIAL
        )
    
    def test_factor_3_cooldown_no_prior_cognition(self):
        """Factor 3: No prior cognition → cooldown elapsed."""
        now = datetime.now()
        assert CognitionEligibilityChecker.check_factor_3_cooldown(None, now, 5)
    
    def test_factor_3_cooldown_elapsed(self):
        """Factor 3: Cooldown elapsed."""
        now = datetime.now()
        last_time = now - timedelta(minutes=10)
        assert CognitionEligibilityChecker.check_factor_3_cooldown(last_time, now, 5)
    
    def test_factor_3_cooldown_not_elapsed(self):
        """Factor 3: Cooldown not elapsed."""
        now = datetime.now()
        last_time = now - timedelta(minutes=2)
        assert not CognitionEligibilityChecker.check_factor_3_cooldown(last_time, now, 5)
    
    def test_factor_3_cooldown_remaining(self):
        """Factor 3: Get remaining cooldown time."""
        now = datetime.now()
        last_time = now - timedelta(minutes=2)
        remaining = CognitionEligibilityChecker.check_factor_3_cooldown_remaining(
            last_time, now, 5
        )
        assert remaining is not None
        assert remaining.total_seconds() > 0
        assert remaining.total_seconds() <= 180  # ~3 minutes (=180 at boundary)
    
    def test_factor_4_behavioral_choice_non_trivial(self):
        """Factor 4: Non-trivial behavioral choice exists."""
        choices = [
            BehavioralChoice(
                choice_type=BehavioralChoiceType.ESCALATION_VS_DEESCALATION,
                description="escalate or deescalate",
                stakes=0.5
            )
        ]
        assert CognitionEligibilityChecker.check_factor_4_behavioral_choice(choices)
    
    def test_factor_4_behavioral_choice_all_trivial(self):
        """Factor 4: No non-trivial choice."""
        choices = [
            BehavioralChoice(
                choice_type=BehavioralChoiceType.RESPONSE_TO_DIRECT_ADDRESS,
                description="say anything",
                stakes=0.1
            )
        ]
        assert not CognitionEligibilityChecker.check_factor_4_behavioral_choice(choices)
    
    def test_eligibility_all_pass(self):
        """Eligibility check: all factors pass."""
        now = datetime.now()
        choices = [BehavioralChoice(
            choice_type=BehavioralChoiceType.CONFLICT_NAVIGATION,
            description="navigate conflict",
            stakes=0.7
        )]
        result = CognitionEligibilityChecker.check_eligibility(
            m_score_value=0.6,
            m_threshold=0.4,
            event_triviality=EventTrivialityClassification.SIGNIFICANT,
            last_cognition_time=now - timedelta(minutes=10),
            current_time=now,
            cooldown_minutes=5,
            behavioral_choices=choices
        )
        assert result.is_eligible
        assert result.factor_1_m_score_sufficient
        assert result.factor_2_event_not_trivial
        assert result.factor_3_cooldown_elapsed
        assert result.factor_4_behavioral_choice_exists
    
    def test_eligibility_m_score_fails(self):
        """Eligibility check: M score fails."""
        now = datetime.now()
        result = CognitionEligibilityChecker.check_eligibility(
            m_score_value=0.2,
            m_threshold=0.4,
            event_triviality=EventTrivialityClassification.SIGNIFICANT,
            last_cognition_time=now - timedelta(minutes=10),
            current_time=now,
            cooldown_minutes=5,
            behavioral_choices=[BehavioralChoice(
                choice_type=BehavioralChoiceType.CONFLICT_NAVIGATION,
                description="",
                stakes=0.7
            )]
        )
        assert not result.is_eligible
        assert not result.factor_1_m_score_sufficient


class TestLLMResponseValidator:
    """Tests for LLM response validation."""
    
    def test_validate_no_numeric_state_assignment(self):
        """Reject: 'set trust to 0.8' patterns."""
        text = "she decides to set her trust to 0.8"
        error = LLMResponseValidator.validate_no_numeric_values(text)
        assert error is not None
    
    def test_validate_numeric_context_allowed(self):
        """Allow: numbers in context ('at 2pm', 'group of 3')."""
        text = "she meets him at 2pm with a group of 3 friends"
        error = LLMResponseValidator.validate_no_numeric_values(text)
        assert error is None
    
    def test_validate_no_personality_redefinition(self):
        """Reject: 'is now a completely different person'."""
        text = "Rebecca is now a completely different person"
        error = LLMResponseValidator.validate_no_personality_redefinition(text)
        assert error is not None
    
    def test_validate_personality_shift_allowed(self):
        """Allow: personality shift descriptions."""
        text = "Rebecca becomes more protective of Alice"
        error = LLMResponseValidator.validate_no_personality_redefinition(text)
        assert error is None
    
    def test_validate_response_valid(self):
        """Valid response passes validation."""
        response_dict = {
            "utterance": "I understand",
            "action": "nods thoughtfully",
            "stance_shifts": [{
                "target": "alice",
                "description": "gives benefit of doubt"
            }],
            "intention_updates": [{
                "operation": "create",
                "type": "support",
                "target": "alice",
                "horizon": "medium",
                "description": "help her through this"
            }]
        }
        result = LLMResponseValidator.validate_cognition_response(response_dict)
        assert result.is_valid
        assert len(result.stance_shifts) == 1
        assert len(result.intention_updates) == 1
    
    def test_validate_response_missing_fields(self):
        """Missing required fields caught."""
        response_dict = {
            "stance_shifts": [{
                "target": "alice"
                # Missing description
            }]
        }
        result = LLMResponseValidator.validate_cognition_response(response_dict)
        assert not result.is_valid
        assert len(result.validation_errors) > 0


class TestStanceShiftMapper:
    """Tests for stance shift → numeric mapping."""
    
    def test_get_stance_shift_mapping_found(self):
        """Retrieve existing stance mapping."""
        mapping = StanceShiftMapper.get_stance_shift_mapping("benefit_of_doubt")
        assert mapping is not None
        assert "trust" in mapping.relationship_deltas
    
    def test_get_stance_shift_mapping_not_found(self):
        """Unknown stance returns None."""
        mapping = StanceShiftMapper.get_stance_shift_mapping("unknown_stance_xyz")
        assert mapping is None
    
    def test_apply_stance_shift_trust(self):
        """Apply trust-boosting stance."""
        rel = {"warmth": 0.5, "trust": 0.5, "tension": 0.3}
        updated = StanceShiftMapper.apply_stance_shift(rel, "benefit_of_doubt")
        assert updated["trust"] > rel["trust"]
        assert updated["tension"] < rel["tension"]
    
    def test_apply_stance_shift_warmth(self):
        """Apply warmth-increasing stance."""
        rel = {"warmth": 0.3, "trust": 0.5, "tension": 0.5}
        updated = StanceShiftMapper.apply_stance_shift(rel, "increase_warmth")
        assert updated["warmth"] > rel["warmth"]
    
    def test_apply_stance_shift_unknown(self):
        """Unknown stance returns unchanged."""
        rel = {"warmth": 0.5, "trust": 0.5, "tension": 0.3}
        updated = StanceShiftMapper.apply_stance_shift(rel, "unknown_xyz")
        assert updated == rel


class TestIntentionUpdateMapper:
    """Tests for intention update → numeric mapping."""
    
    def test_compute_intention_drive_effects_create_support(self):
        """Create support intention affects drives."""
        effects = IntentionUpdateMapper.compute_intention_drive_effects(
            IntentionOperationType.CREATE,
            IntentionType.SUPPORT,
            IntentionHorizon.MEDIUM
        )
        assert "relatedness" in effects
        assert effects["relatedness"] > 0
    
    def test_compute_intention_drive_effects_drop_drops_effect(self):
        """Drop operation reverses effect."""
        create_effects = IntentionUpdateMapper.compute_intention_drive_effects(
            IntentionOperationType.CREATE,
            IntentionType.SUPPORT,
            IntentionHorizon.MEDIUM
        )
        drop_effects = IntentionUpdateMapper.compute_intention_drive_effects(
            IntentionOperationType.DROP,
            IntentionType.SUPPORT,
            IntentionHorizon.MEDIUM
        )
        for drive in create_effects:
            if drive in drop_effects:
                assert drop_effects[drive] * create_effects[drive] < 0  # Opposite sign
    
    def test_compute_intention_drive_effects_horizon_scaling(self):
        """Horizon affects effect magnitude."""
        short = IntentionUpdateMapper.compute_intention_drive_effects(
            IntentionOperationType.CREATE,
            IntentionType.SUPPORT,
            IntentionHorizon.SHORT
        )
        long = IntentionUpdateMapper.compute_intention_drive_effects(
            IntentionOperationType.CREATE,
            IntentionType.SUPPORT,
            IntentionHorizon.LONG
        )
        # Short horizon should have larger effect magnitudes
        short_mag = max(abs(v) for v in short.values()) if short else 0
        long_mag = max(abs(v) for v in long.values()) if long else 0
        assert short_mag > long_mag
    
    def test_apply_intention_update_avoid(self):
        """Apply avoid intention updates drives."""
        drives = {"autonomy": 0.5, "safety": 0.5, "competence": 0.5, "relatedness": 0.5, "novelty": 0.5}
        updated = IntentionUpdateMapper.apply_intention_update(
            drives,
            IntentionOperationType.CREATE,
            IntentionType.AVOID,
            IntentionHorizon.MEDIUM
        )
        assert updated["autonomy"] < drives["autonomy"]
        assert updated["safety"] > drives["safety"]


class TestCognitionServiceIntegration:
    """Integration tests for complete cognition pipeline."""
    
    def test_cognition_input_output_structure(self):
        """CognitionInput and CognitionOutput have expected structure."""
        now = datetime.now()
        input_obj = CognitionInput(
            agent_id="rebecca",
            event_type="speech",
            event_time=now,
            event_description="Alice tells Rebecca about her day",
            personality_kernel={},
            personality_activation={},
            mood=(0.5, 0.5),
            drives={"autonomy": 0.5, "competence": 0.5, "relatedness": 0.5, "novelty": 0.5, "safety": 0.5},
            arcs={},
            energy=0.7,
            relationships={},
            intentions={},
            memories={"episodic": [], "biographical": []},
            event_participants={"alice": {"name": "Alice"}},
            event_topics=["work"],
            event_triviality=EventTrivialityClassification.MODERATE,
            behavioral_choices=[BehavioralChoice(
                choice_type=BehavioralChoiceType.RESPONSE_TO_DIRECT_ADDRESS,
                description="respond",
                stakes=0.5
            )],
            last_cognition_time=now - timedelta(minutes=10)
        )
        
        assert input_obj.agent_id == "rebecca"
        assert input_obj.event_type == "speech"
    
    def test_cognition_service_processes_input(self):
        """CognitionService can process a valid input."""
        now = datetime.now()
        input_obj = CognitionInput(
            agent_id="rebecca",
            event_type="speech",
            event_time=now,
            event_description="Test event",
            personality_kernel={"name": "Rebecca"},
            personality_activation={},
            mood=(0.5, 0.5),
            drives={"autonomy": 0.5, "competence": 0.5, "relatedness": 0.5, "novelty": 0.5, "safety": 0.5},
            arcs={},
            energy=0.7,
            relationships={},
            intentions={},
            memories={"episodic": [], "biographical": []},
            event_participants={},
            event_topics=[],
            event_triviality=EventTrivialityClassification.TRIVIAL,
            behavioral_choices=[]
        )
        
        output = CognitionService.process_cognition(input_obj)
        
        assert output.agent_id == "rebecca"
        assert isinstance(output.was_eligible, bool)
        assert output.eligibility_result is not None
    
    def test_cognition_service_ineligible_trivial(self):
        """Trivial events don't trigger cognition."""
        now = datetime.now()
        input_obj = CognitionInput(
            agent_id="rebecca",
            event_type="small_talk",
            event_time=now,
            event_description="Small talk",
            personality_kernel={},
            personality_activation={},
            mood=(0.5, 0.5),
            drives={"autonomy": 0.5, "competence": 0.5, "relatedness": 0.5, "novelty": 0.5, "safety": 0.5},
            arcs={},
            energy=0.7,
            relationships={},
            intentions={},
            memories={"episodic": [], "biographical": []},
            event_participants={},
            event_topics=[],
            event_triviality=EventTrivialityClassification.TRIVIAL,
            behavioral_choices=[]
        )
        
        output = CognitionService.process_cognition(input_obj)
        assert not output.was_eligible
        assert not output.llm_called


class TestDeterminism:
    """Tests for determinism of cognition calculations."""
    
    def test_salience_computation_deterministic(self):
        """Same inputs produce identical salience."""
        people = {"alice": {"name": "Alice", "proximity_type": "physically_present"}}
        rels = {"alice": {"warmth": 0.5, "trust": 0.5, "tension": 0.3}}
        
        result1 = SalienceCalculator.compute_people_salience(people, rels)
        result2 = SalienceCalculator.compute_people_salience(people, rels)
        
        assert result1 == result2
    
    def test_meaningfulness_computation_deterministic(self):
        """Same inputs produce identical M score."""
        salience_context = AgentSalienceContext(
            agent_id="rebecca",
            people_salience={"alice": 0.7},
            topic_salience={},
            object_salience={},
            drive_salience={},
            arc_salience={}
        )
        drives = {"autonomy": 0.5, "competence": 0.5, "relatedness": 0.5, "novelty": 0.5, "safety": 0.5}
        
        m1 = MeaningfulnessCalculator.compute_m_score(
            salience_context, drives, {}, {}, 0.7
        )
        m2 = MeaningfulnessCalculator.compute_m_score(
            salience_context, drives, {}, {}, 0.7
        )
        
        assert m1.total_m == m2.total_m
        assert m1.salience_max == m2.salience_max
    
    def test_stance_shift_deterministic(self):
        """Same stance shift produces identical relationship delta."""
        rel = {"warmth": 0.5, "trust": 0.5, "tension": 0.3, "comfort": 0.6}
        
        updated1 = StanceShiftMapper.apply_stance_shift(rel.copy(), "increase_warmth")
        updated2 = StanceShiftMapper.apply_stance_shift(rel.copy(), "increase_warmth")
        
        assert updated1 == updated2


class TestCalendarAndUnexpectedEventContext:
    """Tests for calendar/obligation and unexpected-event context integration."""
    
    def test_cognition_input_accepts_calendar_context(self):
        """CognitionInput accepts calendar context."""
        now = datetime.now()
        input_obj = CognitionInput(
            agent_id="rebecca",
            event_type="event",
            event_time=now,
            event_description="Test",
            personality_kernel={},
            personality_activation={},
            mood=(0.5, 0.5),
            drives={"autonomy": 0.5, "competence": 0.5, "relatedness": 0.5, "novelty": 0.5, "safety": 0.5},
            arcs={},
            energy=0.7,
            relationships={},
            intentions={},
            memories={"episodic": [], "biographical": []},
            event_participants={},
            event_topics=[],
            event_triviality=EventTrivialityClassification.MODERATE,
            behavioral_choices=[],
            relevant_calendar_context="upcoming dinner at 7pm"
        )
        
        assert input_obj.relevant_calendar_context == "upcoming dinner at 7pm"
    
    def test_cognition_input_accepts_unexpected_event_context(self):
        """CognitionInput accepts unexpected event context."""
        now = datetime.now()
        input_obj = CognitionInput(
            agent_id="rebecca",
            event_type="event",
            event_time=now,
            event_description="Test",
            personality_kernel={},
            personality_activation={},
            mood=(0.5, 0.5),
            drives={"autonomy": 0.5, "competence": 0.5, "relatedness": 0.5, "novelty": 0.5, "safety": 0.5},
            arcs={},
            energy=0.7,
            relationships={},
            intentions={},
            memories={"episodic": [], "biographical": []},
            event_participants={},
            event_topics=[],
            event_triviality=EventTrivialityClassification.SIGNIFICANT,
            behavioral_choices=[],
            relevant_unexpected_event_context="unexpected job offer"
        )
        
        assert input_obj.relevant_unexpected_event_context == "unexpected job offer"
