## NUMERIC → SEMANTIC MAPPING TABLE
### (LLM INTERFACE TEMPLATES • EXAMPLES ARE NON-NORMATIVE)

This document defines the pattern for converting numeric internal state into compact semantic summaries for LLMs.

All numeric → semantic mappings MUST be deterministic and rule-based.

All phrases below are **Examples — NON-NORMATIVE**.  
They illustrate the pattern, they are not enforced strings.  
The implementation can use different but equivalent wordings.


## 1. MOOD (VALENCE × AROUSAL)

| valence range      | arousal range       | Example — NON-NORMATIVE summary                                   |
|--------------------|---------------------|--------------------------------------------------------------------|
| > +0.4             | < 0.4               | "She feels quietly content and at ease."                          |
| > +0.4             | ≥ 0.4               | "She feels upbeat and energised."                                 |
| between -0.2, +0.2 | < 0.3               | "She feels fairly neutral and low-key."                           |
| between -0.2, +0.2 | ≥ 0.3               | "She feels neutral but somewhat alert."                           |
| < -0.4             | < 0.4               | "She feels low and a bit flat."                                   |
| < -0.4             | ≥ 0.4               | "She feels upset and agitated."                                   |

Implementation MUST:
- choose semantic buckets
- ensure each agent gets at most one mood summary phrase at a time


## 2. DRIVES

Drives are stored as unsatisfied levels ∈ [0,1].  
High levels = high unmet need.

### 2.1 Relatedness

| relatedness level      | Example — NON-NORMATIVE summary                                        |
|------------------------|-------------------------------------------------------------------------|
| < 0.3                  | "She feels generally connected and not especially lonely."             |
| 0.3–0.7                | "She would appreciate some closeness or quality time."                 |
| > 0.7                  | "She has been feeling neglected and wants more closeness."             |

### 2.2 Autonomy

| autonomy level         | Example — NON-NORMATIVE summary                                        |
|------------------------|-------------------------------------------------------------------------|
| < 0.3                  | "She feels free to make her own choices."                              |
| 0.3–0.7                | "She is somewhat sensitive about being directed or controlled."        |
| > 0.7                  | "She feels constrained and strongly wants more freedom."               |

### 2.3 Competence

| competence level       | Example — NON-NORMATIVE summary                                        |
|------------------------|-------------------------------------------------------------------------|
| < 0.3                  | "She feels capable and effective."                                     |
| 0.3–0.7                | "She is somewhat unsure about how well she's handling things."         |
| > 0.7                  | "She has been feeling ineffective and doubting herself."               |

### 2.4 Novelty

| novelty level          | Example — NON-NORMATIVE summary                                        |
|------------------------|-------------------------------------------------------------------------|
| < 0.3                  | "She feels stimulated enough; routine is okay right now."              |
| 0.3–0.7                | "She wouldn't mind some change or variety."                            |
| > 0.7                  | "She feels stuck in a rut and craves something different."             |

### 2.5 Safety

| safety level           | Example — NON-NORMATIVE summary                                        |
|------------------------|-------------------------------------------------------------------------|
| < 0.3                  | "She feels generally safe and secure."                                 |
| 0.3–0.7                | "She feels somewhat on edge and cautious."                             |
| > 0.7                  | "She feels unsafe or unsettled and wants things to be predictable."    |


## 3. RELATIONSHIP EDGES (A → B)

### 3.1 Warmth, Trust, Tension — Combined

You MUST derive a small number of qualitative “relationship states” from numeric edges.  
Example pattern:

| warmth       | trust        | tension     | Example — NON-NORMATIVE summary                                          |
|--------------|--------------|-------------|---------------------------------------------------------------------------|
| > 0.5        | > 0.5        | < 0.3       | "She generally feels close and safe with them."                           |
| > 0.3        | between 0, .5| 0.3–0.7     | "She cares but there is some strain and uncertainty."                     |
| > 0          | < 0          | > 0.4       | "She is conflicted: there is some pull toward them but also mistrust."   |
| < 0          | < 0          | > 0.5       | "She mostly feels negative and guarded around them."                      |
| around 0     | around 0     | < 0.2       | "She feels fairly neutral; there's not much emotional investment yet."    |

Attraction and comfort can be described separately if relevant:

- high attraction + high comfort → "She feels physically attracted and at ease with them."
- high attraction + low comfort → "She feels attracted, but also somewhat uneasy."


## 4. ARCS

Arcs have:

- intensity ∈ [0,1]
- valence_bias ∈ [-1,1]
- topic_vector (semantic)

Example mapping:

