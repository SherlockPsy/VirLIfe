"""
PFEE Logger

Implements:
- PFEE_ARCHITECTURE.md §2.9
- PFEE_PLAN.md Phase P8

Internal logging and traceability for PFEE.
"""

from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, Column, Integer, String, JSON, DateTime, Text
from sqlalchemy.sql import func
from datetime import datetime
import json

from backend.persistence.models import Base


class PFEELogModel(Base):
    """Database model for PFEE logs."""
    __tablename__ = "pfee_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    cycle_id = Column(String, nullable=True)  # UUID for perception cycle
    log_type = Column(String, nullable=False)  # "trigger", "potential", "entity", "llm_call", "error", "cycle"
    component = Column(String, nullable=False)  # Component name
    message = Column(Text, nullable=True)
    metadata = Column(JSON, default={}, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class PFEELogger:
    """
    Internal logger for PFEE observability.
    
    Logs are for system owner only, not visible to in-world user.
    """
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.current_cycle_id: Optional[str] = None
    
    def start_perception_cycle(self, cycle_id: str) -> None:
        """Start a new perception cycle."""
        self.current_cycle_id = cycle_id
    
    def log_trigger_firing(
        self,
        trigger_reason: str,
        agent_id: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Log a trigger firing."""
        log_entry = PFEELogModel(
            cycle_id=self.current_cycle_id,
            log_type="trigger",
            component="TriggerEvaluator",
            message=f"Trigger fired: {trigger_reason}",
            log_metadata={
                "trigger_reason": trigger_reason,
                "agent_id": agent_id,
                **(metadata or {})
            }
        )
        self.session.add(log_entry)
    
    def log_potential_resolution(
        self,
        potential_id: int,
        potential_type: str,
        resolved_entity: Dict[str, Any]
    ) -> None:
        """Log a potential resolution."""
        log_entry = PFEELogModel(
            cycle_id=self.current_cycle_id,
            log_type="potential",
            component="PotentialResolver",
            message=f"Potential resolved: {potential_type}",
            log_metadata={
                "potential_id": potential_id,
                "potential_type": potential_type,
                "resolved_entity": resolved_entity
            }
        )
        self.session.add(log_entry)
    
    def log_entity_classification(
        self,
        entity_id: int,
        entity_type: str,
        persistence_level: str,
        reason: str
    ) -> None:
        """Log entity classification."""
        log_entry = PFEELogModel(
            cycle_id=self.current_cycle_id,
            log_type="entity",
            component="EntityPersistenceManager",
            message=f"Entity classified: {persistence_level}",
            log_metadata={
                "entity_id": entity_id,
                "entity_type": entity_type,
                "persistence_level": persistence_level,
                "reason": reason
            }
        )
        self.session.add(log_entry)
    
    def log_llm_call(
        self,
        llm_type: str,
        purpose: str,
        agent_id: Optional[int] = None
    ) -> None:
        """Log an LLM call."""
        log_entry = PFEELogModel(
            cycle_id=self.current_cycle_id,
            log_type="llm_call",
            component="PerceptionOrchestrator",
            message=f"LLM call: {llm_type} for {purpose}",
            log_metadata={
                "llm_type": llm_type,
                "purpose": purpose,
                "agent_id": agent_id
            }
        )
        self.session.add(log_entry)
    
    def log_error(
        self,
        component: str,
        error_type: str,
        message: str,
        exception: Optional[Exception] = None
    ) -> None:
        """Log an error."""
        error_metadata = {
            "error_type": error_type,
            "message": message
        }
        if exception:
            error_metadata["exception_type"] = type(exception).__name__
            error_metadata["exception_message"] = str(exception)
        
        log_entry = PFEELogModel(
            cycle_id=self.current_cycle_id,
            log_type="error",
            component=component,
            message=f"Error: {error_type}",
            log_metadata=error_metadata
        )
        self.session.add(log_entry)
    
    def log_perception_cycle(
        self,
        triggers: List[Dict[str, Any]],
        resolved_potentials: List[Dict[str, Any]],
        entities: List[Dict[str, Any]],
        cognition_output: Optional[Dict[str, Any]],
        renderer_output: Optional[Dict[str, Any]]
    ) -> None:
        """Log complete perception cycle."""
        log_entry = PFEELogModel(
            cycle_id=self.current_cycle_id,
            log_type="cycle",
            component="PerceptionOrchestrator",
            message="Perception cycle completed",
            log_metadata={
                "triggers": triggers,
                "resolved_potentials": resolved_potentials,
                "entities_instantiated": len(entities),
                "cognition_called": cognition_output is not None,
                "renderer_called": renderer_output is not None
            }
        )
        self.session.add(log_entry)
        # Flush to ensure log is persisted
        # Note: actual commit happens in orchestrator

