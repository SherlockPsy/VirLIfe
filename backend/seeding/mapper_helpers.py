"""
Helper utilities for data mapping.

This module provides parsing, transformation, and utility functions used by
the data mappers to convert raw data files into structured objects.
"""

import json
import csv
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import re


def parse_archetypes_from_personalities_file(file_path: Path) -> List[Dict[str, Any]]:
    """
    Parse Personalities.txt and extract all 15 archetypes into canonical structure.
    
    Returns:
        List of archetype dicts with keys: name, essence, core_drives, tensions,
        behavioural_colour, variation_spectrum, core_traits, motivations, fears
    """
    archetypes = []
    
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    current_archetype = None
    current_section = None
    i = 0
    
    while i < len(lines):
        line = lines[i].strip()
        
        # Check for archetype header: "1 – The Nurturer"
        match = re.match(r'^(\d+)\s*–\s*(.+)$', line)
        if match:
            # Save previous archetype if exists
            if current_archetype:
                archetypes.append(current_archetype)
            
            # Start new archetype
            num, name = match.groups()
            current_archetype = {
                "number": int(num),
                "name": name.strip(),
                "essence": "",
                "core_drives": [],
                "tensions": "",
                "behavioural_colour": "",
                "variation_spectrum": "",
                "core_traits": [],
                "motivations": [],
                "fears": []
            }
            current_section = None
            i += 1
            continue
        
        # Check for section headers
        if current_archetype:
            if line == "Essence":
                current_section = "essence"
                i += 1
                # Collect essence content until next section or blank line
                essence_lines = []
                while i < len(lines) and lines[i].strip() and not re.match(r'^(Core Drives|Typical Tensions|Behavioural Colour|Variation Spectrum|⸻|\d+\s*–)', lines[i].strip()):
                    essence_lines.append(lines[i].strip())
                    i += 1
                current_archetype["essence"] = " ".join(essence_lines)
                continue
                
            elif line == "Core Drives":
                current_section = "core_drives"
                i += 1
                # Collect drives (separated by ·)
                drives_line = ""
                while i < len(lines) and lines[i].strip() and not re.match(r'^(Typical Tensions|Behavioural Colour|Variation Spectrum|⸻|\d+\s*–)', lines[i].strip()):
                    drives_line += " " + lines[i].strip()
                    i += 1
                # Split by · or newline
                drives = [d.strip() for d in re.split(r'[·\n]+', drives_line) if d.strip()]
                current_archetype["core_drives"] = drives
                current_archetype["motivations"] = drives
                continue
                
            elif line == "Typical Tensions":
                current_section = "tensions"
                i += 1
                tension_lines = []
                while i < len(lines) and lines[i].strip() and not re.match(r'^(Behavioural Colour|Variation Spectrum|⸻|\d+\s*–)', lines[i].strip()):
                    tension_lines.append(lines[i].strip())
                    i += 1
                current_archetype["tensions"] = " ".join(tension_lines)
                # Extract fears from tensions
                tensions_text = current_archetype["tensions"].lower()
                if "fear" in tensions_text:
                    fear_matches = re.findall(r'fears?\s+([^.]+)', current_archetype["tensions"], re.IGNORECASE)
                    current_archetype["fears"] = [f.strip() for f in fear_matches if f.strip()]
                continue
                
            elif line == "Behavioural Colour":
                current_section = "behavioural_colour"
                i += 1
                colour_lines = []
                while i < len(lines) and lines[i].strip() and not re.match(r'^(Variation Spectrum|⸻|\d+\s*–)', lines[i].strip()):
                    colour_lines.append(lines[i].strip())
                    i += 1
                current_archetype["behavioural_colour"] = " ".join(colour_lines)
                continue
                
            elif line == "Variation Spectrum":
                current_section = "variation_spectrum"
                i += 1
                spectrum_lines = []
                while i < len(lines) and lines[i].strip() and not re.match(r'^(⸻|\d+\s*–)', lines[i].strip()):
                    spectrum_lines.append(lines[i].strip())
                    i += 1
                current_archetype["variation_spectrum"] = " ".join(spectrum_lines)
                continue
        
        i += 1
    
    # Don't forget the last archetype
    if current_archetype:
        archetypes.append(current_archetype)
    
    return archetypes


