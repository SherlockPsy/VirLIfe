import unittest
from datetime import datetime, timedelta
from backend.autonomy.engine import AutonomyEngine
from backend.persistence.models import (
    AgentModel, EventModel, RelationshipModel, ArcModel, IntentionModel, MemoryModel
)

class TestAutonomyEngine(unittest.TestCase):
    def setUp(self):
        self.engine = AutonomyEngine()
        
        # Setup a dummy agent
        self.agent = AgentModel(
            id=1,
            name="Test Agent",
            drives={
                "relatedness": {"level": 0.5, "sensitivity": 1.0},
                "curiosity": {"level": 0.5, "sensitivity": 1.0},
                "competence": {"level": 0.5, "sensitivity": 1.0},
                "novelty": {"level": 0.5, "sensitivity": 1.0},
                "safety": {"level": 0.5, "sensitivity": 1.0}
            },
            mood={"valence": 0.0, "arousal": 0.0},
            energy=1.0,
            memories=[],
            arcs=[],
            intentions=[],
            relationships=[]
        )

    def test_drive_updates(self):
        """Test that events update drives correctly."""
        # Event that should boost relatedness drive
        event = EventModel(
            type="interaction",
            description="Had a nice chat",
            source_entity_id="user:1",
            target_entity_id="agent:1",
            payload={"sentiment": 0.8},
            timestamp=datetime.now()
        )
        
        # Initial state
        initial_relatedness = self.agent.drives["relatedness"]["level"]
        
        # Process
        self.engine.update_agent_internal_state(self.agent, [event])
        
        # Check result - relatedness drive should increase
        new_relatedness = self.agent.drives["relatedness"]["level"]
        self.assertGreater(new_relatedness, initial_relatedness)

    def test_mood_updates(self):
        """Test that drive changes affect mood."""
        # Event that boosts drives should improve valence
        event = EventModel(
            type="interaction",
            description="Great interaction",
            source_entity_id="user:1",
            target_entity_id="agent:1",
            payload={"sentiment": 1.0},
            timestamp=datetime.now()
        )
        
        self.engine.update_agent_internal_state(self.agent, [event])
        
        # Valence should be positive
        self.assertGreater(self.agent.mood["valence"], 0.0)

    def test_arc_progression(self):
        """Test that arcs decay or reinforce."""
        # Add an arc
        arc = ArcModel(
            type="curiosity_arc",
            intensity=0.8,
            decay_rate=0.1,
            agent_id=self.agent.id
        )
        self.agent.arcs.append(arc)
        
        # Process with no relevant events -> should decay
        self.engine.update_agent_internal_state(self.agent, [])
        
        self.assertLess(arc.intensity, 0.8)

    def test_relationship_drift(self):
        """Test that relationships decay over time."""
        rel = RelationshipModel(
            source_agent_id=self.agent.id,
            target_user_id=1,
            warmth=0.8,
            volatility=0.1,
            tension=0.0,
            familiarity=0.5,
            trust=0.5,
            attraction=0.0,
            comfort=0.5
        )
        self.agent.relationships.append(rel)
        
        # Process
        self.engine.update_agent_internal_state(self.agent, [])
        
        # Should decay slightly towards 0
        self.assertLess(rel.warmth, 0.8)

    def test_intention_completion(self):
        """Test intention completion logic."""
        intention = IntentionModel(
            description="Check calendar:123",
            type="action",
            agent_id=self.agent.id,
            priority=0.5
        )
        self.agent.intentions.append(intention)
        
        # Event matching the intention
        event = EventModel(
            type="action_completed",
            description="Completed task",
            payload={"calendar_id": "123"},
            timestamp=datetime.now()
        )
        
        self.engine.update_agent_internal_state(self.agent, [event])
        
        # Intention should be removed
        self.assertEqual(len(self.agent.intentions), 0)

    def test_energy_depletion(self):
        """Test energy goes down."""
        initial_energy = self.agent.energy
        
        # Process tick
        self.engine.update_agent_internal_state(self.agent, [])
        
        self.assertLess(self.agent.energy, initial_energy)

    def test_memory_creation(self):
        """Test high salience events create memories."""
        # High impact event
        event = EventModel(
            type="incursion_sensory",
            description="A loud explosion!",
            source_entity_id="system",
            timestamp=datetime.now(),
            payload={}
        )
        
        self.engine.update_agent_internal_state(self.agent, [event])
        
        # Should have created a memory
        self.assertEqual(len(self.agent.memories), 1)
        self.assertEqual(self.agent.memories[0].type, "episodic")

if __name__ == '__main__':
    unittest.main()
