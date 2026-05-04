"""
Agent Registry - Track all agents with metadata
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional
import uuid


class RiskTier(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class DataClassification(Enum):
    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    RESTRICTED = "restricted"


class AgentStatus(Enum):
    ACTIVE = "active"
    PENDING = "pending"
    DEPRECATED = "deprecated"
    RETIRED = "retired"


@dataclass
class AgentMetadata:
    """Metadata for an agent"""
    owner: str  # Technical owner email
    sponsor: Optional[str] = None  # Business owner email
    use_case: str = ""
    data_classification: DataClassification = DataClassification.INTERNAL
    risk_tier: RiskTier = RiskTier.MEDIUM
    tags: list = field(default_factory=list)


@dataclass
class Agent:
    """Agent identity representation"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    status: AgentStatus = AgentStatus.PENDING
    metadata: AgentMetadata = field(default_factory=AgentMetadata)
    service_principal_id: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    deprecated_at: Optional[datetime] = None


class AgentRegistry:
    """In-memory agent registry for tracking agent identities"""
    
    def __init__(self):
        self._agents: dict[str, Agent] = {}
    
    def register(self, agent: Agent) -> Agent:
        """Register a new agent"""
        agent.id = str(uuid.uuid4())
        agent.created_at = datetime.utcnow()
        agent.updated_at = datetime.utcnow()
        self._agents[agent.id] = agent
        return agent
    
    def get(self, agent_id: str) -> Optional[Agent]:
        """Get an agent by ID"""
        return self._agents.get(agent_id)
    
    def get_by_name(self, name: str) -> Optional[Agent]:
        """Get an agent by name"""
        for agent in self._agents.values():
            if agent.name == name:
                return agent
        return None
    
    def list_all(self) -> list[Agent]:
        """List all registered agents"""
        return list(self._agents.values())
    
    def update(self, agent_id: str, **kwargs) -> Optional[Agent]:
        """Update an agent"""
        agent = self._agents.get(agent_id)
        if agent:
            for key, value in kwargs.items():
                if hasattr(agent, key):
                    setattr(agent, key, value)
            agent.updated_at = datetime.utcnow()
        return agent
    
    def deprecate(self, agent_id: str) -> Optional[Agent]:
        """Deprecate an agent"""
        agent = self._agents.get(agent_id)
        if agent:
            agent.status = AgentStatus.DEPRECATED
            agent.deprecated_at = datetime.utcnow()
            agent.updated_at = datetime.utcnow()
        return agent
    
    def delete(self, agent_id: str) -> bool:
        """Delete an agent"""
        if agent_id in self._agents:
            del self._agents[agent_id]
            return True
        return False