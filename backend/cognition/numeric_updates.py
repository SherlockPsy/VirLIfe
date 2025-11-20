"""
Post-Cognition Numeric Update Mapping Module

Implements deterministic mappings from LLM output (stance_shifts, intention_updates)
back to numeric state updates.

Per cognition_flow.md §6 and MASTER_SPEC.

"The Autonomy Engine MUST:
...
3. Map stance_shifts → numeric updates:
   - use deterministic mapping tables
   - e.g., 'she decides to give him the benefit of the doubt' → small increase in trust, small decrease in tension.
   - mapping MUST be stable and global (no per-instance improvisations).
4. Map intention_updates:
   - create new intentions with appropriate priority/horizon.
   - boost or lower existing priorities.
   - drop intentions where instructed."
"""

from dataclasses import dataclass, field
from typing import Dict, Optional, List
from enum import Enum


class IntentionOperationType(Enum):
    """Types of intention operations from LLM output."""
    CREATE = "create"
    BOOST = "boost"
    LOWER = "lower"
    DROP = "drop"


class IntentionType(Enum):
    """Types of intentions."""
    AVOID = "avoid"
    RAISE = "raise"
    SUPPORT = "support"
    PROTECT = "protect"
    DISTANCE = "distance"


class IntentionHorizon(Enum):
    """Time horizons for intentions."""
    SHORT = "short"      # Minutes to hours
    MEDIUM = "medium"    # Hours to days
    LONG = "long"        # Days to weeks


@dataclass
class StanceShiftMapping:
    """Deterministic numeric effect of a single stance shift."""
    description: str               # "give benefit of the doubt", "escalate distrust", etc.
    relationship_deltas: Dict[str, float] = field(default_factory=dict)
    # Keys: "warmth", "trust", "tension", "comfort", "attraction", "familiarity"
    # Values: delta to apply [-1, 1]
    
    def apply_to_relationship(self, rel: Dict[str, float]) -> Dict[str, float]:
        """Apply this mapping to a relationship dict."""
        result = rel.copy()
        for key, delta in self.relationship_deltas.items():
            if key in result:
                result[key] = max(-1.0, min(1.0, result[key] + delta))
        return result


