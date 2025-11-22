"""
PFEE Cognition Input Builder

Implements Section C.5 of the blueprint:
- Constructs CognitionInput from trigger + WorldState + SemanticFrame
- Determines vantage agent (never George)
- Builds scene description, internal state summary, constraints, rules
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
from dataclasses import dataclass

from backend.cognition.service import SemanticCognitionInput
from backend.cognition.eligibility import EventTrivialityClassification, BehavioralChoice


def build_cognition_input(
    trigger: Dict[str, Any],
    world_state: Dict[str, Any],
    semantics: Dict[str, Any]
) -> SemanticCognitionInput:
    """
    C.5: Construct the exact input structure for cognition.
    
    Implements Section C.5 of the blueprint:
    - Determines vantage agent (never George)
    - Builds scene description
    - Builds internal state summary for vantage agent
    - Adds constraints and rules
    - Constructs SemanticCognitionInput
    
    Args:
        trigger: Dict with trigger_type, actor_agent_id, user_message, etc.
        world_state: WorldState dict from world_state_builder
        semantics: SemanticFrame dict from semantic_mapping
    
    Returns:
        SemanticCognitionInput object ready for cognition service
    """
    # C.5.1: Determine Vantage Agent (never George)
    vantage_agent_id = _determine_vantage_agent(trigger, world_state)
    if not vantage_agent_id:
        raise ValueError("Cannot determine vantage agent (no valid agent found)")
    
    # Get vantage agent data
    vantage_agent_data = None
    vantage_semantics = None
    for agent_data in world_state.get("agents_in_scene", []):
        if agent_data["id"] == vantage_agent_id:
            vantage_agent_data = agent_data
            break
    
    for agent_sem in semantics.get("agents", []):
        if agent_sem.get("agent_id") == vantage_agent_id:
            vantage_semantics = agent_sem
            break
    
    if not vantage_agent_data or not vantage_semantics:
        raise ValueError(f"Vantage agent {vantage_agent_id} not found in scene")
    
    # C.5.2: Scene Description
    scene_description_text = _build_scene_description(world_state, trigger)
    
    # C.5.3: Internal State Summary for Vantage Agent
    vantage_internal_state_text = _build_vantage_internal_state(vantage_semantics)
    
    # C.5.4: Other Agents in Scene
    other_agents_text = _build_other_agents_text(world_state, semantics, vantage_agent_id)
    
    # C.5.4: Constraints and Rules
    rules_and_constraints_text = _build_rules_and_constraints(world_state)
    
    # C.5.5: Build CognitionInput
    event_description = trigger.get("event_description", "")
    if not event_description:
        if trigger.get("trigger_type") == "user_input":
            event_description = f"User says: {trigger.get('user_message', '')}"
        elif trigger.get("trigger_type") == "agent_initiative":
            event_description = f"{vantage_agent_data.get('name', 'Agent')} is initiating an interaction"
        else:
            event_description = "An event occurs in the world"
    
    # Build personality dict from semantics
    personality = {
        "summary": vantage_semantics.get("personality_summary_text", ""),
        "identity": vantage_semantics.get("identity_summary", "")
    }
    
    # Build relationships summary
    relationships_summary = vantage_semantics.get("relationship_summaries_text", {})
    
    # Build arcs summary
    arcs_summary_text = vantage_semantics.get("arc_summaries_text", "")
    arcs_summary = []
    if arcs_summary_text:
        arcs_summary = [arcs_summary_text]  # Can be split into list if needed
    
    # Build memories (already semantic from world_state)
    memories_dict = {
        "relevant": vantage_semantics.get("memory_summaries_text", "").split(". ") if vantage_semantics.get("memory_summaries_text") else []
    }
    
    # Build event participants
    event_participants = {}
    for agent_data in world_state.get("agents_in_scene", []):
        if agent_data.get("is_real_user"):
            event_participants[f"user_{agent_data['id']}"] = {
                "name": agent_data.get("name", "George"),
                "role": "user",
                "is_real_user": True
            }
        else:
            event_participants[f"agent_{agent_data['id']}"] = {
                "name": agent_data.get("name", "Unknown"),
                "role": "agent",
                "is_real_user": False
            }
    
    # Build SemanticCognitionInput
    cognition_input = SemanticCognitionInput(
        agent_id=str(vantage_agent_id),
        event_type=trigger.get("trigger_type", "unknown"),
        event_time=world_state.get("current_time", datetime.now()),
        event_description=event_description,
        personality=personality,
        personality_activation="",  # Will be derived from emotional state
        mood_summary=vantage_semantics.get("current_emotional_state_text", ""),
        drives_summary=[],  # Already included in emotional state
        relationships_summary=relationships_summary,
        arcs_summary=arcs_summary,
        energy_summary="",  # Can be derived from agent data if needed
        intentions_summary=[],  # Can be extracted from agent data
        memories=memories_dict,
        event_participants=event_participants,
        event_topics=_extract_event_topics(trigger, vantage_semantics),
        event_triviality=EventTrivialityClassification.SIGNIFICANT,  # Default, can be refined
        behavioral_choices=[],  # Can be derived if needed
        relevant_calendar_context=None,  # Can be added if calendar items relevant
        relevant_unexpected_event_context=None,
        eligibility_metadata={
            "scene_description": scene_description_text,
            "vantage_internal_state": vantage_internal_state_text,
            "other_agents": other_agents_text,
            "rules_and_constraints": rules_and_constraints_text
        }
    )
    
    return cognition_input


def _determine_vantage_agent(
    trigger: Dict[str, Any],
    world_state: Dict[str, Any]
) -> Optional[int]:
    """
    C.5.1: Determine Vantage Agent (never George).
    
    Rules:
    - If trigger_type == "agent_initiative": vantage = actor_agent_id
    - If trigger_type == "user_input": vantage = primary interaction partner (e.g., Rebecca)
    - For info events or time ticks: vantage = agent whose influence fields/arcs triggered
    - NEVER George
    """
    trigger_type = trigger.get("trigger_type")
    george_agent_id = world_state.get("george_agent_id")
    agents_in_scene = world_state.get("agents_in_scene", [])
    
    if trigger_type == "agent_initiative":
        actor_agent_id = trigger.get("actor_agent_id")
        if actor_agent_id and actor_agent_id != george_agent_id:
            # Verify agent is in scene and not George
            for agent in agents_in_scene:
                if agent["id"] == actor_agent_id and not agent.get("is_real_user"):
                    return actor_agent_id
    
    elif trigger_type == "user_input":
        # Choose primary interaction partner (e.g., Rebecca)
        for agent in agents_in_scene:
            if not agent.get("is_real_user"):
                # Check if this is a primary partner
                status_flags = agent.get("status_flags", {})
                if isinstance(status_flags, dict) and status_flags.get("is_partner_of_george"):
                    return agent["id"]
        
        # Fallback to first non-George agent
        for agent in agents_in_scene:
            if not agent.get("is_real_user"):
                return agent["id"]
    
    elif trigger_type in ["info_event", "time_tick"]:
        # Find agent whose influence fields or arcs triggered the perception
        # For now, use first non-George agent with active arcs
        for agent in agents_in_scene:
            if not agent.get("is_real_user"):
                arcs = agent.get("arcs", [])
                if arcs and len(arcs) > 0:
                    return agent["id"]
        
        # Fallback to first non-George agent
        for agent in agents_in_scene:
            if not agent.get("is_real_user"):
                return agent["id"]
    
    # Default: first non-George agent
    for agent in agents_in_scene:
        if not agent.get("is_real_user"):
            return agent["id"]
    
    return None


def _build_scene_description(
    world_state: Dict[str, Any],
    trigger: Dict[str, Any]
) -> str:
    """
    C.5.2: Construct scene description.
    
    Includes:
    - Location, time of day, who is present
    - Physical context (room description)
    - External facts about George (what he's doing, not internal state)
    """
    parts = []
    
    # Location and time
    location = world_state.get("location", {})
    location_name = location.get("name", "the location")
    current_time = world_state.get("current_time")
    
    parts.append(f"The scene is in {location_name}.")
    
    if current_time:
        time_str = _format_time_of_day(current_time)
        parts.append(f"It is {time_str}.")
    
    # Who is present
    agents_in_scene = world_state.get("agents_in_scene", [])
    agent_names = []
    george_present = False
    for agent in agents_in_scene:
        if agent.get("is_real_user"):
            george_present = True
            agent_names.append("George")
        else:
            agent_names.append(agent.get("name", "Unknown"))
    
    if agent_names:
        names_str = ", ".join(agent_names)
        parts.append(f"Present: {names_str}.")
    
    # Physical context
    location_desc = location.get("description", "")
    if location_desc:
        parts.append(location_desc)
    
    # External facts about George (if present)
    if george_present:
        george_agent_data = None
        for agent in agents_in_scene:
            if agent.get("is_real_user"):
                george_agent_data = agent
                break
        
        if george_agent_data:
            public_profile = george_agent_data.get("public_profile", {})
            if public_profile.get("profession"):
                parts.append(f"George works as {public_profile['profession']}.")
            
            # What George is doing (from trigger if user_input)
            trigger_type = trigger.get("trigger_type")
            if trigger_type == "user_input":
                user_message = trigger.get("user_message", "")
                if user_message:
                    parts.append(f"George says: '{user_message}'")
                else:
                    parts.append("George is present and interacting.")
            else:
                parts.append("George is present in the scene.")
    
    return " ".join(parts)


def _build_vantage_internal_state(
    vantage_semantics: Dict[str, Any]
) -> str:
    """
    C.5.3: Build internal state summary for vantage agent.
    
    Includes:
    - Personality summary
    - Current emotional/motivational state
    - Relevant relationships (especially with George and other present agents)
    - Active arcs and unresolved tensions
    - Key memories relevant now
    """
    parts = []
    
    # Personality summary
    personality_summary = vantage_semantics.get("personality_summary_text", "")
    if personality_summary:
        parts.append(f"Her personality: {personality_summary}")
    
    # Current emotional state
    emotional_state = vantage_semantics.get("current_emotional_state_text", "")
    if emotional_state:
        parts.append(emotional_state)
    
    # Relationships
    relationships_text = vantage_semantics.get("relationship_summaries_text", {})
    if relationships_text:
        for target_id, rel_text in relationships_text.items():
            if rel_text:
                parts.append(rel_text)
    
    # Active arcs
    arcs_text = vantage_semantics.get("arc_summaries_text", "")
    if arcs_text:
        parts.append(arcs_text)
    
    # Unresolved tensions
    tensions_text = vantage_semantics.get("unresolved_tensions_text", "")
    if tensions_text:
        parts.append(tensions_text)
    
    # Key memories
    memories_text = vantage_semantics.get("memory_summaries_text", "")
    if memories_text:
        parts.append(f"Relevant memories: {memories_text}")
    
    return " ".join(parts)


def _build_other_agents_text(
    world_state: Dict[str, Any],
    semantics: Dict[str, Any],
    vantage_agent_id: int
) -> str:
    """Build description of other agents in the scene."""
    parts = []
    
    agents_in_scene = world_state.get("agents_in_scene", [])
    agents_semantics = semantics.get("agents", [])
    
    for agent_data in agents_in_scene:
        agent_id = agent_data["id"]
        if agent_id == vantage_agent_id:
            continue
        
        agent_name = agent_data.get("name", "Unknown")
        
        # Find semantics for this agent
        agent_sem = None
        for sem in agents_semantics:
            if sem.get("agent_id") == agent_id:
                agent_sem = sem
                break
        
        if agent_data.get("is_real_user"):
            # George: external only
            parts.append(f"{agent_name} is present. He is the real user, and his inner thoughts are not simulated.")
        else:
            # Other agents: brief summary
            identity = agent_sem.get("identity_summary", "") if agent_sem else ""
            if identity:
                parts.append(f"{agent_name}: {identity}")
    
    return " ".join(parts)


def _build_rules_and_constraints(
    world_state: Dict[str, Any]
) -> str:
    """
    C.5.4: Build rules and constraints text.
    
    Reminds cognition of:
    - Global constraints (monogamy, relationship rules, George being real)
    - No fabrication rules
    - George protection rules
    """
    rules = [
        "RULES AND CONSTRAINTS:",
        "",
        "1. George is the real user. His inner thoughts, feelings, and psychological state are NEVER simulated.",
        "   - Do NOT generate memories for George.",
        "   - Do NOT simulate George's internal state (drives, mood, thoughts).",
        "   - Only describe George's external actions and words as observed.",
        "",
        "2. Relationship rules:",
        "   - The relationship between Rebecca and George is exclusive and monogamous.",
        "   - Do NOT introduce affairs, break-ups, or radical relationship changes.",
        "   - Changes to relationships must be gradual and grounded in existing state.",
        "",
        "3. Continuity rules:",
        "   - Do NOT fabricate new life events not grounded in existing memories or state.",
        "   - Do NOT assume large off-screen arcs have resolved without recorded events.",
        "   - Respect temporal continuity (time advances modestly, not in large jumps).",
        "",
        "4. World constraints:",
        "   - Physical movement must respect location adjacency.",
        "   - Objects must exist in the current location to be referenced.",
        "   - Agents must be present in the scene to interact with.",
        ""
    ]
    
    return "\n".join(rules)


def _extract_event_topics(
    trigger: Dict[str, Any],
    vantage_semantics: Dict[str, Any]
) -> List[str]:
    """Extract topics from trigger and vantage agent's state."""
    topics = []
    
    # From trigger
    user_message = trigger.get("user_message", "")
    if user_message:
        # Simple keyword extraction (can be enhanced)
        words = user_message.lower().split()
        for word in words:
            if len(word) > 4:  # Skip short words
                topics.append(word)
    
    # From unresolved tensions
    tensions_text = vantage_semantics.get("unresolved_tensions_text", "")
    if tensions_text:
        # Extract key topics
        topics.append("unresolved_tensions")
    
    # From arcs
    arcs_text = vantage_semantics.get("arc_summaries_text", "")
    if arcs_text:
        topics.append("active_arcs")
    
    return topics[:5]  # Limit to 5 topics


def _format_time_of_day(dt: datetime) -> str:
    """Format datetime to time of day description."""
    hour = dt.hour
    if hour < 6:
        return "early morning"
    elif hour < 12:
        return "morning"
    elif hour < 14:
        return "midday"
    elif hour < 17:
        return "afternoon"
    elif hour < 20:
        return "evening"
    elif hour < 22:
        return "late evening"
    else:
        return "night"

