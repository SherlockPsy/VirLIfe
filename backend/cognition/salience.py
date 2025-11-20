"""
Salience Calculation Module

Computes salience scores for various entity types (people, topics, objects, internal concerns)
and aggregates them for meaningfulness computation.

Per cognition_flow.md §3.3 and MASTER_SPEC §SECTION 9.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
from enum import Enum


class SalienceCategory(Enum):
    """Categories of salience computation."""
    PEOPLE = "people"
    TOPICS = "topics"
    OBJECTS = "objects"
    INTERNAL_DRIVES = "internal_drives"
    INTERNAL_ARCS = "internal_arcs"


@dataclass
class SalienceScore:
    """Individual salience score with source tracking."""
    category: SalienceCategory
    entity_id: str
    entity_name: Optional[str] = None
    score: float = 0.0  # [0, 1]
    
    def __post_init__(self):
        self.score = max(0.0, min(1.0, self.score))


@dataclass
class AgentSalienceContext:
    """Full salience context for an agent at a moment."""
    agent_id: str
    people_salience: Dict[str, float] = field(default_factory=dict)  # person_id -> salience [0,1]
    topic_salience: Dict[str, float] = field(default_factory=dict)   # topic -> salience [0,1]
    object_salience: Dict[str, float] = field(default_factory=dict)  # object_id -> salience [0,1]
    drive_salience: Dict[str, float] = field(default_factory=dict)   # drive_name -> salience [0,1]
    arc_salience: Dict[str, float] = field(default_factory=dict)     # arc_topic -> salience [0,1]
    
    @property
    def max_salience(self) -> float:
        """Return the maximum salience across all categories."""
        all_scores = (
            list(self.people_salience.values()) +
            list(self.topic_salience.values()) +
            list(self.object_salience.values()) +
            list(self.drive_salience.values()) +
            list(self.arc_salience.values())
        )
        return max(all_scores) if all_scores else 0.0


class SalienceCalculator:
    """
    Deterministic salience computation.
    
    Per cognition_flow.md §3.3:
    "Compute salience for:
    - people present (including user if physically there),
    - topics implied by E,
    - objects,
    - internal concerns (drives, arcs)."
    """
    
    # Salience weights for different entity types
    # These determine relative importance of entity types when aggregating
    PEOPLE_BASE_WEIGHT = 1.0
    TOPICS_BASE_WEIGHT = 0.8
    OBJECTS_BASE_WEIGHT = 0.6
    DRIVE_BASE_WEIGHT = 0.9
    ARC_BASE_WEIGHT = 0.95
    
    # Proximity/presence modifiers for people
    PHYSICALLY_PRESENT_MULTIPLIER = 1.0
    RECENTLY_INTERACTED_MULTIPLIER = 0.7
    MENTIONED_MULTIPLIER = 0.5
    BACKGROUND_MULTIPLIER = 0.2
    
    # Drive pressure conversion to salience
    # Maps drive level [0, 1] to salience [0, 1]
    @staticmethod
    def drive_level_to_salience(level: float) -> float:
        """Convert drive level [0,1] to salience [0,1] via nonlinear mapping.
        
        High drive pressure is highly salient.
        """
        # Quadratic mapping: high pressure = high salience
        return min(1.0, max(0.0, level ** 1.5))
    
    # Arc intensity conversion to salience
    @staticmethod
    def arc_intensity_to_salience(intensity: float) -> float:
        """Convert arc intensity [0,1] to salience [0,1] via nonlinear mapping.
        
        Hot arcs are highly salient (emotional threads).
        """
        # Quadratic mapping: high intensity = high salience
        return min(1.0, max(0.0, intensity ** 1.5))
    
    @staticmethod
    def compute_people_salience(
        people: Dict[str, Dict],  # {person_id: {name, proximity_type, ...}}
        agent_relationships: Dict[str, Dict]  # {person_id: {warmth, trust, tension, ...}}
    ) -> Dict[str, float]:
        """
        Compute salience for people present.
        
        Args:
            people: Dict mapping person_id to {name, proximity_type, ...}
                    proximity_type in [physically_present, recently_interacted, mentioned, background]
            agent_relationships: Dict mapping person_id to relationship dict
        
        Returns:
            Dict of person_id -> salience [0, 1]
        """
        result = {}
        
        for person_id, person_data in people.items():
            proximity_type = person_data.get("proximity_type", "background")
            
            # Base salience from proximity
            if proximity_type == "physically_present":
                base_salience = SalienceCalculator.PHYSICALLY_PRESENT_MULTIPLIER
            elif proximity_type == "recently_interacted":
                base_salience = SalienceCalculator.RECENTLY_INTERACTED_MULTIPLIER
            elif proximity_type == "mentioned":
                base_salience = SalienceCalculator.MENTIONED_MULTIPLIER
            else:  # background
                base_salience = SalienceCalculator.BACKGROUND_MULTIPLIER
            
            # Relationship stakes boost salience
            if person_id in agent_relationships:
                rel = agent_relationships[person_id]
                rel_stakes = max(
                    abs(rel.get("warmth", 0)),
                    abs(rel.get("trust", 0)),
                    rel.get("tension", 0)
                )
                # Relationship stakes boost base salience
                base_salience = min(1.0, base_salience + 0.3 * rel_stakes)
            
            result[person_id] = min(1.0, max(0.0, base_salience))
        
        return result
    
    @staticmethod
    def compute_topic_salience(
        topics: List[str],
        agent_arcs: Dict[str, Dict],  # {arc_topic: {intensity, valence_bias, ...}}
        agent_intentions: Dict[str, Dict]  # {intention_id: {type, target, priority, ...}}
    ) -> Dict[str, float]:
        """
        Compute salience for topics mentioned/implied by the event.
        
        Args:
            topics: List of topic strings ("conflict", "intimacy", "work", etc.)
            agent_arcs: Dict of arc_topic -> arc dict
            agent_intentions: Dict of intention_id -> intention dict
        
        Returns:
            Dict of topic -> salience [0, 1]
        """
        result = {}
        
        for topic in topics:
            base_salience = 0.5  # Topics are moderately salient by default
            
            # Arc involvement boosts topic salience
            if topic in agent_arcs:
                arc = agent_arcs[topic]
                arc_salience = SalienceCalculator.arc_intensity_to_salience(
                    arc.get("intensity", 0.0)
                )
                base_salience = min(1.0, base_salience + 0.3 * arc_salience)
            
            # Intention involvement boosts topic salience
            for intention in agent_intentions.values():
                if intention.get("type") == topic or intention.get("target") == topic:
                    base_salience = min(1.0, base_salience + 0.2)
            
            result[topic] = min(1.0, max(0.0, base_salience))
        
        return result
    
    @staticmethod
    def compute_object_salience(
        objects: Dict[str, Dict]  # {object_id: {name, relevance_type, ...}}
    ) -> Dict[str, float]:
        """
        Compute salience for objects in the scene.
        
        Args:
            objects: Dict mapping object_id to {name, relevance_type, ...}
                     relevance_type in [critical, important, background]
        
        Returns:
            Dict of object_id -> salience [0, 1]
        """
        result = {}
        
        for obj_id, obj_data in objects.items():
            relevance_type = obj_data.get("relevance_type", "background")
            
            if relevance_type == "critical":
                salience = 0.9
            elif relevance_type == "important":
                salience = 0.6
            else:  # background
                salience = 0.2
            
            result[obj_id] = min(1.0, max(0.0, salience))
        
        return result
    
    @staticmethod
    def compute_drive_salience(
        drive_levels: Dict[str, float]  # {drive_name: level [0,1]}
    ) -> Dict[str, float]:
        """
        Compute salience for agent's drive pressures.
        
        High drive pressure = high salience.
        Per cognition_flow.md: "drive_pressure_max = max(d_level)"
        
        Args:
            drive_levels: Dict of drive_name -> level [0, 1]
        
        Returns:
            Dict of drive_name -> salience [0, 1]
        """
        result = {}
        
        for drive_name, level in drive_levels.items():
            salience = SalienceCalculator.drive_level_to_salience(level)
            result[drive_name] = salience
        
        return result
    
    @staticmethod
    def compute_arc_salience(
        arcs: Dict[str, Dict]  # {arc_topic: {intensity, valence_bias, ...}}
    ) -> Dict[str, float]:
        """
        Compute salience for agent's active arcs.
        
        Hot arcs = high salience.
        Per cognition_flow.md: "arc_hot = max(arc.intensity)"
        
        Args:
            arcs: Dict of arc_topic -> {intensity [0,1], valence_bias, ...}
        
        Returns:
            Dict of arc_topic -> salience [0, 1]
        """
        result = {}
        
        for arc_topic, arc_data in arcs.items():
            intensity = arc_data.get("intensity", 0.0)
            salience = SalienceCalculator.arc_intensity_to_salience(intensity)
            result[arc_topic] = salience
        
        return result
    
    @staticmethod
    def build_salience_context(
        agent_id: str,
        people: Dict[str, Dict],
        topics: List[str],
        objects: Dict[str, Dict],
        drive_levels: Dict[str, float],
        arcs: Dict[str, Dict],
        agent_relationships: Dict[str, Dict],
        agent_intentions: Dict[str, Dict]
    ) -> AgentSalienceContext:
        """
        Build complete salience context for an agent.
        
        Args:
            agent_id: ID of the agent
            people: Dict of person_id -> person data
            topics: List of topic strings
            objects: Dict of object_id -> object data
            drive_levels: Dict of drive_name -> level
            arcs: Dict of arc_topic -> arc data
            agent_relationships: Dict of person_id -> relationship data
            agent_intentions: Dict of intention_id -> intention data
        
        Returns:
            AgentSalienceContext with all salience computations filled
        """
        return AgentSalienceContext(
            agent_id=agent_id,
            people_salience=SalienceCalculator.compute_people_salience(people, agent_relationships),
            topic_salience=SalienceCalculator.compute_topic_salience(topics, arcs, agent_intentions),
            object_salience=SalienceCalculator.compute_object_salience(objects),
            drive_salience=SalienceCalculator.compute_drive_salience(drive_levels),
            arc_salience=SalienceCalculator.compute_arc_salience(arcs)
        )
