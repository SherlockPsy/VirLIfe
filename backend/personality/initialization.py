import json
import os
from typing import Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from backend.personality.templates import TemplateLibrary
from backend.personality.compiler import PersonalityCompiler
from backend.persistence.repo import AgentRepo, WorldRepo, UserRepo
from backend.persistence.models import RelationshipModel

class CharacterInitializer:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.template_library = TemplateLibrary()
        self.compiler = PersonalityCompiler(self.template_library)
        self.agent_repo = AgentRepo(session)
        self.world_repo = WorldRepo(session)
        self.user_repo = UserRepo(session)

    async def initialize_character(self, fingerprint_path: str, world_id: int, location_id: int):
        """
        Reads a fingerprint file, compiles personality, and persists the agent.
        """
        if not os.path.exists(fingerprint_path):
            raise FileNotFoundError(f"Fingerprint not found: {fingerprint_path}")

        with open(fingerprint_path, 'r') as f:
            data = json.load(f)

        name = data["name"]
        mixture = data["template_mixture"]
        modifiers = data.get("fingerprint_modifiers", {}).get("kernel_adjustments", {})
        semantic_additions = data.get("fingerprint_modifiers", {}).get("semantic_additions", [])
        
        # 1. Compile Kernel
        kernel = self.compiler.compile_kernel(mixture, modifiers)
        
        # 2. Compile Summaries
        stable_summary = self.compiler.compile_stable_summary(mixture, semantic_additions)
        domain_summaries = self.compiler.compile_domain_summaries(mixture)
        
        # 3. Create Agent
        agent_data = {
            "name": name,
            "world_id": world_id,
            "location_id": location_id,
            "personality_kernel": kernel,
            "personality_summaries": {"stable": stable_summary},
            "domain_summaries": domain_summaries,
            "drives": { # Default drives
                "relatedness": {"level": 0.5, "sensitivity": 1.0},
                "autonomy": {"level": 0.5, "sensitivity": 1.0},
                "competence": {"level": 0.5, "sensitivity": 1.0},
                "novelty": {"level": 0.5, "sensitivity": 1.0},
                "safety": {"level": 0.5, "sensitivity": 1.0}
            },
            "mood": {"valence": 0.0, "arousal": 0.0},
            "energy": 1.0
        }
        
        # Check if agent exists
        existing = await self.agent_repo.get_agent_by_name(name)
        if existing:
            # Update existing? Or skip? For now, let's assume we skip or overwrite if needed.
            # But repo create_agent inserts new.
            # Let's just return existing for safety in this basic impl.
            return existing

        agent = await self.agent_repo.create_agent(agent_data)
        
        # 4. Initialize Biography
        for bio_fact in data.get("initial_biography", []):
            await self.agent_repo.add_memory(agent.id, {
                "type": "biographical",
                "description": bio_fact,
                "salience": 1.0,
                "semantic_tags": ["background"]
            })
            
        # 5. Initialize Relationships
        # Note: This requires the target to exist. 
        # If target is "user", we need to find the user.
        initial_rels = data.get("initial_relationships", {})
        for target_name, metrics in initial_rels.items():
            if target_name.lower() == "user":
                # Find or create default user?
                # In a real flow, user should exist.
                # We'll try to find a user named "User" or "George" (from context)
                # For now, let's assume a user exists or we skip.
                # We will implement a helper to find ANY user for now.
                # Or just skip if no user found.
                pass 
                # TODO: Implement relationship wiring once User is guaranteed.
        
        return agent

    async def wire_initial_relationships(self, agent_id: int, fingerprint_path: str, user_id: int):
        """
        Separate step to wire relationships after all entities exist.
        """
        with open(fingerprint_path, 'r') as f:
            data = json.load(f)
            
        initial_rels = data.get("initial_relationships", {})
        for target_name, metrics in initial_rels.items():
            if target_name.lower() == "user":
                rel = RelationshipModel(
                    source_agent_id=agent_id,
                    target_user_id=user_id,
                    **metrics
                )
                self.session.add(rel)
        
        await self.session.flush()