class StanceShiftMapper:
    """
    Deterministic mapping from stance shift descriptions to numeric relationship updates.
    
    Per cognition_flow.md §6:
    "use deterministic mapping tables:
    e.g., 'she decides to give him the benefit of the doubt' → small increase in trust, small decrease in tension."
    
    All mappings are STABLE and GLOBAL — no per-instance improvisations.
    """
    
    # Library of canonical stance shifts and their numeric effects
    # These are the ONLY allowed stance shifts
    STANCE_SHIFT_MAPPINGS = {
        # Trust and benefit of doubt
        "benefit_of_doubt": StanceShiftMapping(
            description="gives the benefit of the doubt",
            relationship_deltas={"trust": 0.1, "tension": -0.1}
        ),
        "reassess_trust": StanceShiftMapping(
            description="reassesses their trust",
            relationship_deltas={"trust": 0.15}
        ),
        "withdraw_trust": StanceShiftMapping(
            description="withdraws trust",
            relationship_deltas={"trust": -0.2, "tension": 0.1}
        ),
        
        # Warmth/coldness shifts
        "soften_warmth": StanceShiftMapping(
            description="softens their emotional stance",
            relationship_deltas={"warmth": 0.15, "tension": -0.1}
        ),
        "increase_warmth": StanceShiftMapping(
            description="feels more warmth toward them",
            relationship_deltas={"warmth": 0.2, "comfort": 0.1}
        ),
        "decrease_warmth": StanceShiftMapping(
            description="feels less warmth",
            relationship_deltas={"warmth": -0.15, "tension": 0.1}
        ),
        "cold_distance": StanceShiftMapping(
            description="becomes emotionally cold and distant",
            relationship_deltas={"warmth": -0.3, "tension": 0.2}
        ),
        
        # Tension escalation/deescalation
        "escalate_tension": StanceShiftMapping(
            description="escalates tension and hostility",
            relationship_deltas={"tension": 0.25, "warmth": -0.1}
        ),
        "deescalate_tension": StanceShiftMapping(
            description="deescalates tension",
            relationship_deltas={"tension": -0.2, "warmth": 0.1}
        ),
        "resolve_conflict": StanceShiftMapping(
            description="moves toward conflict resolution",
            relationship_deltas={"tension": -0.25, "trust": 0.15, "warmth": 0.1}
        ),
        
        # Commitment and comfort
        "increase_commitment": StanceShiftMapping(
            description="increases emotional commitment",
            relationship_deltas={"warmth": 0.15, "trust": 0.1, "comfort": 0.2}
        ),
        "decrease_commitment": StanceShiftMapping(
            description="decreases emotional commitment",
            relationship_deltas={"warmth": -0.2, "comfort": -0.15}
        ),
        "seek_comfort": StanceShiftMapping(
            description="seeks comfort and reassurance",
            relationship_deltas={"comfort": 0.2, "warmth": 0.1}
        ),
        "withdraw_comfort": StanceShiftMapping(
            description="withdraws comfort and support",
            relationship_deltas={"comfort": -0.2, "tension": 0.1}
        ),
        
        # Attraction/intimacy
        "increase_attraction": StanceShiftMapping(
            description="feels more attracted",
            relationship_deltas={"attraction": 0.2, "warmth": 0.1}
        ),
        "decrease_attraction": StanceShiftMapping(
            description="feels less attracted",
            relationship_deltas={"attraction": -0.2}
        ),
        
        # Familiarity/understanding
        "increase_understanding": StanceShiftMapping(
            description="deepens understanding",
            relationship_deltas={"familiarity": 0.15, "trust": 0.1, "warmth": 0.05}
        ),
        "misunderstanding": StanceShiftMapping(
            description="experiences misunderstanding",
            relationship_deltas={"familiarity": -0.1, "tension": 0.15}
        ),
        
        # Complex shifts
        "protective_concern": StanceShiftMapping(
            description="feels protective concern",
            relationship_deltas={"warmth": 0.1, "comfort": 0.15, "tension": -0.1}
        ),
        "betrayal": StanceShiftMapping(
            description="feels betrayed",
            relationship_deltas={"trust": -0.3, "warmth": -0.2, "tension": 0.2}
        ),
        "reconciliation": StanceShiftMapping(
            description="moves toward reconciliation",
            relationship_deltas={"trust": 0.2, "warmth": 0.2, "tension": -0.2}
        )
    }
    
    @staticmethod
    def get_stance_shift_mapping(
        stance_description: str
    ) -> Optional[StanceShiftMapping]:
        """
        Look up a stance shift mapping by description.
        
        Args:
            stance_description: Stance key or description
        
        Returns:
            StanceShiftMapping if found, None if not in canonical list
        """
        # Try exact match on key
        for key, mapping in StanceShiftMapper.STANCE_SHIFT_MAPPINGS.items():
            if key == stance_description or mapping.description == stance_description:
                return mapping
        
        return None
    
    @staticmethod
    def apply_stance_shift(
        rel_dict: Dict[str, float],
        stance_description: str
    ) -> Dict[str, float]:
        """
        Apply a stance shift to a relationship dict.
        
        Args:
            rel_dict: Current relationship {warmth, trust, tension, ...}
            stance_description: Stance shift description/key
        
        Returns:
            Updated relationship dict, or original if stance not found
        """
        mapping = StanceShiftMapper.get_stance_shift_mapping(stance_description)
        
        if mapping is None:
            # Unknown stance shift — log but don't apply
            return rel_dict.copy()
        
        return mapping.apply_to_relationship(rel_dict)


@dataclass
class IntentionUpdateEffect:
    """Effect of an intention operation on drive state."""
    operation: IntentionOperationType
    intention_type: IntentionType
    target: Optional[str]              # person_id or topic
    horizon: IntentionHorizon
    description: str
    
    # Drive pressure deltas (how intentions affect drives)
    drive_deltas: Dict[str, float] = field(default_factory=dict)
    # Keys: "autonomy", "competence", "relatedness", "novelty", "safety"
    # Values: delta to apply [-1, 1]


