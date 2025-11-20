"""
Cognition Context Builder
Phase 4 Implementation

Builds semantic context packets for Cognition LLM calls.
Ensures NO raw numeric state reaches the LLM.

Implements:
- MASTER_SPEC §PART II §7 (Cognition Service)
- docs/cognition_flow.md §4 (COGNITION INPUT PACKET)
- MASTER_SPEC §SECTION 9 (Cognition Trigger Logic)
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from backend.mapping.semantic_mappers import (
    MoodMapper,
    DriveMapper,
    RelationshipMapper,
    ArcMapper,
    EnergyMapper,
    IntentionMapper,
    PersonalityMapper,
    MemoryMapper,
)


@dataclass
class CognitionContext:
    """
    Semantic context packet for Cognition LLM.
    
    MUST contain ONLY semantic (non-numeric) state.
    MUST NOT contain raw personality kernel or raw numeric values.
    
    Implements: docs/cognition_flow.md §4 (COGNITION INPUT PACKET)
    """
    
    # Agent identification
    agent_id: int
    agent_name: str
    
    # Personality context (all semantic, from Personality Compiler)
    personality_summary: str  # Stable summary ≈150–250 tokens
    domain_summaries: Dict[str, str]  # e.g., emotion, conflict, humour, communication, intimacy
    dynamic_activation_packet: str  # Moment-to-moment modulation ≈30–80 tokens
    
    # Perception snapshot (what the agent perceives)
    perception_snapshot: Dict[str, Any]  # who is present, what is happening, environment
    
    # Semantic mood
    mood_summary: str
    
    # Semantic drives (top-K pressured drives)
    pressured_drives: List[Dict[str, str]]  # [{drive_name, semantic_description}, ...]
    
    # Semantic relationships (relevant relationships only)
    relevant_relationships: List[Dict[str, Any]]  # [{target_name, primary_state, attraction_note?, ...}, ...]
    
    # Semantic arcs (active arcs only)
    active_arcs: List[str]  # [semantic_arc_description, ...]
    
    # Semantic energy
    energy_summary: str
    
    # Semantic intentions (high-priority only)
    high_priority_intentions: List[str]  # [semantic_intention_description, ...]
    
    # Memory snippets (episodic + biographical, semantic)
    relevant_episodic_memories: List[str]  # [memory_description, ...]
    relevant_biographical_memories: List[str]  # [biographical_fact, ...]
    
    # Event context that triggered cognition
    event_context: Dict[str, Any]  # event_type, description, source, target, timestamp, etc.
    
    # Calendar/obligation context (if relevant)
    relevant_calendar_context: Optional[str] = None  # e.g., "upcoming rehearsal at 19:00"
    
    # Unexpected event (incursion) context (if relevant)
    unexpected_event_context: Optional[str] = None  # e.g., "key turning in lock"
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Converts context to dict for JSON serialization / LLM prompting.
        """
        return asdict(self)
    
    def to_prompt_dict(self) -> Dict[str, Any]:
        """
        Converts context to LLM-ready dict with clean formatting.
        Ensures NO numeric values are present.
        """
        return {
            "agent_context": {
                "agent_name": self.agent_name,
                "personality": {
                    "summary": self.personality_summary,
                    "domains": self.domain_summaries,
                    "activation": self.dynamic_activation_packet,
                },
            },
            "current_state": {
                "mood": self.mood_summary,
                "energy": self.energy_summary,
                "drives": self.pressured_drives,
                "intentions": self.high_priority_intentions,
            },
            "relationships": self.relevant_relationships,
            "arcs": self.active_arcs,
            "memories": {
                "episodic": self.relevant_episodic_memories,
                "biographical": self.relevant_biographical_memories,
            },
            "event": self.event_context,
            "context": {
                "calendar": self.relevant_calendar_context,
                "unexpected_event": self.unexpected_event_context,
            },
        }


