"""
Semantic Mappers - Deterministic Numeric → Semantic Conversions

Implements all bucket-based mappings from numeric internal state to semantic text.
All mappings are DETERMINISTIC and rule-based.

Implements:
- MASTER_SPEC §SECTION 12 — NUMERIC → SEMANTIC MAPPING
- docs/numeric_semantic_mapping.md §1-9
"""

from typing import Dict, List, Optional, Tuple


class MoodMapper:
    """
    Maps mood (valence × arousal) to semantic summary.
    
    Valence ∈ [-1.0, 1.0]
    Arousal ∈ [0.0, 1.0]
    
    Implements: docs/numeric_semantic_mapping.md §1
    """
    
    @staticmethod
    def map_mood(valence: float, arousal: float) -> str:
        """
        Returns deterministic semantic summary for mood state.
        
        Args:
            valence: Emotional tone [-1.0 (negative) to +1.0 (positive)]
            arousal: Activation level [0.0 (calm) to 1.0 (highly aroused)]
            
        Returns:
            Semantic mood description (non-numeric)
        """
        # Clamp to valid ranges
        valence = max(-1.0, min(1.0, valence))
        arousal = max(0.0, min(1.0, arousal))
        
        # Bucket-based mapping: (valence_bucket, arousal_bucket) -> phrase
        if valence > 0.4:  # Positive valence
            if arousal < 0.4:  # Low arousal
                return "She feels quietly content and at ease."
            else:  # High arousal
                return "She feels upbeat and energised."
        elif valence >= -0.2 and valence <= 0.2:  # Neutral valence
            if arousal < 0.3:  # Low arousal
                return "She feels fairly neutral and low-key."
            else:  # Medium+ arousal
                return "She feels neutral but somewhat alert."
        else:  # Negative valence (valence < -0.2)
            if arousal < 0.4:  # Low arousal
                return "She feels low and a bit flat."
            else:  # High arousal
                return "She feels upset and agitated."


