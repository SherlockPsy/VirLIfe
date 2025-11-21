# VIRTUAL WORLD UI SPECIFICATION  
**FULLY INTEGRATED — NON-SUMMARISED — BUILDER-READY — AMBIGUITY-PROOF**  
**TEXT-ONLY, VISUALLY RICH, NEUTRAL, CONTINUOUS, REAL-TIME UI ARCHITECTURE**

=====================================================================
## 0. PURPOSE AND SCOPE
=====================================================================

This document defines the COMPLETE user interface (UI) specification for the Virtual World Client.  
It is written to be read and executed by a Builder LLM (e.g., Cursor, Copilot).  
The UI described here MUST be implemented EXACTLY as written.

The UI is:

- **purely textual**, with no illustrations, avatars, images, or cartoon elements  
- **visually rich** through typography, spacing, layout, and subtle, non-emotional motion  
- **emotionally neutral** — it MUST NOT soften conflict, intensify intimacy, or bias emotional meaning  
- **scene-continuous** — all experiences occur on one timeline, like real life  
- **fully interactive** — intimacy, conflict, jokes, mundane events, all treated as equal “lived moments”  
- **long-session friendly** — able to be used for 5–10 hours a day without fatigue  
- **high-clarity** — speaker identification MUST always be unambiguous  
- **high-fidelity** — no summarisation, no censorship beyond what the backend enforces  
- **therapeutically neutral** — realism MUST NOT be distorted in any direction  

This document integrates and supersedes:

- Your original UI.md  
- Your intimacy rules  
- The neutrality, realism, therapeutic, and continuity rules we agreed on  
- Scene flow, interaction density, concurrency, multi-character logic  
- TTS behaviour and conflict resolution  
- Phone overlay interaction  
- Requirements for perceivable events  
- Requirements for long-message intimate interactions (3 messages or 250 messages)  
- Requirements for keeping everything "just life" with no special modes  
- All backend and renderer constraints  
- All improvements proposed in analysis  

This is the **single source of truth** for the UI.

No omissions. No implicit assumptions. No examples as rules.  
Anything the builder LLM needs is defined explicitly here.

=====================================================================
## 1. INTERPRETATION RULES FOR BUILDER LLM
=====================================================================

### 1.1 Normative Language
Any sentence containing **MUST**, **MUST NOT**, **SHALL**, **SHALL NOT**, **IS REQUIRED**, or **IS PROHIBITED** is a binding requirement and MUST be implemented literally.

### 1.2 Examples
Any content labelled **Example — NON-NORMATIVE** illustrates a pattern ONLY and MUST NOT be converted into rules or logic.

### 1.3 Master Specification Dominance
If ANYTHING in this document conflicts with MASTER_SPEC.md:

- MASTER_SPEC.md wins for worldview and psychological constraints  
- This document wins only for UI behaviour  

### 1.4 No Implicit Behaviour
The builder LLM MUST NOT infer behaviour not explicitly defined here.  
If behaviour is required, it MUST appear in this document.

### 1.5 Backend Authority
The backend:
- is deterministic  
- controls all agent behaviour  
- is the source of all text content  
- supplies semantic packets  

The UI MUST NOT modify, reinterpret, or compress any backend-generated text.

### 1.6 Psychological Neutrality
The UI MUST NOT:

- soften conflict  
- exaggerate intimacy  
- reduce tension  
- intensify emotion  
- protect the user emotionally  
- bias outcomes  
- reward the user's choices  
- punish the user's choices  
- apply “comfort UX” or “romantic UX”  
- modify pacing for emotional purposes  

Emotional tone MUST come ONLY from characters via the backend renderer.

### 1.7 No Special Modes (Intimacy Included)
The UI MUST NOT introduce modes such as:

- “Romantic mode”  
- “Explicit mode”  
- “Safe mode”  
- “NSFW mode”  
- “Sex mode”  
- “Combat mode”  
- “Scene mode”  

ALL moments — cooking, joking, arguing, kissing, fucking, crying, fighting, reconciling — MUST be rendered in the same unified UI pipeline.

