"""
Meaningfulness (M) Score Computation Module

Implements the M formula for cognition triggering decision.
Per cognition_flow.md §3.3 and MASTER_SPEC §SECTION 9.

M = w1 * salience_max
  + w2 * drive_pressure_max
  + w3 * arc_hot
  + w4 * rel_stakes
  - w5 * (1 - energy)
"""

from dataclasses import dataclass
from typing import Dict, Optional
from backend.cognition.salience import AgentSalienceContext


# Default weights for M score computation
# These can be tuned for game balance but MUST be globally consistent
MEANINGFULNESS_WEIGHTS = {
    "w1_salience": 0.25,           # Salience contribution
    "w2_drive_pressure": 0.25,     # Drive pressure contribution
    "w3_arc_intensity": 0.25,      # Arc intensity contribution
    "w4_rel_stakes": 0.15,         # Relationship stakes contribution
    "w5_energy_fatigue": 0.10      # Energy fatigue penalty (subtracted)
}

# Default threshold for cognition eligibility
# If M >= this threshold, cognition may be triggered (if other conditions met)
DEFAULT_COGNITION_THRESHOLD = 0.4


@dataclass
class MeaningfulnessScore:
    """Detailed M score computation with component breakdown."""
    total_m: float                  # Final M score [0, 1]
    
    # Component contributions
    salience_max: float            # Max salience across all categories
    drive_pressure_max: float      # Max drive level
    arc_hot: float                 # Max arc intensity
    rel_stakes_max: float          # Max relationship stake
    energy: float                  # Current energy [0, 1]
    
    # Component scores (before weighting)
    w1_salience_term: float        # w1 * salience_max
    w2_drive_term: float           # w2 * drive_pressure_max
    w3_arc_term: float             # w3 * arc_hot
    w4_rel_term: float             # w4 * rel_stakes_max
    w5_energy_penalty: float       # -w5 * (1 - energy)
    
    # Metadata
    is_above_threshold: bool       # Whether M >= threshold
    threshold: float               # The threshold used
    
    def __str__(self) -> str:
        """Human-readable M score summary."""
        return (
            f"M={self.total_m:.3f} (above_threshold={self.is_above_threshold}) "
            f"[salience={self.salience_max:.2f}, drive={self.drive_pressure_max:.2f}, "
            f"arc={self.arc_hot:.2f}, rel={self.rel_stakes_max:.2f}, energy={self.energy:.2f}]"
        )


class MeaningfulnessCalculator:
    """
    Deterministic meaningfulness computation.
    
    Per cognition_flow.md §3.3:
    "For each candidate agent A, cognition MUST ONLY be triggered if ALL are true:
    1. M ≥ cognition_threshold.
    2. Event type is not classified as trivial.
    3. Cognition cooldown window for A has elapsed.
    4. There exists at least one non-trivial behavioural choice to be made."
    
    This module handles condition 1 (M computation and threshold check).
    """
    
    @staticmethod
    def compute_m_score(
        salience_context: AgentSalienceContext,
        drive_levels: Dict[str, float],
        arcs: Dict[str, Dict],
        relationships: Dict[str, Dict],
        energy: float,
        weights: Optional[Dict[str, float]] = None,
        threshold: float = DEFAULT_COGNITION_THRESHOLD
    ) -> MeaningfulnessScore:
        """
        Compute meaningfulness score M for an agent.
        
        Args:
            salience_context: AgentSalienceContext with all salience computations
            drive_levels: Dict of drive_name -> level [0, 1]
            arcs: Dict of arc_topic -> {intensity, valence_bias, ...}
            relationships: Dict of person_id -> {warmth, trust, tension, ...}
            energy: Current energy level [0, 1]
            weights: Optional override of MEANINGFULNESS_WEIGHTS
            threshold: Cognition threshold (default DEFAULT_COGNITION_THRESHOLD)
        
        Returns:
            MeaningfulnessScore with full computation breakdown
        """
        if weights is None:
            weights = MEANINGFULNESS_WEIGHTS
        
        # Clamp energy to [0, 1]
        energy = max(0.0, min(1.0, energy))
        
        # Extract component values from salience context
        salience_max = salience_context.max_salience
        
        # Drive pressure max
        drive_pressure_max = max(drive_levels.values()) if drive_levels else 0.0
        drive_pressure_max = max(0.0, min(1.0, drive_pressure_max))
        
        # Arc hot (maximum intensity)
        arc_hot = max([arc.get("intensity", 0.0) for arc in arcs.values()]) if arcs else 0.0
        arc_hot = max(0.0, min(1.0, arc_hot))
        
        # Relationship stakes (max of abs(warmth), abs(trust), tension across all relationships)
        rel_stakes_max = 0.0
        for rel in relationships.values():
            rel_stakes = max(
                abs(rel.get("warmth", 0.0)),
                abs(rel.get("trust", 0.0)),
                rel.get("tension", 0.0)
            )
            rel_stakes_max = max(rel_stakes_max, rel_stakes)
        rel_stakes_max = max(0.0, min(1.0, rel_stakes_max))
        
        # Compute M score with weighted components
        w1 = weights["w1_salience"]
        w2 = weights["w2_drive_pressure"]
        w3 = weights["w3_arc_intensity"]
        w4 = weights["w4_rel_stakes"]
        w5 = weights["w5_energy_fatigue"]
        
        w1_term = w1 * salience_max
        w2_term = w2 * drive_pressure_max
        w3_term = w3 * arc_hot
        w4_term = w4 * rel_stakes_max
        w5_term = -w5 * (1.0 - energy)  # Negative penalty for low energy
        
        total_m = w1_term + w2_term + w3_term + w4_term + w5_term
        total_m = max(0.0, min(1.0, total_m))  # Clamp to [0, 1]
        
        return MeaningfulnessScore(
            total_m=total_m,
            salience_max=salience_max,
            drive_pressure_max=drive_pressure_max,
            arc_hot=arc_hot,
            rel_stakes_max=rel_stakes_max,
            energy=energy,
            w1_salience_term=w1_term,
            w2_drive_term=w2_term,
            w3_arc_term=w3_term,
            w4_rel_term=w4_term,
            w5_energy_penalty=w5_term,
            is_above_threshold=(total_m >= threshold),
            threshold=threshold
        )
    
    @staticmethod
    def is_meaningfulness_sufficient(
        m_score: MeaningfulnessScore
    ) -> bool:
        """
        Check if meaningfulness score meets threshold.
        
        Per cognition_flow.md §3.4:
        "For each agent A, cognition MUST ONLY be triggered if ALL are true:
        1. M ≥ cognition_threshold."
        
        Args:
            m_score: MeaningfulnessScore object
        
        Returns:
            True if m_score.total_m >= m_score.threshold
        """
        return m_score.is_above_threshold
