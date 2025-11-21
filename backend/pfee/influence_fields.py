"""
PFEE Influence Field Manager

Implements:
- PFEE_ARCHITECTURE.md §2.7
- PFEE_LOGIC.md §3
- PFEE_PLAN.md Phase P2

Manages cross-time influence fields for persistent agents and systems.
"""

from dataclasses import dataclass
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, Column, Integer, String, JSON, DateTime, ForeignKey
from sqlalchemy.sql import func
from datetime import datetime

from backend.persistence.models import Base
from backend.persistence.models import AgentModel


class InfluenceFieldModel(Base):
    """Database model for agent influence fields."""
    __tablename__ = "pfee_influence_fields"
    
    id = Column(Integer, primary_key=True, index=True)
    agent_id = Column(Integer, ForeignKey("agents.id"), nullable=False, unique=True)
    mood_offset = Column(JSON, default={}, nullable=False)  # {valence_delta, arousal_delta}
    drive_pressures = Column(JSON, default={}, nullable=False)  # {drive_name: pressure_delta}
    pending_contact_probability = Column(JSON, default={}, nullable=False)  # {contact_type: probability}
    unresolved_tension_topics = Column(JSON, default=[], nullable=False)  # List of topic strings
    last_updated_timestamp = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


@dataclass
class InfluenceSnapshot:
    """Snapshot of influence field state."""
    agent_id: int
    mood_offset: Dict[str, float]
    drive_pressures: Dict[str, float]
    pending_contact_probability: Dict[str, float]
    unresolved_tension_topics: List[str]
    last_updated: datetime


class InfluenceFieldManager:
    """
    Manages cross-time influence fields.
    
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
        # Get all persistent agents
        agents = world_state.get("persistent_agents", [])
        
        for agent_data in agents:
            agent_id = agent_data.get("id")
            if not agent_id:
                continue
            
            # Compute background deltas deterministically
            deltas = await self._compute_background_deltas(agent_data, world_state)
            
            # Load or create influence field
            field = await self._load_or_create_influence_field(agent_id)
            
            # Apply deltas
            field = await self._apply_deltas(field, deltas)
            
            # Persist
            field.last_updated_timestamp = datetime.utcnow()
            await self.session.flush()
    
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
            agent_id=field.agent_id,
            mood_offset=field.mood_offset or {},
            drive_pressures=field.drive_pressures or {},
            pending_contact_probability=field.pending_contact_probability or {},
            unresolved_tension_topics=field.unresolved_tension_topics or [],
            last_updated=field.last_updated_timestamp
        )
    
    async def _compute_background_deltas(
        self,
        agent_data: Dict[str, Any],
        world_state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Compute background deltas deterministically.
        
        No LLM calls. Pure deterministic logic based on:
        - agent's current state
        - world time
        - schedules
        - recent events
        """
        deltas = {
            "mood_offset": {"valence_delta": 0.0, "arousal_delta": 0.0},
            "drive_pressures": {},
            "pending_contact_probability": {},
            "unresolved_tension_topics": []
        }
        
        # Example: if agent has high drive pressure, it may influence future mood
        drives = agent_data.get("drives", {})
        if isinstance(drives, dict):
            for drive_name, drive_data in drives.items():
                if isinstance(drive_data, dict):
                    level = drive_data.get("level", 0.0)
                    if level > 0.7:  # High unmet need
                        deltas["drive_pressures"][drive_name] = level * 0.1  # Small persistent pressure
        
        # Example: if agent has active arcs with negative valence, add tension topics
        arcs = agent_data.get("arcs", {})
        if isinstance(arcs, dict):
            for arc_name, arc_data in arcs.items():
                if isinstance(arc_data, dict):
                    intensity = arc_data.get("intensity", 0.0)
                    valence_bias = arc_data.get("valence_bias", 0.0)
                    if intensity > 0.5 and valence_bias < -0.3:
                        topic = arc_data.get("topic_vector", ["unknown"])[0] if arc_data.get("topic_vector") else "unknown"
                        deltas["unresolved_tension_topics"].append(topic)
        
        return deltas
    
    async def _load_or_create_influence_field(
        self,
        agent_id: int
    ) -> Optional[InfluenceFieldModel]:
        """Load or create influence field for agent."""
        stmt = select(InfluenceFieldModel).where(InfluenceFieldModel.agent_id == agent_id)
        result = await self.session.execute(stmt)
        field = result.scalars().first()
        
        if not field:
            field = InfluenceFieldModel(
                agent_id=agent_id,
                mood_offset={},
                drive_pressures={},
                pending_contact_probability={},
                unresolved_tension_topics=[]
            )
            self.session.add(field)
            await self.session.flush()
        
        return field
    
    async def _apply_deltas(
        self,
        field: InfluenceFieldModel,
        deltas: Dict[str, Any]
    ) -> InfluenceFieldModel:
        """Apply deltas to influence field."""
        # Update mood offset
        mood_deltas = deltas.get("mood_offset", {})
        current_mood = field.mood_offset or {}
        field.mood_offset = {
            "valence_delta": current_mood.get("valence_delta", 0.0) + mood_deltas.get("valence_delta", 0.0),
            "arousal_delta": current_mood.get("arousal_delta", 0.0) + mood_deltas.get("arousal_delta", 0.0)
        }
        
        # Update drive pressures (accumulate)
        drive_deltas = deltas.get("drive_pressures", {})
        current_drives = field.drive_pressures or {}
        for drive_name, delta in drive_deltas.items():
            current_drives[drive_name] = current_drives.get(drive_name, 0.0) + delta
        field.drive_pressures = current_drives
        
        # Update pending contact probability
        contact_deltas = deltas.get("pending_contact_probability", {})
        current_contacts = field.pending_contact_probability or {}
        for contact_type, prob in contact_deltas.items():
            current_contacts[contact_type] = prob  # Replace, not accumulate
        field.pending_contact_probability = current_contacts
        
        # Update unresolved tension topics (merge, deduplicate)
        tension_deltas = deltas.get("unresolved_tension_topics", [])
        current_tensions = field.unresolved_tension_topics or []
        combined = list(set(current_tensions + tension_deltas))
        field.unresolved_tension_topics = combined
        
        return field

