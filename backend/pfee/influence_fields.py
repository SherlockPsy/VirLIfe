"""
PFEE Influence Field Manager

Implements:
- PFEE_ARCHITECTURE.md §2.7
- PFEE_LOGIC.md §3
- PFEE_PLAN.md Phase P2

Manages cross-time influence fields for persistent agents and systems.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select


# InfluenceFieldModel is now defined in backend/persistence/models.py
# Import it here for backward compatibility
from backend.persistence.models import InfluenceFieldModel


@dataclass
class InfluenceSnapshot:
    """Snapshot of influence field state for an agent."""
    agent_id: int
    mood_offset: Dict[str, float] = field(default_factory=dict)  # {valence, arousal}
    drive_pressures: Dict[str, float] = field(default_factory=dict)
    pending_contact_probability: float = 0.0
    unresolved_tension_topics: List[str] = field(default_factory=list)
    last_updated: Optional[datetime] = None


class InfluenceFieldManager:
    """
    Manages influence fields for agents.
    
    Implements PFEE_LOGIC.md §3 influence field logic.
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    async def update_influence_fields_from_background(
        self,
        world_state: Dict[str, Any]
    ) -> None:
        """
        Update influence fields from background world state.
        
        Implements PFEE_LOGIC.md §3.1
        
        Uses background logic (not LLM) to compute deltas.
        """
        try:
            if not isinstance(world_state, dict):
                return

            persistent_agents = world_state.get("persistent_agents", [])
            if not isinstance(persistent_agents, list):
                return

            for agent_data in persistent_agents:
                if not isinstance(agent_data, dict):
                    continue
                    
                agent_id = agent_data.get("id")
                if not agent_id:
                    continue

                try:
                    # Compute background deltas deterministically
                    deltas = self._compute_background_deltas(agent_data, world_state)

                    # Load or create influence field
                    field = await self._load_or_create_influence_field(agent_id)

                    # Apply deltas
                    field = self._apply_deltas(field, deltas)

                    # Persist
                    self.session.add(field)
                except Exception as e:
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.error(f"Error updating influence field for agent {agent_id}: {str(e)}", exc_info=True)
                    continue

            await self.session.flush()
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error updating influence fields from background: {str(e)}", exc_info=True)

    async def query_influence_for_agent(
        self,
        agent_id: int
    ) -> Optional[InfluenceSnapshot]:
        """
        Query influence field for an agent.
        
        Implements PFEE_LOGIC.md §3.2
        """
        field = await self._load_or_create_influence_field(agent_id)
        if not field:
            return None

        return InfluenceSnapshot(
            agent_id=agent_id,
            mood_offset=field.mood_offset or {},
            drive_pressures=field.drive_pressures or {},
            pending_contact_probability=field.pending_contact_probability or 0.0,
            unresolved_tension_topics=field.unresolved_tension_topics or [],
            last_updated=field.last_updated_timestamp
        )

    def _compute_background_deltas(
        self,
        agent_data: Dict[str, Any],
        world_state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Compute background deltas deterministically.
        
        No LLM calls - pure deterministic logic based on:
        - agent's current state
        - world time
        - schedules
        - relationships
        """
        deltas = {
            "mood_offset": {"valence": 0.0, "arousal": 0.0},
            "drive_pressures": {},
            "pending_contact_probability": 0.0,
            "unresolved_tension_topics": []
        }

        # Check for missed obligations (increases competence pressure)
        calendar_items = agent_data.get("calendar_items", [])
        current_time = world_state.get("current_time")
        if current_time:
            for item in calendar_items:
                if item.get("status") == "missed":
                    # Increase competence drive pressure
                    deltas["drive_pressures"]["competence"] = 0.1

        # Check for upcoming important events (increases arousal)
        for item in calendar_items:
            if item.get("status") == "pending":
                start_time = item.get("start_time")
                if start_time and current_time:
                    time_until = (start_time - current_time).total_seconds()
                    if 0 < time_until < 3600:  # Within 1 hour
                        deltas["mood_offset"]["arousal"] = 0.1

        # Check relationships for unresolved tensions
        relationships = agent_data.get("relationships", [])
        for rel in relationships:
            tension = rel.get("tension", 0.0)
            if tension > 0.5:
                # Add topic if relationship has unresolved tension
                topic = rel.get("tension_topic", "relationship_issue")
                if topic not in deltas["unresolved_tension_topics"]:
                    deltas["unresolved_tension_topics"].append(topic)

        # Pending contact probability based on relationship warmth and time since last contact
        for rel in relationships:
            warmth = rel.get("warmth", 0.0)
            if warmth > 0.5:
                # Higher warmth = higher probability of pending contact
                deltas["pending_contact_probability"] = max(
                    deltas["pending_contact_probability"],
                    warmth * 0.3
                )

        return deltas

    async def _load_or_create_influence_field(
        self,
        agent_id: int
    ) -> InfluenceFieldModel:
        """Load existing influence field or create new one."""
        from sqlalchemy import select
        stmt = select(InfluenceFieldModel).where(
            InfluenceFieldModel.agent_id == agent_id
        )
        result = await self.session.execute(stmt)
        field = result.scalars().first()

        if not field:
            field = InfluenceFieldModel(agent_id=agent_id)
            self.session.add(field)

        return field

    def _apply_deltas(
        self,
        field: InfluenceFieldModel,
        deltas: Dict[str, Any]
    ) -> InfluenceFieldModel:
        """Apply deltas to influence field."""
        # Update mood offset
        mood_offset = field.mood_offset or {}
        delta_mood = deltas.get("mood_offset", {})
        mood_offset["valence"] = mood_offset.get("valence", 0.0) + delta_mood.get("valence", 0.0)
        mood_offset["arousal"] = mood_offset.get("arousal", 0.0) + delta_mood.get("arousal", 0.0)
        # Clamp to reasonable ranges
        mood_offset["valence"] = max(-1.0, min(1.0, mood_offset["valence"]))
        mood_offset["arousal"] = max(0.0, min(1.0, mood_offset["arousal"]))
        field.mood_offset = mood_offset

        # Update drive pressures
        drive_pressures = field.drive_pressures or {}
        delta_drives = deltas.get("drive_pressures", {})
        for drive_name, delta_value in delta_drives.items():
            current = drive_pressures.get(drive_name, 0.0)
            drive_pressures[drive_name] = max(0.0, min(1.0, current + delta_value))
        field.drive_pressures = drive_pressures

        # Update pending contact probability
        delta_prob = deltas.get("pending_contact_probability", 0.0)
        field.pending_contact_probability = min(1.0, field.pending_contact_probability + delta_prob)

        # Update unresolved tension topics
        existing_topics = set(field.unresolved_tension_topics or [])
        new_topics = deltas.get("unresolved_tension_topics", [])
        field.unresolved_tension_topics = list(existing_topics.union(new_topics))

        return field

