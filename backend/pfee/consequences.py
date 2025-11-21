"""
PFEE Consequence Integrator

Implements:
- PFEE_ARCHITECTURE.md §2.5
- PFEE_LOGIC.md §7
- PFEE_PLAN.md Phase P5

Integrates LLM outputs back into world state and psychology.
"""

from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from backend.persistence.repo import AgentRepo, WorldRepo
from backend.persistence.models import AgentModel, MemoryModel, ArcModel, IntentionModel
from backend.autonomy.engine import AutonomyEngine
from sqlalchemy import select


class ConsequenceIntegrator:
    """
    Integrates LLM outputs back into world state.
    
    Implements PFEE_LOGIC.md §7 consequence integration logic.
    """
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.agent_repo = AgentRepo(session)
        self.world_repo = WorldRepo(session)
        self.autonomy_engine = AutonomyEngine()
    
    async def apply_perception_outcome(
        self,
        cognition_output: Optional[Dict[str, Any]],
        renderer_output: Optional[Dict[str, Any]],
        world_state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Apply the consequences of LLM outputs to world state.
        
        Implements PFEE_LOGIC.md §7
        
        Steps:
        1. Apply agent utterances and actions
        2. Apply physical consequences from renderer
        3. Update psychology deterministically
        4. Create episodic memories when salience >= threshold
        5. Update biographical memory where applicable
        6. Update potentials and influence fields
        """
        updated_world_state = world_state.copy()
        
        # 1. Apply agent utterances and actions
        if cognition_output:
            await self._apply_agent_actions(cognition_output, updated_world_state)
            await self._apply_stance_and_intention_shifts(cognition_output, updated_world_state)
        
        # 2. Apply physical consequences from renderer (structured, not raw text)
        if renderer_output:
            await self._apply_physical_changes(renderer_output, updated_world_state)
        
        # 3. Update psychology deterministically
        await self._update_psychology_from_events(updated_world_state)
        
        # 4. Create episodic memories when salience >= threshold
        await self._store_episodic_memories(updated_world_state, cognition_output)
        
        # 5. Update biographical memory where applicable
        await self._update_biographical_memory(updated_world_state, cognition_output)
        
        # 6. Update potentials and influence fields
        await self._update_potentials_and_influence(updated_world_state)
        
        return updated_world_state
    
    async def _apply_agent_actions(
        self,
        cognition_output: Dict[str, Any],
        world_state: Dict[str, Any]
    ) -> None:
        """Apply agent utterances and actions to world state."""
        agent_id = cognition_output.get("agent_id")
        if not agent_id:
            return
        
        utterance = cognition_output.get("utterance")
        action = cognition_output.get("action")
        
        # Store utterance/action in world state for renderer
        if utterance:
            world_state.setdefault("recent_utterances", []).append({
                "agent_id": agent_id,
                "utterance": utterance,
                "timestamp": world_state.get("current_time")
            })
        
        if action:
            world_state.setdefault("recent_actions", []).append({
                "agent_id": agent_id,
                "action": action,
                "timestamp": world_state.get("current_time")
            })
    
    async def _apply_stance_and_intention_shifts(
        self,
        cognition_output: Dict[str, Any],
        world_state: Dict[str, Any]
    ) -> None:
        """Apply stance shifts and intention updates deterministically."""
        agent_id = cognition_output.get("agent_id")
        if not agent_id:
            return
        
        agent = await self.agent_repo.get_agent_by_id(int(agent_id))
        if not agent:
            return
        
        # Apply stance shifts via deterministic mapping
        stance_shifts = cognition_output.get("stance_shifts", [])
        for shift in stance_shifts:
            target = shift.get("target")
            description = shift.get("description", "")
            
            # Deterministic mapping: description → numeric deltas
            # Example: "give benefit of the doubt" → small trust increase, small tension decrease
            if "benefit of the doubt" in description.lower():
                # Update relationship deterministically
                relationships = await self.agent_repo.get_relationships(int(agent_id))
                for rel in relationships:
                    if (rel.target_agent_id and str(rel.target_agent_id) == target) or \
                       (rel.target_user_id and f"user:{rel.target_user_id}" == target):
                        rel.trust = min(1.0, rel.trust + 0.1)
                        rel.tension = max(0.0, rel.tension - 0.05)
        
        # Apply intention updates
        intention_updates = cognition_output.get("intention_updates", [])
        for update in intention_updates:
            operation = update.get("operation")
            intent_type = update.get("type")
            description = update.get("description", "")
            
            if operation == "create":
                # Create new intention
                new_intention = IntentionModel(
                    agent_id=int(agent_id),
                    description=description,
                    type=intent_type,
                    priority=0.7,  # Default priority
                    horizon=update.get("horizon", "short")
                )
                self.session.add(new_intention)
            elif operation == "boost":
                # Increase priority of existing intention
                stmt = select(IntentionModel).where(
                    IntentionModel.agent_id == int(agent_id),
                    IntentionModel.type == intent_type
                )
                result = await self.session.execute(stmt)
                intention = result.scalars().first()
                if intention:
                    intention.priority = min(1.0, intention.priority + 0.2)
            elif operation == "lower":
                # Decrease priority
                stmt = select(IntentionModel).where(
                    IntentionModel.agent_id == int(agent_id),
                    IntentionModel.type == intent_type
                )
                result = await self.session.execute(stmt)
                intention = result.scalars().first()
                if intention:
                    intention.priority = max(0.0, intention.priority - 0.2)
            elif operation == "drop":
                # Remove intention
                stmt = select(IntentionModel).where(
                    IntentionModel.agent_id == int(agent_id),
                    IntentionModel.type == intent_type
                )
                result = await self.session.execute(stmt)
                intention = result.scalars().first()
                if intention:
                    await self.session.delete(intention)
        
        await self.session.flush()
    
    async def _apply_physical_changes(
        self,
        renderer_output: Dict[str, Any],
        world_state: Dict[str, Any]
    ) -> None:
        """Apply physical changes from renderer output."""
        physical_changes = renderer_output.get("physical_changes", {})
        # Physical changes are applied to world state
        # For now, we store them in world_state for future reference
        world_state["physical_changes"] = physical_changes
    
    async def _update_psychology_from_events(
        self,
        world_state: Dict[str, Any]
    ) -> None:
        """Update psychology deterministically from events."""
        # This is handled by Autonomy Engine
        # PFEE just ensures it's called after perception
        agents_present = world_state.get("persistent_agents_present_with_user", [])
        for agent_data in agents_present:
            agent_id = agent_data.get("id")
            if agent_id:
                # Autonomy engine will update drives, mood, relationships, etc.
                # This is called separately by the gateway
                pass
    
    async def _store_episodic_memories(
        self,
        world_state: Dict[str, Any],
        cognition_output: Optional[Dict[str, Any]]
    ) -> None:
        """Create episodic memories when salience >= threshold."""
        SALIENCE_THRESHOLD = 0.5
        
        if not cognition_output:
            return
        
        agent_id = cognition_output.get("agent_id")
        if not agent_id:
            return
        
        # Check if event is salient enough
        event_salience = world_state.get("salience", 0.0)
        if event_salience < SALIENCE_THRESHOLD:
            return
        
        # Create episodic memory
        description = f"Agent {agent_id} acted: {cognition_output.get('utterance', '')} {cognition_output.get('action', '')}"
        memory = MemoryModel(
            agent_id=int(agent_id),
            type="episodic",
            description=description,
            timestamp=world_state.get("current_time"),
            salience=event_salience,
            semantic_tags=["perception_cycle", "agent_action"]
        )
        self.session.add(memory)
        await self.session.flush()
    
    async def _update_biographical_memory(
        self,
        world_state: Dict[str, Any],
        cognition_output: Optional[Dict[str, Any]]
    ) -> None:
        """Update biographical memory when stable patterns are reinforced."""
        # Biographical memory updates are handled by Autonomy Engine
        # PFEE just ensures they're considered
        pass
    
    async def _update_potentials_and_influence(
        self,
        world_state: Dict[str, Any]
    ) -> None:
        """Update potentials and influence fields."""
        # This is handled by PotentialResolver and InfluenceFieldManager
        # Called separately by orchestrator
        pass

