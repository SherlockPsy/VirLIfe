"""
PFEE Validation Result

Structured result for LLM output validation.
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any


@dataclass
class ValidationResult:
    """Result of LLM output validation against world state."""
    is_valid: bool
    reason: Optional[str] = None
    corrected_output: Optional[Dict[str, Any]] = None
    
    @classmethod
    def valid(cls) -> "ValidationResult":
        """Valid output."""
        return cls(is_valid=True)
    
    @classmethod
    def invalid(cls, reason: str) -> "ValidationResult":
        """Invalid output."""
        return cls(is_valid=False, reason=reason)

