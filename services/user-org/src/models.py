from sqlalchemy import Column, String, DateTime, ForeignKey, Integer, Float, text
from sqlalchemy.dialects.postgresql import UUID, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from src.database import Base
import uuid

class User(Base):
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=False)
    password_hash = Column(String, nullable=True)
    invitation_token = Column(String, nullable=True)
    invitation_expires = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    memberships = relationship("Membership", back_populates="user")

class Organization(Base):
    __tablename__ = "organizations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    domain = Column(String, unique=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    memberships = relationship("Membership", back_populates="organization")

class Membership(Base):
    __tablename__ = "memberships"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"))
    role = Column(String, default="member") # admin, member
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    user = relationship("User", back_populates="memberships")
    organization = relationship("Organization", back_populates="memberships")

class Company(Base):
    __tablename__ = "companies"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    slug = Column(String, unique=True, nullable=False)
    display_name = Column(String, nullable=False)
    # Add other fields if needed from init.sql
    
    organization_companies = relationship("OrganizationCompany", back_populates="company")

class OrganizationCompany(Base):
    __tablename__ = "organization_companies"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"))
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    organization = relationship("Organization")
    company = relationship("Company", back_populates="organization_companies")

class Event(Base):
    __tablename__ = "events"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    article_id = Column(UUID(as_uuid=True), nullable=False) # FK to articles, but we might not map Article model here yet
    primary_company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"))
    event_type = Column(String)
    headline_summary = Column(String)
    short_summary = Column(String)
    detailed_summary = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # New LLM Insight Fields
    overall_impact = Column(Integer)
    importance_level = Column(String)
    urgency = Column(String)
    time_horizon = Column(String)
    
    key_points = Column(JSON)
    recommended_teams = Column(JSON)
    affected_areas = Column(JSON)
    tags = Column(JSON)
    
    confidence_explanation = Column(String)
    risk_score = Column(Integer)
    opportunity_score = Column(Integer)
    sentiment = Column(String)
    sentiment_score = Column(Float)
    threat_level = Column(String)
    confidence_level = Column(String)
    recommended_actions = Column(String)
    
    impact_on_market = Column(String)
    impact_on_products = Column(String)
    impact_on_competitors = Column(String)
    impact_on_customers = Column(String)
    impact_on_talent = Column(String)
    impact_on_regulation = Column(String)
    
    organization_events = relationship("OrganizationEvent", back_populates="event")
    primary_company = relationship("Company")

class OrganizationEvent(Base):
    __tablename__ = "organization_events"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"))
    event_id = Column(UUID(as_uuid=True), ForeignKey("events.id", ondelete="CASCADE"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    organization = relationship("Organization")
    event = relationship("Event", back_populates="organization_events")

class Task(Base):
    __tablename__ = "tasks"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    event_id = Column(UUID(as_uuid=True), ForeignKey("events.id", ondelete="SET NULL"), nullable=True)
    
    title = Column(String, nullable=False)
    description = Column(String, nullable=True)
    status = Column(String, default="todo", nullable=False)  # todo, in_progress, done
    priority = Column(String, default="medium", nullable=False)  # low, medium, high
    due_date = Column(DateTime(timezone=True), nullable=True)
    
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=False)
    assigned_to = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    organization = relationship("Organization")
    event = relationship("Event")
    creator = relationship("User", foreign_keys=[created_by])
    assignee = relationship("User", foreign_keys=[assigned_to])
    comments = relationship("TaskComment", back_populates="task", cascade="all, delete-orphan")

class TaskComment(Base):
    __tablename__ = "task_comments"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    task_id = Column(UUID(as_uuid=True), ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    text = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    task = relationship("Task", back_populates="comments")
    user = relationship("User")