class DriveMapper:
    """
    Maps individual drive levels to semantic summaries.
    
    Each drive: level ∈ [0.0 (satisfied), 1.0 (unmet)]
    
    Implements: docs/numeric_semantic_mapping.md §2
    """
    
    DRIVE_NAMES = ["relatedness", "autonomy", "competence", "novelty", "safety"]
    
    @staticmethod
    def map_relatedness(level: float) -> str:
        """
        Maps relatedness drive level to semantic description.
        
        Implements: docs/numeric_semantic_mapping.md §2.1
        """
        level = max(0.0, min(1.0, level))
        
        if level < 0.3:
            return "She feels generally connected and not especially lonely."
        elif level < 0.7:
            return "She would appreciate some closeness or quality time."
        else:
            return "She has been feeling neglected and wants more closeness."
    
    @staticmethod
    def map_autonomy(level: float) -> str:
        """
        Maps autonomy drive level to semantic description.
        
        Implements: docs/numeric_semantic_mapping.md §2.2
        """
        level = max(0.0, min(1.0, level))
        
        if level < 0.3:
            return "She feels free to make her own choices."
        elif level < 0.7:
            return "She is somewhat sensitive about being directed or controlled."
        else:
            return "She feels constrained and strongly wants more freedom."
    
    @staticmethod
    def map_competence(level: float) -> str:
        """
        Maps competence drive level to semantic description.
        
        Implements: docs/numeric_semantic_mapping.md §2.3
        """
        level = max(0.0, min(1.0, level))
        
        if level < 0.3:
            return "She feels capable and effective."
        elif level < 0.7:
            return "She is somewhat unsure about how well she's handling things."
        else:
            return "She has been feeling ineffective and doubting herself."
    
    @staticmethod
    def map_novelty(level: float) -> str:
        """
        Maps novelty drive level to semantic description.
        
        Implements: docs/numeric_semantic_mapping.md §2.4
        """
        level = max(0.0, min(1.0, level))
        
        if level < 0.3:
            return "She feels stimulated enough; routine is okay right now."
        elif level < 0.7:
            return "She wouldn't mind some change or variety."
        else:
            return "She feels stuck in a rut and craves something different."
    
    @staticmethod
    def map_safety(level: float) -> str:
        """
        Maps safety drive level to semantic description.
        
        Implements: docs/numeric_semantic_mapping.md §2.5
        """
        level = max(0.0, min(1.0, level))
        
        if level < 0.3:
            return "She feels generally safe and secure."
        elif level < 0.7:
            return "She feels somewhat on edge and cautious."
        else:
            return "She feels unsafe or unsettled and wants things to be predictable."
    
    @staticmethod
    def map_drive(drive_name: str, level: float) -> str:
        """
        Maps any drive by name to semantic description.
        
        Args:
            drive_name: One of ["relatedness", "autonomy", "competence", "novelty", "safety"]
            level: Drive level [0.0, 1.0]
            
        Returns:
            Semantic description (non-numeric)
        """
        if drive_name == "relatedness":
            return DriveMapper.map_relatedness(level)
        elif drive_name == "autonomy":
            return DriveMapper.map_autonomy(level)
        elif drive_name == "competence":
            return DriveMapper.map_competence(level)
        elif drive_name == "novelty":
            return DriveMapper.map_novelty(level)
        elif drive_name == "safety":
            return DriveMapper.map_safety(level)
        else:
            raise ValueError(f"Unknown drive: {drive_name}")
    
    @staticmethod
    def map_drives_summary(drives: Dict[str, Dict]) -> Dict[str, str]:
        """
        Maps all drives to semantic summaries.
        
        Args:
            drives: Dict of {drive_name: {level: float, sensitivity: float}}
            
        Returns:
            Dict of {drive_name: semantic_description}
        """
        result = {}
        for drive_name in DriveMapper.DRIVE_NAMES:
            if drive_name in drives:
                level = drives[drive_name].get("level", 0.5)
                result[drive_name] = DriveMapper.map_drive(drive_name, level)
        return result
    
    @staticmethod
    def get_highest_pressure_drives(drives: Dict[str, Dict], top_k: int = 2) -> List[Tuple[str, str]]:
        """
        Returns the top K most pressured (highest level) drives with semantic descriptions.
        
        Args:
            drives: Dict of {drive_name: {level: float, sensitivity: float}}
            top_k: Number of top drives to return
            
        Returns:
            List of (drive_name, semantic_description) tuples
        """
        drive_levels = [
            (name, drives[name].get("level", 0.5))
            for name in DriveMapper.DRIVE_NAMES
            if name in drives
        ]
        # Sort by level (descending)
        drive_levels.sort(key=lambda x: x[1], reverse=True)
        
        result = []
        for drive_name, level in drive_levels[:top_k]:
            semantic = DriveMapper.map_drive(drive_name, level)
            result.append((drive_name, semantic))
        return result


