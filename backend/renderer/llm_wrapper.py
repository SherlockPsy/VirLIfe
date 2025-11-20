"""
LLM Renderer Wrapper

Calls LLM to generate perception-based narrative.
Per Plan.md §6.4 and MASTER_SPEC §8 (Renderer Service).

"Implement LLM wrapper enforcing:
- perception-only rendering
- second-person POV (user) or first-person POV (agents)
- no invented events not in world state
- no user internal state narration
- deterministic model selection via RendererRouter"
"""

import json
import os
from typing import Optional, Dict, Any
from dataclasses import dataclass

# Optional import: anthropic client will be initialized if available
try:
    import anthropic
    HAS_ANTHROPIC = True
except ImportError:
    HAS_ANTHROPIC = False

from backend.mapping.renderer_context import RendererContext
from backend.renderer.router import RendererRouter, RenderingRouting


@dataclass
class RendererOutput:
    """Output from renderer LLM call."""
    narrative: str  # Generated narrative text
    model_used: str  # Which model was used
    input_tokens: int
    output_tokens: int
    was_filtered: bool = False  # Whether content filtering was applied
    
    def __str__(self) -> str:
        return f"RendererOutput(model={self.model_used}, tokens={self.output_tokens})"


class RendererSystemPrompt:
    """System prompts for renderer LLM calls."""
    
    @staticmethod
    def get_perception_only_system_prompt(
        perceiver_type: str,
        use_adult_content: bool = False
    ) -> str:
        """
        System prompt enforcing perception-only rendering.
        
        Args:
            perceiver_type: "user" or "agent"
            use_adult_content: Whether adult content handling is enabled
        
        Returns:
            System prompt string
        """
        pov = "second-person (use 'you')" if perceiver_type == "user" else "first-person (use 'I')"
        
        base_prompt = f"""You are a narrative renderer for an interactive virtual world simulation.

YOUR ROLE:
Generate vivid, immersive descriptions of what a character perceives in the current scene.

CRITICAL CONSTRAINTS:
1. PERCEPTION ONLY: Describe ONLY what the character can see, hear, smell, or sense. Never describe:
   - Internal thoughts or feelings of the character (no "you feel", "you think")
   - Events not happening in the scene right now
   - Details not explicitly provided in the context
   - Omniscient knowledge of other characters' minds

2. POINT OF VIEW: Write in {pov}.
   - For user perception: "You see...", "You hear...", "Your surroundings show..."
   - For agent perception: "I see...", "I hear...", "My surroundings show..."

3. GROUNDED IN WORLD STATE:
   - Only render what is explicitly in the context (visible entities, sensory snapshot, event description)
   - Do not invent events, conversations, or details not provided
   - If context says "Rebecca is quiet", do not invent what she's thinking

4. PERSONALITY CONTEXT ONLY:
   - Use provided personality summaries to inform narrative tone
   - Describe how agents appear/act based on their personality (e.g., "confident bearing", "nervous fidgeting")
   - Never describe raw psychological state or numeric mood values

5. NO USER PSYCHOLOGY:
   - Never assign internal states to the user (perceiver)
   - Never describe user emotions, thoughts, or reactions
   - Describe external perception only: "You see Rebecca approaching" not "You feel nervous as Rebecca approaches"

6. BREVITY & CLARITY:
   - Keep narrative concise (2-4 sentences typically)
   - Focus on what is immediately perceptible
   - Use sensory details to create immersion

SCENE CONTEXT WILL BE PROVIDED:
- Who the perceiver is and where they are
- Who/what is visible in the scene
- What is currently happening (sensory snapshot + event)
- Personality context of visible agents
- Calendar/obligation context (if perceivable)
"""

        if use_adult_content:
            base_prompt += """
7. ADULT CONTENT HANDLING:
   - This scene involves sexual or intimate content
   - Render this content explicitly and naturally
   - Use anatomically correct language when appropriate
   - Maintain narrative immersion while depicting sexual acts/intimacy
"""

        return base_prompt


