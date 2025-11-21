"""
PFEE Information Event Manager

Implements:
- PFEE_ARCHITECTURE.md §2.8
- PFEE_LOGIC.md §8
- PFEE_PLAN.md Phase P7

Manages information events as first-class perceptions.
"""

from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from backend.pfee.entities import EntityPersistenceManager, EntityType, PersistenceLevel


class InfoEventType(str, Enum):
    """Types of information events."""
    MESSAGE = "message"
    EMAIL = "email"
    NOTIFICATION = "notification"
    CALENDAR_ALERT = "calendar_alert"
    NEWS = "news"
    SOCIAL_CONTENT = "social_content"
    PHONE_CALL = "phone_call"


# InfoEventModel is now defined in backend/persistence/models.py
# Import it here for backward compatibility
from backend.persistence.models import InfoEventModel


@dataclass
class InfoEvent:
    """Information event ready for perception."""
    id: int
    type: InfoEventType
    sender_id: Optional[int]
    sender_type: str
    recipient_id: Optional[int]
    recipient_type: str
    content: Optional[str]
    metadata: Dict[str, Any]
    scheduled_time: datetime


class InformationEventManager:
    """
    Manages information events.
    
    Implements PFEE_LOGIC.md §8 information events logic.
    """

    def __init__(self, session: AsyncSession):
        self.session = session
        self.entity_manager = EntityPersistenceManager(session)

    async def compute_due_information_events(
        self,
        world_state: Dict[str, Any]
    ) -> List[InfoEvent]:
        """
        Compute information events that are due based on schedules and influence.
        
        Implements PFEE_LOGIC.md §8.1
        
        Purely deterministic, no LLM.
        """
        current_time = world_state.get("current_time")
        if not current_time:
            return []

        # Query for undelivered events scheduled for current time or earlier
        from sqlalchemy import select
        stmt = select(InfoEventModel).where(
            InfoEventModel.scheduled_time <= current_time,
            InfoEventModel.delivered == False
        )
        result = await self.session.execute(stmt)
        due_models = result.scalars().all()

        events = []
        for model in due_models:
            event = InfoEvent(
                id=model.id,
                type=InfoEventType(model.type),
                sender_id=model.sender_id,
                sender_type=model.sender_type or "unknown",
                recipient_id=model.recipient_id,
                recipient_type=model.recipient_type or "unknown",
                content=model.content,
                metadata=model.metadata or {},
                scheduled_time=model.scheduled_time
            )
            events.append(event)

        return events

    async def build_info_event_perception(
        self,
        info_event: InfoEvent,
        world_state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Build perception packet for information event.
        
        Implements PFEE_LOGIC.md §8.2
        """
        # Resolve sender as Persistent/Thin
        sender = await self._resolve_sender(info_event, world_state)

        # Classify sender persistence
        if sender:
            sender_context = {
                "entity_id": sender.get("id"),
                "entity_type": EntityType.PERSON if info_event.sender_type == "agent" else None
            }
            persistence_level = await self.entity_manager.classify_entity_persistence(
                sender,
                sender_context,
                EntityType.PERSON if info_event.sender_type == "agent" else EntityType.INFORMATION_SOURCE
            )

            # Promote to persistent if needed
            if persistence_level == PersistenceLevel.PERSISTENT and sender.get("id"):
                await self.entity_manager.promote_to_persistent(
                    sender["id"],
                    EntityType.PERSON if info_event.sender_type == "agent" else EntityType.INFORMATION_SOURCE
                )

        # Build renderer packet
        relationship_context = await self._build_relationship_context(info_event, world_state)
        perception_packet = {
            "event_type": "info_event",
            "info_event_type": info_event.type.value,
            "sender_identity": self._build_sender_identity_summary(info_event, sender),
            "content": info_event.content,
            "channel": info_event.metadata.get("channel", "unknown"),
            "relationship_context": relationship_context
        }

        # Mark as delivered
        await self._mark_event_delivered(info_event.id)

        return perception_packet

    async def _resolve_sender(
        self,
        info_event: InfoEvent,
        world_state: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Resolve sender entity from info event."""
        if not info_event.sender_id:
            return None

        if info_event.sender_type == "agent":
            # Load agent
            from backend.persistence.repo import AgentRepo
            agent_repo = AgentRepo(self.session)
            agent = await agent_repo.get_agent_by_id(info_event.sender_id)
            if agent:
                return {
                    "id": agent.id,
                    "name": agent.name,
                    "type": "agent"
                }
        elif info_event.sender_type == "user":
            # Load user
            from backend.persistence.repo import UserRepo
            user_repo = UserRepo(self.session)
            user = await user_repo.get_user_by_id(info_event.sender_id)
            if user:
                return {
                    "id": user.id,
                    "name": user.name,
                    "type": "user"
                }

        return None

    def _build_sender_identity_summary(
        self,
        info_event: InfoEvent,
        sender: Optional[Dict[str, Any]]
    ) -> str:
        """Build semantic summary of sender identity."""
        if sender:
            sender_name = sender.get('name', 'Unknown')
            sender_type = sender.get('type', 'unknown')
            # Add relationship context if available
            relationship_note = ""
            if sender_type == "agent":
                # Could add relationship warmth/trust note here
                relationship_note = ""
            return f"{sender_name} ({sender_type}){relationship_note}"
        else:
            # Thin entity - use metadata
            sender_name = info_event.metadata.get("sender_name", "Unknown sender")
            sender_role = info_event.metadata.get("sender_role", "")
            if sender_role:
                return f"{sender_name} ({sender_role})"
            return sender_name

    async def _build_relationship_context(
        self,
        info_event: InfoEvent,
        world_state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Build relationship context for info event."""
        from backend.persistence.repo import AgentRepo
        
        context = {
            "sender_known": info_event.sender_type in ["agent", "user"],
            "familiarity": info_event.metadata.get("familiarity", "unknown")
        }
        
        # If sender is an agent, try to get relationship data
        if info_event.sender_type == "agent" and info_event.sender_id:
            try:
                agent_repo = AgentRepo(self.session)
                # Get relationships for recipient if it's an agent
                if info_event.recipient_type == "agent" and info_event.recipient_id:
                    relationships = await agent_repo.get_relationships(info_event.recipient_id)
                    for rel in relationships:
                        if rel.target_agent_id == info_event.sender_id:
                            context["warmth"] = rel.warmth
                            context["trust"] = rel.trust
                            context["tension"] = rel.tension
                            break
            except Exception:
                # If relationship lookup fails, continue with basic context
                pass
        
        return context

    async def _mark_event_delivered(self, event_id: int) -> None:
        """Mark information event as delivered."""
        from sqlalchemy import update
        stmt = update(InfoEventModel).where(
            InfoEventModel.id == event_id
        ).values(
            delivered=True,
            delivered_at=datetime.now(datetime.timezone.utc)
        )
        await self.session.execute(stmt)
        await self.session.flush()

    async def create_info_event(
        self,
        event_type: InfoEventType,
        sender_id: Optional[int],
        sender_type: str,
        recipient_id: Optional[int],
        recipient_type: str,
        content: Optional[str],
        scheduled_time: datetime,
        metadata: Optional[Dict[str, Any]] = None
    ) -> InfoEventModel:
        """Create a new information event."""
        event = InfoEventModel(
            type=event_type.value,
            sender_id=sender_id,
            sender_type=sender_type,
            recipient_id=recipient_id,
            recipient_type=recipient_type,
            content=content,
            scheduled_time=scheduled_time,
            metadata=metadata or {}
        )
        self.session.add(event)
        await self.session.flush()
        return event

