"""
Data mapping functions for converting raw data files to structured objects.

This module implements deterministic mapping functions as specified in Section A
of the blueprint. These functions prepare structured objects for seeding the database,
but do NOT write to the database directly.
"""

from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import json
import re
from datetime import datetime

from .mapper_helpers import (
    parse_archetypes_from_personalities_file,
    load_fingerprint_json,
    load_master_profile_csv,
    load_connections_csv,
    load_baseline_txt,
    load_george_profile_txt,
    compute_archetype_blend,
    map_closeness_sentiment_to_relationship_vector
)


# Constants for data source paths
DATA_SOURCES_DIR = Path(__file__).parent.parent / "data_sources"

PERSONALITIES_FILE = DATA_SOURCES_DIR / "Personalities.txt"
FINGERPRINT_FILE = DATA_SOURCES_DIR / "Rebecca_Fingerprint.json"
MASTER_PROFILE_FILE = DATA_SOURCES_DIR / "Rebecca Master Profile .csv"
CONNECTIONS_FILE = DATA_SOURCES_DIR / "Rebecca Ferguson - Connections.csv"
BASELINE_FILE = DATA_SOURCES_DIR / "Sim Baseline.txt"
GEORGE_PROFILE_FILE = DATA_SOURCES_DIR / "George_Profile.txt"


def map_archetypes() -> List[Dict[str, Any]]:
    """
    Parse Personalities.txt and return all 15 archetypes in canonical structure.
    
    Returns:
        List of archetype dicts with canonical structure.
    """
    return parse_archetypes_from_personalities_file(PERSONALITIES_FILE)