class RelationshipMapper:
    """
    Maps relationship edge metrics to semantic summaries.
    
    Relationship dimensions:
    - warmth: [-1.0, 1.0]
    - trust: [0.0, 1.0]
    - tension: [0.0, 1.0]
    - attraction: [0.0, 1.0]
    - familiarity: [0.0, 1.0]
    - comfort: [0.0, 1.0]
    - volatility: [0.0, 1.0]
    
    Implements: docs/numeric_semantic_mapping.md §3
    """
    
    @staticmethod
    def map_relationship_state(
        warmth: float,
        trust: float,
        tension: float,
        attraction: Optional[float] = None,
        comfort: Optional[float] = None,
    ) -> str:
        """
        Maps core relationship dimensions (warmth, trust, tension) to semantic description.
        
        Implements: docs/numeric_semantic_mapping.md §3.1
        """
        # Clamp ranges
        warmth = max(-1.0, min(1.0, warmth))
        trust = max(0.0, min(1.0, trust))
        tension = max(0.0, min(1.0, tension))
        
        # Bucket-based logic
        if warmth > 0.5 and trust > 0.5 and tension < 0.3:
            return "She generally feels close and safe with them."
        elif warmth > 0.3 and trust >= 0.0 and trust <= 0.5 and 0.3 <= tension <= 0.7:
            return "She cares but there is some strain and uncertainty."
        elif warmth > 0.0 and trust < 0.0 and tension > 0.4:
            return "She is conflicted: there is some pull toward them but also mistrust."
        elif warmth < -0.2 and trust < 0.3 and tension > 0.5:
            return "She mostly feels negative and guarded around them."
        elif warmth < 0.0 and tension > 0.6:
            return "She feels significant conflict and mistrust in this relationship."
        elif warmth >= -0.1 and warmth <= 0.1 and trust >= 0.0 and trust <= 0.5 and tension < 0.2:
            return "She feels fairly neutral; there's not much emotional investment yet."
        else:
            # Fallback for edge cases
            return "She has a mixed, complex relationship dynamic."
    
    @staticmethod
    def map_relationship_full(
        warmth: float,
        trust: float,
        tension: float,
        attraction: Optional[float] = None,
        comfort: Optional[float] = None,
        familiarity: Optional[float] = None,
    ) -> Dict[str, str]:
        """
        Returns comprehensive relationship state mapping.
        
        Returns:
            Dict with keys:
            - "primary_state": main relationship description
            - "attraction_note": (optional) attraction dimension
            - "comfort_note": (optional) comfort dimension
        """
        result = {
            "primary_state": RelationshipMapper.map_relationship_state(
                warmth, trust, tension, attraction, comfort
            )
        }
        
        # Add attraction note if relevant
        if attraction is not None:
            attraction = max(0.0, min(1.0, attraction))
            if attraction > 0.6:
                if comfort is not None and comfort > 0.5:
                    result["attraction_note"] = "She feels physically attracted and at ease with them."
                else:
                    result["attraction_note"] = "She feels attracted, but also somewhat uneasy."
            elif attraction > 0.3:
                result["attraction_note"] = "She finds them somewhat appealing."
        
        # Add comfort note if relevant
        if comfort is not None:
            comfort = max(0.0, min(1.0, comfort))
            if comfort > 0.7:
                result["comfort_note"] = "She feels at ease in their presence."
            elif comfort > 0.4:
                result["comfort_note"] = "She feels reasonably comfortable around them."
            else:
                result["comfort_note"] = "She feels somewhat uncomfortable around them."
        
        return result


class ArcMapper:
    """
    Maps arcs (emotional/narrative threads) to semantic summaries.
    
    Arc dimensions:
    - intensity: [0.0, 1.0]
    - valence_bias: [-1.0 (negative), 1.0 (positive)]
    - topic_vector: List[str] (keywords)
    
    Implements: docs/numeric_semantic_mapping.md §4
    """
    
    @staticmethod
    def map_arc(intensity: float, valence_bias: float, topic: str) -> str:
        """
        Maps arc state to semantic description.
        
        Args:
            intensity: Arc intensity [0.0, 1.0]
            valence_bias: Emotional tone [-1.0, 1.0]
            topic: Topic or keyword for the arc
            
        Returns:
            Semantic arc description
            
        Implements: docs/numeric_semantic_mapping.md §4
        """
        intensity = max(0.0, min(1.0, intensity))
        valence_bias = max(-1.0, min(1.0, valence_bias))
        
        if intensity > 0.7 and valence_bias < -0.3:
            return f"There is a raw, unresolved sore spot around {topic}."
        elif 0.4 <= intensity <= 0.7 and valence_bias < -0.3:
            return f"There is a lingering tension around {topic}."
        elif intensity > 0.7 and valence_bias > 0.3:
            return f"There is an ongoing positive emotional thread around {topic}."
        elif 0.4 <= intensity <= 0.7 and valence_bias > 0.3:
            return f"They have a gentle, positive theme around {topic}."
        elif intensity < 0.3:
            return f"There is only a mild background sensitivity around {topic}, if any."
        else:
            # Medium intensity, neutral bias
            return f"There is an active but balanced thread around {topic}."
    
    @staticmethod
    def map_arcs_summary(arcs: List[Dict]) -> List[str]:
        """
        Maps all active arcs to semantic descriptions.
        
        Args:
            arcs: List of arc dicts with keys: intensity, valence_bias, topic_vector (list of keywords)
            
        Returns:
            List of semantic arc descriptions
        """
        summaries = []
        for arc in arcs:
            if arc.get("intensity", 0) < 0.2:  # Skip very weak arcs
                continue
            
            intensity = arc.get("intensity", 0)
            valence_bias = arc.get("valence_bias", 0)
            # Use first keyword from topic_vector as the topic
            topic_vector = arc.get("topic_vector", [])
            topic = topic_vector[0] if topic_vector else "something"
            
            summary = ArcMapper.map_arc(intensity, valence_bias, topic)
            summaries.append(summary)
        
        return summaries


