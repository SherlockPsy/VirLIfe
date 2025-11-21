from __future__ import annotations

from typing import Any, Dict, List, Optional

from backend.cognition.service import CognitionOutput
from backend.cognition.llm_wrapper import (
    CognitionLLMResponse,
    StanceShiftOutput,
    IntentionUpdateOutput,
)


class FakeCognitionService:
    """
    Deterministic cognition service used in tests.

    Scenarios:
    - simple_dialogue: friendly utterance + stance shift
    - invalid_action: physically impossible action (validation failure)
    - relationship_update: stance + intention updates applied deterministically
    """

    def __init__(self, scenario: str = "simple_dialogue"):
        self.scenario = scenario
        self.calls: List[Any] = []

    def process_semantic_cognition(self, cognition_input) -> CognitionOutput:
        self.calls.append(cognition_input)
        response = self._build_response()
        eligibility_result = None
        if cognition_input.eligibility_metadata:
            eligibility_result = cognition_input.eligibility_metadata.get("eligibility_result")

        return CognitionOutput(
            agent_id=cognition_input.agent_id,
            event_time=cognition_input.event_time,
            was_eligible=True,
            eligibility_result=eligibility_result,
            llm_called=True,
            llm_response=response,
        )

    def _build_response(self) -> CognitionLLMResponse:
        if self.scenario == "invalid_action":
            return CognitionLLMResponse(
                utterance="She insists she can phase through matter.",
                action="She teleports through the solid wall.",
                stance_shifts=[],
                intention_updates=[],
            )

        if self.scenario == "relationship_update":
            return CognitionLLMResponse(
                utterance="She decides to give them the benefit of the doubt.",
                action="She steps a little closer.",
                stance_shifts=[
                    StanceShiftOutput(
                        target="agent:200",
                        description="Gives benefit of the doubt and softens posture.",
                    )
                ],
                intention_updates=[
                    IntentionUpdateOutput(
                        operation="create",
                        type="support",
                        target="agent:200",
                        horizon="short",
                        description="She wants to be more supportive for the rest of the day.",
                    )
                ],
            )

        # Default: simple dialogue
        return CognitionLLMResponse(
            utterance="She smiles and says it's nice to talk.",
            action="She gestures gently toward the user.",
            stance_shifts=[
                StanceShiftOutput(
                    target="agent:200",
                    description="Offers a reassuring smile and eases tension.",
                )
            ],
            intention_updates=[],
        )


class FakeRenderEngine:
    """Deterministic render engine stub."""

    def __init__(self, text: str = "Rendered response."):
        self.text = text
        self.calls: List[Dict[str, Any]] = []

    async def render_world_state(
        self,
        *,
        perceiver_id: int,
        perceiver_type: str,
    ) -> str:
        self.calls.append({"perceiver_id": perceiver_id, "perceiver_type": perceiver_type})
        return self.text

