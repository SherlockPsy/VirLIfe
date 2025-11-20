from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from backend.persistence.database import Base
import datetime

class WorldModel(Base):
    __tablename__ = "worlds"

    id = Column(Integer, primary_key=True, index=True)
    current_tick = Column(Integer, default=0, nullable=False)
    current_time = Column(DateTime(timezone=True), default=func.now(), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    locations = relationship("LocationModel", back_populates="world")
    events = relationship("EventModel", back_populates="world")
    agents = relationship("AgentModel", back_populates="world")

class LocationModel(Base):
    __tablename__ = "locations"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    world_id = Column(Integer, ForeignKey("worlds.id"), nullable=False)
    attributes = Column(JSON, default={}) # For tags, properties

    world = relationship("WorldModel", back_populates="locations")
    agents = relationship("AgentModel", back_populates="location")
    objects = relationship("ObjectModel", back_populates="location")

class UserModel(Base):
    """
    Represents THE HUMAN USER.
    MUST NOT contain any psychological state (mood, drives, etc).
    Used only for identity and physical presence.
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, unique=True)
    # No internal state columns allowed.

class AgentModel(Base):
    __tablename__ = "agents"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    world_id = Column(Integer, ForeignKey("worlds.id"), nullable=False)
    location_id = Column(Integer, ForeignKey("locations.id"), nullable=True)
    
    # Physical/Energy State
    energy = Column(Float, default=1.0, nullable=False)
    
    # Psychological State (JSONB for structured data)
    # Mood: {valence: float, arousal: float}
    mood = Column(JSON, default={"valence": 0.0, "arousal": 0.0}, nullable=False)
    
    # Drives: {drive_name: {level: float, sensitivity: float}}
    drives = Column(JSON, default={}, nullable=False)
    
    # Personality
    personality_kernel = Column(JSON, default={}, nullable=False)
    personality_summaries = Column(JSON, default={}, nullable=False) # stable, domain
    domain_summaries = Column(JSON, default={}, nullable=False) # Explicit domain summaries if separate
    
    # Context
    cached_context_fragments = Column(JSON, default={}, nullable=False)
    status_flags = Column(JSON, default={}, nullable=False)
    
    last_cognition_timestamp = Column(DateTime(timezone=True), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    world = relationship("WorldModel", back_populates="agents")
    location = relationship("LocationModel", back_populates="agents")
    
    memories = relationship("MemoryModel", back_populates="agent")
    arcs = relationship("ArcModel", back_populates="agent")
    intentions = relationship("IntentionModel", back_populates="agent")
    
    # Relationships originating from this agent
    relationships = relationship("RelationshipModel", foreign_keys="[RelationshipModel.source_agent_id]", back_populates="source_agent")
    
    calendar_items = relationship("CalendarModel", back_populates="agent")

class RelationshipModel(Base):
    __tablename__ = "relationships"

    id = Column(Integer, primary_key=True, index=True)
    source_agent_id = Column(Integer, ForeignKey("agents.id"), nullable=False)
    
    # Target can be an agent or the user. 
    # We will use nullable FKs and a type discriminator or just separate columns.
    # Simpler: target_agent_id (nullable), target_user_id (nullable).
    target_agent_id = Column(Integer, ForeignKey("agents.id"), nullable=True)
    target_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Metrics
    warmth = Column(Float, default=0.0)
    trust = Column(Float, default=0.0)
    tension = Column(Float, default=0.0)
    attraction = Column(Float, default=0.0)
    familiarity = Column(Float, default=0.0)
    comfort = Column(Float, default=0.0)
    volatility = Column(Float, default=0.0)
    
    source_agent = relationship("AgentModel", foreign_keys=[source_agent_id], back_populates="relationships")
    # We don't strictly need back_populates for targets unless we want to query "who likes this user"

class MemoryModel(Base):
    __tablename__ = "memories"

    id = Column(Integer, primary_key=True, index=True)
    agent_id = Column(Integer, ForeignKey("agents.id"), nullable=False)
    
    type = Column(String, nullable=False) # "episodic" or "biographical"
    description = Column(Text, nullable=False)
    timestamp = Column(DateTime(timezone=True), nullable=True) # Nullable for biographical facts? Or use creation time.
    salience = Column(Float, default=0.0)
    semantic_tags = Column(JSON, default=[])
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    agent = relationship("AgentModel", back_populates="memories")

class ArcModel(Base):
    __tablename__ = "arcs"

    id = Column(Integer, primary_key=True, index=True)
    agent_id = Column(Integer, ForeignKey("agents.id"), nullable=False)
    
    type = Column(String, nullable=False) # Name/Type of arc
    intensity = Column(Float, default=0.0)
    valence_bias = Column(Float, default=0.0)
    topic_vector = Column(JSON, default=[]) # Semantic keywords or vector representation
    decay_rate = Column(Float, default=0.1)
    
    agent = relationship("AgentModel", back_populates="arcs")

class IntentionModel(Base):
    __tablename__ = "intentions"

    id = Column(Integer, primary_key=True, index=True)
    agent_id = Column(Integer, ForeignKey("agents.id"), nullable=False)
    
    description = Column(Text, nullable=False)
    priority = Column(Float, default=0.0)
    horizon = Column(String, default="short") # short, medium, long
    type = Column(String, default="action")
    stability = Column(Float, default=0.5)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    agent = relationship("AgentModel", back_populates="intentions")

class ObjectModel(Base):
    __tablename__ = "objects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    location_id = Column(Integer, ForeignKey("locations.id"), nullable=False)
    state = Column(JSON, default={})
    
    location = relationship("LocationModel", back_populates="objects")

class EventModel(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    world_id = Column(Integer, ForeignKey("worlds.id"), nullable=False)
    
    type = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    
    # Source/Target identifiers (can be "agent:1", "user:1", "system", "object:5")
    source_entity_id = Column(String, nullable=True)
    target_entity_id = Column(String, nullable=True)
    
    payload = Column(JSON, default={})
    
    tick = Column(Integer, nullable=False)
    timestamp = Column(DateTime(timezone=True), nullable=False)
    processed = Column(Boolean, default=False)
    
    world = relationship("WorldModel", back_populates="events")

class CalendarModel(Base):
    __tablename__ = "calendars"

    id = Column(Integer, primary_key=True, index=True)
    agent_id = Column(Integer, ForeignKey("agents.id"), nullable=False)
    
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    start_time = Column(DateTime(timezone=True), nullable=False)
    end_time = Column(DateTime(timezone=True), nullable=True)
    
    # Type: "appointment", "obligation", "plan", "routine"
    type = Column(String, default="appointment")
    
    # Status: "pending", "active", "completed", "missed", "cancelled"
    status = Column(String, default="pending")
    
    # Recurrence rule (optional, simplified for now)
    recurrence_rule = Column(String, nullable=True) 
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    agent = relationship("AgentModel", back_populates="calendar_items")