class EnergyMapper:
    """
    Maps energy level to semantic summary.
    
    Energy: [0.0 (depleted), 1.0 (fully energised)]
    
    Implements: docs/numeric_semantic_mapping.md §5
    """
    
    @staticmethod
    def map_energy(energy: float) -> str:
        """
        Maps energy level to semantic description.
        
        Args:
            energy: Energy level [0.0, 1.0]
            
        Returns:
            Semantic energy description
        """
        energy = max(0.0, min(1.0, energy))
        
        if energy > 0.7:
            return "She feels energetic and has capacity to engage."
        elif 0.3 <= energy <= 0.7:
            return "She feels somewhat tired but still functional."
        else:
            return "She feels drained and has little capacity to engage."


class IntentionMapper:
    """
    Maps intentions to semantic descriptions.
    
    Intention dimensions:
    - priority: [0.0 (low), 1.0 (urgent)]
    - horizon: ["short", "medium", "long"]
    - type: intention type string
    
    Implements: docs/numeric_semantic_mapping.md §6
    """
    
    @staticmethod
    def map_intention(intention_type: str, priority: float, target: Optional[str] = None) -> str:
        """
        Maps individual intention to semantic description.
        
        Args:
            intention_type: Type of intention (e.g., "avoid_topic", "raise_issue", "be_supportive")
            priority: Priority level [0.0, 1.0]
            target: Optional target entity name
            
        Returns:
            Semantic intention description
        """
        priority = max(0.0, min(1.0, priority))
        
        # Parse intention type
        if "avoid" in intention_type.lower():
            intensity = "actively trying to avoid" if priority > 0.6 else "trying to avoid"
            topic = target or "something"
            return f"She is {intensity} talking about {topic}."
        
        elif "raise" in intention_type.lower() or "bring_up" in intention_type.lower():
            intensity = "needs to bring up" if priority > 0.6 else "intends to bring up"
            topic = target or "something"
            return f"She {intensity} {topic} soon."
        
        elif "support" in intention_type.lower() or "be_supportive" in intention_type.lower():
            intensity = "determined to support" if priority > 0.6 else "trying to be more supportive toward"
            person = target or "them"
            return f"She is {intensity} {person}."
        
        elif "protect" in intention_type.lower():
            person = target or "someone"
            return f"She intends to look out for {person}."
        
        elif "distance" in intention_type.lower() or "withdraw" in intention_type.lower():
            intensity = "determined to maintain distance from" if priority > 0.6 else "thinking about some distance from"
            person = target or "someone"
            return f"She is {intensity} {person}."
        
        else:
            # Generic fallback
            topic = target or "something"
            return f"She has an intention regarding {topic}."
    
    @staticmethod
    def map_intentions_summary(intentions: List[Dict]) -> List[str]:
        """
        Maps high-priority intentions to semantic descriptions.
        
        Args:
            intentions: List of intention dicts with keys: type, priority, target (optional), horizon
            
        Returns:
            List of semantic intention descriptions (high-priority only)
        """
        # Filter to medium+ priority
        high_priority = [i for i in intentions if i.get("priority", 0) >= 0.4]
        # Sort by priority descending
        high_priority.sort(key=lambda i: i.get("priority", 0), reverse=True)
        
        summaries = []
        for intention in high_priority[:3]:  # Limit to top 3
            intent_type = intention.get("type", "unknown")
            priority = intention.get("priority", 0.5)
            target = intention.get("target")
            
            summary = IntentionMapper.map_intention(intent_type, priority, target)
            summaries.append(summary)
        
        return summaries


