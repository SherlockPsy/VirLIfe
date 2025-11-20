import random
import datetime
from typing import List, Optional, Dict
from backend.persistence.models import WorldModel, AgentModel, EventModel

class IncursionGenerator:
    """
    Implements Appendix I: Unexpected Events (Incursions).
    Generates deterministic, world-grounded events that interrupt the flow.
    """

    def __init__(self):
        # Templates are used to construct descriptions, but the *trigger* is logic-based.
        self.sensory_templates = [
            "A sudden draft chills the room.",
            "The hum of the ventilation system changes pitch.",
            "A distant siren wails outside.",
            "The lights flicker briefly.",
            "A heavy thud comes from the floor above."
        ]
        
        self.micro_irregularity_templates = [
            "A small object falls off a shelf nearby.",
            "The wifi connection indicator blinks red for a moment.",
            "A fly buzzes persistently around the room."
        ]

    def generate_incursions(self, world: WorldModel, agents: List[AgentModel]) -> List[dict]:
        """
        Deterministically generates incursions based on world tick and state.
        Returns a list of event data dicts.
        """
        incursions = []
        
        # Seed random with world tick for absolute determinism
        # We use a specific salt for incursions to avoid correlation with other random events
        rng = random.Random(f"incursion_{world.current_tick}_{world.id}")
        
        # 1. Environmental / Sensory Incursions
        # Probability based on time of day (e.g., more noise during day, more creaks at night)
        hour = world.current_time.hour
        is_night = hour < 6 or hour > 22
        
        base_prob = 0.05 # 5% chance per tick (assuming 1 min tick)
        if is_night:
            base_prob = 0.08 # Quieter, so sounds are more noticeable/incursive
            
        if rng.random() < base_prob:
            template = rng.choice(self.sensory_templates)
            incursions.append({
                "world_id": world.id,
                "type": "incursion_sensory",
                "description": template,
                "tick": world.current_tick,
                "timestamp": world.current_time,
                "source_entity_id": "environment",
                "target_entity_id": "all", # Perceived by everyone in relevant locations
                "payload": {"category": "sensory"}
            })

        # 2. Micro-Irregularities (Entropy)
        if rng.random() < 0.02:
            template = rng.choice(self.micro_irregularity_templates)
            incursions.append({
                "world_id": world.id,
                "type": "incursion_irregularity",
                "description": template,
                "tick": world.current_tick,
                "timestamp": world.current_time,
                "source_entity_id": "environment",
                "target_entity_id": "all",
                "payload": {"category": "irregularity"}
            })

        # 3. Communication / Digital Incursions
        # Modeled based on agent activity (even off-screen).
        # If an agent is NOT in the same location as the user (or main focus),
        # they might send a message.
        # This requires knowing who is where.
        # For now, we simulate "digital noise" or generic notifications if we don't have full context.
        # Real agent messages should come from the Autonomy Engine (intentions), 
        # but "spam" or "system alerts" are world incursions.
        
        if rng.random() < 0.03:
            incursions.append({
                "world_id": world.id,
                "type": "incursion_digital",
                "description": "A notification chimes on a nearby device.",
                "tick": world.current_tick,
                "timestamp": world.current_time,
                "source_entity_id": "system",
                "target_entity_id": "all",
                "payload": {"category": "digital"}
            })

        return incursions
