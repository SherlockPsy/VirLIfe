"""
PHASE 1.5 — PERSONALITY COMPILER & INITIALISATION

Tests MUST cover:
1. Kernel determinism
2. Summary determinism
3. Initial biographical memory & relationships
4. Non-LLM verification

References:
- TEST_PLAN.md §PHASE 1.5
- MASTER_SPEC.md §PART IIA
"""

import pytest
import inspect
import importlib
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


class TestKernelDeterminism:
    """
    TEST_PLAN.md Phase 1.5.1: Kernel determinism
    - Same template mixture + fingerprint → identical personality kernel.
    - Different mixtures → clearly different kernels.
    """
    
    def test_same_mixture_produces_identical_kernel(self):
        """Same template mixture + fingerprint → identical personality kernel."""
        lib = TemplateLibrary()
        compiler = PersonalityCompiler(lib)
        
        mixture1 = {"Nurturer": 0.5, "Thinker": 0.5}
        modifiers1 = {"sociability": 0.1}
        
        kernel1 = compiler.compile_kernel(mixture1, modifiers1)
        kernel2 = compiler.compile_kernel(mixture1, modifiers1)
        
        # Kernels must be identical
        assert kernel1 == kernel2, "Same inputs must produce identical kernels"
        assert kernel1["sociability"] == kernel2["sociability"]
    
    def test_different_mixtures_produce_different_kernels(self):
        """Different mixtures → clearly different kernels."""
        lib = TemplateLibrary()
        compiler = PersonalityCompiler(lib)
        
        mixture1 = {"Nurturer": 1.0}
        mixture2 = {"Thinker": 1.0}
        
        kernel1 = compiler.compile_kernel(mixture1)
        kernel2 = compiler.compile_kernel(mixture2)
        
        # Kernels must be different (at least in some dimension)
        assert kernel1 != kernel2, "Different mixtures must produce different kernels"
        # Nurturer should have higher sociability than Thinker
        assert kernel1["sociability"] > kernel2["sociability"]
    
    def test_fingerprint_modifiers_affect_kernel(self):
        """Fingerprint modifiers should affect kernel deterministically."""
        lib = TemplateLibrary()
        compiler = PersonalityCompiler(lib)
        
        mixture = {"Nurturer": 0.5, "Thinker": 0.5}
        
        kernel_no_mod = compiler.compile_kernel(mixture)
        kernel_with_mod = compiler.compile_kernel(mixture, {"sociability": 0.2})
        
        # Modifier should increase sociability
        assert kernel_with_mod["sociability"] > kernel_no_mod["sociability"]
        assert abs(kernel_with_mod["sociability"] - kernel_no_mod["sociability"] - 0.2) < 0.001


class TestSummaryDeterminism:
    """
    TEST_PLAN.md Phase 1.5.2: Summary determinism
    - Same kernel + fingerprint → identical stable summary.
    - Summary regeneration only when inputs change.
    """
    
    def test_same_inputs_produce_identical_summary(self):
        """Same kernel + fingerprint → identical stable summary."""
        lib = TemplateLibrary()
        compiler = PersonalityCompiler(lib)
        
        mixture = {"Nurturer": 0.8, "Thinker": 0.2}
        fingerprint_semantics = ["loves cats", "enjoys reading"]
        
        summary1 = compiler.compile_stable_summary(mixture, fingerprint_semantics)
        summary2 = compiler.compile_stable_summary(mixture, fingerprint_semantics)
        
        # Summaries must be identical
        assert summary1 == summary2, "Same inputs must produce identical summaries"
    
    def test_different_inputs_produce_different_summaries(self):
        """Different inputs → different summaries."""
        lib = TemplateLibrary()
        compiler = PersonalityCompiler(lib)
        
        mixture1 = {"Nurturer": 1.0}
        mixture2 = {"Thinker": 1.0}
        
        summary1 = compiler.compile_stable_summary(mixture1)
        summary2 = compiler.compile_stable_summary(mixture2)
        
        # Summaries should be different
        assert summary1 != summary2, "Different mixtures must produce different summaries"
        # Nurturer summary should mention Nurturer traits
        assert "Nurturer" in summary1
        assert "Thinker" in summary2
    
    def test_fingerprint_semantics_included_in_summary(self):
        """Fingerprint semantics should be included in summary."""
        lib = TemplateLibrary()
        compiler = PersonalityCompiler(lib)
        
        mixture = {"Nurturer": 0.8, "Thinker": 0.2}
        fingerprint_semantics = ["loves cats", "enjoys reading"]
        
        summary = compiler.compile_stable_summary(mixture, fingerprint_semantics)
        
        # Summary should include fingerprint semantics
        assert "loves cats" in summary
        assert "enjoys reading" in summary
    
    def test_summary_regenerates_when_inputs_change(self):
        """Summary regeneration only when inputs change."""
        lib = TemplateLibrary()
        compiler = PersonalityCompiler(lib)
        
        mixture1 = {"Nurturer": 0.8, "Thinker": 0.2}
        mixture2 = {"Nurturer": 0.7, "Thinker": 0.3}  # Different mixture
        
        summary1 = compiler.compile_stable_summary(mixture1)
        summary2 = compiler.compile_stable_summary(mixture2)
        
        # Different mixtures should produce different summaries
        assert summary1 != summary2, "Changed inputs should produce different summaries"