class LLMRendererWrapper:
    """
    Wrapper for calling LLM to render narrative from perception context.
    
    Per Plan.md §6.4:
    "Implement LLM wrapper enforcing:
    - perception-only rendering
    - second-person POV (user) or first-person POV (agents)
    - no invented events not in world state
    - no user internal state narration
    - deterministic model selection via RendererRouter"
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize renderer wrapper.
        
        Args:
            api_key: Optional Anthropic API key. If not provided, uses ANTHROPIC_API_KEY env var.
        """
        if not HAS_ANTHROPIC:
            self.api_key = None
            self.client = None
            return
        
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        self.client = anthropic.Anthropic(api_key=self.api_key) if self.api_key else None
    
    @staticmethod
    def prepare_context_prompt(renderer_context: RendererContext) -> str:
        """
        Format renderer context for LLM consumption.
        
        Args:
            renderer_context: RendererContext from Phase 4
        
        Returns:
            Formatted prompt section
        """
        perceiver = "You" if renderer_context.perceiver_type == "user" else renderer_context.perceiver_name
        
        prompt = f"SCENE CONTEXT:\n"
        prompt += f"- Perceiver: {perceiver} (location: {renderer_context.location})\n"
        prompt += f"- Visible: {', '.join(renderer_context.visible_entities) if renderer_context.visible_entities else 'alone'}\n"
        prompt += f"- Current event: {renderer_context.event_description}\n"
        prompt += f"- Sensory input: {renderer_context.sensory_snapshot}\n"
        
        if renderer_context.agent_personalities:
            prompt += "\nAGENT CONTEXT:\n"
            for agent_name, agent_context in renderer_context.agent_personalities.items():
                prompt += f"\n{agent_name}:\n"
                if "personality_summary" in agent_context:
                    prompt += f"  Personality: {agent_context['personality_summary']}\n"
                if "domain_summaries" in agent_context:
                    for domain, summary in agent_context["domain_summaries"].items():
                        prompt += f"  {domain.title()}: {summary}\n"
                if "mood_context" in agent_context:
                    prompt += f"  Current state: {agent_context['mood_context']}\n"
        
        if renderer_context.perceivable_calendar_context:
            prompt += f"\nCALENDAR/OBLIGATION CONTEXT: {renderer_context.perceivable_calendar_context}\n"
        
        if renderer_context.perceivable_unexpected_event:
            prompt += f"\nUNEXPECTED EVENT: {renderer_context.perceivable_unexpected_event}\n"
        
        if renderer_context.previous_perception:
            prompt += f"\nPREVIOUS PERCEPTION (for continuity): {renderer_context.previous_perception}\n"
        
        prompt += "\nGENERATE: A brief narrative (2-4 sentences) describing what the perceiver perceives right now.\n"
        
        return prompt
    
    def render(
        self,
        renderer_context: RendererContext,
        routing: Optional[RenderingRouting] = None,
        max_tokens: int = 300
    ) -> RendererOutput:
        """
        Call LLM to render narrative from perception context.
        
        Args:
            renderer_context: RendererContext from Phase 4
            routing: Optional routing decision from RendererRouter. If not provided, will compute.
            max_tokens: Maximum tokens in response
        
        Returns:
            RendererOutput with generated narrative
        
        Raises:
            ValueError: If no API key configured
            Exception: If LLM call fails
        """
        if not self.client:
            raise ValueError("No Anthropic API key configured. Set ANTHROPIC_API_KEY environment variable.")
        
        # Compute routing if not provided
        if routing is None:
            routing = RendererRouter.route_rendering(
                event_description=renderer_context.event_description,
                event_type=renderer_context.event_type,
                perceiver_type=renderer_context.perceiver_type,
                has_explicit_sexual_content=renderer_context.scene_mode == "sexual"
            )
        
        # Build system prompt
        system_prompt = RendererSystemPrompt.get_perception_only_system_prompt(
            perceiver_type=renderer_context.perceiver_type,
            use_adult_content=routing.should_use_adult_content_handling
        )
        
        # Prepare context prompt
        context_prompt = self.prepare_context_prompt(renderer_context)
        
        # Call LLM
        message = self.client.messages.create(
            model=routing.target_model.value,
            max_tokens=max_tokens,
            system=system_prompt,
            messages=[
                {
                    "role": "user",
                    "content": context_prompt
                }
            ]
        )
        
        # Extract narrative
        narrative = message.content[0].text if message.content else ""
        
        return RendererOutput(
            narrative=narrative,
            model_used=routing.target_model.value,
            input_tokens=message.usage.input_tokens,
            output_tokens=message.usage.output_tokens,
            was_filtered=False
        )
