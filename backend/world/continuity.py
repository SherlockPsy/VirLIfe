import datetime
from typing import Dict, Optional
from backend.persistence.models import AgentModel, WorldModel

class ContinuityEngine:
    """
    Handles deterministic off-screen continuity.
    Ensures agents have a life when not interacting with the user.
    Implements minimal routine logic (Phase 2 requirement).
    """
    
    def __init__(self):
        # Simple deterministic routine map: Hour -> Location Name (or ID logic)
        # In a real system, this would be loaded from DB or Agent config.
        # For Phase 2, we hardcode a basic schedule for testing continuity.
        self.default_schedule = {
            0: "Bedroom",
            8: "Kitchen",
            9: "Work/Study",
            13: "Kitchen",
            14: "Work/Study",
            18: "Living Room",
            22: "Bedroom"
        }

    def get_scheduled_location_name(self, agent: AgentModel, time: datetime.datetime) -> str:
        """
        Determines where an agent SHOULD be based on their routine.
        """
        hour = time.hour
        # Find the latest schedule slot that fits
        target_loc = "Bedroom" # Default
        for h in sorted(self.default_schedule.keys()):
            if hour >= h:
                target_loc = self.default_schedule[h]
        return target_loc

    def update_agent_continuity(self, agent: AgentModel, world: WorldModel, locations_map: Dict[str, int]) -> Optional[int]:
        """
        Checks if agent needs to move based on routine.
        Returns target_location_id if movement is needed, else None.
        """
        # If agent is "busy" or in a specific interaction, we might skip (Autonomy handles that later).
        # For Phase 2, we enforce the routine strictly for off-screen agents.
        
        target_name = self.get_scheduled_location_name(agent, world.current_time)
        
        # Resolve name to ID
        target_id = locations_map.get(target_name)
        if not target_id:
            return None # Location doesn't exist in this world
            
        if agent.location_id != target_id:
            return target_id
            
        return None
