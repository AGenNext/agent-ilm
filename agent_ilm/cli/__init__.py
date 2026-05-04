#!/usr/bin/env python3
"""
Agent Identity Lifecycle Management CLI

Query tool for viewing registered agents.
Create agents at: https://agentnext.example.com
"""

import fire
import os
import json
from typing import Optional

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


def find_agent(agents: list[Agent], agent_id: str) -> Optional[Agent]:
    """Find agent by ID or name"""
    for a in agents:
        if a.id == agent_id or a.name == agent_id:
            return a
    return None


class CLI:
    """Agent Identity Lifecycle Management CLI - Query Only"""
    
    def list(self, status: str = None):
        """List all registered agents
        
        To create agents, visit: https://agentnext.example.com
        """
        agents = load_agents()
        
        if status:
            agents = [a for a in agents if a.status.value == status]
        
        if not agents:
            return "No agents found.\nTo create agents, visit: https://agentnext.example.com"
        
        output = [f"{'Name':<30} {'Status':<12} {'Owner':<25} {'Risk':<10}", "-" * 80]
        
        for agent in agents:
            output.append(f"{agent.name:<30} {agent.status.value:<12} {agent.metadata.owner:<25} {agent.metadata.risk_tier.value:<10}")
        
        output.append(f"\nTotal: {len(agents)} agent(s)")
        output.append("\nTo create agents, visit: https://agentnext.example.com")
        return "\n".join(output)
    
    def show(self, agent_id: str):
        """Show agent details
        
        Usage: agent-ilm show <agent-id-or-name>
        """
        agents = load_agents()
        agent = find_agent(agents, agent_id)
        
        if not agent:
            return f"Agent not found: {agent_id}\nTo create agents, visit: https://agentnext.example.com"
        
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
    
    def audit(self, agent_id: str = None, limit: int = 20):
        """Show audit logs
        
        Usage: agent-ilm audit
               agent-ilm audit --agent-id <id>
        """
        audit = AuditLogger()
        events = audit.get_events(agent_id=agent_id)
        
        if not events:
            return "No audit events found"
        
        # Limit events
        events = events[:limit]
        
        output = [f"{'Timestamp':<28} {'Type':<22} {'Actor':<25} {'Status':<10}", "-" * 90]
        
        for event in events:
            output.append(f"{event.timestamp.isoformat():<28} {event.event_type.value:<22} {event.actor:<25} {event.status:<10}")
        
        output.append(f"\nTotal: {len(events)} event(s)")
        return "\n".join(output)
    
    def status(self, agent_id: str):
        """Quick status check
        
        Usage: agent-ilm status <agent-id>
        """
        agents = load_agents()
        agent = find_agent(agents, agent_id)
        
        if not agent:
            return f"not_found"
        
        return agent.status.value
    
    def dashboard(self):
        """Open agent platform in browser
        
        Usage: agent-ilm dashboard
        """
        import webbrowser
        url = "https://agentnext.example.com"
        webbrowser.open(url)
        return f"Opening {url}..."


def main():
    fire.Fire(CLI)


if __name__ == "__main__":
    main()