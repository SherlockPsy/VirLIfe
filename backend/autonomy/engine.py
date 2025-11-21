import math
from typing import Dict, List, Optional
from backend.persistence.models import AgentModel, EventModel

class AutonomyEngine:
    """
    Implements the numeric internal life of agents (Phase 3).
    Deterministic, no LLM calls.
    """

    def __init__(self):
        # Configuration constants (could be moved to settings/config later)
        self.DRIVE_BASELINE = 0.5
        self.DRIVE_DRIFT_FACTOR = 0.01 # Per tick drift towards baseline
        self.MOOD_DECAY_RATE = 0.05
        self.VALENCE_SENSITIVITY = 0.2
        
        # Core Drives
        self.DRIVE_NAMES = ["relatedness", "autonomy", "competence", "novelty", "safety"]

    def update_agent_internal_state(self, agent: AgentModel, events: List[EventModel]):
        """
        Main entry point for updating an agent's internal state based on recent events.
        Should be called every tick or when processing events.
        """
        # 1. Calculate Drive Changes
        drive_deltas = self._calculate_drive_deltas(agent, events)
        
        # 2. Update Drives
        self._apply_drive_updates(agent, drive_deltas)
        
        # 3. Update Mood based on Drive Changes and Events
        self._update_mood(agent, drive_deltas, events)
        
        # 4. Update Arcs
        self._update_arcs(agent, events)
        
        # 5. Update Relationships
        self._update_relationships(agent, events)
        
        # 6. Update Intentions
        self._update_intentions(agent, events)
        
        # 7. Update Energy
        self._update_energy(agent, events)
        
        # 8. Process Memories (Episodic & Biographical)
        self._process_memories(agent, events)
        
        # 9. Apply Baseline Drift (Homeostasis)
        self._apply_homeostasis(agent)

    def _calculate_drive_deltas(self, agent: AgentModel, events: List[EventModel]) -> Dict[str, float]:
        """
        Determines the impact of events on each drive.
        Returns a dictionary of deltas {drive_name: delta}.
        """
        deltas = {d: 0.0 for d in self.DRIVE_NAMES}
        
        for event in events:
            effects = self._map_event_to_drive_effects(event)
            for drive, effect in effects.items():
                if drive in deltas:
                    # Apply sensitivity
                    # Ensure drives dict exists and is not None
                    if agent.drives is None:
                        agent.drives = {}
                    sensitivity = agent.drives.get(drive, {}).get("sensitivity", 1.0)
                    deltas[drive] += effect * sensitivity
                    
        return deltas

    def _map_event_to_drive_effects(self, event: EventModel) -> Dict[str, float]:
        """
        Deterministic mapping of events to drive effects.
        This is the 'Logic Layer' mapping rule (Section 3.1).
        """
        effects = {}
        
        # Basic mapping based on event type (Phase 3 implementation)
        # In a full system, this would be more granular based on payload/description analysis
        # or a lookup table.
        
        if event.type == "interaction":
            # Positive interaction boosts relatedness
            effects["relatedness"] = 0.1
            
        elif event.type == "conflict":
            effects["relatedness"] = -0.2
            effects["safety"] = -0.1
            effects["arousal"] = 0.3 # Special key for mood
            
        elif event.type == "achievement":
            effects["competence"] = 0.2
            effects["autonomy"] = 0.1
            
        elif event.type == "failure":
            effects["competence"] = -0.15
            
        elif event.type == "incursion_sensory":
            effects["safety"] = -0.05
            effects["novelty"] = 0.1
            effects["arousal"] = 0.1
            
        elif event.type == "incursion_irregularity":
            effects["safety"] = -0.02
            effects["novelty"] = 0.05
            
        elif event.type == "calendar_missed":
            effects["competence"] = -0.1
            effects["safety"] = -0.05 # Anxiety
            
        elif event.type == "calendar_start":
            # Neutral/Positive depending on context, but generally increases arousal/focus
            effects["arousal"] = 0.05
            
        return effects

    def _apply_drive_updates(self, agent: AgentModel, deltas: Dict[str, float]):
        """
        Applies deltas to agent drives, clamping to [0.0, 1.0].
        """
        # Ensure drives dict exists and is not None
        if agent.drives is None:
            agent.drives = {}
        current_drives = agent.drives.copy() # Ensure we don't mutate in place without reassignment if it's a dict
        
        for drive in self.DRIVE_NAMES:
            if drive not in current_drives:
                # Initialize if missing
                current_drives[drive] = {"level": self.DRIVE_BASELINE, "sensitivity": 1.0}
            
            current_level = current_drives[drive]["level"]
            delta = deltas.get(drive, 0.0)
            
            new_level = max(0.0, min(1.0, current_level + delta))
            current_drives[drive]["level"] = new_level
            
        agent.drives = current_drives

    def _update_mood(self, agent: AgentModel, drive_deltas: Dict[str, float], events: List[EventModel]):
        """
        Updates Valence and Arousal (Law 2).
        """
        # Ensure mood dict exists and is not None
        if agent.mood is None:
            agent.mood = {"valence": 0.0, "arousal": 0.0}
        current_mood = agent.mood.copy()
        valence = current_mood.get("valence", 0.0)
        arousal = current_mood.get("arousal", 0.0)
        
        # 1. Valence Update
        # Valence moves based on weighted drive satisfaction/dissatisfaction
        # Sum of all drive deltas gives a rough proxy for "things getting better or worse"
        net_drive_change = sum(drive_deltas.values())
        valence += net_drive_change * self.VALENCE_SENSITIVITY
        
        # Clamp Valence [-1.0, 1.0]
        valence = max(-1.0, min(1.0, valence))
        
        # 2. Arousal Update
        # Increases with novelty, shock, conflict (mapped in events)
        arousal_delta = 0.0
        for event in events:
            effects = self._map_event_to_drive_effects(event)
            arousal_delta += effects.get("arousal", 0.0)
            
            # Novelty drive change also feeds arousal
            if "novelty" in effects and effects["novelty"] > 0:
                arousal_delta += effects["novelty"] * 0.5
                
        arousal += arousal_delta
        
        # Clamp Arousal [0.0, 1.0]
        arousal = max(0.0, min(1.0, arousal))
        
        current_mood["valence"] = valence
        current_mood["arousal"] = arousal
        agent.mood = current_mood

    def _apply_homeostasis(self, agent: AgentModel):
        """
        Applies baseline drift to drives and mood decay.
        """
        # Drive Drift
        # Ensure drives dict exists and is not None
        if agent.drives is None:
            agent.drives = {}
        current_drives = agent.drives.copy()
        for drive in self.DRIVE_NAMES:
            if drive in current_drives:
                level = current_drives[drive]["level"]
                # Drift towards baseline
                level += (self.DRIVE_BASELINE - level) * self.DRIVE_DRIFT_FACTOR
                current_drives[drive]["level"] = level
        agent.drives = current_drives
        
        # Mood Decay
        # Ensure mood dict exists and is not None
        if agent.mood is None:
            agent.mood = {"valence": 0.0, "arousal": 0.0}
        current_mood = agent.mood.copy()
        valence = current_mood.get("valence", 0.0)
        arousal = current_mood.get("arousal", 0.0)
        
        # Valence decays towards 0 (neutral)
        valence *= (1.0 - self.MOOD_DECAY_RATE)
        
        # Arousal decays towards 0 (calm) - or a baseline if defined
        arousal *= (1.0 - self.MOOD_DECAY_RATE)
        
        current_mood["valence"] = valence
        current_mood["arousal"] = arousal
        agent.mood = current_mood

    def _update_arcs(self, agent: AgentModel, events: List[EventModel]):
        """
        Updates arc intensity based on event relevance (Law 3).
        """
        # We need to iterate over agent's arcs.
        # Assuming agent.arcs is a list of ArcModel objects loaded in session.
        if not agent.arcs:
            return

        for arc in agent.arcs:
            # Decay
            # Assuming this runs every tick or we calculate delta_t.
            # For simplicity in Phase 3, we assume fixed tick duration or per-update decay.
            # Law 3: arc.intensity ← arc.intensity * (1 - arc.decay_rate * Δt)
            # We'll use a fixed small decay per update cycle for now.
            decay = arc.decay_rate * 0.01 # Scaling factor
            arc.intensity = arc.intensity * (1.0 - decay)
            
            # Reinforcement
            # Check if any event matches arc topic_vector
            for event in events:
                if self._is_arc_relevant(arc, event):
                    # Increase intensity
                    # Magnitude depends on event importance/salience (default 0.1)
                    arc.intensity = min(1.0, arc.intensity + 0.1)

    def _is_arc_relevant(self, arc, event: EventModel) -> bool:
        """
        Checks if event semantically matches arc.
        Phase 3: Simple keyword matching.
        """
        if not arc.topic_vector:
            return False
            
        # topic_vector is JSON list of keywords
        keywords = arc.topic_vector
        description = event.description.lower()
        
        for kw in keywords:
            if kw.lower() in description:
                return True
        return False

    def _update_relationships(self, agent: AgentModel, events: List[EventModel]):
        """
        Updates relationship edges (Law 4).
        """
        # 1. Event-based updates
        for event in events:
            # Check if event involves another agent/user
            target_id = event.target_entity_id
            source_id = event.source_entity_id
            
            # Identify the "other" party
            other_id = None
            if source_id == f"agent:{agent.id}" and target_id:
                other_id = target_id
            elif target_id == f"agent:{agent.id}" and source_id:
                other_id = source_id
                
            if other_id:
                # Find relationship edge
                rel = self._find_relationship(agent, other_id)
                if rel:
                    self._apply_relationship_update(rel, event)

        # 2. Passive Decay (Drift)
        # Relationships drift towards neutral over time if not reinforced
        for rel in agent.relationships:
            # Warmth decays towards 0
            rel.warmth *= 0.995
            # Tension decays towards 0 (healing)
            rel.tension *= 0.99
            # Familiarity decays very slowly
            rel.familiarity *= 0.999

    def _find_relationship(self, agent: AgentModel, target_entity_id: str):
        """
        Helper to find relationship object from list.
        target_entity_id format: "agent:1" or "user:1"
        """
        # Parse ID
        try:
            type_, id_str = target_entity_id.split(":")
            id_val = int(id_str)
        except ValueError:
            return None
            
        for rel in agent.relationships:
            if type_ == "agent" and rel.target_agent_id == id_val:
                return rel
            if type_ == "user" and rel.target_user_id == id_val:
                return rel
        return None

    def _apply_relationship_update(self, rel, event: EventModel):
        """
        Applies deterministic updates to relationship metrics.
        """
        # Volatility scales the effect
        volatility = rel.volatility
        scale = 1.0 + volatility
        
        if event.type == "interaction":
            # Positive interaction
            rel.warmth = min(1.0, rel.warmth + 0.05 * scale)
            rel.familiarity = min(1.0, rel.familiarity + 0.02)
            rel.tension = max(0.0, rel.tension - 0.05 * scale)
            
        elif event.type == "conflict":
            rel.tension = min(1.0, rel.tension + 0.1 * scale)
            rel.warmth = max(-1.0, rel.warmth - 0.1 * scale)
            rel.trust = max(-1.0, rel.trust - 0.05 * scale)
            
        elif event.type == "betrayal":
            rel.trust = max(-1.0, rel.trust - 0.3 * scale)
            rel.tension = min(1.0, rel.tension + 0.2 * scale)
            
    def _update_intentions(self, agent: AgentModel, events: List[EventModel]):
        """
        Updates intentions based on events and needs (Task 3.5).
        Integrates Calendar/Obligation logic (Task 3.10).
        """
        completed_calendar_ids = set()
        
        # 1. Process Calendar Events -> Intentions
        for event in events:
            if event.type == "calendar_reminder":
                # Create intention to prepare/attend
                calendar_id = event.payload.get("calendar_id")
                if not self._has_intention_for_calendar(agent, calendar_id):
                    self._add_intention(agent, {
                        "description": f"Prepare for {event.description}",
                        "priority": 0.8,
                        "type": "obligation",
                        "horizon": "short",
                        "payload": {"calendar_id": calendar_id}
                    })
            
            elif event.type == "calendar_start":
                # Escalate priority of existing intention or create new one
                calendar_id = event.payload.get("calendar_id")
                self._escalate_intention_priority(agent, calendar_id, 1.0)
                
            elif event.type == "action_completed":
                # Mark intention as completed
                calendar_id = event.payload.get("calendar_id")
                if calendar_id:
                    completed_calendar_ids.add(str(calendar_id))

        # 2. Decay/Drop Intentions
        # Remove completed or stale intentions
        active_intentions = []
        for intention in agent.intentions:
            # Check completion
            is_completed = False
            for cid in completed_calendar_ids:
                if cid in intention.description:
                    is_completed = True
                    break
            
            if is_completed:
                continue # Skip adding to active list (effectively removing)

            if intention.type != "obligation":
                intention.priority -= 0.01 # Decay
            
            if intention.priority > 0.1:
                active_intentions.append(intention)
        
        # Update the list (in-memory simulation of persistence update)
        # In real ORM, we would delete the objects. Here we replace the list reference if possible,
        # but since it's an instrumented list, we should probably clear and re-add or remove.
        # For the test to pass, we need to modify the list in place.
        agent.intentions[:] = active_intentions
        
    def _has_intention_for_calendar(self, agent: AgentModel, calendar_id: int) -> bool:
        # Check payload of intentions (assuming we store metadata there)
        # IntentionModel doesn't have payload column in Phase 1 schema?
        # Let's check models.py.
        # IntentionModel has: description, priority, horizon, type, stability.
        # No payload. We might need to rely on description parsing or add payload column.
        # For Phase 3 compliance without schema change, we'll use description matching.
        return any(str(calendar_id) in i.description for i in agent.intentions)

    def _add_intention(self, agent: AgentModel, data: dict):
        # In a real engine, we'd create the model and add to session.
        # Since we don't have the session here easily, we might need to return ops
        # or assume agent.intentions is a collection we can append to (if using SA).
        # But creating a new ORM object requires the class.
        from backend.persistence.models import IntentionModel
        new_intention = IntentionModel(
            agent_id=agent.id,
            description=data["description"],
            priority=data["priority"],
            type=data["type"],
            horizon=data["horizon"]
        )
        agent.intentions.append(new_intention)

    def _escalate_intention_priority(self, agent: AgentModel, calendar_id: int, new_priority: float):
        for intention in agent.intentions:
            if str(calendar_id) in intention.description:
                intention.priority = max(intention.priority, new_priority)

    def _update_energy(self, agent: AgentModel, events: List[EventModel]):
        """
        Updates energy levels (Law 5).
        """
        # Depletion
        # Base metabolic rate
        agent.energy = max(0.0, agent.energy - 0.005)
        
        for event in events:
            if event.type == "conflict":
                agent.energy -= 0.1
            elif event.type == "work":
                agent.energy -= 0.05
                
        # Restoration
        # Check location or time
        # If night time (e.g. 23:00 - 07:00), restore energy
        # We need world time. But we only have events.
        # We can check the timestamp of the last event or pass world context.
        # For now, let's assume we pass world context or infer from events.
        # Actually, update_agent_internal_state signature is (agent, events).
        # We should probably pass 'world' or 'current_time' too.
        # For Phase 3, we'll stick to event-driven or simple logic.
        
        # If energy is very low, force rest intention?
        if agent.energy < 0.2:
            # Add rest intention
            pass

    def _process_memories(self, agent: AgentModel, events: List[EventModel]):
        """
        Creates episodic memories and ingests biographical facts (Tasks 3.7, 3.8).
        """
        MEMORY_THRESHOLD = 0.6
        
        for event in events:
            salience = self._calculate_salience(agent, event)
            
            if salience >= MEMORY_THRESHOLD:
                self._create_episodic_memory(agent, event, salience)
                
            # Biographical Ingestion (Simplified for Phase 3)
            # Check for explicit disclosures or patterns
            if event.type == "disclosure":
                self._create_biographical_memory(agent, event)

    def _calculate_salience(self, agent: AgentModel, event: EventModel) -> float:
        """
        Computes salience based on Section 8.
        """
        salience = 0.0
        
        # 1. Sensory Prominence (Base based on type)
        if event.type in ["incursion_sensory", "conflict", "achievement"]:
            salience += 0.4
        elif event.type == "interaction":
            salience += 0.3
        else:
            salience += 0.1
            
        # 2. Relational Stakes
        # If event involves someone with high relationship volatility or intensity
        # We need to check target/source
        # (Simplified logic for Phase 3)
        if event.source_entity_id == "user:1" or event.target_entity_id == "user:1":
            salience += 0.2 # User presence factor
            
        # 3. Drive Pressure
        # If event affects a drive that is currently extreme (very low or very high)
        effects = self._map_event_to_drive_effects(event)
        for drive, effect in effects.items():
            # Ensure drives dict exists and is not None
            if agent.drives is None:
                agent.drives = {}
            current_level = agent.drives.get(drive, {}).get("level", 0.5)
            if abs(current_level - 0.5) > 0.3: # Extreme drive
                salience += 0.2
                
        # 4. Novelty
        if event.type.startswith("incursion"):
            salience += 0.3
            
        return min(1.0, salience)

    def _create_episodic_memory(self, agent: AgentModel, event: EventModel, salience: float):
        from backend.persistence.models import MemoryModel
        
        # Create memory
        memory = MemoryModel(
            agent_id=agent.id,
            type="episodic",
            description=event.description,
            timestamp=event.timestamp,
            salience=salience,
            semantic_tags=event.payload.get("tags", [])
        )
        agent.memories.append(memory)

    def _create_biographical_memory(self, agent: AgentModel, event: EventModel):
        from backend.persistence.models import MemoryModel
        
        # Create bio memory
        memory = MemoryModel(
            agent_id=agent.id,
            type="biographical",
            description=f"Learned: {event.description}",
            timestamp=event.timestamp,
            salience=1.0, # Bio facts are usually high salience/permanent
            semantic_tags=["fact", "disclosure"]
        )
        agent.memories.append(memory)