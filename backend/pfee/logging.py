"""
PFEE Logger

Implements:
- PFEE_ARCHITECTURE.md §2.9
- PFEE_PLAN.md Phase P8

Provides internal logging and traceability for PFEE decisions.
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum
from sqlalchemy.ext.asyncio import AsyncSession


class PFEELogLevel(str, Enum):
    """Log levels for PFEE."""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


# PFEELogModel is now defined in backend/persistence/models.py
# Import it here for backward compatibility
from backend.persistence.models import PFEELogModel


class PFEELogger:
    """
    Internal logger for PFEE decisions and traces.
    
    Logs are for system owner only, not part of in-world perception.
    """

    def __init__(self, session: AsyncSession, enable_db_logging: bool = True):
        self.session = session
        self.enable_db_logging = enable_db_logging
        self.python_logger = logging.getLogger("pfee")
        self.current_cycle_id: Optional[str] = None

    def start_perception_cycle(self, cycle_id: Optional[str] = None) -> None:
        """Start a new perception cycle for logging."""
        if not cycle_id:
            import uuid
            cycle_id = str(uuid.uuid4())
        self.current_cycle_id = cycle_id

    def log_perception_cycle(
        self,
        decisions: List[Dict[str, Any]],
        resolved_potentials: List[Dict[str, Any]],
        entities: List[Dict[str, Any]],
        cognition_output: Optional[Dict[str, Any]],
        renderer_output: Optional[Dict[str, Any]]
    ) -> None:
        """
        Log a complete perception cycle.
        
        Implements PFEE_PLAN.md Phase P8 logging requirements.
        """
        self.log_info(
            component="PerceptionOrchestrator",
            event_type="perception_cycle",
            message="Perception cycle completed",
            metadata={
                "decisions": decisions,
                "resolved_potentials_count": len(resolved_potentials),
                "entities_count": len(entities),
                "cognition_called": cognition_output is not None,
                "renderer_called": renderer_output is not None
            }
        )

    def log_trigger_firing(
        self,
        trigger_reason: str,
        agent_id: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Log when a trigger fires."""
        self.log_info(
            component="TriggerEvaluator",
            event_type="trigger_fired",
            message=f"Trigger fired: {trigger_reason}",
            metadata={
                "trigger_reason": trigger_reason,
                "agent_id": agent_id,
                **(metadata or {})
            }
        )

    def log_potential_resolution(
        self,
        potential_id: int,
        potential_type: str,
        resolved_entity: Optional[Dict[str, Any]] = None
    ) -> None:
        """Log when a potential is resolved."""
        self.log_info(
            component="PotentialResolver",
            event_type="potential_resolved",
            message=f"Potential resolved: {potential_type}",
            metadata={
                "potential_id": potential_id,
                "potential_type": potential_type,
                "resolved_entity": resolved_entity
            }
        )

    def log_entity_classification(
        self,
        entity_id: int,
        entity_type: str,
        persistence_level: str,
        reason: str
    ) -> None:
        """Log entity persistence classification."""
        self.log_info(
            component="EntityPersistenceManager",
            event_type="entity_classified",
            message=f"Entity classified as {persistence_level}",
            metadata={
                "entity_id": entity_id,
                "entity_type": entity_type,
                "persistence_level": persistence_level,
                "reason": reason
            }
        )

    def log_influence_field_update(
        self,
        agent_id: int,
        updates: Dict[str, Any]
    ) -> None:
        """Log influence field updates."""
        self.log_info(
            component="InfluenceFieldManager",
            event_type="influence_field_updated",
            message=f"Influence field updated for agent {agent_id}",
            metadata={
                "agent_id": agent_id,
                "updates": updates
            }
        )

    def log_llm_call(
        self,
        llm_type: str,  # "cognition" or "renderer"
        purpose: str,
        agent_id: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Log LLM call."""
        self.log_info(
            component="LLM",
            event_type="llm_call",
            message=f"{llm_type} LLM called: {purpose}",
            metadata={
                "llm_type": llm_type,
                "purpose": purpose,
                "agent_id": agent_id,
                **(metadata or {})
            }
        )

    def log_info(
        self,
        component: str,
        event_type: str,
        message: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Log info-level message."""
        self._log(PFEELogLevel.INFO, component, event_type, message, metadata)

    def log_warning(
        self,
        component: str,
        event_type: str,
        message: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Log warning-level message."""
        self._log(PFEELogLevel.WARNING, component, event_type, message, metadata)

    def log_error(
        self,
        component: str,
        event_type: str,
        message: str,
        metadata: Optional[Dict[str, Any]] = None,
        exception: Optional[Exception] = None
    ) -> None:
        """Log error-level message."""
        error_metadata = metadata or {}
        if exception:
            error_metadata["exception_type"] = type(exception).__name__
            error_metadata["exception_message"] = str(exception)
        self._log(PFEELogLevel.ERROR, component, event_type, message, error_metadata)

    def _log(
        self,
        level: PFEELogLevel,
        component: str,
        event_type: str,
        message: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Internal logging method."""
        # Python logger
        log_message = f"[{component}] {message}"
        if level == PFEELogLevel.ERROR:
            self.python_logger.error(log_message, extra={"metadata": metadata})
        elif level == PFEELogLevel.WARNING:
            self.python_logger.warning(log_message, extra={"metadata": metadata})
        else:
            self.python_logger.info(log_message, extra={"metadata": metadata})

        # Database logger (if enabled)
        if self.enable_db_logging:
            log_entry = PFEELogModel(
                log_level=level.value,
                cycle_id=self.current_cycle_id,
                component=component,
                event_type=event_type,
                message=message,
                metadata=metadata or {}
            )
            self.session.add(log_entry)
            # Note: flush happens in orchestrator or caller

