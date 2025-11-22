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
from backend.persistence.models import (
    AgentModel, MemoryModel, ArcModel, IntentionModel,
    RelationshipModel, LocationModel
)
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
    
    async def integrate_cognition_consequences(
        self,
        world_state: Dict[str, Any],
        validation_result: Any,
        cognition_output: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        C.7: Apply validated and corrected cognition output to DB.
        
        Implements Section C.7 of the blueprint:
        - Updates intentions (non-George only)
        - Updates relationships (non-George pairs only)
        - Updates arcs (non-George only)
        - Creates memories (non-George only)
        - Updates drives and mood (non-George only)
        - Updates influence fields
        - Updates agent positions (George only if user-triggered)
        - Updates world time (if small jump)
        
        Args:
            world_state: WorldState dict from world_state_builder
            validation_result: ValidationResult with corrected_output
            cognition_output: Optional original cognition output
        """
        # Get corrected output from validation result
        if hasattr(validation_result, 'corrected_output'):
            corrected_output = validation_result.corrected_output
        elif validation_result and isinstance(validation_result, dict):
            corrected_output = validation_result.get("corrected_output")
        else:
            corrected_output = cognition_output or {}
        
        if not corrected_output:
            return
        
        # Get George agent ID for protection
        george_agent_id = world_state.get("george_agent_id")
        
        # C.7.1: Intentions Updates (non-George only)
        await self._update_intentions(world_state, corrected_output, george_agent_id)
        
        # C.7.2: Relationships Updates (non-George pairs only)
        await self._update_relationships(world_state, corrected_output, george_agent_id)
        
        # C.7.3: Arcs Updates (non-George only)
        await self._update_arcs(world_state, corrected_output, george_agent_id)
        
        # C.7.4: Memories Creation (non-George only)
        await self._create_memories(world_state, corrected_output, george_agent_id)
        
        # C.7.5: Drives and Mood Updates (non-George only)
        await self._update_drives_and_mood(world_state, corrected_output, george_agent_id)
        
        # C.7.6: Influence Fields Updates
        await self._update_influence_fields(world_state, corrected_output, george_agent_id)
        
        # C.7.7: Agent Positions and World State Changes
        await self._update_agent_positions(world_state, corrected_output, george_agent_id)
        
        await self.session.flush()
    
    async def apply_perception_outcome(
        self,
        cognition_output: Optional[Dict[str, Any]],
        renderer_output: Optional[Dict[str, Any]],
        world_state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Legacy wrapper for backward compatibility.
        Delegates to integrate_cognition_consequences.
        """
        from backend.pfee.validation import ValidationResult
        
        # Create a validation result (assume already validated)
        validation_result = ValidationResult.valid()
        if cognition_output:
            validation_result.corrected_output = cognition_output
        
        await self.integrate_cognition_consequences(world_state, validation_result, cognition_output)
        
        return world_state
    
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
    
    async def _update_intentions(
        self,
        world_state: Dict[str, Any],
        cognition_output: Dict[str, Any],
        george_agent_id: Optional[int]
    ) -> None:
        """C.7.1: Update intentions for non-George agents only."""
        intention_updates = cognition_output.get("intention_updates", [])
        for update in intention_updates:
            if not isinstance(update, dict):
                continue
            
            agent_id = update.get("agent_id")
            if not agent_id or agent_id == george_agent_id:
                continue  # Skip George
            
            operation = update.get("operation", "create")
            description = update.get("description", "")
            intent_type = update.get("type", "action")
            
            if operation == "create":
                new_intention = IntentionModel(
                    agent_id=int(agent_id),
                    description=description,
                    type=intent_type,
                    priority=update.get("priority", 0.7),
                    horizon=update.get("horizon", "short"),
                    stability=update.get("stability", 0.5)
                )
                self.session.add(new_intention)
            elif operation == "update":
                stmt = select(IntentionModel).where(
                    IntentionModel.agent_id == int(agent_id),
                    IntentionModel.type == intent_type
                )
                result = await self.session.execute(stmt)
                intention = result.scalars().first()
                if intention:
                    if "priority" in update:
                        intention.priority = max(0.0, min(1.0, update["priority"]))
                    if "description" in update:
                        intention.description = update["description"]
    
    async def _update_relationships(
        self,
        world_state: Dict[str, Any],
        cognition_output: Dict[str, Any],
        george_agent_id: Optional[int]
    ) -> None:
        """C.7.2: Update relationships for non-George agent pairs only."""
        relationship_updates = cognition_output.get("relationship_updates", [])
        for update in relationship_updates:
            if not isinstance(update, dict):
                continue
            
            source_agent_id = update.get("source_agent_id")
            target_agent_id = update.get("target_agent_id")
            
            # Skip if involves George as source (he doesn't have internal relationships)
            if source_agent_id == george_agent_id:
                continue
            
            # Make small, bounded adjustments (±0.05)
            warmth_delta = update.get("warmth_delta", 0.0)
            trust_delta = update.get("trust_delta", 0.0)
            tension_delta = update.get("tension_delta", 0.0)
            
            # Clamp deltas to ±0.05
            warmth_delta = max(-0.05, min(0.05, warmth_delta))
            trust_delta = max(-0.05, min(0.05, trust_delta))
            tension_delta = max(-0.05, min(0.05, tension_delta))
            
            # Find relationship
            stmt = select(RelationshipModel).where(
                RelationshipModel.source_agent_id == int(source_agent_id)
            )
            if target_agent_id:
                stmt = stmt.where(RelationshipModel.target_agent_id == int(target_agent_id))
            
            result = await self.session.execute(stmt)
            relationship = result.scalars().first()
            if relationship:
                relationship.warmth = max(0.0, min(1.0, relationship.warmth + warmth_delta))
                relationship.trust = max(0.0, min(1.0, relationship.trust + trust_delta))
                relationship.tension = max(0.0, min(1.0, relationship.tension + tension_delta))
    
    async def _update_arcs(
        self,
        world_state: Dict[str, Any],
        cognition_output: Dict[str, Any],
        george_agent_id: Optional[int]
    ) -> None:
        """C.7.3: Update arcs for non-George agents only."""
        arc_updates = cognition_output.get("arc_updates", [])
        for update in arc_updates:
            if not isinstance(update, dict):
                continue
            
            agent_id = update.get("agent_id")
            if not agent_id or agent_id == george_agent_id:
                continue  # Skip George - never create/modify arcs for George
            
            arc_name = update.get("arc_name")
            progress_delta = update.get("progress_delta", 0.0)
            
            # Find arc
            stmt = select(ArcModel).where(
                ArcModel.agent_id == int(agent_id),
                ArcModel.type == arc_name
            )
            result = await self.session.execute(stmt)
            arc = result.scalars().first()
            
            if arc:
                # Update progress in topic_vector if it's a dict
                topic_vector = arc.topic_vector if isinstance(arc.topic_vector, dict) else {}
                current_progress = topic_vector.get("progress", 0.0)
                new_progress = max(0.0, min(1.0, current_progress + progress_delta))
                
                # Update topic_vector with new progress
                if isinstance(arc.topic_vector, dict):
                    arc.topic_vector["progress"] = new_progress
                    if new_progress >= 0.95:
                        arc.topic_vector["status"] = "completed"
    
    async def _create_memories(
        self,
        world_state: Dict[str, Any],
        cognition_output: Dict[str, Any],
        george_agent_id: Optional[int]
    ) -> None:
        """C.7.4: Create memories for non-George agents only."""
        memory_updates = cognition_output.get("memory_updates", [])
        for mem_update in memory_updates:
            if not isinstance(mem_update, dict):
                continue
            
            agent_id = mem_update.get("agent_id")
            if not agent_id or agent_id == george_agent_id:
                continue  # Skip George - DO NOT create memories for George
            
            description = mem_update.get("description", "")
            mem_type = mem_update.get("type", "episodic")
            salience = mem_update.get("salience", 0.5)
            tags = mem_update.get("tags", [])
            
            if salience >= 0.5:  # Only create if salient
                memory = MemoryModel(
                    agent_id=int(agent_id),
                    type=mem_type,
                    description=description,
                    timestamp=world_state.get("current_time"),
                    salience=salience,
                    semantic_tags=tags
                )
                self.session.add(memory)
        
        # Legacy: also check from old format
        if not memory_updates:
            agent_id = cognition_output.get("agent_id")
            if agent_id and agent_id != george_agent_id:
                # Old format: check salience from world_state
                event_salience = world_state.get("salience", 0.0)
                if event_salience >= 0.5:
                    description = f"{cognition_output.get('utterance', '')} {cognition_output.get('action', '')}"
                    if description.strip():
                        memory = MemoryModel(
                            agent_id=int(agent_id),
                            type="episodic",
                            description=description,
                            timestamp=world_state.get("current_time"),
                            salience=event_salience,
                            semantic_tags=["perception_cycle", "agent_action"]
                        )
                        self.session.add(memory)
    
    async def _update_drives_and_mood(
        self,
        world_state: Dict[str, Any],
        cognition_output: Dict[str, Any],
        george_agent_id: Optional[int]
    ) -> None:
        """C.7.5: Update drives and mood for non-George agents only."""
        agent_id = cognition_output.get("agent_id")
        if not agent_id or agent_id == george_agent_id:
            return  # Skip George - never update his drives/mood
        
        agent = await self.agent_repo.get_agent_by_id(int(agent_id))
        if not agent or agent.is_real_user:
            return  # Extra check for George
        
        # Small adjustments per cycle (±0.05)
        drive_updates = cognition_output.get("drive_updates", {})
        for drive_name, delta in drive_updates.items():
            if not isinstance(agent.drives, dict):
                agent.drives = {}
            
            if drive_name in agent.drives:
                drive_data = agent.drives[drive_name]
                if isinstance(drive_data, dict):
                    current = drive_data.get("current", drive_data.get("baseline", 0.5))
                    delta_clamped = max(-0.05, min(0.05, delta))
                    drive_data["current"] = max(0.0, min(1.0, current + delta_clamped))
                else:
                    # If it's a float, convert to dict
                    current = float(drive_data) if isinstance(drive_data, (int, float)) else 0.5
                    delta_clamped = max(-0.05, min(0.05, delta))
                    agent.drives[drive_name] = {
                        "baseline": current,
                        "current": max(0.0, min(1.0, current + delta_clamped))
                    }
        
        # Mood updates (small adjustments)
        mood_updates = cognition_output.get("mood_updates", {})
        if mood_updates and isinstance(agent.mood, dict):
            valence_delta = mood_updates.get("valence_delta", 0.0)
            arousal_delta = mood_updates.get("arousal_delta", 0.0)
            
            valence_delta = max(-0.05, min(0.05, valence_delta))
            arousal_delta = max(-0.05, min(0.05, arousal_delta))
            
            current_valence = agent.mood.get("baseline_valence", agent.mood.get("valence", 0.0))
            current_arousal = agent.mood.get("baseline_arousal", agent.mood.get("arousal", 0.5))
            
            agent.mood["baseline_valence"] = max(-1.0, min(1.0, current_valence + valence_delta))
            agent.mood["baseline_arousal"] = max(0.0, min(1.0, current_arousal + arousal_delta))
    
    async def _update_influence_fields(
        self,
        world_state: Dict[str, Any],
        cognition_output: Dict[str, Any],
        george_agent_id: Optional[int]
    ) -> None:
        """C.7.6: Update influence fields."""
        from backend.persistence.models import InfluenceFieldModel
        
        agent_id = cognition_output.get("agent_id")
        if not agent_id or agent_id == george_agent_id:
            return  # Skip George
        
        # Check if topic was addressed
        utterance = cognition_output.get("utterance", "").lower()
        
        # Load influence field
        stmt = select(InfluenceFieldModel).where(InfluenceFieldModel.agent_id == int(agent_id))
        result = await self.session.execute(stmt)
        influence_field = result.scalars().first()
        
        if influence_field:
            unresolved_topics = influence_field.unresolved_tension_topics
            if isinstance(unresolved_topics, dict):
                # Check if any topics were addressed in utterance
                for topic, topic_data in unresolved_topics.items():
                    if isinstance(topic_data, dict):
                        tags = topic_data.get("tags", [])
                        # Simple check: if topic tags appear in utterance
                        topic_mentioned = any(tag.lower() in utterance for tag in tags)
                        
                        if topic_mentioned:
                            # Decrease pressure (topic was addressed)
                            current_pressure = topic_data.get("pressure", 0.5)
                            topic_data["pressure"] = max(0.0, current_pressure - 0.1)
                            topic_data["last_updated"] = world_state.get("current_time")
                
                influence_field.unresolved_tension_topics = unresolved_topics
                influence_field.last_updated_timestamp = world_state.get("current_time")
    
    async def _update_agent_positions(
        self,
        world_state: Dict[str, Any],
        cognition_output: Dict[str, Any],
        george_agent_id: Optional[int]
    ) -> None:
        """C.7.7: Update agent positions (George only if user-triggered)."""
        action = cognition_output.get("action", "").lower()
        agent_id = cognition_output.get("agent_id")
        
        # Check for movement keywords
        location_keywords = ["moves to", "goes to", "walks to", "enters"]
        moved = False
        new_location_name = None
        
        for keyword in location_keywords:
            if keyword in action:
                # Extract location name (simplified)
                parts = action.split(keyword)
                if len(parts) > 1:
                    new_location_name = parts[1].strip().split()[0]
                    moved = True
                    break
        
        if moved and agent_id:
            # Only allow George movement if user-triggered (handled by gateway)
            # For now, skip automatic movement of George
            if agent_id == george_agent_id:
                return  # Don't move George automatically
            
            # Find location
            world_id = world_state.get("world_id")
            stmt = select(LocationModel).where(
                LocationModel.world_id == world_id,
                LocationModel.name.ilike(f"%{new_location_name}%")
            )
            result = await self.session.execute(stmt)
            location = result.scalars().first()
            
            if location:
                agent = await self.agent_repo.get_agent_by_id(int(agent_id))
                if agent and not agent.is_real_user:  # Extra George check
                    current_location_id = agent.location_id
                    # Verify adjacency
                    if current_location_id in location.adjacency or current_location_id == location.id:
                        agent.location_id = location.id
    
    async def _store_episodic_memories(
        self,
        world_state: Dict[str, Any],
        cognition_output: Optional[Dict[str, Any]]
    ) -> None:
        """Legacy method for backward compatibility."""
        george_agent_id = world_state.get("george_agent_id")
        await self._create_memories(world_state, cognition_output or {}, george_agent_id)
    
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

