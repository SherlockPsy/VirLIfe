"""
PFEE Information Event Manager

Implements:
- PFEE_ARCHITECTURE.md §2.8
- PFEE_LOGIC.md §8
- PFEE_PLAN.md Phase P7

Manages non-physical informational events (messages, emails, notifications).
"""

from dataclasses import dataclass
from typing import Dict, Any, List, Optional
from enum import Enum
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, Column, Integer, String, JSON, DateTime, ForeignKey
from sqlalchemy.sql import func
from datetime import datetime

from backend.persistence.models import Base
from backend.pfee.entities import EntityPersistenceManager, EntityType, PersistenceLevel


class InfoEventType(str, Enum):
    """Types of information events."""
    MESSAGE = "message"
    EMAIL = "email"
    NOTIFICATION = "notification"
    CALENDAR_ALERT = "calendar_alert"
    NEWS = "news"
    SOCIAL_CONTENT = "social_content"


class InfoEventModel(Base):
    """Database model for information events."""
    __tablename__ = "pfee_info_events"
    
    id = Column(Integer, primary_key=True, index=True)
    type = Column(String, nullable=False)  # InfoEventType
    content = Column(JSON, default={}, nullable=False)
    sender_id = Column(Integer, nullable=True)  # Can be agent_id or external
    sender_type = Column(String, nullable=False)  # "agent", "external", "system"
    recipient_id = Column(Integer, nullable=True)  # Usually user_id
    due_time = Column(DateTime(timezone=True), nullable=True)
    processed = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


@dataclass
class InfoEvent:
    """Information event representation."""
    id: int
    type: InfoEventType
    content: Dict[str, Any]
    sender_id: Optional[int]
    sender_type: str
    recipient_id: Optional[int]
    due_time: Optional[datetime]


class InformationEventManager:
    """
    Manages information events.
    
    Implements PFEE_LOGIC.md §8 information event logic.
    """
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.entity_manager = EntityPersistenceManager(session)
    
    async def compute_due_information_events(
        self,
        world_state: Dict[str, Any]
    ) -> List[InfoEvent]:
        """
        Compute information events that are due.
        
        Implements PFEE_LOGIC.md §8
        
        Purely deterministic, no LLM calls.
        """
        current_time = world_state.get("current_time")
        if not current_time:
            return []
        
        # Load unprocessed events that are due
        stmt = select(InfoEventModel).where(
            InfoEventModel.processed == False,
            InfoEventModel.due_time <= current_time
        )
        result = await self.session.execute(stmt)
        events_models = result.scalars().all()
        
        info_events = []
        for ev_model in events_models:
            info_event = InfoEvent(
                id=ev_model.id,
                type=InfoEventType(ev_model.type),
                content=ev_model.content or {},
                sender_id=ev_model.sender_id,
                sender_type=ev_model.sender_type,
                recipient_id=ev_model.recipient_id,
                due_time=ev_model.due_time
            )
            info_events.append(info_event)
        
        return info_events
    
    async def create_info_event(
        self,
        event_type: InfoEventType,
        content: Dict[str, Any],
        sender_id: Optional[int],
        sender_type: str,
        recipient_id: Optional[int],
        due_time: Optional[datetime] = None
    ) -> int:
        """Create a new information event."""
        event = InfoEventModel(
            type=event_type.value,
            content=content,
            sender_id=sender_id,
            sender_type=sender_type,
            recipient_id=recipient_id,
            due_time=due_time or datetime.utcnow(),
            processed=False
        )
        self.session.add(event)
        await self.session.flush()
        return event.id
    
    async def mark_event_processed(self, event_id: int) -> None:
        """Mark an information event as processed."""
        stmt = select(InfoEventModel).where(InfoEventModel.id == event_id)
        result = await self.session.execute(stmt)
        event = result.scalars().first()
        if event:
            event.processed = True
            await self.session.flush()
    
    async def resolve_sender_persistence(
        self,
        sender_id: int,
        sender_type: str,
        context: Dict[str, Any]
    ) -> PersistenceLevel:
        """
        Resolve sender as Persistent or Thin.
        
        Implements PFEE_LOGIC.md §8 sender resolution.
        """
        if sender_type == "agent":
            # Agents are always persistent
            return PersistenceLevel.PERSISTENT
        elif sender_type == "external":
            # External senders are typically Thin unless they have obligations
            entity = {
                "id": sender_id,
                "type": "information_source"
            }
            persistence = await self.entity_manager.classify_entity_persistence(
                entity, context, EntityType.INFORMATION_SOURCE
            )
            return persistence
        else:
            # System events are ephemeral
            return PersistenceLevel.EPHEMERAL

