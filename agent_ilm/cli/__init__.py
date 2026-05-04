#!/usr/bin/env python3
"""
Agent Identity Lifecycle Management CLI

A CLI tool for managing AI agent identities in Microsoft Entra ID.
Built with Google Fire framework.
"""

import fire
import os
import json
from typing import Optional, List

from agent_ilm import Agent, AgentMetadata, RiskTier, DataClassification, AgentStatus
from agent_ilm import AuditLogger, AuditEventType

STATE_FILE = os.path.expanduser("~/.agent-ilm/state.json")


def load_agents() -> list[Agent]:
    """Load agents from state file"""
    agents = []
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE) as f:
                data = json.load(f)
                for item in data.get("agents", []):
                    agent = Agent(
                        id=item["id"],
                        name=item["name"],
                        description=item.get("description", ""),
                        status=AgentStatus(item.get("status", "pending")),
                        metadata=AgentMetadata(
                            owner=item["metadata"]["owner"],
                            sponsor=item["metadata"].get("sponsor"),
                            use_case=item["metadata"].get("use_case", ""),
                            risk_tier=RiskTier(item["metadata"].get("risk_tier", "medium")),
                            data_classification=DataClassification(item["metadata"].get("data_classification", "internal"))
                        ),
                        service_principal_id=item.get("service_principal_id")
                    )
                    agents.append(agent)
        except Exception:
            pass
    return agents


def save_agents(agents: list[Agent]) -> None:
    """Save agents to state file"""
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    data = {
        "agents": [
            {
                "id": a.id,
                "name": a.name,
                "description": a.description,
                "status": a.status.value,
                "metadata": {
                    "owner": a.metadata.owner,
                    "sponsor": a.metadata.sponsor,
                    "use_case": a.metadata.use_case,
                    "risk_tier": a.metadata.risk_tier.value,
                    "data_classification": a.metadata.data_classification.value
                },
                "service_principal_id": a.service_principal_id
            }
            for a in agents
        ]
    }
    with open(STATE_FILE, "w") as f:
        json.dump(data, f)


def find_agent(agents: list[Agent], agent_id: str) -> Optional[Agent]:
    """Find agent by ID or name"""
    for a in agents:
        if a.id == agent_id or a.name == agent_id:
            return a
    return None


class CLI:
    """Agent Identity Lifecycle Management CLI"""
    
    def register(
        self,
        name: str,
        owner: str,
        description: str = "",
        sponsor: str = None,
        use_case: str = "",
        risk_tier: str = "medium",
        data_classification: str = "internal"
    ):
        """Register a new agent"""
        agents = load_agents()
        metadata = AgentMetadata(
            owner=owner,
            sponsor=sponsor,
            use_case=use_case or "",
            risk_tier=RiskTier(risk_tier),
            data_classification=DataClassification(data_classification)
        )
        
        agent = Agent(
            name=name,
            description=description or "",
            status=AgentStatus.ACTIVE,
            metadata=metadata
        )
        
        agents.append(agent)
        save_agents(agents)
        
        # Audit log
        audit = AuditLogger()
        audit.log(
            event_type=AuditEventType.AGENT_REGISTERED,
            agent_id=agent.id,
            actor=owner,
            action="register_agent",
            details={"name": name, "risk_tier": risk_tier}
        )
        
        return f"✓ Registered agent: {agent.name} (ID: {agent.id})"
    
    def list(self):
        """List all agents"""
        agents = load_agents()
        
        if not agents:
            return "No agents registered"
        
        output = [f"{'Name':<30} {'Status':<12} {'Owner':<25} {'Risk':<10}", "-" * 80]
        
        for agent in agents:
            output.append(f"{agent.name:<30} {agent.status.value:<12} {agent.metadata.owner:<25} {agent.metadata.risk_tier.value:<10}")
        
        output.append(f"\nTotal: {len(agents)} agent(s)")
        return "\n".join(output)
    
    def show(self, agent_id: str):
        """Show agent details"""
        agents = load_agents()
        agent = find_agent(agents, agent_id)
        
        if not agent:
            return f"Agent not found: {agent_id}"
        
        lines = [
            f"Name: {agent.name}",
            f"ID: {agent.id}",
            f"Status: {agent.status.value}",
            f"Description: {agent.description}",
            f"Owner: {agent.metadata.owner}",
            f"Sponsor: {agent.metadata.sponsor or '-'}",
            f"Use Case: {agent.metadata.use_case or '-'}",
            f"Risk Tier: {agent.metadata.risk_tier.value}",
            f"Data Classification: {agent.metadata.data_classification.value}",
        ]
        return "\n".join(lines)
    
    def update(
        self,
        agent_id: str,
        name: str = None,
        description: str = None,
        owner: str = None,
        sponsor: str = None
    ):
        """Update an agent"""
        agents = load_agents()
        agent = find_agent(agents, agent_id)
        
        if not agent:
            return f"Agent not found: {agent_id}"
        
        if name:
            agent.name = name
        if description:
            agent.description = description
        if owner:
            agent.metadata.owner = owner
        if sponsor:
            agent.metadata.sponsor = sponsor
        
        save_agents(agents)
        
        audit = AuditLogger()
        audit.log(
            event_type=AuditEventType.AGENT_UPDATED,
            agent_id=agent.id,
            actor=owner or "unknown",
            action="update_agent",
            details={"name": agent.name}
        )
        
        return f"✓ Updated agent: {agent.name}"
    
    def deprecate(self, agent_id: str):
        """Deprecate an agent"""
        agents = load_agents()
        agent = find_agent(agents, agent_id)
        
        if not agent:
            return f"Agent not found: {agent_id}"
        
        agent.status = AgentStatus.DEPRECATED
        from datetime import datetime
        agent.deprecated_at = datetime.utcnow()
        
        save_agents(agents)
        
        audit = AuditLogger()
        audit.log(
            event_type=AuditEventType.AGENT_DEPRECATED,
            agent_id=agent.id,
            actor="cli",
            action="deprecate_agent"
        )
        
        return f"✓ Deprecated agent: {agent.name}"
    
    def audit(self, agent_id: str = None):
        """Show audit logs"""
        audit = AuditLogger()
        events = audit.get_events(agent_id=agent_id)
        
        if not events:
            return "No audit events found"
        
        output = [f"{'Timestamp':<28} {'Type':<22} {'Actor':<25} {'Status':<10}", "-" * 90]
        
        for event in events:
            output.append(f"{event.timestamp.isoformat():<28} {event.event_type.value:<22} {event.actor:<25} {event.status:<10}")
        
        output.append(f"\nTotal: {len(events)} event(s)")
        return "\n".join(output)


def main():
    fire.Fire(CLI)


if __name__ == "__main__":
    main()