def load_fingerprint_json(file_path: Path) -> Dict[str, Any]:
    """Load and return the fingerprint JSON file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def load_master_profile_csv(file_path: Path) -> List[Dict[str, str]]:
    """Load the master profile CSV and return as list of dicts."""
    rows = []
    with open(file_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    return rows


def load_connections_csv(file_path: Path) -> List[Dict[str, str]]:
    """Load the connections CSV and return as list of dicts."""
    rows = []
    with open(file_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    return rows


def load_baseline_txt(file_path: Path) -> str:
    """Load the baseline text file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()


def load_george_profile_txt(file_path: Path) -> str:
    """Load George's profile text file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()


def compute_archetype_blend(
    fingerprint: Dict[str, Any],
    archetypes: List[Dict[str, Any]]
) -> Dict[str, float]:
    """
    Compute archetype blend by matching fingerprint traits to archetype descriptors.
    
    Uses cosine similarity or nearest-match scoring between fingerprint traits
    and archetype descriptors. Returns a dict mapping archetype names to percentages.
    
    For now, uses a simplified scoring method based on keyword matching and
    fingerprint engine values. In a full implementation, this would use proper
    vector similarity.
    """
    blend = {}
    
    # Extract fingerprint traits/values
    # For now, we'll use a simplified approach based on engines and master_profile
    # In a full implementation, this would analyze trait dimensions more carefully
    
    # Check which archetypes match best based on fingerprint data
    # This is a placeholder - real implementation would compute proper similarity
    for archetype in archetypes:
        score = 0.0
        name_lower = archetype["name"].lower()
        
        # Simple keyword matching based on fingerprint notes and master profile
        # This is a simplification - real implementation would use vector similarity
        if fingerprint.get("notes"):
            notes_lower = fingerprint.get("notes", "").lower()
            if "performer" in name_lower or "rebel" in name_lower:
                if "independence" in notes_lower or "authentic" in notes_lower:
                    score += 0.3
            if "nurturer" in name_lower or "protector" in name_lower:
                if "care" in notes_lower or "loyal" in notes_lower:
                    score += 0.3
        
        blend[archetype["name"]] = min(score, 1.0)
    
    # Normalize to percentages (should sum to 1.0)
    total = sum(blend.values())
    if total > 0:
        blend = {k: v / total for k, v in blend.items()}
    else:
        # Default equal distribution if no matches
        blend = {a["name"]: 1.0 / len(archetypes) for a in archetypes}
    
    return blend


def map_closeness_sentiment_to_relationship_vector(
    closeness_sentiment: str
) -> Dict[str, float]:
    """
    Map a closeness/sentiment string from Connections CSV to relationship vector.
    
    Returns dict with keys: warmth, trust, attraction, familiarity, tension,
    volatility, comfort
    
    All values are in [0.0, 1.0] range.
    """
    text = closeness_sentiment.lower()
    
    # Default neutral values
    vector = {
        "warmth": 0.5,
        "trust": 0.5,
        "attraction": 0.0,
        "familiarity": 0.5,
        "tension": 0.0,
        "volatility": 0.0,
        "comfort": 0.5
    }
    
    # Parse sentiment keywords
    if "close" in text or "deep" in text or "central" in text:
        vector["warmth"] = 0.9
        vector["trust"] = 0.9
        vector["familiarity"] = 0.9
        vector["comfort"] = 0.9
    elif "warm" in text or "affectionate" in text:
        vector["warmth"] = 0.8
        vector["comfort"] = 0.7
    elif "admiration" in text or "respect" in text:
        vector["warmth"] = 0.7
        vector["trust"] = 0.8
    elif "positive" in text or "professional" in text:
        vector["warmth"] = 0.6
        vector["trust"] = 0.6
    elif "neutral" in text:
        vector["warmth"] = 0.5
        vector["trust"] = 0.5
    elif "strained" in text or "complex" in text:
        vector["warmth"] = 0.3
        vector["tension"] = 0.4
        vector["trust"] = 0.4
    
    # Professional relationships
    if "professional" in text:
        vector["attraction"] = 0.0
        vector["familiarity"] = 0.6
    
    # Family relationships
    if "family" in text or "mother" in text or "father" in text or "son" in text or "daughter" in text:
        vector["warmth"] = max(vector["warmth"], 0.8)
        vector["trust"] = max(vector["trust"], 0.8)
        vector["familiarity"] = 0.95
        vector["comfort"] = 0.9
    
    # Clamp all values to [0.0, 1.0]
    for key in vector:
        vector[key] = max(0.0, min(1.0, vector[key]))
    
    return vector