def map_rebecca_fingerprint_to_personality_kernel(
    fingerprint: Optional[Dict[str, Any]] = None,
    archetypes: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """
    Map Rebecca_Fingerprint.json to personality_kernel structure.
    
    The personality_kernel must contain:
    - trait_dimensions: dict of dimension_name -> value
    - core_motivations: list of strings
    - core_fears: list of strings
    - internal_conflicts: list of strings
    - archetype_blend: dict of archetype_name -> percentage
    
    Args:
        fingerprint: Loaded fingerprint JSON (if None, loads from file)
        archetypes: List of parsed archetypes (if None, loads from file)
    
    Returns:
        personality_kernel dict ready for agents.personality_kernel field
    """
    if fingerprint is None:
        fingerprint = load_fingerprint_json(FINGERPRINT_FILE)
    
    if archetypes is None:
        archetypes = map_archetypes()
    
    kernel = {
        "trait_dimensions": {},
        "core_motivations": [],
        "core_fears": [],
        "internal_conflicts": [],
        "archetype_blend": {}
    }
    
    # Extract trait dimensions from fingerprint engines
    # The fingerprint has an "engines" dict with various engines
    if "engines" in fingerprint:
        for engine_id, engine_data in fingerprint["engines"].items():
            if isinstance(engine_data, dict):
                # Extract bias as a trait dimension
                if "bias" in engine_data:
                    kernel["trait_dimensions"][f"engine_{engine_id}_bias"] = engine_data["bias"]
                if "volatility" in engine_data:
                    kernel["trait_dimensions"][f"engine_{engine_id}_volatility"] = engine_data["volatility"]
    
    # Extract maslow initial_priors as trait dimensions
    if "maslow" in fingerprint and "initial_priors" in fingerprint["maslow"]:
        for level, value in fingerprint["maslow"]["initial_priors"].items():
            kernel["trait_dimensions"][f"maslow_{level}"] = value
    
    # Compute archetype blend
    kernel["archetype_blend"] = compute_archetype_blend(fingerprint, archetypes)
    
    # Extract motivations and fears from master profile (will be done separately)
    # For now, leave empty - will be populated by map_rebecca_personality_summaries
    
    return kernel


def map_rebecca_personality_summaries(
    fingerprint: Optional[Dict[str, Any]] = None,
    master_profile: Optional[List[Dict[str, str]]] = None
) -> Dict[str, str]:
    """
    Map Rebecca Master Profile.csv + Fingerprint to personality_summaries.
    
    Returns:
        Dict with keys: self_view, love_style, career_style, conflict_style,
        public_image, private_self
        
    Each value is a 4-8 sentence summary extracted from the CSV.
    """
    if master_profile is None:
        master_profile = load_master_profile_csv(MASTER_PROFILE_FILE)
    
    summaries = {
        "self_view": "",
        "love_style": "",
        "career_style": "",
        "conflict_style": "",
        "public_image": "",
        "private_self": ""
    }
    
    # Group CSV entries by relevant categories
    self_view_entries = []
    love_entries = []
    career_entries = []
    conflict_entries = []
    public_image_entries = []
    private_self_entries = []
    
    for row in master_profile:
        entry_type = row.get("Type", "").lower()
        subtype = row.get("Subtype/Category", "").lower()
        entry = row.get("Entry (verbatim)", "")
        
        if not entry:
            continue
        
        # Map to summary categories
        if entry_type == "trait" or subtype == "personality":
            self_view_entries.append(entry)
        
        if subtype == "career" or "work" in subtype or "acting" in subtype:
            career_entries.append(entry)
            public_image_entries.append(entry)
        
        if "romance" in subtype or "relationship" in subtype:
            love_entries.append(entry)
            private_self_entries.append(entry)
        
        if "conflict" in subtype or "confrontation" in subtype:
            conflict_entries.append(entry)
        
        if "fame" in subtype or "public" in subtype:
            public_image_entries.append(entry)
        
        if "family" in subtype or "private" in subtype or "personal" in subtype:
            private_self_entries.append(entry)
    
    # Compress entries into summaries (4-8 sentences each)
    summaries["self_view"] = _compress_entries_to_summary(self_view_entries, max_sentences=6)
    summaries["love_style"] = _compress_entries_to_summary(love_entries, max_sentences=6)
    summaries["career_style"] = _compress_entries_to_summary(career_entries, max_sentences=6)
    summaries["conflict_style"] = _compress_entries_to_summary(conflict_entries, max_sentences=5)
    summaries["public_image"] = _compress_entries_to_summary(public_image_entries, max_sentences=6)
    summaries["private_self"] = _compress_entries_to_summary(private_self_entries, max_sentences=6)
    
    return summaries


def map_rebecca_drives(
    fingerprint: Optional[Dict[str, Any]] = None,
    archetypes: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Dict[str, float]]:
    """
    Map fingerprint + archetypes to drives structure.
    
    Returns:
        Dict with keys: attachment, autonomy, achievement, creativity, recognition,
        privacy, security, novelty
        
        Each value is: {"baseline": float, "sensitivity": float}
        
        All values in [0.0, 1.0] range.
    """
    if fingerprint is None:
        fingerprint = load_fingerprint_json(FINGERPRINT_FILE)
    
    drives = {
        "attachment": {"baseline": 0.5, "sensitivity": 0.5},
        "autonomy": {"baseline": 0.5, "sensitivity": 0.5},
        "achievement": {"baseline": 0.5, "sensitivity": 0.5},
        "creativity": {"baseline": 0.5, "sensitivity": 0.5},
        "recognition": {"baseline": 0.5, "sensitivity": 0.5},
        "privacy": {"baseline": 0.5, "sensitivity": 0.5},
        "security": {"baseline": 0.5, "sensitivity": 0.5},
        "novelty": {"baseline": 0.5, "sensitivity": 0.5}
    }
    
    # Extract from maslow initial_priors for baseline values
    if "maslow" in fingerprint and "initial_priors" in fingerprint["maslow"]:
        priors = fingerprint["maslow"]["initial_priors"]
        
        # Map maslow levels to drives
        # P (Physical) -> security
        # S (Safety) -> security
        # B (Belonging) -> attachment
        # E (Esteem) -> recognition, achievement
        # A (Self-actualization) -> creativity, autonomy
        
        if "B" in priors:
            drives["attachment"]["baseline"] = priors["B"]
        if "E" in priors:
            drives["recognition"]["baseline"] = priors["E"]
            drives["achievement"]["baseline"] = priors["E"]
        if "A" in priors:
            drives["creativity"]["baseline"] = priors["A"]
            drives["autonomy"]["baseline"] = priors["A"]
        if "S" in priors:
            drives["security"]["baseline"] = priors["S"]
    
    # Extract from engines for sensitivity
    if "engines" in fingerprint:
        # Use volatility values as sensitivity proxies
        volatility_values = [e.get("volatility", 0.5) for e in fingerprint["engines"].values() if isinstance(e, dict)]
        if volatility_values:
            avg_volatility = sum(volatility_values) / len(volatility_values)
            # Map volatility to sensitivity (higher volatility = higher sensitivity)
            for drive_name in drives:
                drives[drive_name]["sensitivity"] = avg_volatility
    
    return drives


def map_rebecca_mood(
    fingerprint: Optional[Dict[str, Any]] = None
) -> Dict[str, float]:
    """
    Map fingerprint to mood structure.
    
    Returns:
        Dict with keys: baseline_valence, baseline_arousal, anxiety_prone,
        frustration_prone, optimism_tendency
        
        All values in [0.0, 1.0] range (or [-1.0, 1.0] for valence).
    """
    if fingerprint is None:
        fingerprint = load_fingerprint_json(FINGERPRINT_FILE)
    
    mood = {
        "baseline_valence": 0.0,
        "baseline_arousal": 0.5,
        "anxiety_prone": 0.0,
        "frustration_prone": 0.0,
        "optimism_tendency": 0.5
    }
    
    # Extract from affect engine if present
    if "engines" in fingerprint:
        for engine_id, engine_data in fingerprint["engines"].items():
            if isinstance(engine_data, dict) and engine_data.get("family") == "affect":
                # Use bias as valence indicator
                bias = engine_data.get("bias", 0.0)
                mood["baseline_valence"] = bias  # May need to normalize
                # Use volatility as arousal indicator
                volatility = engine_data.get("volatility", 0.5)
                mood["baseline_arousal"] = volatility
    
    return mood


def map_rebecca_domain_summaries(
    master_profile: Optional[List[Dict[str, str]]] = None
) -> Dict[str, str]:
    """
    Map master profile CSV to domain_summaries.
    
    Returns:
        Dict with keys: career, family, romance, friends, fame_and_public_life,
        creativity, health_and_body
        
    Each value is a compressed paragraph of factual content (not summary).
    """
    if master_profile is None:
        master_profile = load_master_profile_csv(MASTER_PROFILE_FILE)
    
    domains = {
        "career": [],
        "family": [],
        "romance": [],
        "friends": [],
        "fame_and_public_life": [],
        "creativity": [],
        "health_and_body": []
    }
    
    # Group entries by domain
    for row in master_profile:
        entry = row.get("Entry (verbatim)", "")
        subtype = row.get("Subtype/Category", "").lower()
        category = row.get("Category", "").lower()
        
        if not entry:
            continue
        
        # Map to domains
        if "career" in subtype or "work" in subtype or "acting" in subtype or category == "work":
            domains["career"].append(entry)
        
        if "family" in subtype or "mother" in subtype or "father" in subtype or "son" in subtype or "daughter" in subtype:
            domains["family"].append(entry)
        
        if "romance" in subtype or "relationship" in subtype or "love" in subtype:
            domains["romance"].append(entry)
        
        if "friend" in subtype or "social" in subtype:
            domains["friends"].append(entry)
        
        if "fame" in subtype or "public" in subtype or "celebrity" in subtype:
            domains["fame_and_public_life"].append(entry)
        
        if "creativity" in subtype or "art" in subtype or "music" in subtype:
            domains["creativity"].append(entry)
        
        if "health" in subtype or "body" in subtype or "physical" in subtype:
            domains["health_and_body"].append(entry)
    
    # Compress each domain into structured paragraph
    result = {}
    for domain_name, entries in domains.items():
        result[domain_name] = _compress_entries_to_paragraph(entries)
    
    return result


def map_rebecca_status_flags(
    baseline: Optional[str] = None,
    master_profile: Optional[List[Dict[str, str]]] = None
) -> Dict[str, Any]:
    """
    Map baseline doc + profile to status_flags.
    
    Returns:
        Dict with keys: is_celebrity, is_partner_of_george, relationship_status,
        lives_with_george, relationship_is_public, etc.
    """
    flags = {
        "is_celebrity": True,  # Rebecca is a celebrity actress
        "is_partner_of_george": True,
        "relationship_status": "exclusive",
        "lives_with_george": True,
        "relationship_is_public": False  # From baseline: "We have kept our relationship a secret so far"
    }
    
    if baseline is None:
        baseline = load_baseline_txt(BASELINE_FILE)
    
    baseline_lower = baseline.lower()
    
    # Extract flags from baseline
    if "monogamous" in baseline_lower and "exclusive" in baseline_lower:
        flags["relationship_status"] = "exclusive"
    
    if "moved in" in baseline_lower or "live together" in baseline_lower:
        flags["lives_with_george"] = True
    
    if "kept our relationship a secret" in baseline_lower or "not public" in baseline_lower:
        flags["relationship_is_public"] = False
    
    return flags


def map_connections_to_relationships(
    connections: Optional[List[Dict[str, str]]] = None
) -> List[Dict[str, Any]]:
    """
    Map Connections CSV to relationship structures.
    
    Returns:
        List of relationship dicts, each with:
        - target_name: str
        - category: str
        - relationship_vector: dict with warmth, trust, attraction, familiarity,
          tension, volatility, comfort (all floats in [0.0, 1.0])
    """
    if connections is None:
        connections = load_connections_csv(CONNECTIONS_FILE)
    
    relationships = []
    
    for row in connections:
        target_name = row.get("Name", "").strip()
        if not target_name:
            continue
        
        category = row.get("Category", "").strip()
        closeness_sentiment = row.get("Closeness/Sentiment", "").strip()
        
        # Map closeness/sentiment to relationship vector
        relationship_vector = map_closeness_sentiment_to_relationship_vector(closeness_sentiment)
        
        relationships.append({
            "target_name": target_name,
            "category": category,
            "relationship_vector": relationship_vector,
            "context": row.get("Relationship/Context", "").strip(),
            "project": row.get("Project/Link", "").strip()
        })
    
    return relationships


def map_baseline_to_locations(
    baseline: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Extract locations from Sim Baseline.txt.
    
    Returns:
        List of location dicts, each with:
        - name: str
        - description: str
        - floor: str (ground/first/outside)
        - adjacency: list of location names (adjacent to this location)
    """
    if baseline is None:
        baseline = load_baseline_txt(BASELINE_FILE)
    
    locations = []
    
    # Parse baseline to extract house layout
    # Ground Floor locations
    ground_floor = [
        {"name": "Kitchen", "description": "Kitchen with dining area", "floor": "ground"},
        {"name": "Small Toilet", "description": "Small toilet under the steps", "floor": "ground"},
        {"name": "Lounge", "description": "Lounge room", "floor": "ground"},
        {"name": "Hallway", "description": "Ground floor hallway", "floor": "ground"},
        {"name": "Entryway", "description": "Front entryway", "floor": "ground"}
    ]
    
    # First Floor locations
    first_floor = [
        {"name": "Our Bedroom", "description": "Main bedroom", "floor": "first"},
        {"name": "Rebecca's Office", "description": "Room converted from George's office to be Rebecca's office for work and reading, also used as sanctuary", "floor": "first"},
        {"name": "Studio", "description": "Studio with guitars, music gear, and recording equipment, also used as George's office", "floor": "first"},
        {"name": "Lucy's Room", "description": "Lucy's room for whenever she comes to stay", "floor": "first"},
        {"name": "Bathroom", "description": "Bathroom with both bathtub and separate shower", "floor": "first"},
        {"name": "Attic", "description": "Attic space", "floor": "first"},
        {"name": "Hallway First Floor", "description": "First floor hallway", "floor": "first"}
    ]
    
    # Outside locations
    outside = [
        {"name": "Front Garden", "description": "Garden in the front", "floor": "outside"},
        {"name": "Side Garden", "description": "Garden at the side", "floor": "outside"},
        {"name": "Back Garden", "description": "Garden at the back with decking for eating, sitting, and spending time", "floor": "outside"},
        {"name": "Double Garage", "description": "Double garage", "floor": "outside"},
        {"name": "Driveway", "description": "Driveway", "floor": "outside"}
    ]
    
    all_locations = ground_floor + first_floor + outside
    
    # Set adjacency relationships
    # Ground floor adjacencies
    location_map = {loc["name"]: loc for loc in all_locations}
    
    location_map["Kitchen"]["adjacency"] = ["Hallway", "Small Toilet"]
    location_map["Lounge"]["adjacency"] = ["Hallway"]
    location_map["Hallway"]["adjacency"] = ["Kitchen", "Lounge", "Entryway", "Small Toilet"]
    location_map["Entryway"]["adjacency"] = ["Hallway", "Front Garden"]
    location_map["Small Toilet"]["adjacency"] = ["Hallway"]
    
    # First floor adjacencies
    location_map["Our Bedroom"]["adjacency"] = ["Hallway First Floor"]
    location_map["Rebecca's Office"]["adjacency"] = ["Hallway First Floor"]
    location_map["Studio"]["adjacency"] = ["Hallway First Floor"]
    location_map["Lucy's Room"]["adjacency"] = ["Hallway First Floor"]
    location_map["Bathroom"]["adjacency"] = ["Hallway First Floor"]
    location_map["Attic"]["adjacency"] = ["Hallway First Floor"]
    location_map["Hallway First Floor"]["adjacency"] = ["Our Bedroom", "Rebecca's Office", "Studio", "Lucy's Room", "Bathroom", "Attic"]
    
    # Outside adjacencies
    location_map["Front Garden"]["adjacency"] = ["Entryway"]
    location_map["Side Garden"]["adjacency"] = []
    location_map["Back Garden"]["adjacency"] = ["Double Garage"]
    location_map["Double Garage"]["adjacency"] = ["Back Garden", "Driveway"]
    location_map["Driveway"]["adjacency"] = ["Double Garage", "Front Garden"]
    
    return all_locations


def map_baseline_to_objects(
    baseline: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Extract significant objects from Sim Baseline.txt.
    
    Returns:
        List of object dicts, each with:
        - name: str
        - description: str
        - location_name: str (location where object is located)
    """
    if baseline is None:
        baseline = load_baseline_txt(BASELINE_FILE)
    
    objects = []
    
    # Extract objects mentioned in baseline
    baseline_lower = baseline.lower()
    
    # Studio objects
    if "guitars" in baseline_lower or "music gear" in baseline_lower or "recording equipment" in baseline_lower:
        objects.append({
            "name": "Guitars",
            "description": "George's guitars",
            "location_name": "Studio"
        })
        objects.append({
            "name": "Music Gear",
            "description": "Music equipment",
            "location_name": "Studio"
        })
        objects.append({
            "name": "Recording Equipment",
            "description": "Recording studio equipment",
            "location_name": "Studio"
        })
    
    # Decking in back garden
    if "decking" in baseline_lower:
        objects.append({
            "name": "Decking",
            "description": "Decking used for eating, sitting, and spending time",
            "location_name": "Back Garden"
        })
    
    return objects


def map_george_profile() -> Dict[str, Any]:
    """
    Map George_Profile.txt to George agent structure (external-only data).
    
    Returns:
        Dict with external/public information about George:
        - name: str
        - age: int
        - height: str
        - weight: str
        - profession: str
        - education: list of str
        - hobbies: list of str
        - public_profile: dict
        
    NOTE: This does NOT include any internal psychological state.
    """
    profile_text = load_george_profile_txt(GEORGE_PROFILE_FILE)
    
    george_data = {
        "name": "George",
        "age": 53,
        "height": "166cm",
        "weight": "90kg",
        "profession": "VP of SaaS and AI strategy at a software company",
        "education": [
            "BA(Hons) in Multimedia",
            "MSc in Music Technology",
            "MBA",
            "ITIL Expert's diploma",
            "Diploma in Communications"
        ],
        "hobbies": [
            "Playing guitar and composing music",
            "Playing chess",
            "Gigging with band mates (blues and classic rock)"
        ],
        "public_profile": {
            "profession": "VP of SaaS and AI strategy at a software company",
            "hobbies": "Guitar, composing music, chess",
            "musical_influences": ["Mark Knopfler", "BB King"]
        }
    }
    
    return george_data


# Helper functions

def _compress_entries_to_summary(entries: List[str], max_sentences: int = 6) -> str:
    """Compress list of entries into a summary of max_sentences sentences."""
    if not entries:
        return ""
    
    # Join entries and split into sentences
    text = " ".join(entries)
    sentences = re.split(r'[.!?]+\s+', text)
    sentences = [s.strip() for s in sentences if s.strip()]
    
    # Take first max_sentences sentences
    selected = sentences[:max_sentences]
    summary = ". ".join(selected)
    if summary and not summary.endswith(('.', '!', '?')):
        summary += "."
    
    return summary


def _compress_entries_to_paragraph(entries: List[str]) -> str:
    """Compress list of entries into a structured paragraph (factual content, not summary)."""
    if not entries:
        return ""
    
    # Join entries with spaces
    return " ".join(entries)


def map_memories_for_rebecca(
    master_profile: Optional[List[Dict[str, str]]] = None,
    baseline: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Map master profile CSV + baseline to memories for Rebecca.
    
    Returns:
        List of memory dicts, each with:
        - type: "biographical" or "episodic"
        - content: str
        - tags: list of str
        - salience: float (0.0-1.0)
        - time_reference: Optional[str] (nullable)
    """
    if master_profile is None:
        master_profile = load_master_profile_csv(MASTER_PROFILE_FILE)
    
    if baseline is None:
        baseline = load_baseline_txt(BASELINE_FILE)
    
    memories = []
    
    # Extract biographical memories from master profile
    for row in master_profile:
        entry_type = row.get("Type", "").lower()
        entry = row.get("Entry (verbatim)", "")
        subtype = row.get("Subtype/Category", "").lower()
        
        if not entry:
            continue
        
        # Determine memory type
        memory_type = "biographical"
        if entry_type == "fact" and "career" in subtype:
            # Career milestones are biographical
            memory_type = "biographical"
        
        # Determine salience based on importance
        salience = 0.5  # Default
        if "breakthrough" in subtype or "award" in subtype or "milestone" in subtype:
            salience = 0.8
        elif "major" in subtype or "important" in subtype:
            salience = 0.7
        elif entry_type == "fact":
            salience = 0.6
        
        # Extract tags from subtype and category
        tags = []
        if "career" in subtype:
            tags.append("career")
        if "family" in subtype:
            tags.append("family")
        if "romance" in subtype or "relationship" in subtype:
            tags.append("romance")
        if "fame" in subtype or "public" in subtype:
            tags.append("fame")
        
        # Extract time reference if available
        time_reference = None
        if "year" in entry.lower():
            year_match = re.search(r'(\d{4})', entry)
            if year_match:
                time_reference = year_match.group(1)
        
        memories.append({
            "type": memory_type,
            "content": entry,
            "tags": tags,
            "salience": salience,
            "time_reference": time_reference
        })
    
    # Extract episodic memories from baseline (e.g., meeting George)
    baseline_lower = baseline.lower()
    if "greatest showman" in baseline_lower or "white dress" in baseline_lower:
        memories.append({
            "type": "episodic",
            "content": "Seeing Rebecca in The Greatest Showman wearing a white dress and singing, which transformed me as a person and made me believe in beauty and love again",
            "tags": ["romance", "turning_point", "george"],
            "salience": 0.95,
            "time_reference": "8 years ago"
        })
    
    if "richmond" in baseline_lower or "restaurant" in baseline_lower or "wine" in baseline_lower:
        memories.append({
            "type": "episodic",
            "content": "Meeting Rebecca in a restaurant in Richmond where I accidentally knocked her chair and spilled wine all over her, which was the starting point for us getting together",
            "tags": ["romance", "meeting", "george"],
            "salience": 0.9,
            "time_reference": None
        })
    
    return memories


def map_arcs_for_rebecca(
    master_profile: Optional[List[Dict[str, str]]] = None,
    baseline: Optional[str] = None,
    fingerprint: Optional[Dict[str, Any]] = None
) -> List[Dict[str, Any]]:
    """
    Map master profile + baseline + fingerprint to arcs for Rebecca.
    
    Returns:
        List of arc dicts, each with:
        - name: str
        - description: str
        - status: "active"
        - importance: float (0.0-1.0)
        - arc_state: dict with core_tension, desired_outcomes, fears, progress
    """
    arcs = []
    
    if baseline is None:
        baseline = load_baseline_txt(BASELINE_FILE)
    
    baseline_lower = baseline.lower()
    
    # Arc 1: Fame/Private-life tension
    arcs.append({
        "name": "Fame and Private Life Balance",
        "description": "Tension between public celebrity persona and private personal life",
        "status": "active",
        "importance": 0.8,
        "arc_state": {
            "core_tension": "Balancing public visibility with private authenticity",
            "desired_outcomes": [
                "Maintain authentic self while navigating celebrity demands",
                "Protect private relationships from public scrutiny"
            ],
            "fears": [
                "Loss of privacy",
                "Misrepresentation in media",
                "Impact on personal relationships"
            ],
            "progress": 0.5
        }
    })
    
    # Arc 2: Relationship secrecy vs going public
    if "secret" in baseline_lower and "reveal" in baseline_lower:
        arcs.append({
            "name": "Relationship Secrecy vs Going Public",
            "description": "Decision about revealing relationship with George publicly",
            "status": "active",
            "importance": 0.9,
            "arc_state": {
                "core_tension": "Want to stop limiting freedom but concerned about public reaction",
                "desired_outcomes": [
                    "Reveal relationship publicly",
                    "Maintain relationship quality",
                    "Reduce limitations on freedom"
                ],
                "fears": [
                    "Negative public reaction",
                    "Impact on career",
                    "Loss of privacy"
                ],
                "progress": 0.7  # "We are very close in deciding to reveal it"
            }
        })
    
    # Arc 3: Career evolution
    arcs.append({
        "name": "Career Evolution",
        "description": "Ongoing development as an actress and artist",
        "status": "active",
        "importance": 0.7,
        "arc_state": {
            "core_tension": "Balancing creative fulfillment with career opportunities",
            "desired_outcomes": [
                "Continue growing as an artist",
                "Take on meaningful roles",
                "Maintain creative integrity"
            ],
            "fears": [
                "Typecasting",
                "Loss of creative control"
            ],
            "progress": 0.6
        }
    })
    
    # Arc 4: Personal emotional evolution
    arcs.append({
        "name": "Personal Emotional Evolution",
        "description": "Ongoing personal growth and emotional development",
        "status": "active",
        "importance": 0.6,
        "arc_state": {
            "core_tension": "Growing into deeper authenticity and emotional connection",
            "desired_outcomes": [
                "Deeper emotional connections",
                "Personal authenticity",
                "Emotional stability"
            ],
            "fears": [
                "Emotional vulnerability",
                "Loss of independence"
            ],
            "progress": 0.5
        }
    })
    
    return arcs


def map_influence_fields_for_rebecca(
    arcs: Optional[List[Dict[str, Any]]] = None,
    fingerprint: Optional[Dict[str, Any]] = None,
    baseline: Optional[str] = None
) -> Dict[str, Any]:
    """
    Map arcs + fingerprint + baseline to influence fields for Rebecca.
    
    Returns:
        Dict with structure:
        - unresolved_topics: dict mapping topic names to {pressure, tags, last_updated}
        - background_bias: dict with warmth_bias, avoidance_bias, assertiveness_bias, etc.
    """
    if arcs is None:
        arcs = map_arcs_for_rebecca()
    
    if fingerprint is None:
        fingerprint = load_fingerprint_json(FINGERPRINT_FILE)
    
    if baseline is None:
        baseline = load_baseline_txt(BASELINE_FILE)
    
    influence_field = {
        "unresolved_topics": {},
        "background_bias": {}
    }
    
    # Extract unresolved topics from arcs
    for arc in arcs:
        arc_name = arc["name"]
        # Create topics from arc tensions
        if "secrecy" in arc_name.lower() or "public" in arc_name.lower():
            influence_field["unresolved_topics"]["relationship_privacy"] = {
                "pressure": 0.8,
                "tags": ["romance", "privacy", "public"],
                "last_updated": None  # Will be set during seeding
            }
        
        if "fame" in arc_name.lower():
            influence_field["unresolved_topics"]["public_private_balance"] = {
                "pressure": 0.6,
                "tags": ["fame", "privacy", "career"],
                "last_updated": None
            }
    
    # Extract background bias from fingerprint
    if "engines" in fingerprint:
        # Use volatility values as bias indicators
        volatility_values = [e.get("volatility", 0.5) for e in fingerprint["engines"].values() if isinstance(e, dict)]
        if volatility_values:
            avg_volatility = sum(volatility_values) / len(volatility_values)
            influence_field["background_bias"]["warmth_bias"] = 0.7  # Default based on personality
            influence_field["background_bias"]["avoidance_bias"] = 1.0 - avg_volatility
            influence_field["background_bias"]["assertiveness_bias"] = avg_volatility
    
    # Add unresolved topic from baseline (secrecy vs going public)
    baseline_lower = baseline.lower()
    if "very close in deciding to reveal" in baseline_lower:
        influence_field["unresolved_topics"]["going_public_decision"] = {
            "pressure": 0.9,
            "tags": ["romance", "privacy", "decision"],
            "last_updated": None
        }
    
    return influence_field


def map_calendar_entries_for_rebecca() -> List[Dict[str, Any]]:
    """
    Map baseline + profile to calendar entries for Rebecca.
    
    Returns:
        List of calendar entry dicts, each with:
        - title: str
        - description: Optional[str]
        - start_time: Optional[datetime] (nullable for now, will be set during seeding)
        - end_time: Optional[datetime] (nullable)
        - recurrence: Optional[str] (RRULE or null)
        - type: str
        - metadata: dict
    """
    # For now, return minimal calendar entries
    # In a full implementation, this would extract specific scheduled events
    # from the master profile and baseline
    
    calendar_entries = [
        {
            "title": "Work routine",
            "description": "Regular work commitments and acting projects",
            "start_time": None,  # Will be set during seeding
            "end_time": None,
            "recurrence": None,  # Could be "FREQ=WEEKLY" etc.
            "type": "routine",
            "metadata": {}
        }
    ]
    
    return calendar_entries