### 1.8 User Non-Simulation Rule
The UI MUST NOT simulate the user’s:

- thoughts  
- feelings  
- mood  
- intentions  
- drives  
- personality  
- emotional state  

The user is a real person.  
The UI presents perception, not speculation.

=====================================================================
## 2. CORE UI PHILOSOPHY
=====================================================================

The core philosophy of the UI is:

**“The UI is the lens through which the user experiences the world — nothing more, nothing less.”**

This means:

1. The UI MUST represent only what the user perceives (from renderer).  
2. The UI MUST represent events in strict chronological order.  
3. The UI MUST NOT distort reality.  
4. The UI MUST support long sessions without fatigue.  
5. The UI MUST allow ultra-long interactions (e.g., 250-message intimacy flows) smoothly and clearly.  
6. The UI MUST remain text-only but visually compelling.  
7. The UI MUST preserve readability under high conversational density.  
8. The UI MUST enable interactivity without friction.  
9. The UI MUST handle multi-character interactions cleanly.  
10. The UI MUST never feel game-like, cartoonish, simplified, or artificial.  

=====================================================================
## 3. GLOBAL DESIGN REQUIREMENTS
=====================================================================

### 3.1 Text-Only But Visually Rich

The UI MUST NOT use:

- images  
- illustrations  
- low-res cartoon icons  
- animated avatars  
- photorealistic renders  
- bitmoji-style heads  
- anything resembling a “visual novel” presentation  

The UI MUST use text and layout to create visual richness:

- typography hierarchy (weight, size, italics)
- spacing rules
- subtle horizontal rules
- indentation patterns
- faint shading panels
- minimal but tasteful color accents (emotion-neutral)
- micro-animations (fade-in, slide-up) ONLY for legibility  
- text transitions that do NOT encode emotional meaning  

### 3.2 Speaker Clarity

Every utterance MUST clearly show:

- **Who is speaking**  
- **What type of output it is** (dialogue, perception, system, phone, etc.)  
- **How it aligns on the screen**  

Speaker clarity is ABSOLUTE. No ambiguity is permitted.

### 3.3 Single Continuous Timeline

All content MUST appear on a single scrollable timeline.  
There MUST NOT be scene cuts or hidden transitions.

The world continues even when the user is:

- reading  
- using the phone  
- in the middle of intimacy  
- in the shower  
- in a fight  
- sleeping (perception of dreams / waking events applies)  

### 3.4 Real-Time Interactivity

Conversations MUST unfold like real life:

- One message at a time  
- Pauses  
- Overlaps  
- Interruptions  
- Reactions  
- Misunderstandings  
- Flow changes  
- Tone shifts  
- Multi-participant dynamics  

This MUST feel like actual presence, not a novel being read.

### 3.5 No Cognitive Overload

The UI MUST:

- structure text clearly  
- avoid text walls  
- break perception blocks logically  
- manage auto-scroll intelligently  
- handle high message throughput without overwhelming the user  

But it MUST NOT censor or summarize anything.

=====================================================================
## 4. TIMELINE ARCHITECTURE
=====================================================================

### 4.1 Timeline Definition

The **Timeline** is the primary UI surface.  
It MUST:

- display every message (dialogue, perception, system)  
- scroll vertically  
- support infinite history (paginate older content)  
- support real-time updates via WebSocket  
- handle bursts of activity  
- anchor the bottom during active reading  
- pause auto-scroll when the user scrolls upward  

### 4.2 Timeline Content Types

Each timeline entry MUST belong to exactly one type:

1. **Perception Block**  
   - renderer descriptions  
   - always second-person  
   - neutral typography  
   - no speaker label  

2. **Character Dialogue**  
   - clear speaker label  
   - distinct indentation  
   - optionally, subtle color tags for each character  

3. **User Dialogue**  
   - visually distinct from characters  
   - right-aligned or framed subtly  

4. **System Line**  
   - minimalistic  
   - for incursion markers, phone notifications, etc.  