| intensity    | valence_bias        | Example — NON-NORMATIVE summary                                        |
|--------------|---------------------|-------------------------------------------------------------------------|
| > 0.7        | < -0.3              | "There is a raw, unresolved sore spot around [topic]."                 |
| 0.4–0.7      | < -0.3              | "There is a lingering tension around [topic]."                         |
| > 0.7        | > 0.3               | "There is an ongoing positive emotional thread around [topic]."        |
| 0.4–0.7      | > 0.3               | "They have a gentle, positive theme around [topic]."                   |
| < 0.3        | any                 | "There is only a mild background sensitivity around [topic], if any."  |


## 5. ENERGY

| energy       | Example — NON-NORMATIVE summary                                        |
|--------------|-------------------------------------------------------------------------|
| > 0.7        | "She feels energetic and has capacity to engage."                      |
| 0.3–0.7      | "She feels somewhat tired but still functional."                       |
| < 0.3        | "She feels drained and has little capacity to engage."                 |


## 6. INTENTIONS

Intentions are semantic already (type + priority).  
Mapping to semantic form is straightforward:

Examples — NON-NORMATIVE:

- High-priority intention `avoid_topic_X` → "She is actively trying to avoid talking about [topic]."
- High-priority intention `raise_issue_X` → "She intends to bring up [topic] soon."
- Medium-priority intention `be_supportive_to_Y` → "She is trying to be more supportive toward [Y]."


## 7. BIOGRAPHICAL MEMORY

Biographical facts should be exposed to LLM as plain sentences.

Examples — NON-NORMATIVE:

- "She knows that he went through a rough divorce a few years ago."
- "She knows that he tends to withdraw when overwhelmed."
- "She knows that he strongly values honesty."

These MUST only come from facts or stable patterns derived from observable behaviour or explicit disclosure.


## 8. IMPLEMENTATION REQUIREMENTS

- All mappings MUST be pure functions from numeric state ranges → short text snippets.
- LLM MUST NEVER see the underlying numeric values.
- The exact boundaries and phrasing can be tuned, but the pattern MUST remain:
  - discretize numeric ranges  
  - choose one semantic phrase per dimension (or combination)  
  - feed that to the LLM as part of context.


## 9. PERSONALITY (KERNEL → SEMANTIC SUMMARIES)

Personality is represented internally as a **kernel** (numeric vector) compiled from template mixes and optional fingerprints.  
LLMs MUST NOT see the kernel directly; they see only semantic summaries derived from it.

### 9.1 Stable Personality Summary

Implementation MUST:

- map the personality kernel → a short, stable summary (≈150–250 tokens) capturing:
  - communication style
  - emotional style
  - conflict style
  - connection style
  - regulation tendencies
  - general outlook

Example — NON-NORMATIVE:

- "She tends to think before speaking, dislikes sudden confrontations, and values emotional honesty but finds it hard to initiate difficult conversations."

This summary:

- MUST be cached
- MUST be regenerated only when personality kernel or fingerprint changes
- MUST be included in every cognition/renderer context where the agent is involved

### 9.2 Domain Personality Summaries

Implementation MUST derive smaller domain-specific summaries, e.g.:

- emotion regulation (how they handle strong feelings)
- conflict style (approach, avoid, attack, appease)
- humour style (dry, playful, literal, absurd, etc.)
- communication style (direct vs indirect, verbose vs terse)
- intimacy/sexuality style (adults only; used only by adult-capable renderer)

Each domain summary:

- SHOULD be 50–120 tokens
- MUST be cached and stable
- MAY be conditionally included in LLM prompts depending on context

All example phrasings in these summaries are NON-NORMATIVE; pattern and determinism are normative.

### 9.3 Dynamic Activation Packet

At runtime, personality expression MUST be modulated by current state:

- drives
- mood
- arcs
- relationship edges
- relevant episodic/biographical memory
- energy

Implementation MUST compute a small “activation packet” per cognition event that says how the stable personality is currently tilted.

Example — NON-NORMATIVE:

- "Right now she is more defensive than usual because she feels tired and slightly cornered."

Requirements:

- MUST be derived deterministically from numeric state + kernel
- MUST NOT involve any LLM calls
- SHOULD be limited to ~30–80 tokens
- MUST be included in cognition prompts for that agent

### 9.4 No Direct Personality in LLM Outputs

LLM outputs:

- MUST NOT set or alter the personality kernel directly
- MUST NOT redefine stable traits (“she is now a completely different person”)  
- MAY imply stance shifts and long-term changes, which are then translated into kernel or summary adjustments via deterministic rules outside the LLM

Any permanent personality change:

- MUST be controlled by the Personality Compiler / Autonomy Engine
- MUST NOT be applied directly from raw LLM text