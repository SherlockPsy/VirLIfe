import json
import os
from typing import Dict, List, Any
from pydantic import BaseModel

class PersonalityTemplate(BaseModel):
    kernel: Dict[str, float]
    semantic_traits: List[str]
    communication_style: str
    conflict_style: str
    humour_style: str

class TemplateLibrary:
    def __init__(self, templates_path: str = "data/templates/base_templates.json"):
        self.templates_path = templates_path
        self.templates: Dict[str, PersonalityTemplate] = {}
        self.load_templates()

    def load_templates(self):
        if not os.path.exists(self.templates_path):
            raise FileNotFoundError(f"Templates file not found at {self.templates_path}")
        
        with open(self.templates_path, 'r') as f:
            data = json.load(f)
            
        for name, content in data.items():
            self.templates[name] = PersonalityTemplate(**content)

    def get_template(self, name: str) -> PersonalityTemplate:
        if name not in self.templates:
            raise ValueError(f"Template '{name}' not found in library.")
        return self.templates[name]

    def list_templates(self) -> List[str]:
        return list(self.templates.keys())