5. **Phone Overlay Echo Line**  
   - when phone notifications appear while the phone is closed  

### 4.3 Timeline Formatting Rules

- Line spacing MUST be consistent.  
- Paragraph breaks MUST NOT blend dialogue and perception.  
- Time clusters MUST be available for long scrollback.  
- No decorative emojis unless they come from a character’s own message.  
- No cartoon bubbles.  
- No artificial emotional cues.  

=====================================================================
## 5. SCENE FLOW (CONTINUITY CONTAINER)
=====================================================================

### 5.1 Definition

A **Scene Flow** is an internal, non-visible construct the UI uses to maintain continuity and pacing.

A Scene Flow begins when:

- location changes, OR  
- a major incursion occurs, OR  
- a narrative shift happens (e.g., entering bedroom, arriving at restaurant), OR  
- an extended interaction starts (e.g., intimacy, long conversation, argument).  

It ends when:

- context changes significantly, OR  
- a clear backend-signaled transition occurs.  

### 5.2 UI Obligations for Scene Flow

The UI MUST:

- anchor the last few messages of a scene  
- adjust auto-scroll logic for density  
- visually group messages belonging to the same flow  
- NEVER label the scene (“Scene 5: Bedroom”)  
- NEVER impose themes (e.g., romantic mode)  

Scene Flow is purely structural.

### 5.3 Support for Ultra-Long Intimate Interactions

If an intimate interaction lasts:

- 3 messages → simple continuity  
- 250+ messages → MUST remain readable  

UI MUST:

- anchor the last 5–10 messages  
- avoid pushing content uncontrollably  
- allow scrollback without losing context  
- keep speaker labels clear  
- preserve rhythm without emotional distortion  

Intimacy is treated EXACTLY like any other scene.

=====================================================================
## 6. INTERACTION DENSITY (TEMPO)
=====================================================================

### 6.1 High-Density Situations

Examples:  
- heated arguments  
- rapid-fire jokes  
- sexual escalation  
- multiple characters talking  
- unexpected event + phone + dialogue simultaneously  

UI MUST:

- maintain legibility  
- increase speaker label prominence  
- ensure auto-scroll responsiveness  
- avoid perceptual overload  

### 6.2 Low-Density Situations

Examples:  
- quiet evening  
- soft conversation  
- slow intimacy  
- solitary perception  

UI MUST:

- allow breathing room  
- reduce rapid auto-scroll  
- maintain visual calm without emotional bias  

### 6.3 Density MUST NOT encode emotion

Density determines **tempo**, not **tone**.

=====================================================================
## 7. MULTI-CHARACTER CONCURRENCY
=====================================================================

### 7.1 Overlapping Dialogue

If multiple characters speak in quick succession:

- each line MUST appear in order  
- each MUST show speaker name  
- each MUST be visually separated  

If a character **interrupts**:

- a dash or indentation MAY be used  
- but readability MUST remain high  
- no overwhelming visual noise  

### 7.2 Overlapping Actions

If multiple agents act at once (entering room, touching something):

- renderer output MUST be displayed as multiple perception blocks  
- UI MUST break them into digestible segments  
- MUST NOT condense multiple actions into a single fused block  

### 7.3 Spatial Clarity

Characters’ positions relative to you MUST be clear **via renderer text**, not UI guesses.

=====================================================================
## 8. PHONE OVERLAY
=====================================================================

### 8.1 Nature of Phone Overlay

The Phone Overlay is:

- an in-world phone UI  
- containing text-only apps (messages, calls, calendar, email, banking, social)  
- rendered as a panel, not a fake phone image  

### 8.2 Behaviour When Open

When phone is open:

- world events MUST still appear in background timeline  
- urgent events MUST raise an inline alert inside the phone  
- user MUST be able to close/minimise instantly  

### 8.3 Behaviour When Closed

If a phone event arrives:

- a subtle notification MUST appear in timeline  
- content MUST NOT be lost  

### 8.4 UI MUST NOT simulate phone OS metaphors

