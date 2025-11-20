import pytest
from backend.personality.templates import TemplateLibrary
from backend.personality.compiler import PersonalityCompiler
from backend.personality.initialization import CharacterInitializer
from backend.persistence.repo import WorldRepo, UserRepo, AgentRepo
from backend.persistence.models import LocationModel

def test_template_loading():
    lib = TemplateLibrary()
    assert "Nurturer" in lib.list_templates()
    template = lib.get_template("Nurturer")
    assert template.kernel["sociability"] == 0.8

def test_compiler_kernel_mixing():
    lib = TemplateLibrary()
    compiler = PersonalityCompiler(lib)
    
    mixture = {"Nurturer": 0.5, "Thinker": 0.5}
    kernel = compiler.compile_kernel(mixture)
    
    # Nurturer sociability 0.8, Thinker 0.4 -> Avg 0.6
    assert abs(kernel["sociability"] - 0.6) < 0.001
    
    # Test modifiers
    modifiers = {"sociability": 0.1}
    kernel_mod = compiler.compile_kernel(mixture, modifiers)
    assert abs(kernel_mod["sociability"] - 0.7) < 0.001

def test_compiler_summaries():
    lib = TemplateLibrary()
    compiler = PersonalityCompiler(lib)
    
    mixture = {"Nurturer": 0.8, "Thinker": 0.2}
    summary = compiler.compile_stable_summary(mixture, ["loves cats"])
    
    assert "Nurturer" in summary
    assert "loves cats" in summary
    assert "Communication Style" in summary

@pytest.mark.asyncio
async def test_character_initialization(db_session):
    # Setup World & Location
    world_repo = WorldRepo(db_session)
    world = await world_repo.create_world()
    location = LocationModel(name="Home", description="Home", world_id=world.id)
    db_session.add(location)
    await db_session.flush()
    
    # Setup User
    user_repo = UserRepo(db_session)
    user = await user_repo.create_user("George")
    
    # Initialize Character
    initializer = CharacterInitializer(db_session)
    fingerprint_path = "data/fingerprints/rebecca.json"
    
    agent = await initializer.initialize_character(fingerprint_path, world.id, location.id)
    
    assert agent.name == "Rebecca"
    assert agent.personality_kernel["sociability"] > 0 # Should be populated
    assert "Nurturer" in agent.personality_summaries["stable"] # Check for template name instead of agent name
    
    # Check Biography
    agent_repo = AgentRepo(db_session)
    fetched_agent = await agent_repo.get_agent_by_id(agent.id)
    assert len(fetched_agent.memories) > 0
    assert fetched_agent.memories[0].type == "biographical"
    
    # Wire Relationships
    await initializer.wire_initial_relationships(agent.id, fingerprint_path, user.id)
    
    rels = await agent_repo.get_relationships(agent.id)
    assert len(rels) == 1
    assert rels[0].target_user_id == user.id
    assert rels[0].warmth == 0.8
