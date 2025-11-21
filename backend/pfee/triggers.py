"""
PFEE Trigger Evaluator

Implements:
- PFEE_ARCHITECTURE.md §2.1
- PFEE_LOGIC.md §4
- PFEE_PLAN.md Phase P3

Evaluates when perception events should occur.
"""

from dataclasses import dataclass
from typing import Dict, Any, List, Optional
from enum import Enum
from sqlalchemy.ext.asyncio import AsyncSession

from backend.pfee.potentials import ResolvedPotential


class TriggerReason(str, Enum):
    """Reasons for perception triggers."""
    USER_ACTION = "user_action"
    AGENT_INITIATIVE = "agent_initiative"
    INTERRUPTION = "interruption"
    INFO_EVENT = "info_event"
    ENVIRONMENT_SHIFT = "environment_shift"
    NONE = "none"


@dataclass
class TriggerDecision:
    """Decision about whether to trigger perception."""
    should_trigger: bool
    reason: TriggerReason
    agent_id: Optional[int] = None
    potential_id: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None
    
    @classmethod
    def none(cls) -> "TriggerDecision":
        """No trigger."""
        return cls(
            should_trigger=False,
            reason=TriggerReason.NONE
        )
    
    @classmethod
    def perception_required(
        cls,
        reason: TriggerReason,
        agent_id: Optional[int] = None,
        potential_id: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> "TriggerDecision":
        """Trigger perception."""
        return cls(
            should_trigger=True,
            reason=reason,
            agent_id=agent_id,
            potential_id=potential_id,
            metadata=metadata or {}
        )


class TriggerEvaluator:
    """
    Evaluates perception triggers.
    
    Implements PFEE_LOGIC.md §4 trigger evaluation logic.
    """
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def evaluate_user_action_trigger(
        self,
        user_action: Optional[Dict[str, Any]],
        world_state: Dict[str, Any]
    ) -> TriggerDecision:
        """
        Evaluate user action trigger.
        
        Implements PFEE_LOGIC.md §4.1
        
        Rules:
        - None action → no trigger
        - Trivial physical actions → no trigger
        - Internal instructions without perceptual consequences → no trigger
        - Social/interpretive actions → trigger
        - Context-changing actions → trigger
        """
        if user_action is None:
            return TriggerDecision.none()
        
        # Trivial physical actions
        if self._is_trivial_physical_action(user_action):
            return TriggerDecision.none()
        
        # Internal instructions without perceptual consequences
        if self._is_internal_instruction_without_perceptual_consequences(user_action):
            return TriggerDecision.none()
        
        # Social/interpretive actions
        if self._action_targets_agent_or_entity(user_action, world_state):
            return TriggerDecision.perception_required(
                reason=TriggerReason.USER_ACTION,
                metadata={"action_type": user_action.get("type"), "text": user_action.get("text")}
            )
        
        # Context-changing actions
        if self._action_changes_context_meaningfully(user_action, world_state):
            return TriggerDecision.perception_required(
                reason=TriggerReason.USER_ACTION,
                metadata={"action_type": user_action.get("type")}
            )
        
        return TriggerDecision.none()
    
    async def evaluate_agent_initiative_triggers(
        self,
        world_state: Dict[str, Any]
    ) -> List[TriggerDecision]:
        """
        Evaluate agent initiative triggers.
        
        Implements PFEE_LOGIC.md §4.2
        """
        decisions = []
        agents_present = world_state.get("persistent_agents_present_with_user", [])
        
        for agent_data in agents_present:
            agent_id = agent_data.get("id")
            if not agent_id:
                continue
            
            if await self._agent_has_initiative_to_act(agent_data, world_state):
                decisions.append(TriggerDecision.perception_required(
                    reason=TriggerReason.AGENT_INITIATIVE,
                    agent_id=agent_id
                ))
        
        return decisions
    
    async def evaluate_interruption_triggers(
        self,
        world_state: Dict[str, Any],
        resolved_potentials: List[ResolvedPotential]
    ) -> List[TriggerDecision]:
        """
        Evaluate interruption triggers.
        
        Implements PFEE_LOGIC.md §4.3
        """
        decisions = []
        
        for rp in resolved_potentials:
            if self._is_interruptive(rp):
                decisions.append(TriggerDecision.perception_required(
                    reason=TriggerReason.INTERRUPTION,
                    potential_id=rp.id,
                    metadata={"potential_type": rp.potential_type.value}
                ))
        
        return decisions
    
    async def evaluate_info_event_triggers(
        self,
        world_state: Dict[str, Any],
        info_events: List[Dict[str, Any]]
    ) -> List[TriggerDecision]:
        """
        Evaluate information event triggers.
        
        Implements PFEE_LOGIC.md §4.4
        """
        decisions = []
        
        for ev in info_events:
            decisions.append(TriggerDecision.perception_required(
                reason=TriggerReason.INFO_EVENT,
                metadata={"info_event_id": ev.get("id"), "type": ev.get("type")}
            ))
        
        return decisions
    
    async def evaluate_environment_triggers(
        self,
        world_state: Dict[str, Any],
        environmental_shifts: List[Dict[str, Any]]
    ) -> List[TriggerDecision]:
        """
        Evaluate environmental/atmospheric shift triggers.
        
        Implements PFEE_LOGIC.md §4.5
        """
        decisions = []
        SALIENCE_THRESHOLD = 0.3  # Minimum salience for environmental trigger
        
        for shift in environmental_shifts:
            salience = shift.get("salience", 0.0)
            if salience >= SALIENCE_THRESHOLD:
                decisions.append(TriggerDecision.perception_required(
                    reason=TriggerReason.ENVIRONMENT_SHIFT,
                    metadata={"shift_id": shift.get("id"), "type": shift.get("type")}
                ))
        
        return decisions
    
    def _is_trivial_physical_action(self, user_action: Dict[str, Any]) -> bool:
        """Check if action is trivial physical action."""
        action_type = user_action.get("type", "")
        trivial_types = {"blink", "breathe", "shift_weight", "minor_posture_change"}
        return action_type in trivial_types
    
    def _is_internal_instruction_without_perceptual_consequences(
        self,
        user_action: Dict[str, Any]
    ) -> bool:
        """Check if action is internal instruction without perceptual consequences."""
        action_type = user_action.get("type", "")
        internal_types = {"show_logs", "debug_command", "system_query"}
        return action_type in internal_types
    
    def _action_targets_agent_or_entity(
        self,
        user_action: Dict[str, Any],
        world_state: Dict[str, Any]
    ) -> bool:
        """Check if action targets an agent or entity."""
        if user_action.get("target_id"):
            return True
        
        action_type = user_action.get("type", "")
        social_types = {"speak", "touch", "look_at", "approach", "interact"}
        return action_type in social_types
    
    def _action_changes_context_meaningfully(
        self,
        user_action: Dict[str, Any],
        world_state: Dict[str, Any]
    ) -> bool:
        """Check if action changes context meaningfully."""
        action_type = user_action.get("type", "")
        context_changing_types = {"move", "travel", "change_location", "open_door", "close_door"}
        return action_type in context_changing_types
    
    async def _agent_has_initiative_to_act(
        self,
        agent_data: Dict[str, Any],
        world_state: Dict[str, Any]
    ) -> bool:
        """
        Check if agent has initiative to act.
        
        Deterministic check based on:
        - drive pressure
        - mood
        - energy
        - relationship dynamics
        - intentions
        """
        # High drive pressure increases initiative
        drives = agent_data.get("drives", {})
        if isinstance(drives, dict):
            for drive_data in drives.values():
                if isinstance(drive_data, dict):
                    level = drive_data.get("level", 0.0)
                    if level > 0.7:  # High unmet need
                        return True
        
        # High energy increases initiative
        energy = agent_data.get("energy", 1.0)
        if energy > 0.7:
            # Check if agent has active intentions
            intentions = agent_data.get("intentions", {})
            if intentions:
                return True
        
        # Active arcs increase initiative
        arcs = agent_data.get("arcs", {})
        if isinstance(arcs, dict):
            for arc_data in arcs.values():
                if isinstance(arc_data, dict):
                    intensity = arc_data.get("intensity", 0.0)
                    if intensity > 0.6:
                        return True
        
        return False
    
    def _is_interruptive(self, resolved_potential: ResolvedPotential) -> bool:
        """Check if resolved potential is interruptive."""
        interruptive_types = {
            "dog_encounter",
            "fan_approach",
            "delivery",
            "travel_interruption",
            "environmental_event"
        }
        return resolved_potential.potential_type.value in interruptive_types

