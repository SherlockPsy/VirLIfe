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
    
    @staticmethod
    def map_world_state_to_semantics(world_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        C.4: Convert numeric/internal world_state into natural-language descriptors.
        
        Implements Section C.4 of the blueprint:
        - Maps agent personalities, drives, mood, relationships, arcs, memories
        - Enforces George protection (external-only for George)
        - Builds SemanticFrame structure
        
        Args:
            world_state: WorldState dict from world_state_builder
            
        Returns:
            SemanticFrame dict with semantic descriptions per agent
        """
        semantic_frame = {
            "agents": [],
            "george_in_scene": world_state.get("george_in_scene", False),
            "george_agent_id": world_state.get("george_agent_id")
        }
        
        agents_in_scene = world_state.get("agents_in_scene", [])
        relationships = world_state.get("relationships", {})
        george_agent_id = world_state.get("george_agent_id")
        
        for agent_data in agents_in_scene:
            agent_id = agent_data["id"]
            is_real_user = agent_data.get("is_real_user", False)
            
            if is_real_user:
                # C.4.6: George Semantics (External Only)
                george_frame = _build_george_semantics(
                    agent_data, relationships, agents_in_scene
                )
                semantic_frame["agents"].append(george_frame)
            else:
                # C.4.1-4.5: Non-George Agent Semantics
                agent_frame = _build_agent_semantics(
                    agent_data, relationships, agents_in_scene, george_agent_id
                )
                semantic_frame["agents"].append(agent_frame)
        
        return semantic_frame


def _build_george_semantics(
    george_data: Dict[str, Any],
    relationships: Dict[str, Dict[str, Any]],
    agents_in_scene: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    C.4.6: Build semantic frame for George (external-only).
    
    Uses only:
    - How others see him (from relationships and memories)
    - Public facts from public_profile
    """
    george_frame = {
        "agent_id": george_data["id"],
        "name": george_data["name"],
        "identity_summary": _build_george_identity(george_data),
        "relationship_summaries_text": {}
    }
    
    # Build "She sees George as X" style descriptions from others
    for other_agent in agents_in_scene:
        if other_agent.get("is_real_user"):
            continue  # Skip George himself
        
        other_id = other_agent["id"]
        rel_key = f"{other_id}_to_george_user_{george_data['id']}"
        rel = relationships.get(rel_key) or relationships.get(f"{other_id}_to_agent_{george_data['id']}")
        
        if rel:
            rel_text = _build_relationship_summary(rel, other_agent["name"], "George")
            george_frame["relationship_summaries_text"][other_id] = rel_text
    
    return george_frame


def _build_george_identity(george_data: Dict[str, Any]) -> str:
    """Build identity summary from public_profile."""
    public_profile = george_data.get("public_profile", {})
    parts = []
    
    if public_profile.get("profession"):
        parts.append(f"George works as {public_profile['profession']}")
    if public_profile.get("hobbies"):
        parts.append(f"He enjoys {public_profile['hobbies']}")
    
    if parts:
        return ". ".join(parts) + "."
    return "George is present in the scene."


def _build_agent_semantics(
    agent_data: Dict[str, Any],
    relationships: Dict[str, Dict[str, Any]],
    agents_in_scene: List[Dict[str, Any]],
    george_agent_id: Optional[int]
) -> Dict[str, Any]:
    """
    C.4.1-4.5: Build complete semantic frame for non-George agent.
    """
    agent_id = agent_data["id"]
    
    # C.4.1: Personality and Baseline Semantics
    personality_summary_text = _build_personality_summary(agent_data)
    domain_summaries_text = _build_domain_summaries(agent_data)
    
    # C.4.2: Current Emotional and Motivational State
    current_emotional_state_text = _build_emotional_state(agent_data)
    
    # C.4.3: Relationships Semantics
    relationship_summaries_text = _build_relationship_summaries(
        agent_data, relationships, agents_in_scene, george_agent_id
    )
    
    # C.4.4: Arcs and Influence Fields Semantics
    arc_summaries_text = _build_arc_summaries(agent_data)
    unresolved_tensions_text = _build_unresolved_tensions(agent_data)
    
    # C.4.5: Memory Semantics
    memory_summaries_text = _build_memory_summaries(agent_data)
    
    # Identity summary
    identity_summary = _build_identity_summary(agent_data)
    
    return {
        "agent_id": agent_id,
        "name": agent_data["name"],
        "identity_summary": identity_summary,
        "personality_summary_text": personality_summary_text,
        "domain_summaries_text": domain_summaries_text,
        "current_emotional_state_text": current_emotional_state_text,
        "relationship_summaries_text": relationship_summaries_text,
        "arc_summaries_text": arc_summaries_text,
        "unresolved_tensions_text": unresolved_tensions_text,
        "memory_summaries_text": memory_summaries_text
    }


def _build_personality_summary(agent_data: Dict[str, Any]) -> str:
    """C.4.1: Merge personality_summaries into compact text."""
    summaries = agent_data.get("personality_summaries", {})
    if not isinstance(summaries, dict):
        return ""
    
    parts = []
    
    if summaries.get("self_view"):
        parts.append(summaries["self_view"])
    if summaries.get("love_style"):
        parts.append(f"In relationships, {summaries['love_style']}")
    if summaries.get("career_style"):
        parts.append(f"In her career, {summaries['career_style']}")
    if summaries.get("conflict_style"):
        parts.append(f"When conflicts arise, {summaries['conflict_style']}")
    if summaries.get("public_image"):
        parts.append(f"Publicly, {summaries['public_image']}")
    if summaries.get("private_self"):
        parts.append(f"Privately, {summaries['private_self']}")
    
    return " ".join(parts)


def _build_domain_summaries(agent_data: Dict[str, Any]) -> str:
    """C.4.1: Produce domain-specific sentences."""
    domains = agent_data.get("domain_summaries", {})
    if not isinstance(domains, dict):
        return ""
    
    parts = []
    domain_order = ["career", "family", "romance", "friends", "fame_and_public_life", "creativity", "health_and_body"]
    
    for domain in domain_order:
        if domain in domains and domains[domain]:
            # Compress to 1-3 sentences
            text = domains[domain]
            sentences = text.split(". ")
            parts.append(". ".join(sentences[:2]))  # Take first 2 sentences max
    
    return ". ".join(parts) + "." if parts else ""


def _build_emotional_state(agent_data: Dict[str, Any]) -> str:
    """C.4.2: Convert drives and mood to emotional state description."""
    parts = []
    
    # Mood
    mood = agent_data.get("mood", {})
    if isinstance(mood, dict):
        valence = mood.get("baseline_valence", 0.0)
        arousal = mood.get("baseline_arousal", 0.5)
        
        if valence > 0.3:
            parts.append("feels relatively positive")
        elif valence < -0.3:
            parts.append("feels somewhat down")
        
        if arousal > 0.6:
            parts.append("feels alert and engaged")
        elif arousal < 0.3:
            parts.append("feels calm and relaxed")
        
        anxiety = mood.get("anxiety_prone", 0.0)
        if anxiety > 0.5:
            parts.append("tends to feel anxious")
        
        optimism = mood.get("optimism_tendency", 0.5)
        if optimism > 0.6:
            parts.append("generally optimistic")
        elif optimism < 0.4:
            parts.append("tends toward caution")
    
    # Drives
    drives = agent_data.get("drives", {})
    if isinstance(drives, dict):
        drive_pressures = []
        for drive_name, drive_data in drives.items():
            if isinstance(drive_data, dict):
                baseline = drive_data.get("baseline", 0.5)
                current = drive_data.get("current", baseline)
                if current > baseline + 0.2:
                    if drive_name == "attachment":
                        drive_pressures.append("feels a strong need for reassurance and emotional closeness")
                    elif drive_name == "achievement":
                        drive_pressures.append("is driven to accomplish something important")
                    elif drive_name == "recognition":
                        drive_pressures.append("wants to be seen and acknowledged")
        
        if drive_pressures:
            parts.append("Right now, " + ", ".join(drive_pressures[:2]) + ".")
    
    if parts:
        return "She " + ", ".join(parts) + "."
    return "She feels relatively neutral right now."


def _build_relationship_summaries(
    agent_data: Dict[str, Any],
    relationships: Dict[str, Dict[str, Any]],
    agents_in_scene: List[Dict[str, Any]],
    george_agent_id: Optional[int]
) -> Dict[str, str]:
    """C.4.3: Build relationship summaries toward other agents."""
    relationship_summaries = {}
    agent_id = agent_data["id"]
    
    for other_agent in agents_in_scene:
        other_id = other_agent["id"]
        if other_id == agent_id:
            continue
        
        # Find relationship from this agent to other
        rel_key = f"{agent_id}_to_agent_{other_id}"
        rel = relationships.get(rel_key)
        
        if not rel and other_id == george_agent_id:
            # Try user_id format
            rel_key = f"{agent_id}_to_george_user_{other_id}"
            rel = relationships.get(rel_key)
        
        if rel:
            other_name = other_agent.get("name", "them")
            summary = _build_relationship_summary(rel, agent_data["name"], other_name)
            relationship_summaries[str(other_id)] = summary
    
    return relationship_summaries
    
    return relationship_summaries


def _build_relationship_summary(rel: Dict[str, Any], source_name: str, target_name: str) -> str:
    """Convert relationship vector to semantic summary."""
    warmth = rel.get("warmth", 0.0)
    trust = rel.get("trust", 0.0)
    attraction = rel.get("attraction", 0.0)
    tension = rel.get("tension", 0.0)
    comfort = rel.get("comfort", 0.0)
    
    parts = []
    
    if warmth > 0.8 and trust > 0.8:
        parts.append(f"feels very close and trusting toward {target_name}")
    elif warmth > 0.6:
        parts.append(f"feels warm toward {target_name}")
    
    if attraction > 0.7:
        parts.append(f"is strongly attracted to {target_name}")
    elif attraction > 0.5:
        parts.append(f"feels attraction toward {target_name}")
    
    if tension > 0.5:
        parts.append(f"feels some tension with {target_name}")
    elif tension > 0.3:
        parts.append(f"sometimes worries about {target_name}")
    
    if comfort > 0.7:
        parts.append(f"feels comfortable with {target_name}")
    
    if parts:
        return f"She {', '.join(parts[:3])}."  # Limit to 3 statements
    return f"She has a neutral relationship with {target_name}."


def _build_arc_summaries(agent_data: Dict[str, Any]) -> str:
    """C.4.4: Summarize active arcs."""
    arcs = agent_data.get("arcs", [])
    if not arcs:
        return ""
    
    arc_descriptions = []
    for arc in arcs:
        if isinstance(arc, dict):
            arc_name = arc.get("type", "")
            topic_vector = arc.get("topic_vector", {})
            if isinstance(topic_vector, dict):
                description = topic_vector.get("description", arc_name)
                core_tension = topic_vector.get("core_tension", "")
                progress = topic_vector.get("progress", 0.0)
                
                if core_tension:
                    arc_descriptions.append(f"She is in the middle of trying to {core_tension.lower()}")
                elif description:
                    arc_descriptions.append(f"She has an ongoing concern about {description.lower()}")
    
    if arc_descriptions:
        return " ".join(arc_descriptions) + "."
    return ""


def _build_unresolved_tensions(agent_data: Dict[str, Any]) -> str:
    """C.4.4: Summarize unresolved topics from influence fields."""
    influence_fields = agent_data.get("influence_fields", {})
    unresolved_topics = influence_fields.get("unresolved_tension_topics", {})
    
    if not isinstance(unresolved_topics, dict):
        return ""
    
    pressure_threshold = 0.6
    tensions = []
    
    for topic, topic_data in unresolved_topics.items():
        if isinstance(topic_data, dict):
            pressure = topic_data.get("pressure", 0.0)
            if pressure > pressure_threshold:
                tags = topic_data.get("tags", [])
                tag_text = " and ".join(tags[:2]) if tags else topic
                tensions.append(f"She feels increasing internal pressure about {tag_text}")
    
    if tensions:
        return " ".join(tensions) + "."
    return ""


def _build_memory_summaries(agent_data: Dict[str, Any]) -> str:
    """C.4.5: Summarize relevant memories."""
    memories = agent_data.get("memories", [])
    if not memories:
        return ""
    
    memory_descriptions = []
    for mem in memories[:5]:  # Limit to 5 memories
        if isinstance(mem, dict):
            description = mem.get("description", "")
            if description:
                # Compress to 1-2 sentences
                sentences = description.split(". ")
                compressed = ". ".join(sentences[:2])
                memory_descriptions.append(compressed)
    
    if memory_descriptions:
        return " ".join(memory_descriptions) + "."
    return ""


def _build_identity_summary(agent_data: Dict[str, Any]) -> str:
    """Build brief identity summary."""
    name = agent_data.get("name", "Unknown")
    status_flags = agent_data.get("status_flags", {})
    
    if isinstance(status_flags, dict):
        if status_flags.get("is_celebrity"):
            return f"{name} is a celebrated actress and public figure."
        elif status_flags.get("is_partner_of_george"):
            return f"{name} is George's partner."
        elif status_flags.get("is_child_of_george"):
            return f"{name} is George's daughter."
    
    return f"{name} is present in the scene."

