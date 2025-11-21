"""
PFEE Potential Resolver

Implements:
- PFEE_ARCHITECTURE.md §2.2
- PFEE_LOGIC.md §2
- PFEE_PLAN.md Phase P2

Resolves latent potentials into concrete entities/events.
"""

from dataclasses import dataclass
from typing import Dict, Any, List, Optional
from enum import Enum
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime

from backend.persistence.models import PotentialModel


class PotentialType(str, Enum):
    """Types of latent potentials."""
    DOG_ENCOUNTER = "dog_encounter"
    FAN_APPROACH = "fan_approach"
    CLIENT_MESSAGE = "client_message"
    DELIVERY = "delivery"
    TRAVEL_INTERRUPTION = "travel_interruption"
    ENVIRONMENTAL_EVENT = "environmental_event"
    UNKNOWN_CONTACT = "unknown_contact"


class ContextType(str, Enum):
    """Context types for potential registration."""
    PARK = "park"
    AIRPORT = "airport"
    CELEBRITY_PUBLIC = "celebrity_public"
    PHONE = "phone"
    STREET = "street"
    CAFE = "cafe"
    GENERAL = "general"


@dataclass
class ResolvedPotential:
    """A resolved potential with instantiated entity."""
    id: int
    potential_type: PotentialType
    context_type: ContextType
    resolved_entity: Optional[Dict[str, Any]] = None
    parameters: Dict[str, Any] = None


class PotentialResolver:
    """
    Resolves latent potentials into concrete entities/events.
    
    Implements PFEE_LOGIC.md §2 potential resolution logic.
    """
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def register_potential(
        self,
        context: Dict[str, Any],
        potential_type: PotentialType,
        parameters: Dict[str, Any]
    ) -> int:
        """
        Register a new latent potential.
        
        Implements PFEE_LOGIC.md §2.1
        """
        context_type_str = context.get("context_type", ContextType.GENERAL.value)
        
        potential = PotentialModel(
            context_type=context_type_str,
            potential_type=potential_type.value,
            parameters=parameters,
            is_resolved=False
        )
        self.session.add(potential)
        await self.session.flush()
        return potential.id
    
    async def resolve_potentials_for_context(
        self,
        context: Dict[str, Any]
    ) -> List[ResolvedPotential]:
        """
        Resolve potentials matching the current context.
        
        Implements PFEE_LOGIC.md §2.2
        
        Resolution MUST be deterministic given the same inputs.
        """
        context_type = context.get("context_type", ContextType.GENERAL.value)
        
        # Load unresolved potentials matching context
        stmt = select(PotentialModel).where(
            PotentialModel.context_type == context_type,
            PotentialModel.is_resolved == False
        )
        result = await self.session.execute(stmt)
        potentials = result.scalars().all()
        
        resolved = []
        for p in potentials:
            if await self._meets_resolution_criteria(p, context):
                resolved_potential = await self._resolve_single_potential(p, context)
                resolved.append(resolved_potential)
        
        return resolved
    
    async def _meets_resolution_criteria(
        self,
        potential: PotentialModel,
        context: Dict[str, Any]
    ) -> bool:
        """
        Check if potential meets resolution criteria.
        
        Deterministic checks based on:
        - time conditions
        - salience thresholds
        - context matching
        """
        # Time-based checks
        current_time = context.get("current_time")
        if current_time:
            # Check if potential has time constraints
            time_constraints = potential.parameters.get("time_constraints", {})
            if time_constraints:
                hour = current_time.hour if hasattr(current_time, "hour") else 12
                allowed_hours = time_constraints.get("allowed_hours", [])
                if allowed_hours and hour not in allowed_hours:
                    return False
        
        # Salience checks
        salience = context.get("salience", 0.0)
        min_salience = potential.parameters.get("min_salience", 0.0)
        if salience < min_salience:
            return False
        
        # Context matching
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
        Resolve a single potential into a concrete entity.
        
        Deterministic entity instantiation based on potential type and parameters.
        """
        potential_type = PotentialType(potential.potential_type)
        context_type = ContextType(potential.context_type)
        
        # Deterministic entity creation based on potential type
        resolved_entity = None
        
        if potential_type == PotentialType.DOG_ENCOUNTER:
            resolved_entity = {
                "type": "person",
                "name": potential.parameters.get("name", "A dog"),
                "description": potential.parameters.get("description", "A dog approaches"),
                "is_animal": True
            }
        elif potential_type == PotentialType.CLIENT_MESSAGE:
            resolved_entity = {
                "type": "information_source",
                "name": potential.parameters.get("sender_name", "Unknown"),
                "description": "Message from client",
                "message_content": potential.parameters.get("message_content", "")
            }
        elif potential_type == PotentialType.DELIVERY:
            resolved_entity = {
                "type": "object",
                "name": potential.parameters.get("item_name", "Delivery"),
                "description": "A delivery arrives"
            }
        else:
            # Generic entity
            resolved_entity = {
                "type": "person",
                "name": potential.parameters.get("name", "Unknown"),
                "description": potential.parameters.get("description", "")
            }
        
        # Mark potential as resolved
        potential.is_resolved = True
        potential.resolved_at = datetime.utcnow()
        await self.session.flush()
        
        return ResolvedPotential(
            id=potential.id,
            potential_type=potential_type,
            context_type=context_type,
            resolved_entity=resolved_entity,
            parameters=potential.parameters
        )