class MemoryMapper:
    """
    Maps episodic and biographical memories to semantic summaries.
    
    Implements: docs/numeric_semantic_mapping.md §7
    """
    
    @staticmethod
    def format_episodic_memory(description: str, timestamp: Optional[str] = None, salience: float = 0.5) -> str:
        """
        Formats episodic memory description.
        
        Memories should already be semantic; this just ensures consistency.
        
        Args:
            description: Event description (already semantic)
            timestamp: Optional timestamp for context
            salience: Salience [0.0, 1.0]
            
        Returns:
            Formatted episodic memory
        """
        return description
    
    @staticmethod
    def format_biographical_memory(fact: str, source: Optional[str] = None) -> str:
        """
        Formats biographical memory fact.
        
        Facts should be plain sentences, never numeric.
        
        Args:
            fact: Biographical fact (e.g., "She knows he went through a rough divorce.")
            source: Optional source of the fact
            
        Returns:
            Formatted biographical memory
        """
        return fact
    
    @staticmethod
    def format_memory_snippet(memory_dict: Dict) -> str:
        """
        Formats a memory dict into semantic text.
        
        Args:
            memory_dict: Memory object with keys: description, type (episodic/biographical), etc.
            
        Returns:
            Formatted memory text
        """
        memory_type = memory_dict.get("type", "episodic")
        description = memory_dict.get("description", "")
        
        if memory_type == "biographical":
            return MemoryMapper.format_biographical_memory(description)
        else:
            return MemoryMapper.format_episodic_memory(description)