class IntentionUpdateMapper:
    """
    Deterministic mapping from intention operations to numeric state updates.
    
    Per cognition_flow.md §6:
    "4. Map intention_updates:
    - create new intentions with appropriate priority/horizon.
    - boost or lower existing priorities.
    - drop intentions where instructed."
    """
    
    # Drive effects of different intention types
    INTENTION_TYPE_DRIVE_EFFECTS = {
        IntentionType.AVOID.value: {
            "autonomy": -0.1,      # Avoiding reduces autonomy
            "safety": 0.1          # Avoiding increases felt safety
        },
        IntentionType.RAISE.value: {
            "competence": 0.1,     # Raising something is active
            "autonomy": 0.05
        },
        IntentionType.SUPPORT.value: {
            "relatedness": 0.15,   # Supporting is relational
            "autonomy": -0.05      # Slightly constrained by commitment
        },
        IntentionType.PROTECT.value: {
            "safety": 0.1,         # Protecting increases felt protective responsibility
            "relatedness": 0.1     # Relational commitment
        },
        IntentionType.DISTANCE.value: {
            "autonomy": 0.1,       # Distancing increases autonomy
            "relatedness": -0.15   # Distancing reduces relational engagement
        }
    }
    
    # Horizon time effects (longer horizons have less immediate drive effect)
    HORIZON_INTENSITY_MULTIPLIERS = {
        IntentionHorizon.SHORT.value: 1.0,      # Immediate effect
        IntentionHorizon.MEDIUM.value: 0.7,     # Moderate effect
        IntentionHorizon.LONG.value: 0.4        # Small effect
    }
    
    @staticmethod
    def compute_intention_drive_effects(
        operation: IntentionOperationType,
        intention_type: IntentionType,
        horizon: IntentionHorizon
    ) -> Dict[str, float]:
        """
        Compute drive deltas for an intention operation.
        
        Args:
            operation: CREATE, BOOST, LOWER, DROP
            intention_type: Type of intention
            horizon: Time horizon
        
        Returns:
            Dict of drive_name -> delta
        """
        if intention_type.value not in IntentionUpdateMapper.INTENTION_TYPE_DRIVE_EFFECTS:
            return {}
        
        base_effects = IntentionUpdateMapper.INTENTION_TYPE_DRIVE_EFFECTS[intention_type.value].copy()
        
        # Get horizon intensity multiplier
        horizon_key = horizon.value if isinstance(horizon, IntentionHorizon) else horizon
        multiplier = IntentionUpdateMapper.HORIZON_INTENSITY_MULTIPLIERS.get(horizon_key, 0.7)
        
        # Adjust effects based on operation
        if operation == IntentionOperationType.CREATE:
            # Creating an intention applies full effect
            pass
        elif operation == IntentionOperationType.BOOST:
            # Boosting increases effect by 50%
            multiplier *= 1.5
        elif operation == IntentionOperationType.LOWER:
            # Lowering reverses and weakens effect
            multiplier *= -0.5
        elif operation == IntentionOperationType.DROP:
            # Dropping reverses effect (relief/freed from constraint)
            multiplier *= -0.7
        
        # Apply multiplier to all effects
        return {drive: delta * multiplier for drive, delta in base_effects.items()}
    
    @staticmethod
    def apply_intention_update(
        drives: Dict[str, float],
        operation: IntentionOperationType,
        intention_type: IntentionType,
        horizon: IntentionHorizon
    ) -> Dict[str, float]:
        """
        Apply an intention update to drive state.
        
        Args:
            drives: Current drive levels {drive_name: level [0,1]}
            operation: CREATE, BOOST, LOWER, DROP
            intention_type: Type of intention
            horizon: Time horizon
        
        Returns:
            Updated drives dict
        """
        drive_deltas = IntentionUpdateMapper.compute_intention_drive_effects(
            operation, intention_type, horizon
        )
        
        result = drives.copy()
        for drive, delta in drive_deltas.items():
            if drive in result:
                result[drive] = max(0.0, min(1.0, result[drive] + delta))
        
        return result
