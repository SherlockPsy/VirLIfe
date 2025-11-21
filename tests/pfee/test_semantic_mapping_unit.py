from backend.pfee.semantic_mapping import PFEESemanticMapper


def test_numeric_state_maps_to_deterministic_semantics():
    mood = {"valence": 0.35, "arousal": 0.65}
    drives = {
        "relatedness": {"level": 0.9, "sensitivity": 1.0},
        "autonomy": {"level": 0.2, "sensitivity": 1.0},
    }
    relationships = {
        "agent:200": {"warmth": 0.85, "trust": 0.8, "tension": 0.1, "comfort": 0.7}
    }

    summary_one = {
        "mood": PFEESemanticMapper.map_mood_to_semantic(mood),
        "drives": PFEESemanticMapper.map_drives_to_semantic(drives),
        "relationships": PFEESemanticMapper.map_relationships_to_semantic(relationships),
    }
    summary_two = {
        "mood": PFEESemanticMapper.map_mood_to_semantic(mood),
        "drives": PFEESemanticMapper.map_drives_to_semantic(drives),
        "relationships": PFEESemanticMapper.map_relationships_to_semantic(relationships),
    }

    assert summary_one == summary_two
    assert isinstance(summary_one["mood"], str)
    assert all("semantic_description" in drive for drive in summary_one["drives"])


def test_semantic_mapping_does_not_expose_raw_numeric_keys():
    drives = {
        "competence": {"level": 0.83, "sensitivity": 0.9},
    }
    arcs = {
        "contract": {"intensity": 0.75, "valence_bias": -0.4, "topic_vector": ["contract"]}
    }
    mood = {"valence": -0.2, "arousal": 0.4}

    semantic_payload = {
        "drives": PFEESemanticMapper.map_drives_to_semantic(drives),
        "arcs": PFEESemanticMapper.map_arcs_to_semantic(arcs),
        "mood": PFEESemanticMapper.map_mood_to_semantic(mood),
        "activation": PFEESemanticMapper.map_personality_activation_to_semantic(
            personality_kernel={},
            personality_activation={
                "stress_modulation": 0.5,
                "arousal_modulation": 0.4,
                "valence_modulation": -0.2,
                "energy_modulation": 0.6,
            },
            mood=mood,
            drives=drives,
            energy=0.6,
            arcs=arcs,
            relationships={},
        ),
    }

    semantic_str = str(semantic_payload)
    assert "level" not in semantic_str
    assert "0.8" not in semantic_str