class PersonalityMapper:
    """
    Maps personality kernel to semantic summaries.
    
    The personality kernel is numeric (internally).
    This mapper produces:
    1. Stable personality summary (≈150–250 tokens)
    2. Domain summaries (emotion, conflict, humour, communication, intimacy)
    3. Dynamic activation packet (moment-to-moment modulation)
    
    Implements: MASTER_SPEC §PART IIA, docs/numeric_semantic_mapping.md §9
    """
    
    # Personality kernel fields (from MASTER_SPEC §PART IIA §6)
    KERNEL_FIELDS = [
        "sociability",
        "emotional_volatility",
        "dominance",
        "conscientiousness",
        "openness",
        "directness",
        "introspection",
        "humour_activation",
        "conflict_avoidance",
        "intimacy_assertiveness",
        "intimacy_responsiveness",
        "trust_baseline",
        "forgiveness_baseline",
    ]
    
    @staticmethod
    def _kernel_to_traits(kernel: Dict[str, float]) -> Dict[str, str]:
        """
        Converts kernel numeric values to trait descriptors.
        
        Returns dict of {trait_name: trait_description}
        """
        traits = {}
        
        # Sociability [0, 1]
        if "sociability" in kernel:
            val = kernel["sociability"]
            if val > 0.7:
                traits["sociability"] = "outgoing and gregarious"
            elif val > 0.4:
                traits["sociability"] = "balanced in social engagement"
            else:
                traits["sociability"] = "reserved and more introspective"
        
        # Emotional Volatility [0, 1]
        if "emotional_volatility" in kernel:
            val = kernel["emotional_volatility"]
            if val > 0.7:
                traits["emotional_volatility"] = "experiences emotions intensely and can shift quickly"
            elif val > 0.4:
                traits["emotional_volatility"] = "has moderate emotional sensitivity"
            else:
                traits["emotional_volatility"] = "tends to be emotionally stable"
        
        # Dominance [0, 1]
        if "dominance" in kernel:
            val = kernel["dominance"]
            if val > 0.7:
                traits["dominance"] = "naturally takes charge and leads"
            elif val > 0.4:
                traits["dominance"] = "balances assertiveness with deference"
            else:
                traits["dominance"] = "tends to be collaborative or follow others' lead"
        
        # Conscientiousness [0, 1]
        if "conscientiousness" in kernel:
            val = kernel["conscientiousness"]
            if val > 0.7:
                traits["conscientiousness"] = "very organised, reliable, and detail-oriented"
            elif val > 0.4:
                traits["conscientiousness"] = "reasonably responsible and organised"
            else:
                traits["conscientiousness"] = "more spontaneous and less structured"
        
        # Openness [0, 1]
        if "openness" in kernel:
            val = kernel["openness"]
            if val > 0.7:
                traits["openness"] = "curious, creative, and open to new ideas"
            elif val > 0.4:
                traits["openness"] = "moderately open to new experiences"
            else:
                traits["openness"] = "prefers familiar patterns and established ways"
        
        # Directness [0, 1]
        if "directness" in kernel:
            val = kernel["directness"]
            if val > 0.7:
                traits["directness"] = "very direct and straightforward in communication"
            elif val > 0.4:
                traits["directness"] = "moderately direct, balancing honesty with tact"
            else:
                traits["directness"] = "tends to be indirect or diplomatic"
        
        # Conflict Avoidance [0, 1]
        if "conflict_avoidance" in kernel:
            val = kernel["conflict_avoidance"]
            if val > 0.7:
                traits["conflict_avoidance"] = "strongly prefers harmony and tends to avoid confrontation"
            elif val > 0.4:
                traits["conflict_avoidance"] = "somewhat conflict-averse but can engage when necessary"
            else:
                traits["conflict_avoidance"] = "comfortable with direct disagreement"
        
        return traits
    
    @staticmethod
    def kernel_to_stable_summary(kernel: Dict[str, float], name: str = "She") -> str:
        """
        Converts personality kernel to stable personality summary (≈150–250 tokens).
        
        Args:
            kernel: Numeric personality kernel dict
            name: Agent name or pronoun (default "She")
            
        Returns:
            Semantic personality summary
        """
        traits = PersonalityMapper._kernel_to_traits(kernel)
        
        # Build narrative summary
        summary_parts = []
        
        # Sociability + Directness -> communication style
        if "sociability" in traits and "directness" in traits:
            summary_parts.append(
                f"{name} is {traits['sociability']} in nature, and {traits['directness']} in how she expresses herself."
            )
        
        # Emotional volatility -> emotional style
        if "emotional_volatility" in traits:
            summary_parts.append(f"{name} {traits['emotional_volatility']}.")
        
        # Openness + Conscientiousness -> approach to life
        if "openness" in traits and "conscientiousness" in traits:
            summary_parts.append(
                f"{name} is {traits['openness']}, yet also {traits['conscientiousness']}."
            )
        
        # Conflict avoidance -> conflict style
        if "conflict_avoidance" in traits:
            summary_parts.append(f"{name} {traits['conflict_avoidance']}.")
        
        # Dominance -> relational pattern
        if "dominance" in traits:
            if "collaborative" in traits["dominance"].lower() or "follow" in traits["dominance"].lower():
                summary_parts.append(f"{name} {traits['dominance']} and values partnership.")
            else:
                summary_parts.append(f"{name} {traits['dominance']}.")
        
        return " ".join(summary_parts)
    
    @staticmethod
    def kernel_to_domain_summaries(kernel: Dict[str, float]) -> Dict[str, str]:
        """
        Converts kernel to domain-specific summaries.
        
        Returns:
            Dict of {domain: semantic_description}
        """
        domains = {}
        
        # Emotion regulation domain
        emotional_volatility = kernel.get("emotional_volatility", 0.5)
        if emotional_volatility > 0.7:
            domains["emotion_regulation"] = (
                "When stressed, she tends to feel emotions intensely. She benefits from space to process feelings "
                "and often needs time alone to regulate. She can be vulnerable to spiralling if overwhelmed."
            )
        elif emotional_volatility > 0.4:
            domains["emotion_regulation"] = (
                "She has moderate emotional sensitivity. She processes feelings fairly well but may need occasional "
                "reassurance during difficult times."
            )
        else:
            domains["emotion_regulation"] = (
                "She is emotionally stable and even-keeled. She handles stress calmly and rarely loses composure."
            )
        
        # Conflict style domain
        conflict_avoidance = kernel.get("conflict_avoidance", 0.5)
        directness = kernel.get("directness", 0.5)
        
        if conflict_avoidance > 0.7:
            domains["conflict_style"] = (
                "She strongly prefers to avoid conflict and may withdraw or appease rather than engage in disagreement. "
                "She dislikes confrontation and takes criticism personally. She recovers well in warm, reassuring environments."
            )
        elif conflict_avoidance > 0.4:
            if directness > 0.5:
                domains["conflict_style"] = (
                    "She prefers harmony but can address issues when necessary. She tends to be straightforward about problems "
                    "but tries to maintain the relationship while disagreeing."
                )
            else:
                domains["conflict_style"] = (
                    "She prefers to avoid conflict and may hint at problems rather than stating them directly. "
                    "When unavoidable, she addresses issues carefully."
                )
        else:
            domains["conflict_style"] = (
                "She is comfortable with direct disagreement and sees conflict as a way to clarify issues. "
                "She can be blunt but is not usually aggressive. She values honest debate."
            )
        
        # Humour style domain
        humour_activation = kernel.get("humour_activation", 0.5)
        if humour_activation > 0.7:
            domains["humour_style"] = (
                "She has a keen, playful sense of humour and uses jokes to connect with others and defuse tension. "
                "She appreciates absurdist and witty banter."
            )
        elif humour_activation > 0.4:
            domains["humour_style"] = (
                "She has a moderate sense of humour, usually dry or observational. "
                "She appreciates humour but doesn't rely on it heavily in interactions."
            )
        else:
            domains["humour_style"] = (
                "She tends to be serious and is less likely to joke. She may not readily pick up on subtler humour."
            )
        
        # Communication style domain
        openness = kernel.get("openness", 0.5)
        conscientiousness = kernel.get("conscientiousness", 0.5)
        
        if openness > 0.6 and conscientiousness > 0.6:
            domains["communication_style"] = (
                "She communicates clearly and thoughtfully, expressing ideas in an organised way. "
                "She is open to new perspectives and listens well. She enjoys intellectual discussion."
            )
        elif conscientiousness > 0.6:
            domains["communication_style"] = (
                "She is articulate and precise, preferring structured conversation. "
                "She tends to stay on topic and values practical information exchange."
            )
        else:
            domains["communication_style"] = (
                "She communicates in a more fluid, associative way. "
                "She may jump between topics and enjoys spontaneous dialogue."
            )
        
        # Intimacy/Sexuality style domain (adults only; used only by adult renderer)
        intimacy_assertiveness = kernel.get("intimacy_assertiveness", 0.5)
        intimacy_responsiveness = kernel.get("intimacy_responsiveness", 0.5)
        
        domains["intimacy_style"] = (
            f"Assertiveness in intimacy: {'She is confident in initiating' if intimacy_assertiveness > 0.6 else 'She is more responsive than initiating'}. "
            f"Responsiveness: {'She is very receptive to partner cues' if intimacy_responsiveness > 0.6 else 'She may need explicit signals'}."
        )
        
        return domains
    
    @staticmethod
    def compute_dynamic_activation_packet(
        kernel: Dict[str, float],
        drives: Dict[str, Dict],
        mood: Dict[str, float],
        arcs: List[Dict],
        relationships: List[Dict],
        energy: float,
        relevant_memory: Optional[str] = None,
    ) -> str:
        """
        Computes dynamic activation packet: moment-to-moment personality modulation.
        
        This reflects how current state (drives, mood, arcs, relationships, energy)
        temporarily tilts personality expression from the stable kernel.
        
        Returns:
            Semantic description of current personality activation (≈30–80 tokens)
        """
        activations = []
        
        # Mood tilt
        valence = mood.get("valence", 0)
        arousal = mood.get("arousal", 0)
        if valence < -0.3 and arousal > 0.5:
            activations.append("Right now she is more defensive than usual because she feels upset.")
        elif valence > 0.4 and arousal > 0.5:
            activations.append("She is in a buoyant mood and more socially open right now.")
        elif energy < 0.3:
            activations.append("She is tired, which makes her less patient and more withdrawn.")
        
        # Drive pressure tilt
        highest_drives = [(k, v.get("level", 0.5)) for k, v in drives.items()]
        highest_drives.sort(key=lambda x: x[1], reverse=True)
        if highest_drives and highest_drives[0][1] > 0.7:
            drive_name = highest_drives[0][0]
            if drive_name == "safety":
                activations.append(f"She feels somewhat on edge about safety, making her more guarded.")
            elif drive_name == "relatedness":
                activations.append("She is seeking connection, making her more open and warm.")
            elif drive_name == "autonomy":
                activations.append("She feels a need for independence, making her more assertive.")
        
        # Arc influence
        hot_arcs = [a for a in arcs if a.get("intensity", 0) > 0.6]
        if hot_arcs:
            activations.append(f"There are {len(hot_arcs)} emotionally active theme(s) affecting her right now.")
        
        if not activations:
            activations.append("She is in her baseline state.")
        
        return " ".join(activations[:2])  # Limit to 2-3 activation notes
