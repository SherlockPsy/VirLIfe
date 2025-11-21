"""
PFEE Trigger Evaluator

Implements:
- PFEE_ARCHITECTURE.md §2.1
- PFEE_LOGIC.md §4
- PFEE_PLAN.md Phase P3

Evaluates when perception must be generated based on:
- user actions
- agent initiative
- interruptions
- information events
- environmental/atmospheric shifts
"""

from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

from sqlalchemy.ext.asyncio import AsyncSession


class TriggerReason(str, Enum):
    """Reason why perception is triggered."""
    USER_ACTION_SOCIAL = "user_action_social"
    USER_ACTION_CONTEXT_CHANGE = "user_action_context_change"
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
    info_event_id: Optional[int] = None
    shift_id: Optional[int] = None
    metadata: Dict[str, Any] = None

    @classmethod
    def none(cls) -> "TriggerDecision":
        """No trigger needed."""
        return cls(should_trigger=False, reason=TriggerReason.NONE)

    @classmethod
    def perception_required(
        cls,
        reason: TriggerReason,
        agent_id: Optional[int] = None,
        potential_id: Optional[int] = None,
        info_event_id: Optional[int] = None,
        shift_id: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> "TriggerDecision":
        """Perception is required."""
        return cls(
            should_trigger=True,
            reason=reason,
            agent_id=agent_id,
            potential_id=potential_id,
            info_event_id=info_event_id,
            shift_id=shift_id,
            metadata=metadata or {}
        )


class TriggerEvaluator:
    """
    Evaluates perception triggers.
    
    Implements PFEE_LOGIC.md §4 trigger evaluation logic.
    """

    def __init__(self, session: AsyncSession):
        self.session = session
        # Salience threshold for environmental shifts
        self.SALIENCE_THRESHOLD = 0.5

    async def evaluate_user_action_trigger(
        self,
        user_action: Optional[Dict[str, Any]],
        world_state: Dict[str, Any]
    ) -> TriggerDecision:
        """
        Evaluate if a user action should trigger perception.
        
        Implements PFEE_LOGIC.md §4.1
        """
        try:
            if user_action is None:
                return TriggerDecision.none()

            if not isinstance(user_action, dict):
                return TriggerDecision.none()

            # Check if trivial physical action
            if self._is_trivial_physical_action(user_action):
                return TriggerDecision.none()

            # Check if internal instruction without perceptual consequences
            if self._is_internal_instruction(user_action):
                return TriggerDecision.none()

            # Social/interpretive actions
            if self._action_targets_agent_or_entity(user_action, world_state):
                return TriggerDecision.perception_required(
                    reason=TriggerReason.USER_ACTION_SOCIAL,
                    metadata={"action": user_action}
                )

            # Context-changing actions
            if self._action_changes_context_meaningfully(user_action, world_state):
                return TriggerDecision.perception_required(
                    reason=TriggerReason.USER_ACTION_CONTEXT_CHANGE,
                    metadata={"action": user_action}
                )

            return TriggerDecision.none()
        except Exception as e:
            # Log error and return no trigger on exception
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error evaluating user action trigger: {str(e)}", exc_info=True)
            return TriggerDecision.none()

    async def evaluate_agent_initiative_triggers(
        self,
        world_state: Dict[str, Any]
    ) -> List[TriggerDecision]:
        """
        Evaluate if any agents have initiative to act.
        
        Implements PFEE_LOGIC.md §4.2
        """
        try:
            decisions = []
            persistent_agents = world_state.get("persistent_agents_present_with_user", [])

            if not isinstance(persistent_agents, list):
                return decisions

            for agent in persistent_agents:
                if not isinstance(agent, dict):
                    continue
                try:
                    if await self._agent_has_initiative_to_act(agent, world_state):
                        decisions.append(
                            TriggerDecision.perception_required(
                                reason=TriggerReason.AGENT_INITIATIVE,
                                agent_id=agent.get("id"),
                                metadata={"agent_name": agent.get("name")}
                            )
                        )
                except Exception as e:
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.error(f"Error checking agent initiative for agent {agent.get('id')}: {str(e)}", exc_info=True)
                    continue

            return decisions
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error evaluating agent initiative triggers: {str(e)}", exc_info=True)
            return []

    async def evaluate_interruption_triggers(
        self,
        world_state: Dict[str, Any],
        resolved_potentials: List[Dict[str, Any]]
    ) -> List[TriggerDecision]:
        """
        Evaluate interruption triggers from resolved potentials.
        
        Implements PFEE_LOGIC.md §4.3
        """
        decisions = []
        for rp in resolved_potentials:
            if rp.get("is_interruptive", False):
                decisions.append(
                    TriggerDecision.perception_required(
                        reason=TriggerReason.INTERRUPTION,
                        potential_id=rp.get("id"),
                        metadata={"potential_type": rp.get("potential_type")}
                    )
                )
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
            decisions.append(
                TriggerDecision.perception_required(
                    reason=TriggerReason.INFO_EVENT,
                    info_event_id=ev.get("id"),
                    metadata={"event_type": ev.get("type")}
                )
            )
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
        for shift in environmental_shifts:
            salience = shift.get("salience", 0.0)
            if salience >= self.SALIENCE_THRESHOLD:
                decisions.append(
                    TriggerDecision.perception_required(
                        reason=TriggerReason.ENVIRONMENT_SHIFT,
                        shift_id=shift.get("id"),
                        metadata={"shift_type": shift.get("type"), "salience": salience}
                    )
                )
        return decisions

    def _is_trivial_physical_action(self, action: Dict[str, Any]) -> bool:
        """Check if action is trivial (e.g., minor movement, routine gesture)."""
        action_type = action.get("type", "")
        trivial_types = {"minor_movement", "routine_gesture", "internal_thought"}
        return action_type in trivial_types

    def _is_internal_instruction(self, action: Dict[str, Any]) -> bool:
        """Check if action is an internal instruction without perceptual consequences."""
        action_type = action.get("type", "")
        internal_types = {"show_logs", "debug_command", "meta_command"}
        return action_type in internal_types

    def _action_targets_agent_or_entity(
        self,
        action: Dict[str, Any],
        world_state: Dict[str, Any]
    ) -> bool:
        """Check if action targets an agent or entity."""
        target = action.get("target")
        if not target:
            return False
        
        # Check if target is an agent or entity in world state
        agents = world_state.get("agents", [])
        for agent in agents:
            if agent.get("id") == target or agent.get("name") == target:
                return True
        return False

    def _action_changes_context_meaningfully(
        self,
        action: Dict[str, Any],
        world_state: Dict[str, Any]
    ) -> bool:
        """Check if action changes context meaningfully."""
        action_type = action.get("type", "")
        meaningful_types = {
            "speech", "significant_movement", "interaction",
            "location_change", "object_interaction"
        }
        return action_type in meaningful_types

    async def _agent_has_initiative_to_act(
        self,
        agent: Dict[str, Any],
        world_state: Dict[str, Any]
    ) -> bool:
        """
        Check if agent has initiative to act.
        
        Integrates with Autonomy Engine logic to determine if agent should initiate action.
        """
        # Check drive pressure
        drives = agent.get("drives", {})
        drive_pressure_sum = 0.0
        drive_count = 0
        
        for drive_name, drive_data in drives.items():
            if isinstance(drive_data, dict):
                level = drive_data.get("level", 0.0)
                sensitivity = drive_data.get("sensitivity", 1.0)
                # Weighted by sensitivity
                drive_pressure_sum += level * sensitivity
            else:
                level = drive_data
                drive_pressure_sum += level
            drive_count += 1
        
        # Average drive pressure above threshold
        if drive_count > 0:
            avg_drive_pressure = drive_pressure_sum / drive_count
            if avg_drive_pressure > 0.7:  # High unmet need
                return True

        # Check for active high-priority intentions
        intentions = agent.get("intentions", [])
        for intention in intentions:
            if isinstance(intention, dict):
                priority = intention.get("priority", 0.0)
                if priority > 0.7:
                    return True

        # Check mood arousal (high arousal can trigger initiative)
        mood = agent.get("mood", {})
        if isinstance(mood, dict):
            arousal = mood.get("arousal", 0.0)
            if arousal > 0.7:  # High arousal
                return True

        # Check energy (low energy reduces initiative)
        energy = agent.get("energy", 1.0)
        if energy < 0.3:  # Too tired to initiate
            return False

        # Check if agent has been inactive for a while (boredom/restlessness)
        # Check last cognition timestamp if available
        last_cognition = agent.get("last_cognition_timestamp")
        if last_cognition:
            from datetime import datetime, timezone
            if isinstance(last_cognition, str):
                # Parse ISO format
                try:
                    last_cognition = datetime.fromisoformat(last_cognition.replace('Z', '+00:00'))
                except:
                    pass
            
            if isinstance(last_cognition, datetime):
                current_time = world_state.get("current_time", datetime.now(timezone.utc))
                if isinstance(current_time, str):
                    try:
                        current_time = datetime.fromisoformat(current_time.replace('Z', '+00:00'))
                    except:
                        current_time = datetime.now(timezone.utc)
                
                time_since_cognition = (current_time - last_cognition).total_seconds()
                # If inactive for more than 2 hours, may have initiative
                if time_since_cognition > 7200:  # 2 hours
                    # Combine with low energy = restlessness
                    if energy < 0.5:
                        return True
        
        return False

