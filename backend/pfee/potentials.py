"""
PFEE Latent Potentials Resolver

Implements:
- PFEE_ARCHITECTURE.md §2.2
- PFEE_LOGIC.md §2
- PFEE_PLAN.md Phase P2

Resolves latent potentials into concrete entities/events.
"""

from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import Column, Integer, String, Boolean, DateTime, JSON, select
from sqlalchemy.sql import func

from backend.persistence.database import Base


class PotentialType(str, Enum):
    """Types of latent potentials."""
    DOG_ENCOUNTER = "dog_encounter"
    FAN_APPROACH = "fan_approach"
    CLIENT_MESSAGE = "client_message"
    DELIVERY = "delivery"
    TRAVEL_INTERRUPTION = "travel_interruption"
    ENVIRONMENTAL_EVENT = "environmental_event"
    GENERAL = "general"


class ContextType(str, Enum):
    """Context types for potentials."""
    PARK = "park"
    AIRPORT = "airport"
    CELEBRITY_PUBLIC = "celebrity_public"
    PHONE = "phone"
    STREET = "street"
    CAFE = "cafe"
    HOME = "home"
    GENERAL = "general"


# PotentialModel is now defined in backend/persistence/models.py
# Import it here for backward compatibility
from backend.persistence.models import PotentialModel


@dataclass
class ResolvedPotential:
    """A resolved potential ready for instantiation."""
    id: int
    context_type: ContextType
    potential_type: PotentialType
    parameters: Dict[str, Any]
    is_interruptive: bool
    resolved_entity: Optional[Dict[str, Any]] = None


class PotentialResolver:
    """
    Resolves latent potentials into concrete entities/events.
    
    Implements PFEE_LOGIC.md §2 potential resolution logic.
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    async def register_potential(
        self,
        context_type: ContextType,
        potential_type: PotentialType,
        parameters: Dict[str, Any]
    ) -> PotentialModel:
        """
        Register a new latent potential.
        
        Implements PFEE_LOGIC.md §2.1
        """
        potential = PotentialModel(
            context_type=context_type.value,
            potential_type=potential_type.value,
            parameters=parameters
        )
        self.session.add(potential)
        await self.session.flush()
        return potential

    async def resolve_potentials_for_context(
        self,
        context: Dict[str, Any]
    ) -> List[ResolvedPotential]:
        """
        Resolve potentials matching the current context.
        
        Implements PFEE_LOGIC.md §2.2
        """
        try:
            if not isinstance(context, dict):
                return []

            context_type_str = context.get("context_type", "general")
            
            # Load matching unresolved potentials
            stmt = select(PotentialModel).where(
                PotentialModel.context_type == context_type_str,
                PotentialModel.is_resolved == False
            )
            result = await self.session.execute(stmt)
            potentials = result.scalars().all()

            resolved = []
            for p in potentials:
                try:
                    if self._meets_resolution_criteria(p, context):
                        resolved_potential = await self._resolve_single_potential(p, context)
                        resolved.append(resolved_potential)
                        # Mark as resolved
                        p.is_resolved = True
                        p.resolved_at = datetime.now(datetime.timezone.utc)
                except Exception as e:
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.error(f"Error resolving potential {p.id}: {str(e)}", exc_info=True)
                    continue

            await self.session.flush()
            return resolved
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error resolving potentials for context: {str(e)}", exc_info=True)
            return []

    def _meets_resolution_criteria(
        self,
        potential: PotentialModel,
        context: Dict[str, Any]
    ) -> bool:
        """
        Check if potential meets criteria for resolution.
        
        Deterministic check based on time, salience, context match.
        """
        # Check time-based criteria
        time_window = potential.parameters.get("time_window")
        if time_window:
            current_time = context.get("current_time")
            if current_time:
                # Check if current time is within window
                start = time_window.get("start")
                end = time_window.get("end")
                if start and current_time < start:
                    return False
                if end and current_time > end:
                    return False

        # Check salience threshold
        salience_threshold = potential.parameters.get("salience_threshold", 0.0)
        context_salience = context.get("salience", 0.0)
        if context_salience < salience_threshold:
            return False

        # Check context match
        required_context = potential.parameters.get("required_context", {})
        for key, value in required_context.items():
            if context.get(key) != value:
                return False

        return True

    async def _resolve_single_potential(
        self,
        potential: PotentialModel,
        context: Dict[str, Any]
    ) -> ResolvedPotential:
        """
        Resolve a single potential into a concrete entity/event.
        
        Deterministic resolution based on potential type and parameters.
        """
        potential_type = PotentialType(potential.potential_type)
        is_interruptive = potential.parameters.get("is_interruptive", False)

        # Generate resolved entity based on type
        resolved_entity = None
        if potential_type == PotentialType.DOG_ENCOUNTER:
            resolved_entity = {
                "type": "dog",
                "name": potential.parameters.get("dog_name", "a dog"),
                "behavior": potential.parameters.get("behavior", "approaching"),
                "location": context.get("location")
            }
        elif potential_type == PotentialType.CLIENT_MESSAGE:
            resolved_entity = {
                "type": "message",
                "sender": potential.parameters.get("sender_name", "client"),
                "content": potential.parameters.get("content_template", "You have a message"),
                "channel": potential.parameters.get("channel", "phone")
            }
        elif potential_type == PotentialType.DELIVERY:
            resolved_entity = {
                "type": "delivery",
                "item": potential.parameters.get("item", "package"),
                "carrier": potential.parameters.get("carrier", "delivery service"),
                "location": context.get("location")
            }
        else:
            # Generic resolution
            resolved_entity = {
                "type": potential_type.value,
                "parameters": potential.parameters
            }

        return ResolvedPotential(
            id=potential.id,
            context_type=ContextType(potential.context_type),
            potential_type=potential_type,
            parameters=potential.parameters,
            is_interruptive=is_interruptive,
            resolved_entity=resolved_entity
        )

