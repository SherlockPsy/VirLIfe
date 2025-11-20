from typing import Dict, List, Any
from backend.personality.templates import TemplateLibrary, PersonalityTemplate

class PersonalityCompiler:
    def __init__(self, template_library: TemplateLibrary):
        self.library = template_library

    def compile_kernel(self, mixture: Dict[str, float], modifiers: Dict[str, float] = None) -> Dict[str, float]:
        """
        Deterministically mixes personality kernels based on weights.
        Applies optional modifiers from fingerprint.
        """
        # Validate weights sum to approx 1.0
        total_weight = sum(mixture.values())
        if not (0.99 <= total_weight <= 1.01):
            raise ValueError(f"Template weights must sum to 1.0, got {total_weight}")

        # Initialize zeroed kernel
        # We take the keys from the first template in the mixture to know what dimensions exist
        first_template_name = list(mixture.keys())[0]
        dimensions = self.library.get_template(first_template_name).kernel.keys()
        
        mixed_kernel = {dim: 0.0 for dim in dimensions}

        # Weighted sum
        for template_name, weight in mixture.items():
            template = self.library.get_template(template_name)
            for dim, value in template.kernel.items():
                mixed_kernel[dim] += value * weight

        # Apply modifiers
        if modifiers:
            for dim, mod in modifiers.items():
                if dim in mixed_kernel:
                    mixed_kernel[dim] += mod
                    # Clamp to [0.0, 1.0]
                    mixed_kernel[dim] = max(0.0, min(1.0, mixed_kernel[dim]))

        return mixed_kernel

    def compile_stable_summary(self, mixture: Dict[str, float], fingerprint_semantics: List[str] = None) -> str:
        """
        Generates a deterministic semantic summary from the mixture.
        This is a simple concatenation/rule-based generation to avoid LLMs.
        """
        summary_parts = []
        
        # Sort mixture by weight descending to prioritize dominant traits
        sorted_mix = sorted(mixture.items(), key=lambda item: item[1], reverse=True)
        
        summary_parts.append("Personality Structure:")
        for name, weight in sorted_mix:
            if weight > 0.05:
                template = self.library.get_template(name)
                traits = ", ".join(template.semantic_traits[:3])
                summary_parts.append(f"- {name} ({int(weight*100)}%): {traits}.")

        summary_parts.append("\nCommunication Style:")
        # Take the communication style of the dominant template
        dominant_template_name = sorted_mix[0][0]
        dominant_template = self.library.get_template(dominant_template_name)
        summary_parts.append(dominant_template.communication_style)
        
        if fingerprint_semantics:
            summary_parts.append("\nSpecific Traits:")
            summary_parts.append(", ".join(fingerprint_semantics) + ".")

        return "\n".join(summary_parts)

    def compile_domain_summaries(self, mixture: Dict[str, float]) -> Dict[str, str]:
        """
        Generates domain-specific summaries (Conflict, Humour, etc.)
        """
        sorted_mix = sorted(mixture.items(), key=lambda item: item[1], reverse=True)
        dominant_name = sorted_mix[0][0]
        dominant_template = self.library.get_template(dominant_name)
        
        # Secondary influence (if significant)
        secondary_influence = ""
        if len(sorted_mix) > 1 and sorted_mix[1][1] > 0.2:
            sec_name = sorted_mix[1][0]
            sec_template = self.library.get_template(sec_name)
            secondary_influence = f" with elements of {sec_template.humour_style}" # Example logic

        return {
            "communication": dominant_template.communication_style,
            "conflict": dominant_template.conflict_style,
            "humour": dominant_template.humour_style + secondary_influence
        }
