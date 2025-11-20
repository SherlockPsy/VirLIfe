"""
Phase 9: Prompt Optimization Analysis & Recommendations

Task: Reduce LLM prompt token counts by 30-40% without losing semantic fidelity.

================================================================================
CURRENT CONTEXT SIZES
================================================================================

COGNITION LLM CONTEXT (per cognition_flow.md §4):
┌─────────────────────────────────────────────────────────────────────┐
│ Field                               │ Size Range    │ Reduction Target│
├─────────────────────────────────────────────────────────────────────┤
│ personality_summary                 │ 150-250 tok   │ 150-180 tok     │
│ domain_summaries                    │ 200-300 tok   │ 100-150 tok *   │
│ dynamic_activation_packet           │ 30-80 tok     │ 20-50 tok       │
│ mood_summary                        │ 20-40 tok     │ 15-30 tok       │
│ pressured_drives (top-2)            │ 50-100 tok    │ 40-60 tok       │
│ relevant_relationships (top-3)      │ 80-150 tok    │ 60-100 tok      │
│ active_arcs (top-2)                 │ 60-100 tok    │ 40-60 tok       │
│ energy_summary                      │ 15-30 tok     │ 10-20 tok       │
│ high_priority_intentions (top-3)    │ 60-100 tok    │ 40-60 tok       │
│ relevant_episodic_memories (top-3)  │ 150-250 tok   │ 80-120 tok  *   │
│ relevant_biographical_memories (top-3)│ 150-250 tok │ 80-120 tok  *   │
│ event_context                       │ 50-100 tok    │ 40-60 tok       │
│ calendar_context                    │ 20-50 tok     │ 15-30 tok       │
│ unexpected_event_context            │ 20-50 tok     │ 15-30 tok       │
├─────────────────────────────────────────────────────────────────────┤
│ SYSTEM PROMPT                       │ 300-400 tok   │ 250-300 tok *   │
│ CURRENT TOTAL                       │ 1500-2000 tok │ ~1000-1200 tok  │
└─────────────────────────────────────────────────────────────────────┘
* = High-value optimization targets

RENDERER LLM CONTEXT (per MASTER_SPEC §8):
┌─────────────────────────────────────────────────────────────────────┐
│ Field                               │ Size Range    │ Reduction Target│
├─────────────────────────────────────────────────────────────────────┤
│ perceiver context                   │ 20-50 tok     │ 15-30 tok       │
│ location description                │ 30-50 tok     │ 20-40 tok       │
│ visible_entities                    │ 30-60 tok     │ 25-50 tok       │
│ sensory_snapshot                    │ 50-100 tok    │ 30-60 tok   *   │
│ agent_personalities (top-2)         │ 80-120 tok    │ 50-80 tok   *   │
│ event_description                   │ 30-60 tok     │ 20-40 tok       │
│ perceivable_calendar_context        │ 20-40 tok     │ 15-30 tok       │
│ perceivable_unexpected_event_context│ 20-40 tok     │ 15-30 tok       │
├─────────────────────────────────────────────────────────────────────┤
│ SYSTEM PROMPT                       │ 300-400 tok   │ 200-250 tok *   │
│ CURRENT TOTAL                       │ 650-900 tok   │ ~450-600 tok    │
└─────────────────────────────────────────────────────────────────────┘
* = High-value optimization targets

================================================================================
OPTIMIZATION OPPORTUNITIES
================================================================================

PRIORITY 1: System Prompts (High Value, Low Risk)
────────────────────────────────────────────────────

COGNITION SYSTEM PROMPT OPTIMIZATION:
Current: 300-400 tokens (verbose, multiple examples)
Target: 250-300 tokens (concise, principle-based)

Approach:
1. Remove verbose examples → keep only structure
2. Reduce redundant constraint statements
3. Compress domain descriptions from full sentences → bullet points
4. Consolidate "NEVER" statements into single section

Expected reduction: 50-100 tokens
Implementation: Update RendererSystemPrompt.get_perception_only_system_prompt()
               and add CognitionSystemPrompt.get_cognition_system_prompt()

RENDERER SYSTEM PROMPT OPTIMIZATION:
Current: ~400 tokens
Target: 200-250 tokens

Approach:
1. Consolidate 7-point constraint list → 4 core principles
2. Remove redundant POV explanations (use bullets not paragraphs)
3. Replace verbose "CRITICAL CONSTRAINTS" section with 2-3 core rules
4. Adult content handling: 2 sentences not paragraph

Expected reduction: 150-200 tokens
Implementation: Refactor RendererSystemPrompt

────────────────────────────────────────────────────────

PRIORITY 2: Domain Summaries (Medium Value, Medium Risk)
─────────────────────────────────────────────────────

ISSUE: domain_summaries contains 5-6 domains (emotion, conflict, humor, communication, intimacy, intelligence)
       Each domain can be 40-60 tokens individually
       Total: 200-360 tokens

OPTIMIZATION:
1. Include only domains RELEVANT to current event
   - Speech event? Include: emotion, communication, humor
   - Conflict? Include: emotion, conflict, intelligence
   - Intimacy? Include: emotion, intimacy, communication
   
2. Reduce summary length per domain
   - Current: Full 60-80 word summaries
   - Target: 30-40 word summaries (distilled essence only)
   
3. Optional: Exclude very low-activation domains
   - If "intelligence" domain activation < 0.2, skip entirely
   
Expected reduction: 100-150 tokens (50% of domain context)
Implementation: Add domain_relevance_filter() to CognitionContextBuilder
               Update PersonalityMapper to return shorter summaries

────────────────────────────────────────────────────────

PRIORITY 3: Memory Filtering (Medium Value, Medium Risk)
────────────────────────────────────────────────────────

ISSUE: Passing all top-3 episodic + biographical memories
       Each memory: 40-60 tokens (description + metadata)
       Total for memories: 300-400 tokens

OPTIMIZATION:
1. Reduce episodic memories from top-3 → top-2
   - Include only if relevance_score > 0.6
   - Skip memories older than 100 ticks (less relevant)

2. Reduce biographical memories from top-3 → top-2
   - Focus on memories related to current event target

3. Compress memory descriptions
   - Remove timestamp details (system knows relative recency)
   - Remove internal reasoning (just facts)
   
4. Use Qdrant semantic search (Phase 9) to filter
   - Only return truly relevant memories
   - Threshold: 0.65 similarity
   
Expected reduction: 80-120 tokens (25-30% of memory context)
Implementation: Update CognitionContextBuilder.build_context()
               Use qdrant_service.search_all_memories() with higher threshold

────────────────────────────────────────────────────────

PRIORITY 4: Relationship Context (Low-Medium Value, Medium Risk)
────────────────────────────────────────────────────────────

ISSUE: Passing relationships with full state descriptions
       Each relationship: 50-80 tokens
       Total for top-3: 150-240 tokens

OPTIMIZATION:
1. Reduce from top-3 → top-2 relevant relationships
   - Only include if relationship.warmth or relationship.tension > 0.4

2. Compress relationship descriptions
   - Current: "warmth: high, trust: moderate, tension: low"
   - Target: "warm but cautious" (semantic, not enumerated)
   
3. Omit unchanged relationships
   - If relationship state unchanged since last cognition event, skip
   
Expected reduction: 40-80 tokens (25-30% of relationship context)
Implementation: Update CognitionContextBuilder._map_relationships()

────────────────────────────────────────────────────────

PRIORITY 5: Sensory Snapshot Compression (Low Value, High Risk)
──────────────────────────────────────────────────────────────

⚠️ WARNING: Sensory snapshots must be detailed for renderer quality
           Be conservative with compression here

OPTIMIZATION:
1. Compress only redundant descriptors
   - Remove "the" and "a" articles when possible
   - Use telegraphic style: "warm light" not "a warm, flickering light"

2. Limit visible entities to top-3 (already done typically)

3. Use Qdrant to filter most-relevant entities by perception relevance

Expected reduction: 20-40 tokens (small, but preserve quality)
Implementation: Add snapshot_compression() utility (use carefully)

================================================================================
RECOMMENDED IMPLEMENTATION SEQUENCE
================================================================================

PHASE 1 (Safe, High-Value):
1. Optimize system prompts → -100-200 tokens
2. Add domain relevance filtering → -80-120 tokens
3. Reduce memory context → -80-120 tokens
   → Total: ~260-440 token reduction

PHASE 2 (Moderate, Medium-Value):
4. Compress relationship descriptions → -40-80 tokens
5. Add Qdrant-based memory filtering → -40-80 tokens
   → Total: ~80-160 additional tokens

PHASE 3 (Careful, Lower-Value):
6. Sensory snapshot compression → -20-40 tokens (with quality testing)
   → Total: ~20-40 tokens

EXPECTED FINAL RESULT:
Old: 1500-2000 tokens (cognition) + 650-900 tokens (renderer)
     = 2150-2900 tokens total per tick

New: 1000-1200 tokens (cognition) + 450-600 tokens (renderer)
     = 1450-1800 tokens total per tick

Reduction: 400-1100 tokens per tick (~30-40% ✓)

================================================================================
CODE CHANGES REQUIRED
================================================================================

FILES TO MODIFY:

1. backend/mapping/semantic_mappers.py
   - PersonalityMapper.map_personality() → add optional domain_filter parameter
   - Return shorter domain summaries (target: 30-40 tokens each)
   
2. backend/mapping/cognition_context.py
   - CognitionContextBuilder.build_context() → filter by relevance
   - Add _filter_relevant_domains() method
   - Add _filter_relevant_memories() method (use Qdrant scores)
   - Add _compress_relationships() method

3. backend/renderer/llm_wrapper.py
   - RendererSystemPrompt → reduce from 400 → 200-250 tokens
   - Consolidate constraints to 4 core principles

4. backend/cognition/llm_wrapper.py
   - Add CognitionSystemPrompt class (if doesn't exist)
   - Reduce from 300-400 → 250-300 tokens

5. tests/test_phase9_prompt_optimization.py (NEW)
   - Test that prompt sizes meet targets
   - Test that semantic fidelity is preserved
   - Test that cache hit rates improve

================================================================================
TESTING STRATEGY
================================================================================

For each change:
1. Measure token count before/after (use tiktoken library)
2. Run cognition tests to verify correctness unchanged
3. Run renderer tests to verify quality unchanged
4. Check cache hit rates (should improve slightly)
5. Compare LLM response quality (subjective)

Final validation:
- Run 20-30 tick simulation with profiling
- Measure average tokens/tick (target: <1800)
- Verify no regressions in response quality
- Document results in PHASE9_PROMPT_OPTIMIZATION.md

================================================================================
SAFE FALLBACK
================================================================================

If optimizations cause quality degradation:
1. Revert problematic change
2. Use partial optimization (e.g., domain filter only)
3. Keep original for high-stakes events (critical arcs)
4. Cache optimized versions separately

All changes are backward-compatible (optional filters).

================================================================================
"""

# Reference: Cognition and Renderer system prompts locations
#
# COGNITION:
#   - No dedicated system prompt class yet
#   - Build in: backend/cognition/llm_wrapper.py
#
# RENDERER:
#   - RendererSystemPrompt.get_perception_only_system_prompt()
#   - Location: backend/renderer/llm_wrapper.py
#   - Current size: ~380 tokens (includes 7-point constraint list)