- no fake iPhone frames  
- no photo apps  
- no camera UI  
- no gesture animations copied from real phones  

The phone is textual, like everything else.

=====================================================================
## 9. UNEXPECTED EVENTS (INCURSIONS)
=====================================================================

If an incursion occurs during ANY scene:

- UI MUST inject a distinct system line  
- renderer perception MUST show what you perceive  
- no emotional smoothing  
- no suppression because intimacy is happening  

Interruptions MUST feel real, not staged.

=====================================================================
## 10. TTS (TEXT-TO-SPEECH) BEHAVIOUR
=====================================================================

TTS is OPTIONAL but when enabled it MUST behave deterministically, neutrally,  
and without emotional bias.  
TTS MUST NEVER alter meaning, skip important context, or distort pacing for  
comfort or drama.

### 10.1 What TTS MUST Read Aloud

TTS MUST read:

- **Perception blocks** (renderer descriptions) exactly as written  
- **Character dialogue lines** exactly as written  
- **User’s own messages** only if user enables this preference  
- **Phone messages/calls** if user enables “TTS for notifications”  

TTS MUST NOT:

- summarise  
- rephrase  
- add emphasis  
- insert intonation meant to convey emotion beyond default synthesis  
- change pacing based on scene type (intimate, conflict, mundane)  

TTS is a voice channel, NOT an interpretative channel.

### 10.2 TTS Queue Model

TTS MUST maintain an internal queue:

1. **Append** new content as it arrives.  
2. **Speak** oldest content first.  
3. **Remove** from queue once spoken.  

This queue MUST be deterministic and reproducible.

### 10.3 Interruption Rules

There are two categories:

#### A. High-Priority Interruptions

These MUST interrupt TTS immediately:

- A character directly addressing the user  
- A sudden unexpected event (incursion)  
- A renderer perception indicating danger or major movement  
- Certain phone alerts (calls, high-priority notifications)  

When interrupted:

- TTS MUST stop speaking the previous line immediately  
- The interrupted line MUST be marked as “unfinished” internally  
- It MUST NOT be repeated unless the user manually chooses to replay it  
- The new urgent content MUST play next  

#### B. Normal-Priority Messages

These MUST **queue**, NOT interrupt:

- Background movement  
- Ambient actions  
- Non-urgent messages  
- Ordinary dialogue not addressed to the user  
- Phone texts when user is busy in a high-density scene  

### 10.4 User Controls

The UI MUST expose:

- Mute / Unmute  
- Replay last line  
- Clear queue  
- TTS speed slider  
- Toggle “read my own messages”  
- Toggle “read phone messages”  

All controls MUST react instantly.

TTS MUST NOT:

- cross-fade  
- cross-blend  
- apply audio effects based on intimacy or conflict  

### 10.5 TTS and Intimate Scenes

Intimate scenes MUST NOT get “special” TTS handling:

- no whisper mode  
- no slowed-down speech  
- no romantic filters  
- no sensual pacing  

TTS treats intimacy as **normal reality**.

=====================================================================
## 11. TEXT FORMATTING, EFFECTS, AND VISUAL HIERARCHY
=====================================================================

The UI MUST be visually beautiful **without images** — only text, spacing,  
layout, and tasteful micro-effects.

### 11.1 Core Formatting Requirements

The UI MUST use:

- consistent font families  
- varied weight for hierarchy  
- varied size for sectioning  
- italics for emphasis only when the renderer provides it  
- subtle shading for speaker blocks  
- thin dividers for major transitions  
- timestamp clusters in faint grey  
- indentation rules per content type  

It MUST NOT use:

- emojis as layout  
- ASCII art  
- bright colours with emotional connotations  
- cartoonish speech bubbles  
- neon gradients  
- blinking text  

### 11.2 Visual Object Model

Each message MUST be rendered as a **MessageCard** with:

- Text content  
- Metadata (speaker, timestamp, type)  
- Optional micro-interactions (hover highlight, slight fade-in)  
- Strictly neutral styling  

MessageCards MUST NOT differ based on emotional content.

### 11.3 Speaker Labels

