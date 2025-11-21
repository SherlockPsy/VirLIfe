"""
PFEE Entity Persistence Manager

Implements:
- PFEE_ARCHITECTURE.md §2.3
- PFEE_LOGIC.md §1
- PFEE_PLAN.md Phase P1

Manages Persistent vs Ephemeral (Deep vs Thin) entity classification.
"""

from enum import Enum
from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.persistence.models import AgentModel, LocationModel, ObjectModel
from backend.persistence.repo import AgentRepo


class PersistenceLevel(str, Enum):
    """Entity persistence classification."""
    PERSISTENT = "persistent"
    EPHEMERAL = "ephemeral"  # Thin


class EntityType(str, Enum):
    """Types of entities."""
    PERSON = "person"
    LOCATION = "location"
    OBJECT = "object"
    ORGANISATION = "organisation"
    INFORMATION_SOURCE = "information_source"


class EntityPersistenceManager:
    """
    Manages entity persistence classification.
    
    Implements PFEE_LOGIC.md §1 entity persistence logic.
    """
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.agent_repo = AgentRepo(session)
    
    async def classify_entity_persistence(
        self,
        entity: Dict[str, Any],
        context: Dict[str, Any],
        entity_type: EntityType
    ) -> PersistenceLevel:
        """
        Classify entity as Persistent or Ephemeral.
        
        Implements PFEE_LOGIC.md §1.1
        
        Rules:
        - Already marked persistent → PERSISTENT
        - Core person (family, close friend, therapist) → PERSISTENT
        - Long-term obligations with user → PERSISTENT
        - Key location for user routines → PERSISTENT
        - Multiple salient encounters (≥3) → PERSISTENT
        - Tied to biographical memory or core arcs → PERSISTENT
        - Default → EPHEMERAL
        """
        if not isinstance(entity, dict) or not isinstance(context, dict):
            return PersistenceLevel.EPHEMERAL
        
        # Check if already marked persistent
        if entity.get("persistence_level") == PersistenceLevel.PERSISTENT.value:
            return PersistenceLevel.PERSISTENT
        
        # Core person check (family, close friend, therapist, etc.)
        if entity_type == EntityType.PERSON:
            if self._is_core_person(entity):
                return PersistenceLevel.PERSISTENT
        
        # Long-term obligations with user
        if self._has_long_term_obligations_with_user(entity, context):
            return PersistenceLevel.PERSISTENT
        
        # Key location for user routines
        if entity_type == EntityType.LOCATION:
            if self._is_key_location_for_user_routines(entity, context):
                return PersistenceLevel.PERSISTENT
        
        # Multiple salient encounters
        if self._has_been_encountered_in_multiple_salient_events(entity, context):
            return PersistenceLevel.PERSISTENT
        
        # Tied to biographical memory or core arcs
        if self._is_tied_to_biographical_memory_or_core_arcs(entity, context):
            return PersistenceLevel.PERSISTENT
        
        # Default: Ephemeral
        return PersistenceLevel.EPHEMERAL
    
    async def promote_to_persistent(
        self,
        entity_id: int,
        entity_type: EntityType
    ) -> bool:
        """
        Promote an entity from Ephemeral to Persistent.
        
        Implements PFEE_LOGIC.md §1.2
        
        Idempotent: if already persistent, returns True without changes.
        """
        entity = await self._load_entity(entity_id, entity_type)
        if not entity:
            return False
        
        # Check if already persistent (idempotent)
        if hasattr(entity, "persistence_level"):
            if entity.persistence_level == PersistenceLevel.PERSISTENT.value:
                return True
        
        # Update persistence level
        if entity_type == EntityType.PERSON:
            # For agents, store in status_flags
            if hasattr(entity, "status_flags"):
                flags = entity.status_flags or {}
                flags["persistence_level"] = PersistenceLevel.PERSISTENT.value
                entity.status_flags = flags
        elif entity_type == EntityType.OBJECT:
            obj_stmt = select(ObjectModel).where(ObjectModel.id == entity_id)
            obj_result = await self.session.execute(obj_stmt)
            obj = obj_result.scalars().first()
            if obj:
                if not obj.state:
                    obj.state = {}
                obj.state["persistence_level"] = PersistenceLevel.PERSISTENT.value
        elif entity_type == EntityType.LOCATION:
            loc_stmt = select(LocationModel).where(LocationModel.id == entity_id)
            loc_result = await self.session.execute(loc_stmt)
            loc = loc_result.scalars().first()
            if loc:
                if not loc.attributes:
                    loc.attributes = {}
                loc.attributes["persistence_level"] = PersistenceLevel.PERSISTENT.value
        
        await self.session.flush()
        return True
    
    async def is_persistent(
        self,
        entity_id: int,
        entity_type: EntityType
    ) -> bool:
        """Check if entity is persistent."""
        entity = await self._load_entity(entity_id, entity_type)
        if not entity:
            return False
        
        if hasattr(entity, "persistence_level"):
            return entity.persistence_level == PersistenceLevel.PERSISTENT.value
        
        if hasattr(entity, "status_flags"):
            flags = entity.status_flags or {}
            return flags.get("persistence_level") == PersistenceLevel.PERSISTENT.value
        
        # Check JSON fields for objects/locations
        if hasattr(entity, "state") and entity.state:
            return entity.state.get("persistence_level") == PersistenceLevel.PERSISTENT.value
        
        if hasattr(entity, "attributes") and entity.attributes:
            return entity.attributes.get("persistence_level") == PersistenceLevel.PERSISTENT.value
        
        return False
    
    def _is_core_person(self, entity: Dict[str, Any]) -> bool:
        """Check if entity is a core person (family, close friend, therapist)."""
        relationship_type = entity.get("relationship_type", "")
        core_types = {"family", "close_friend", "therapist", "partner", "spouse"}
        return relationship_type in core_types
    
    def _has_long_term_obligations_with_user(
        self,
        entity: Dict[str, Any],
        context: Dict[str, Any]
    ) -> bool:
        """Check if entity has long-term obligations with user."""
        obligations = entity.get("obligations", [])
        for obligation in obligations:
            if obligation.get("with_user", False):
                if obligation.get("is_long_term", False):
                    return True
        return False
    
    def _is_key_location_for_user_routines(
        self,
        entity: Dict[str, Any],
        context: Dict[str, Any]
    ) -> bool:
        """Check if location is key for user routines."""
        location_name = entity.get("name", "")
        key_locations = context.get("user_routine_locations", [])
        return location_name in key_locations
    
    def _has_been_encountered_in_multiple_salient_events(
        self,
        entity: Dict[str, Any],
        context: Dict[str, Any]
    ) -> bool:
        """Check if entity has been encountered in multiple salient events."""
        encounter_count = entity.get("salient_encounter_count", 0)
        return encounter_count >= 3  # Threshold for promotion
    
    def _is_tied_to_biographical_memory_or_core_arcs(
        self,
        entity: Dict[str, Any],
        context: Dict[str, Any]
    ) -> bool:
        """Check if entity is tied to biographical memory or core arcs."""
        # Check if entity appears in biographical memories
        biographical_mentions = entity.get("biographical_mentions", 0)
        if biographical_mentions > 0:
            return True
        
        # Check if entity is part of active core arcs
        active_arcs = context.get("active_arcs", [])
        for arc in active_arcs:
            if entity.get("id") in arc.get("related_entities", []):
                return True
        
        return False
    
    async def _load_entity(
        self,
        entity_id: int,
        entity_type: EntityType
    ) -> Optional[Any]:
        """Load entity from database based on type."""
        if entity_type == EntityType.PERSON:
            return await self.agent_repo.get_agent_by_id(entity_id)
        elif entity_type == EntityType.LOCATION:
            stmt = select(LocationModel).where(LocationModel.id == entity_id)
            result = await self.session.execute(stmt)
            return result.scalars().first()
        elif entity_type == EntityType.OBJECT:
            stmt = select(ObjectModel).where(ObjectModel.id == entity_id)
            result = await self.session.execute(stmt)
            return result.scalars().first()
        else:
            return None