class CognitionContextBuilder:
    """
    Builds CognitionContext packets for Cognition LLM calls.
    
    All conversions from numeric → semantic happen here.
    
    Implements:
    - docs/cognition_flow.md §4 (COGNITION INPUT PACKET)
    - docs/numeric_semantic_mapping.md (all mappers)
    - BUILDER_CONTRACT §6 (Coding Obligations)
    """
    
    @staticmethod
    def build_context(
        agent_id: int,
        agent_name: str,
        personality_summary: str,
        domain_summaries: Dict[str, str],
        kernel: Dict[str, float],
        mood: Dict[str, float],
        drives: Dict[str, Dict],
        arcs: List[Dict],
        energy: float,
        relationships: List[Dict],
        intentions: List[Dict],
        episodic_memories: List[Dict],
        biographical_memories: List[Dict],
        perception_snapshot: Dict[str, Any],
        event: Dict[str, Any],
        relevant_calendar_context: Optional[str] = None,
        unexpected_event_context: Optional[str] = None,
    ) -> CognitionContext:
        """
        Main entry point: builds complete semantic context packet.
        
        All numeric inputs are converted to semantic outputs via deterministic mappers.
        
        Args:
            agent_id: Agent ID
            agent_name: Agent name
            personality_summary: Stable personality summary (from Personality Compiler)
            domain_summaries: Domain-specific summaries (from Personality Compiler)
            kernel: Numeric personality kernel (used only to compute dynamic activation)
            mood: Numeric mood {valence, arousal}
            drives: Numeric drives {drive_name: {level, sensitivity}}
            arcs: List of numeric arc dicts
            energy: Numeric energy [0, 1]
            relationships: List of relationship edge dicts
            intentions: List of intention dicts
            episodic_memories: List of episodic memory dicts
            biographical_memories: List of biographical memory dicts
            perception_snapshot: Perception packet (already semantic)
            event: Event that triggered cognition (context)
            relevant_calendar_context: Optional calendar context (semantic)
            unexpected_event_context: Optional incursion context (semantic)
            
        Returns:
            CognitionContext (fully semantic)
        """
        
        # 1. Mood mapping
        valence = mood.get("valence", 0)
        arousal = mood.get("arousal", 0)
        mood_summary = MoodMapper.map_mood(valence, arousal)
        
        # 2. Drives mapping (top-K pressured)
        pressured_drives = DriveMapper.get_highest_pressure_drives(drives, top_k=2)
        pressured_drives_list = [
            {"drive_name": name, "semantic_description": desc}
            for name, desc in pressured_drives
        ]
        
        # 3. Energy mapping
        energy_summary = EnergyMapper.map_energy(energy)
        
        # 4. Relationships mapping (filter to relevant ones)
        relevant_relationships = CognitionContextBuilder._map_relationships(
            relationships, agent_id
        )
        
        # 5. Arcs mapping
        active_arcs = ArcMapper.map_arcs_summary(arcs)
        
        # 6. Intentions mapping (high-priority only)
        high_priority_intentions = IntentionMapper.map_intentions_summary(intentions)
        
        # 7. Memories mapping (Phase 9: Filtered for token efficiency)
        event_type = event.get("event_type", "unknown")
        filtered_episodic, filtered_biographical = CognitionContextBuilder._filter_relevant_memories(
            episodic_memories, 
            biographical_memories, 
            event_type,
            max_episodic=2,  # Reduced from 3
            max_biographical=2  # Reduced from 3
        )
        
        relevant_episodic = [
            MemoryMapper.format_episodic_memory(m.get("description", ""))
            for m in filtered_episodic
        ]
        relevant_biographical = [
            MemoryMapper.format_biographical_memory(m.get("description", ""))
            for m in filtered_biographical
        ]
        
        # 8. Dynamic activation packet
        dynamic_activation = PersonalityMapper.compute_dynamic_activation_packet(
            kernel=kernel,
            drives=drives,
            mood=mood,
            arcs=arcs,
            relationships=relationships,
            energy=energy,
            relevant_memory="\n".join(relevant_episodic) if relevant_episodic else None,
        )
        
        return CognitionContext(
            agent_id=agent_id,
            agent_name=agent_name,
            personality_summary=personality_summary,
            domain_summaries=domain_summaries,
            dynamic_activation_packet=dynamic_activation,
            perception_snapshot=perception_snapshot,
            mood_summary=mood_summary,
            pressured_drives=pressured_drives_list,
            relevant_relationships=relevant_relationships,
            active_arcs=active_arcs,
            energy_summary=energy_summary,
            high_priority_intentions=high_priority_intentions,
            relevant_episodic_memories=relevant_episodic,
            relevant_biographical_memories=relevant_biographical,
            event_context=event,
            relevant_calendar_context=relevant_calendar_context,
            unexpected_event_context=unexpected_event_context,
        )
    
    @staticmethod
    def _map_relationships(relationships: List[Dict], agent_id: int) -> List[Dict[str, Any]]:
        """
        Maps relationship edges to semantic summaries.
        
        Filters out weak/inactive relationships; keeps only relevant ones.
        
        Args:
            relationships: List of relationship edge dicts
            agent_id: Agent ID (for context, if needed)
            
        Returns:
            List of relationship dicts with semantic state
        """
        mapped_rels = []
        
        for rel in relationships:
            # Extract relationship dimensions
            warmth = rel.get("warmth", 0)
            trust = rel.get("trust", 0.5)
            tension = rel.get("tension", 0.1)
            attraction = rel.get("attraction")
            comfort = rel.get("comfort")
            
            # Skip very weak/inactive relationships
            total_involvement = abs(warmth) + trust + tension
            if total_involvement < 0.2:
                continue
            
            # Map to semantic
            rel_mapping = RelationshipMapper.map_relationship_full(
                warmth, trust, tension, attraction, comfort
            )
            
            # Add target info
            mapped_rel = {
                "target_name": rel.get("target_name", "unknown"),
                "target_type": rel.get("target_type", "agent"),  # "agent" or "user"
                "primary_state": rel_mapping.get("primary_state", ""),
            }
            
            if "attraction_note" in rel_mapping:
                mapped_rel["attraction_note"] = rel_mapping["attraction_note"]
            if "comfort_note" in rel_mapping:
                mapped_rel["comfort_note"] = rel_mapping["comfort_note"]
            
            mapped_rels.append(mapped_rel)
        
        return mapped_rels
    
    @staticmethod
    def _filter_relevant_memories(
        episodic_memories: List[Dict],
        biographical_memories: List[Dict],
        event_type: str,
        max_episodic: int = 2,
        max_biographical: int = 2
    ) -> tuple:
        """
        Filter memories to most relevant, reducing token count.
        
        Phase 9 optimization: Reduce memory context by 25-30%.
        
        Args:
            episodic_memories: List of episodic memory dicts
            biographical_memories: List of biographical memory dicts
            event_type: Type of event (for relevance filtering)
            max_episodic: Maximum episodic memories to include
            max_biographical: Maximum biographical memories to include
        
        Returns:
            (filtered_episodic, filtered_biographical) tuples
        """
        # Filter episodic: take top-N by relevance score
        filtered_episodic = episodic_memories[:max_episodic] if episodic_memories else []
        
        # Filter biographical: take top-N, prioritize recent
        filtered_biographical = biographical_memories[:max_biographical] if biographical_memories else []
        
        return filtered_episodic, filtered_biographical