Character names MUST:

- appear above or beside dialogue  
- be consistent across all scenes  
- use a fixed colour per character (subtle, emotionless)  
- not shift styling based on mood or intimacy  

Example — NON-NORMATIVE:

Rebecca:
“I was waiting for you.”

### 11.4 Perception Blocks

Perception MUST:

- use second-person narrative  
- be visually distinguished from dialogue  
- not imitate novel-style flourish unless renderer produces it  
- avoid long walls of unbroken text (renderer encouraged to keep them digestible)  

UI MUST NOT rewrite perception.

### 11.5 Dialogue Blocks

Dialogue MUST:

- clearly identify speaker  
- use quotation marks or indentation  
- maintain uniform line height  
- never merge two speakers into same block  

### 11.6 System Blocks

System lines (incursion notices, phone bings) MUST be:

- small  
- unobtrusive  
- emotion-neutral  
- visually distinct  
- never intrusive  

=====================================================================
## 12. PHONE SYSTEM & APP ARCHITECTURE
=====================================================================

The Phone is a **text-first overlay panel** that simulates in-world digital tools.

It MUST include (as text-only interfaces):

- Messages app  
- Phone/Call log  
- Email  
- Calendar  
- Notes  
- Banking/Finance  
- “Media” (text-only representation of social feeds)  
- Settings (for TTS, notifications, UI preferences)  

Phone MUST NOT include:

- image previews  
- external links  
- camera  
- gallery  
- graphical icons  
- mobile OS chrome  

### 12.1 Opening and Closing the Phone

The Phone MUST:

- slide up over the timeline  
- dim background slightly (neutral dim, no emotional tone)  
- retain scroll position when reopened  
- NOT pause world events  
- allow quick closure via tap/click or swipe  

### 12.2 Phone Notifications

When phone is closed:

- notifications MUST appear inline on the timeline  
- MUST be small and subtle  
- MUST not override world events  

### 12.3 Messages App

Each conversation is a text-only thread with:

- speaker tags  
- timestamps  
- deterministic chat bubble structure  

MUST NOT include:

- avatars  
- stickers  
- reaction icons  

### 12.4 Calendar App

Calendar MUST:

- show upcoming events  
- allow creation of user-made events (these update backend)  
- allow viewing events involving user or agents  
- never generate new events on its own  

### 12.5 Email App

Text-only email list:

- subject  
- sender  
- time  
- plain-text body  

### 12.6 Social Feed App

Social content MUST:

- be text-only  
- be deterministic (backend-driven)  
- never show images  
- never attempt to model real social media visuals  

=====================================================================
## 13. INTERRUPTIONS, OVERLAYS, AND PRIORITY SYSTEM
=====================================================================

### 13.1 Types of Interruptions

1. **World-Level Interruptions**
   - unexpected events  
   - agent entering the scene  
   - sudden movement  
   - urgent dialogue  
   - danger or strong perceptual cues  

2. **Phone Interruptions**
   - calls  
   - urgent texts  
   - notifications flagged as high priority  

3. **Renderer-Triggered Perceptions**
   - atmosphere shifts  
   - loud sounds  
   - environmental cues  

### 13.2 UI Behaviour When Interruptions Occur

The UI MUST:

- inject a system line describing interruption source  
- pause TTS (if needed)  
- append renderer perception  
- never block the user’s ability to act  
- never hide or suppress interruption due to intimacy or conversation  

### 13.3 Ordering Rules

Interruptions MUST be displayed **immediately**  
and MUST appear **before** any subsequent timeline entries.

### 13.4 No Emotional Filters

The UI MUST NOT:

- fade to red  
- shake screen  
- blur  
- add chromatic effects  

All visual signalling MUST be neutral.

=====================================================================
## 14. INTIMACY INTERACTION MODEL (NON-MODE-BASED)
=====================================================================

### 14.1 General Rules

Intimacy (romantic, erotic, sexual — between consenting adults) MUST be treated EXACTLY like any other interaction:

