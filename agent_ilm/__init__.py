"""
Agent Identity Lifecycle Management (agent-ilm)

Python SDK for managing AI agent identities in Microsoft Entra ID.
"""

__version__ = "0.1.0"
__author__ = "AGenNext"

from agent_ilm.registry import AgentRegistry, Agent, AgentMetadata, RiskTier, DataClassification, AgentStatus
from agent_ilm.entra import EntraIdentityManager, EntraConfig
from agent_ilm.audit import AuditLogger, AuditEvent, AuditEventType
from agent_ilm.decision_graph import DecisionGraphEvent, DecisionGraphLogger, ResourceIdentity

__all__ = [
    "AgentRegistry", 
    "Agent", 
    "AgentMetadata", 
    "RiskTier", 
    "DataClassification",
    "AgentStatus",
    "EntraIdentityManager", 
    "EntraConfig",
    "AuditLogger", 
    "AuditEvent", 
    "AuditEventType",
    "DecisionGraphEvent",
    "DecisionGraphLogger",
    "ResourceIdentity",
    "__version__"
]