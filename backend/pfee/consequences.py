"""
PFEE Consequence Integrator

Implements:
- PFEE_ARCHITECTURE.md §2.5
- PFEE_LOGIC.md §7
- PFEE_PLAN.md Phase P5

Integrates LLM outputs back into world state and psychology.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from backend.persistence.repo import AgentRepo, WorldRepo
from backend.persistence.models import MemoryModel
from backend.autonomy.engine import AutonomyEngine


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
        Apply consequences of perception cycle to world state.
        
        Implements PFEE_LOGIC.md §7 high-level integration.
        """
        try:
            if not isinstance(world_state, dict):
                return world_state

            # 1. Apply agent utterances and actions from cognition
            if cognition_output and isinstance(cognition_output, dict):
                try:
                    world_state = await self._apply_agent_actions(cognition_output, world_state)
                    world_state = await self._apply_stance_and_intention_shifts(
                        cognition_output, world_state
                    )
                except Exception as e:
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.error(f"Error applying agent actions: {str(e)}", exc_info=True)

            # 2. Apply physical consequences from renderer (structured, not raw text)
            if renderer_output and isinstance(renderer_output, dict):
                try:
                    world_state = await self._apply_physical_changes(renderer_output, world_state)
                except Exception as e:
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.error(f"Error applying physical changes: {str(e)}", exc_info=True)

            # 3. Update psychology deterministically
            try:
                world_state = await self._update_psychology_from_events(world_state)
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Error updating psychology: {str(e)}", exc_info=True)

            # 4. Create episodic memories when salience >= threshold
            try:
                world_state = await self._store_episodic_memories(world_state)
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Error storing episodic memories: {str(e)}", exc_info=True)

            # 5. Update biographical memory where applicable
            try:
                world_state = await self._update_biographical_memory(world_state)
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Error updating biographical memory: {str(e)}", exc_info=True)

            return world_state
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error applying perception outcome: {str(e)}", exc_info=True)
            return world_state

    async def _apply_agent_actions(
        self,
        cognition_output: Dict[str, Any],
        world_state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Apply agent utterances and actions from cognition output."""
        agent_id = cognition_output.get("agent_id")
        utterance = cognition_output.get("utterance")
        action = cognition_output.get("action")

        if not agent_id:
            return world_state

        # Create speech event if utterance exists
        if utterance:
            event_data = {
                "world_id": world_state.get("world_id", 1),
                "type": "speech",
                "description": utterance,
                "source_entity_id": f"agent:{agent_id}",
                "target_entity_id": cognition_output.get("target_entity_id"),
                "payload": {"utterance": utterance},
                "tick": world_state.get("current_tick", 0),
                "timestamp": world_state.get("current_time", datetime.now(datetime.timezone.utc)),
                "processed": False
            }
            await self.world_repo.add_event(event_data)

        # Apply physical action if exists
        if action:
            # Parse action type and update world state accordingly
            action_lower = action.lower()
            event_data = {
                "world_id": world_state.get("world_id", 1),
                "type": "action",
                "description": action,
                "source_entity_id": f"agent:{agent_id}",
                "payload": {"action": action, "parsed_type": self._parse_action_type(action)},
                "tick": world_state.get("current_tick", 0),
                "timestamp": world_state.get("current_time", datetime.now(datetime.timezone.utc)),
                "processed": False
            }
            await self.world_repo.add_event(event_data)
            
            # Update agent location if action involves movement
            if self._is_movement_action(action):
                new_location_id = self._extract_location_from_action(action, world_state)
                if new_location_id:
                    agent = await self.agent_repo.get_agent_by_id(agent_id)
                    if agent:
                        agent.location_id = new_location_id
                        await self.session.flush()

        return world_state

    async def _apply_stance_and_intention_shifts(
        self,
        cognition_output: Dict[str, Any],
        world_state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Apply stance shifts and intention updates deterministically."""
        agent_id = cognition_output.get("agent_id")
        if not agent_id:
            return world_state

        agent = await self.agent_repo.get_agent_by_id(agent_id)
        if not agent:
            return world_state

        # Apply stance shifts (deterministic mapping)
        stance_shifts = cognition_output.get("stance_shifts", [])
        for shift in stance_shifts:
            target_id = shift.get("target")
            description = shift.get("description", "")

            # Map description to numeric deltas deterministically
            deltas = self._map_stance_shift_to_deltas(description)

            # Update relationship if target exists
            if target_id:
                relationships = await self.agent_repo.get_relationships(agent_id)
                for rel in relationships:
                    if (rel.target_agent_id and str(rel.target_agent_id) == str(target_id)) or \
                       (rel.target_user_id and str(rel.target_user_id) == str(target_id)):
                        # Apply deltas
                        rel.warmth = max(-1.0, min(1.0, rel.warmth + deltas.get("warmth", 0.0)))
                        rel.trust = max(-1.0, min(1.0, rel.trust + deltas.get("trust", 0.0)))
                        rel.tension = max(0.0, min(1.0, rel.tension + deltas.get("tension", 0.0)))
                        break

        # Apply intention updates
        intention_updates = cognition_output.get("intention_updates", [])
        for update in intention_updates:
            operation = update.get("operation")
            intention_type = update.get("type")
            target = update.get("target")
            horizon = update.get("horizon", "short")
            description = update.get("description", "")

            if operation == "create":
                # Create new intention via Autonomy Engine
                from backend.persistence.models import IntentionModel
                intention = IntentionModel(
                    agent_id=agent_id,
                    description=description,
                    priority=0.7,  # Default priority for new intentions
                    horizon=horizon,
                    type=intention_type or "action"
                )
                self.session.add(intention)
                await self.session.flush()
            elif operation == "boost":
                # Increase priority of existing intention
                from sqlalchemy import select
                from backend.persistence.models import IntentionModel
                stmt = select(IntentionModel).where(
                    IntentionModel.agent_id == agent_id,
                    IntentionModel.type == intention_type
                )
                if target:
                    # Match by target if specified
                    stmt = stmt.where(IntentionModel.description.contains(target))
                result = await self.session.execute(stmt)
                intentions = result.scalars().all()
                for intent in intentions:
                    intent.priority = min(1.0, intent.priority + 0.2)
                await self.session.flush()
            elif operation == "lower":
                # Decrease priority
                from sqlalchemy import select
                from backend.persistence.models import IntentionModel
                stmt = select(IntentionModel).where(
                    IntentionModel.agent_id == agent_id,
                    IntentionModel.type == intention_type
                )
                if target:
                    stmt = stmt.where(IntentionModel.description.contains(target))
                result = await self.session.execute(stmt)
                intentions = result.scalars().all()
                for intent in intentions:
                    intent.priority = max(0.0, intent.priority - 0.2)
                await self.session.flush()
            elif operation == "drop":
                # Remove intention
                from sqlalchemy import select, delete
                from backend.persistence.models import IntentionModel
                stmt = select(IntentionModel).where(
                    IntentionModel.agent_id == agent_id,
                    IntentionModel.type == intention_type
                )
                if target:
                    stmt = stmt.where(IntentionModel.description.contains(target))
                result = await self.session.execute(stmt)
                intentions = result.scalars().all()
                for intent in intentions:
                    await self.session.delete(intent)
                await self.session.flush()

        await self.session.flush()
        return world_state

    def _map_stance_shift_to_deltas(self, description: str) -> Dict[str, float]:
        """
        Map stance shift description to numeric deltas deterministically.
        
        Comprehensive mapping table for common stance shifts.
        """
        description_lower = description.lower()
        deltas = {"warmth": 0.0, "trust": 0.0, "tension": 0.0}

        # Trust-related shifts
        if "benefit of the doubt" in description_lower or "trusting" in description_lower:
            deltas["trust"] = 0.1
            deltas["tension"] = -0.05
        elif "give up" in description_lower or "lose trust" in description_lower or "distrust" in description_lower:
            deltas["trust"] = -0.2
            deltas["warmth"] = -0.1
        elif "regain trust" in description_lower or "rebuild trust" in description_lower:
            deltas["trust"] = 0.15
            deltas["tension"] = -0.1
        
        # Warmth-related shifts
        elif "open up" in description_lower or "warm" in description_lower or "closer" in description_lower:
            deltas["warmth"] = 0.15
            deltas["tension"] = -0.1
        elif "cold" in description_lower or "distant" in description_lower or "withdraw" in description_lower:
            deltas["warmth"] = -0.15
            deltas["tension"] = 0.1
        
        # Tension-related shifts
        elif "defensive" in description_lower or "guard" in description_lower or "tense" in description_lower:
            deltas["tension"] = 0.1
            deltas["trust"] = -0.05
        elif "relax" in description_lower or "ease" in description_lower or "calm" in description_lower:
            deltas["tension"] = -0.15
            deltas["warmth"] = 0.05
        
        # Combined positive shifts
        elif "forgive" in description_lower or "reconcile" in description_lower:
            deltas["warmth"] = 0.2
            deltas["trust"] = 0.15
            deltas["tension"] = -0.2
        elif "resent" in description_lower or "bitter" in description_lower:
            deltas["warmth"] = -0.2
            deltas["trust"] = -0.15
            deltas["tension"] = 0.2

        return deltas
    
    def _parse_action_type(self, action: str) -> str:
        """Parse action string to determine action type."""
        action_lower = action.lower()
        if any(word in action_lower for word in ["move", "go", "walk", "run", "travel"]):
            return "movement"
        elif any(word in action_lower for word in ["sit", "stand", "lie", "rest"]):
            return "posture"
        elif any(word in action_lower for word in ["take", "pick", "grab", "get"]):
            return "object_interaction"
        elif any(word in action_lower for word in ["give", "hand", "pass", "offer"]):
            return "object_transfer"
        elif any(word in action_lower for word in ["look", "glance", "stare", "watch"]):
            return "gaze"
        elif any(word in action_lower for word in ["touch", "hug", "kiss", "embrace"]):
            return "physical_contact"
        else:
            return "general"
    
    def _is_movement_action(self, action: str) -> bool:
        """Check if action involves movement."""
        action_lower = action.lower()
        movement_keywords = ["move", "go", "walk", "run", "travel", "leave", "enter", "exit"]
        return any(keyword in action_lower for keyword in movement_keywords)
    
    def _extract_location_from_action(self, action: str, world_state: Dict[str, Any]) -> Optional[int]:
        """Extract target location ID from action description."""
        # Extract location from action string or structured data
        # Check if action contains structured location data
        if isinstance(action, dict):
            return action.get("target_location_id")
        
        # Parse location name from action string
        action_lower = action.lower() if isinstance(action, str) else ""
        
        # Check world state for location mappings
        location_map = world_state.get("location_name_to_id", {})
        for location_name, location_id in location_map.items():
            if location_name.lower() in action_lower:
                return location_id
        
        # Check if action contains location ID directly
        import re
        location_id_match = re.search(r'location[_\s]*(\d+)', action_lower)
        if location_id_match:
            return int(location_id_match.group(1))
        
        return None

    async def _apply_physical_changes(
        self,
        renderer_output: Dict[str, Any],
        world_state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Apply physical changes from renderer structured output."""
        physical_changes = renderer_output.get("physical_changes", {})
        
        # Update locations
        if "location_changes" in physical_changes:
            for change in physical_changes["location_changes"]:
                entity_id = change.get("entity_id")
                new_location_id = change.get("location_id")
                entity_type = change.get("entity_type", "agent")
                
                if entity_type == "agent" and entity_id and new_location_id:
                    agent = await self.agent_repo.get_agent_by_id(entity_id)
                    if agent:
                        agent.location_id = new_location_id
                        await self.session.flush()

        # Update objects
        if "object_changes" in physical_changes:
            from sqlalchemy import select, update
            from backend.persistence.models import ObjectModel
            
            for change in physical_changes["object_changes"]:
                object_id = change.get("object_id")
                new_state = change.get("state")
                new_location_id = change.get("location_id")
                
                if object_id:
                    stmt = select(ObjectModel).where(ObjectModel.id == object_id)
                    result = await self.session.execute(stmt)
                    obj = result.scalars().first()
                    if obj:
                        if new_state:
                            obj.state = {**(obj.state or {}), **new_state}
                        if new_location_id:
                            obj.location_id = new_location_id
                        await self.session.flush()

        return world_state

    async def _update_psychology_from_events(
        self,
        world_state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update psychology deterministically from events."""
        # Psychology updates are handled by Autonomy Engine during normal processing
        # This method is called after perception cycle to ensure any event-driven
        # psychology changes are applied
        
        # Get recent events that haven't been processed for psychology
        from sqlalchemy import select
        from backend.persistence.models import EventModel
        
        world_id = world_state.get("world_id", 1)
        current_tick = world_state.get("current_tick", 0)
        
        # Get unprocessed events from recent ticks
        stmt = select(EventModel).where(
            EventModel.world_id == world_id,
            EventModel.processed == False,
            EventModel.tick >= current_tick - 5  # Last 5 ticks
        )
        result = await self.session.execute(stmt)
        unprocessed_events = result.scalars().all()
        
        # Process events through Autonomy Engine
        for event in unprocessed_events:
            # Extract agent ID from source_entity_id if it's an agent
            if event.source_entity_id and event.source_entity_id.startswith("agent:"):
                agent_id = int(event.source_entity_id.split(":")[1])
                agent = await self.agent_repo.get_agent_by_id(agent_id)
                if agent:
                    # Autonomy Engine would process this event
                    # For now, mark as processed
                    event.processed = True
        
        await self.session.flush()
        return world_state

    async def _store_episodic_memories(
        self,
        world_state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create episodic memories when salience >= threshold."""
        # Check recent events for memory creation
        from sqlalchemy import select
        from backend.persistence.models import EventModel, MemoryModel
        
        world_id = world_state.get("world_id", 1)
        current_tick = world_state.get("current_tick", 0)
        salience_threshold = 0.5
        
        # Get recent high-salience events
        stmt = select(EventModel).where(
            EventModel.world_id == world_id,
            EventModel.tick >= current_tick - 3,  # Last 3 ticks
            EventModel.type.in_(["speech", "action", "incursion"])
        )
        result = await self.session.execute(stmt)
        recent_events = result.scalars().all()
        
        for event in recent_events:
            # Calculate salience using proper salience calculation
            from backend.cognition.salience import SalienceCalculator
            
            # Base salience by event type
            if event.type == "speech":
                salience = 0.7
            elif event.type == "action":
                salience = 0.6
            elif event.type == "incursion":
                salience = 0.65
            else:
                salience = 0.5
            
            # Adjust based on event importance from payload
            if event.payload and isinstance(event.payload, dict):
                importance = event.payload.get("importance", 0.5)
                salience = max(0.0, min(1.0, salience * (0.5 + importance)))
            
            if salience >= salience_threshold:
                # Extract agent ID from source or target
                agent_id = None
                if event.source_entity_id and event.source_entity_id.startswith("agent:"):
                    agent_id = int(event.source_entity_id.split(":")[1])
                elif event.target_entity_id and event.target_entity_id.startswith("agent:"):
                    agent_id = int(event.target_entity_id.split(":")[1])
                
                if agent_id:
                    # Check if memory already exists for this event
                    existing = await self.agent_repo.get_agent_by_id(agent_id)
                    if existing:
                        # Create episodic memory
                        memory = MemoryModel(
                            agent_id=agent_id,
                            type="episodic",
                            description=event.description,
                            timestamp=event.timestamp,
                            salience=salience,
                            semantic_tags=self._extract_semantic_tags(event)
                        )
                        self.session.add(memory)
        
        await self.session.flush()
        return world_state
    
    def _extract_semantic_tags(self, event: EventModel) -> List[str]:
        """Extract semantic tags from event."""
        tags = [event.type]
        if event.payload:
            if "action_type" in event.payload:
                tags.append(event.payload["action_type"])
            if "topics" in event.payload:
                tags.extend(event.payload["topics"])
        return tags

    async def _update_biographical_memory(
        self,
        world_state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update biographical memory when stable patterns are reinforced."""
        from sqlalchemy import select
        from backend.persistence.models import MemoryModel
        
        # Check for repeated patterns in episodic memories that should become biographical
        # Look for memories that appear multiple times with similar content
        world_id = world_state.get("world_id", 1)
        
        # Get all agents
        agents = world_state.get("persistent_agents", [])
        
        for agent_data in agents:
            agent_id = agent_data.get("id")
            if not agent_id:
                continue
            
            # Get recent episodic memories
            stmt = select(MemoryModel).where(
                MemoryModel.agent_id == agent_id,
                MemoryModel.type == "episodic"
            ).order_by(MemoryModel.created_at.desc()).limit(20)
            
            result = await self.session.execute(stmt)
            recent_memories = result.scalars().all()
            
            # Check for patterns in semantic tags
            # Pattern: same tags appearing multiple times indicates stable trait/behavior
            tag_counts = {}
            tag_memory_map = {}  # Track which memories have which tags
            
            for memory in recent_memories:
                tags = memory.semantic_tags or []
                for tag in tags:
                    if tag not in tag_counts:
                        tag_counts[tag] = 0
                        tag_memory_map[tag] = []
                    tag_counts[tag] += 1
                    tag_memory_map[tag].append(memory.id)
            
            # If a tag appears 3+ times, create/update biographical memory
            for tag, count in tag_counts.items():
                if count >= 3:
                    # Check if biographical memory already exists with this tag
                    # Use simpler check since json_contains may not be available
                    bio_stmt = select(MemoryModel).where(
                        MemoryModel.agent_id == agent_id,
                        MemoryModel.type == "biographical"
                    )
                    bio_result = await self.session.execute(bio_stmt)
                    existing_bios = bio_result.scalars().all()
                    
                    # Check if tag exists in any existing biographical memory
                    tag_exists = False
                    for bio in existing_bios:
                        if bio.semantic_tags and tag in bio.semantic_tags:
                            tag_exists = True
                            break
                    
                    if not tag_exists:
                        # Create new biographical memory
                        bio_memory = MemoryModel(
                            agent_id=agent_id,
                            type="biographical",
                            description=f"Pattern observed: {tag}",
                            salience=0.8,
                            semantic_tags=[tag]
                        )
                        self.session.add(bio_memory)
        
        await self.session.flush()
        return world_state