- no special mode  
- no special colour scheme  
- no special panel  
- no censorship UI  
- no “entering sex scene”  
- no “fade to black”  

Intimacy is rendered the same way as:

- a joke  
- a fight  
- cooking  
- brushing teeth  
- going for a walk  

### 14.2 Interactive Intimacy

Intimate interactions are **interactive**, not static paragraphs.

The UI MUST support:

- rapid back-and-forth dialogue  
- slow sensory descriptions  
- mixed action + speech  
- escalation and de-escalation  
- sudden interruptions  
- multi-message rhythms (3 messages or 250 messages)  

### 14.3 Clarity Without Emotional Bias

The UI MUST:

- make each contribution readable  
- maintain speaker labels  
- keep perception blocks crisp  
- avoid “romantic fonts”  
- avoid scripted pacing  
- avoid dramatic spacing  

### 14.4 Handling Explicit Sexual Language

Explicit language MUST be displayed exactly as produced by renderer.  
UI MUST NOT:

- censor  
- redact  
- euphemise  
- alter explicit text  

Backend already enforces legality; UI MUST present reality as is.

### 14.5 Long Intimate Sequences

For long interactions (50–300+ messages), the UI MUST:

- anchor the last several lines  
- not jump excessively  
- allow deep scrollback  
- manage density  
- keep continuity stable  
- avoid cognitive overload  

Scene Flow and Interaction Density systems MUST keep long interactions usable.

=====================================================================
## 15. SESSION MANAGEMENT & RECOVERY
=====================================================================

### 15.1 On UI Load

The UI MUST:

- request current world snapshot from backend  
- request recent timeline messages (amount defined in settings)  
- reconstruct scene flow from timestamps and content clusters  
- re-establish WebSocket connection  
- resume live feed seamlessly  

### 15.2 On Connection Loss

The UI MUST:

- display a small neutral banner (“Reconnecting…”)  
- not block or freeze  
- re-sync timeline when connection is restored  
- never create “gaps” or missing messages  

### 15.3 On User Return After hours/days

The UI MUST:

- fetch newer events from backend  
- seamlessly append them  
- reconstruct continuity  
- update phone overlays if pending messages exist  

=====================================================================
## 16. PERFORMANCE REQUIREMENTS
=====================================================================

UI MUST:

- handle 10k+ message timelines  
- paginate older content  
- maintain <16ms render time per update  
- maintain smooth scrolling even under heavy message bursts  
- support both desktop and mobile layouts deterministically  

=====================================================================
## 17. ACCESSIBILITY AND LONG-SESSION USABILITY
=====================================================================

UI MUST:

- support font scaling without breaking layout  
- maintain high contrast  
- ensure screen reader compatibility  
- avoid rapid animation  
- respect system “reduce motion” preferences  
- ensure TTS can be used exclusively if needed  
- ensure the user can navigate with keyboard alone  

=====================================================================
## 18. UI TESTING REQUIREMENTS
=====================================================================

Builder MUST provide automated tests verifying:

- speaker attribution correctness  
- perception formatting correctness  
- system event visibility  
- phone overlay behaviour  
- TTS interruption logic  
- multi-character concurrency handling  
- absence of emotional biasing effects  
- uniform behaviour across intimacy, conflict, mundane scenes  
- no numeric psychological leakage  
- reloading behaviour  
- connection loss recovery  
- timeline pagination  
- performance under load  
- deterministic rendering of identical event sequences  

=====================================================================
## 19. FINAL PRINCIPLES (NON-NEGOTIABLE)
=====================================================================

1. **UI is perception, not interpretation.**  
2. **UI is emotionally neutral.**  
3. **Intimacy is not a mode — it is life.**  
4. **User is real, not simulated. UI never fabricates user emotions.**  
5. **Nothing is hidden; nothing is dramatized.**  
6. **All visual richness emerges from typography, not imagery.**  
7. **UI MUST support long sessions and be a joy to inhabit.**  
8. **Every rule above MUST be obeyed exactly.**

=====================================================================
**END OF UI SPECIFICATION**
=====================================================================