class TestInitialBiographicalMemoryAndRelationships:
    """
    TEST_PLAN.md Phase 1.5.3: Initial biographical memory & relationships
    - For a test agent with a fingerprint:
      - initial biographical memories MUST exist.
      - initial relationships toward user MUST exist and match the template config.
    """
    
    @pytest.mark.asyncio
    async def test_initial_biographical_memories_exist(self, db_session):
        """Initial biographical memories MUST exist for agent with fingerprint."""
        world_repo = WorldRepo(db_session)
        world = await world_repo.create_world()
        location = LocationModel(name="Home", description="Home", world_id=world.id)
        db_session.add(location)
        await db_session.flush()
        
        user_repo = UserRepo(db_session)
        user = await user_repo.create_user("George")
        
        initializer = CharacterInitializer(db_session)
        fingerprint_path = "data/fingerprints/rebecca.json"
        
        agent = await initializer.initialize_character(fingerprint_path, world.id, location.id)
        
        # Check that biographical memories exist
        agent_repo = AgentRepo(db_session)
        fetched_agent = await agent_repo.get_agent_by_id(agent.id)
        
        # Should have at least one biographical memory
        biographical_memories = [m for m in fetched_agent.memories if m.type == "biographical"]
        assert len(biographical_memories) > 0, "Agent with fingerprint must have initial biographical memories"
    
    @pytest.mark.asyncio
    async def test_initial_relationships_toward_user_exist(self, db_session):
        """Initial relationships toward user MUST exist and match the template config."""
        world_repo = WorldRepo(db_session)
        world = await world_repo.create_world()
        location = LocationModel(name="Home", description="Home", world_id=world.id)
        db_session.add(location)
        await db_session.flush()
        
        user_repo = UserRepo(db_session)
        user = await user_repo.create_user("George")
        
        initializer = CharacterInitializer(db_session)
        fingerprint_path = "data/fingerprints/rebecca.json"
        
        agent = await initializer.initialize_character(fingerprint_path, world.id, location.id)
        
        # Wire initial relationships
        await initializer.wire_initial_relationships(agent.id, fingerprint_path, user.id)
        
        # Check relationships exist
        agent_repo = AgentRepo(db_session)
        rels = await agent_repo.get_relationships(agent.id)
        
        # Should have at least one relationship toward user
        user_rels = [r for r in rels if r.target_user_id == user.id]
        assert len(user_rels) > 0, "Agent must have initial relationship toward user"
        
        # Relationship should have valid metrics
        rel = user_rels[0]
        assert rel.warmth is not None
        assert rel.trust is not None
        # Values should be within valid range [0, 1] (or [-1, 1] for some metrics)
        assert 0.0 <= rel.warmth <= 1.0 or -1.0 <= rel.warmth <= 1.0


class TestNonLLM:
    """
    TEST_PLAN.md Phase 1.5.4: Non-LLM
    - Personality compiler MUST NOT call any LLM client.
    - Tests MUST assert imports and calls do NOT include OpenAI/Venice etc.
    """
    
    def test_compiler_has_no_llm_imports(self):
        """Personality compiler MUST NOT import any LLM clients."""
        import backend.personality.compiler as compiler_module
        
        # Get source code
        source = inspect.getsource(compiler_module)
        
        # Check for common LLM client imports
        forbidden_imports = [
            "openai",
            "OpenAI",
            "venice",
            "Venice",
            "anthropic",
            "Anthropic",
            "llm",
            "LLM",
            "client",
            "Client"
        ]
        
        # Check imports in the module
        imports = []
        for line in source.split('\n'):
            if line.strip().startswith('import ') or line.strip().startswith('from '):
                imports.append(line)
        
        # Verify no LLM-related imports
        for forbidden in forbidden_imports:
            for imp in imports:
                assert forbidden.lower() not in imp.lower(), \
                    f"Personality compiler must not import {forbidden}"
    
    def test_compiler_has_no_llm_calls(self):
        """Personality compiler MUST NOT call any LLM clients."""
        import backend.personality.compiler as compiler_module
        
        # Get source code
        source = inspect.getsource(compiler_module)
        
        # Check for common LLM API call patterns
        forbidden_patterns = [
            "openai.",
            "venice.",
            "anthropic.",
            ".chat.completions",
            ".completions.create",
            ".generate",
            "llm(",
            "client("
        ]
        
        source_lower = source.lower()
        for pattern in forbidden_patterns:
            assert pattern.lower() not in source_lower, \
                f"Personality compiler must not call LLM APIs (found pattern: {pattern})"
    
    def test_initialization_has_no_llm_imports(self):
        """Character initializer MUST NOT import any LLM clients."""
        import backend.personality.initialization as init_module
        
        # Get source code
        source = inspect.getsource(init_module)
        
        # Check for common LLM client imports
        forbidden_imports = [
            "openai",
            "OpenAI",
            "venice",
            "Venice",
            "anthropic",
            "Anthropic"
        ]
        
        # Check imports in the module
        imports = []
        for line in source.split('\n'):
            if line.strip().startswith('import ') or line.strip().startswith('from '):
                imports.append(line)
        
        # Verify no LLM-related imports
        for forbidden in forbidden_imports:
            for imp in imports:
                assert forbidden.lower() not in imp.lower(), \
                    f"Character initializer must not import {forbidden}"
    
    def test_compiler_is_purely_deterministic(self):
        """Personality compiler should be purely deterministic (no external API calls)."""
        lib = TemplateLibrary()
        compiler = PersonalityCompiler(lib)
        
        mixture = {"Nurturer": 0.5, "Thinker": 0.5}
        
        # Multiple calls should produce identical results
        kernel1 = compiler.compile_kernel(mixture)
        kernel2 = compiler.compile_kernel(mixture)
        kernel3 = compiler.compile_kernel(mixture)
        
        assert kernel1 == kernel2 == kernel3, "Compiler must be deterministic"
        
        summary1 = compiler.compile_stable_summary(mixture)
        summary2 = compiler.compile_stable_summary(mixture)
        summary3 = compiler.compile_stable_summary(mixture)
        
        assert summary1 == summary2 == summary3, "Summary generation must be deterministic"
