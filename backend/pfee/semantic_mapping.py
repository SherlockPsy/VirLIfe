"""
PFEE Semantic Mapping Helpers

Converts numeric internal state to semantic summaries for LLM consumption.
All mappings are deterministic and rule-based.

Implements:
- docs/numeric_semantic_mapping.md
- MASTER_SPEC §SECTION 12 — NUMERIC → SEMANTIC MAPPING

This module ensures PFEE never passes raw numeric state to LLMs.
"""

from typing import Dict, Any, List, Tuple, Optional
from backend.mapping.semantic_mappers import (
    MoodMapper,
    DriveMapper,
    RelationshipMapper,
    ArcMapper,
    EnergyMapper,
    IntentionMapper,
    PersonalityMapper
)


class PFEESemanticMapper:
    """
    Semantic mapping helpers for PFEE.
    
    Converts all numeric state to semantic summaries before LLM calls.
    """
    
    @staticmethod
    def map_mood_to_semantic(mood: Dict[str, float]) -> str:
        """
        Convert numeric mood to semantic summary.
        
        Args:
            mood: {valence: float, arousal: float}
            
        Returns:
            Semantic mood description
        """
        valence = mood.get("valence", 0.0) if isinstance(mood, dict) else 0.0
        arousal = mood.get("arousal", 0.0) if isinstance(mood, dict) else 0.0
        return MoodMapper.map_mood(valence, arousal)
    
    @staticmethod
    def map_drives_to_semantic(drives: Dict[str, Any]) -> List[Dict[str, str]]:
        """
        Convert numeric drives to semantic summaries.
        
        Args:
            drives: {drive_name: {level: float, sensitivity: float}} or {drive_name: float}
            
        Returns:
            List of {drive_name, semantic_description} for pressured drives
        """
        # Get top-K pressured drives
        pressured = DriveMapper.get_highest_pressure_drives(drives, top_k=3)
        return [
            {"drive_name": name, "semantic_description": desc}
            for name, desc in pressured
        ]
    
    @staticmethod
    def map_relationships_to_semantic(
        relationships: Dict[str, Dict[str, float]]
    ) -> Dict[str, Dict[str, str]]:
        """
        Convert numeric relationship edges to semantic summaries.
        
        Args:
            relationships: {person_id: {warmth, trust, tension, ...}}
            
        Returns:
            {person_id: {primary_state, attraction_note?, ...}} (all semantic)
        """
        semantic_relationships = {}
        
        for person_id, rel in relationships.items():
            warmth = rel.get("warmth", 0.0)
            trust = rel.get("trust", 0.0)
            tension = rel.get("tension", 0.0)
            attraction = rel.get("attraction")
            comfort = rel.get("comfort")
            
            # Get primary relationship state
            primary_state = RelationshipMapper.map_relationship_state(
                warmth, trust, tension, attraction, comfort
            )
            
            semantic_relationships[person_id] = {
                "primary_state": primary_state,
                "target": person_id
            }
            
            # Add attraction/comfort notes if relevant
            if attraction is not None and attraction > 0.5:
                if comfort is not None and comfort > 0.5:
                    semantic_relationships[person_id]["attraction_note"] = \
                        "She feels physically attracted and at ease with them."
                elif comfort is not None and comfort < 0.3:
                    semantic_relationships[person_id]["attraction_note"] = \
                        "She feels attracted, but also somewhat uneasy."
        
        return semantic_relationships
    
    @staticmethod
    def map_arcs_to_semantic(arcs: Dict[str, Dict[str, Any]]) -> List[str]:
        """
        Convert numeric arcs to semantic summaries.
        
        Args:
            arcs: {arc_name: {intensity, valence_bias, topic_vector, ...}}
            
        Returns:
            List of semantic arc descriptions
        """
        semantic_arcs = []
        
        for arc_name, arc_data in arcs.items():
            if not isinstance(arc_data, dict):
                continue
            
            intensity = arc_data.get("intensity", 0.0)
            valence_bias = arc_data.get("valence_bias", 0.0)
            topic_vector = arc_data.get("topic_vector", [])
            
            topic = topic_vector[0] if topic_vector else arc_name
            
            if intensity > 0.7:
                if valence_bias < -0.3:
                    semantic_arcs.append(f"There is a raw, unresolved sore spot around {topic}.")
                elif valence_bias > 0.3:
                    semantic_arcs.append(f"There is an ongoing positive emotional thread around {topic}.")
            elif intensity > 0.4:
                if valence_bias < -0.3:
                    semantic_arcs.append(f"There is a lingering tension around {topic}.")
                elif valence_bias > 0.3:
                    semantic_arcs.append(f"They have a gentle, positive theme around {topic}.")
            elif intensity > 0.3:
                semantic_arcs.append(f"There is only a mild background sensitivity around {topic}, if any.")
        
        return semantic_arcs
    
    @staticmethod
    def map_energy_to_semantic(energy: float) -> str:
        """
        Convert numeric energy to semantic summary.
        
        Args:
            energy: float [0, 1]
            
        Returns:
            Semantic energy description
        """
        return EnergyMapper.map_energy(energy)
    
    @staticmethod
    def map_intentions_to_semantic(intentions: Dict[str, Dict[str, Any]]) -> List[str]:
        """
        Convert numeric intentions to semantic summaries.
        
        Args:
            intentions: {intention_id: {description, priority, horizon, type, ...}}
            
        Returns:
            List of semantic intention descriptions (high-priority only)
        """
        semantic_intentions = []
        
        for intent_id, intent_data in intentions.items():
            if not isinstance(intent_data, dict):
                continue
            
            priority = intent_data.get("priority", 0.0)
            if priority < 0.5:  # Only high-priority intentions
                continue
            
            intent_type = intent_data.get("type", "action")
            description = intent_data.get("description", "")
            
            if intent_type == "avoid_topic":
                topic = description.split()[-1] if description else "topic"
                semantic_intentions.append(f"She is actively trying to avoid talking about {topic}.")
            elif intent_type == "raise_issue":
                issue = description.split()[-1] if description else "issue"
                semantic_intentions.append(f"She intends to bring up {issue} soon.")
            elif intent_type == "be_supportive":
                target = description.split()[-1] if description else "them"
                semantic_intentions.append(f"She is trying to be more supportive toward {target}.")
            else:
                semantic_intentions.append(description)
        
        return semantic_intentions
    
    @staticmethod
    def map_personality_activation_to_semantic(
        personality_kernel: Dict[str, Any],
        personality_activation: Dict[str, float],
        mood: Dict[str, float],
        drives: Dict[str, Any],
        energy: float,
        arcs: Dict[str, Dict[str, Any]],
        relationships: Dict[str, Dict[str, float]]
    ) -> str:
        """
        Convert personality activation to semantic dynamic activation packet.
        
        Implements: docs/numeric_semantic_mapping.md §9.3
        
        Args:
            personality_kernel: Numeric personality kernel
            personality_activation: Activation modulation values
            mood: {valence, arousal}
            drives: Drive levels
            energy: Energy level
            arcs: Active arcs
            relationships: Relationship edges
            
        Returns:
            Semantic activation packet (30-80 tokens)
        """
        # Compute activation factors deterministically
        stress = personality_activation.get("stress_modulation", 0.0)
        arousal_mod = personality_activation.get("arousal_modulation", 0.0)
        valence_mod = personality_activation.get("valence_modulation", 0.0)
        energy_mod = personality_activation.get("energy_modulation", 1.0)
        
        # Build semantic description
        parts = []
        
        if stress > 0.6:
            parts.append("more defensive than usual")
        elif stress < 0.3:
            parts.append("relatively relaxed")
        
        if energy_mod < 0.4:
            parts.append("feels tired")
        elif energy_mod > 0.8:
            parts.append("feels energetic")
        
        if valence_mod < -0.3:
            parts.append("slightly down")
        elif valence_mod > 0.3:
            parts.append("slightly upbeat")
        
        if arousal_mod > 0.6:
            parts.append("somewhat alert")
        
        if parts:
            activation_text = f"Right now she is {', '.join(parts)}."
        else:
            activation_text = "Right now she is in a fairly neutral state."
        
        return activation_text

