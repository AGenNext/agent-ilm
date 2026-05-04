#!/usr/bin/env python3
"""
Agent Identity Lifecycle Management CLI

A CLI tool for managing AI agent identities in Microsoft Entra ID.
Similar to Claude Code for developer productivity.
"""

import argparse
import sys
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


def cmd_register(args) -> int:
    """Register a new agent"""
    agents = load_agents()
    metadata = AgentMetadata(
        owner=args.owner,
        sponsor=args.sponsor,
        use_case=args.use_case or "",
        risk_tier=RiskTier(args.risk_tier),
        data_classification=DataClassification(args.data_classification)
    )
    
    agent = Agent(
        name=args.name,
        description=args.description or "",
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
        actor=args.owner,
        action="register_agent",
        details={"name": args.name, "risk_tier": args.risk_tier}
    )
    
    print(f"✓ Registered agent: {agent.name} (ID: {agent.id})")
    return 0


def cmd_list(args) -> int:
    """List all agents"""
    agents = load_agents()
    
    if not agents:
        print("No agents registered")
        return 0
    
    print(f"\n{'Name':<30} {'Status':<12} {'Owner':<25} {'Risk':<10}")
    print("-" * 80)
    
    for agent in agents:
        print(f"{agent.name:<30} {agent.status.value:<12} {agent.metadata.owner:<25} {agent.metadata.risk_tier.value:<10}")
    
    print(f"\nTotal: {len(agents)} agent(s)")
    return 0


def cmd_show(args) -> int:
    """Show agent details"""
    agents = load_agents()
    agent = find_agent(agents, args.agent_id)
    
    if not agent:
        print(f"Agent not found: {args.agent_id}")
        return 1
    
    print(f"\n{'Name:':<20} {agent.name}")
    print(f"{'ID:':<20} {agent.id}")
    print(f"{'Status:':<20} {agent.status.value}")
    print(f"{'Description:':<20} {agent.description}")
    print(f"{'Owner:':<20} {agent.metadata.owner}")
    print(f"{'Sponsor:':<20} {agent.metadata.sponsor or '-'}")
    print(f"{'Use Case:':<20} {agent.metadata.use_case or '-'}")
    print(f"{'Risk Tier:':<20} {agent.metadata.risk_tier.value}")
    print(f"{'Data Classification:':<20} {agent.metadata.data_classification.value}")
    
    return 0


def cmd_update(args) -> int:
    """Update an agent"""
    agents = load_agents()
    agent = find_agent(agents, args.agent_id)
    
    if not agent:
        print(f"Agent not found: {args.agent_id}")
        return 1
    
    if args.name:
        agent.name = args.name
    if args.description:
        agent.description = args.description
    if args.owner:
        agent.metadata.owner = args.owner
    if args.sponsor:
        agent.metadata.sponsor = args.sponsor
    
    save_agents(agents)
    
    audit = AuditLogger()
    audit.log(
        event_type=AuditEventType.AGENT_UPDATED,
        agent_id=agent.id,
        actor=args.owner or "unknown",
        action="update_agent",
        details={"name": agent.name}
    )
    
    print(f"✓ Updated agent: {agent.name}")
    return 0


def cmd_deprecate(args) -> int:
    """Deprecate an agent"""
    agents = load_agents()
    agent = find_agent(agents, args.agent_id)
    
    if not agent:
        print(f"Agent not found: {args.agent_id}")
        return 1
    
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
    
    print(f"✓ Deprecated agent: {agent.name}")
    return 0


def cmd_audit(args) -> int:
    """Show audit logs"""
    audit = AuditLogger()
    events = audit.get_events(agent_id=args.agent_id)
    
    if not events:
        print("No audit events found")
        return 0
    
    print(f"\n{'Timestamp':<28} {'Type':<22} {'Actor':<25} {'Status':<10}")
    print("-" * 90)
    
    for event in events:
        print(f"{event.timestamp.isoformat():<28} {event.event_type.value:<22} {event.actor:<25} {event.status:<10}")
    
    print(f"\nTotal: {len(events)} event(s)")
    return 0


def main():
    parser = argparse.ArgumentParser(
        description="Agent Identity Lifecycle Management CLI",
        prog="agent-ilm"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # register
    p_reg = subparsers.add_parser("register", help="Register a new agent")
    p_reg.add_argument("--name", required=True, help="Agent name")
    p_reg.add_argument("--description", help="Agent description")
    p_reg.add_argument("--owner", required=True, help="Technical owner email")
    p_reg.add_argument("--sponsor", help="Business sponsor email")
    p_reg.add_argument("--use-case", help="Use case")
    p_reg.add_argument("--risk-tier", default="medium", choices=["low", "medium", "high", "critical"], help="Risk tier")
    p_reg.add_argument("--data-classification", default="internal", choices=["public", "internal", "confidential", "restricted"], help="Data classification")
    
    # list
    p_list = subparsers.add_parser("list", help="List all agents")
    
    # show
    p_show = subparsers.add_parser("show", help="Show agent details")
    p_show.add_argument("agent_id", help="Agent ID or name")
    
    # update
    p_update = subparsers.add_parser("update", help="Update an agent")
    p_update.add_argument("agent_id", help="Agent ID")
    p_update.add_argument("--name", help="Agent name")
    p_update.add_argument("--description", help="Agent description")
    p_update.add_argument("--owner", help="Technical owner email")
    p_update.add_argument("--sponsor", help="Business sponsor email")
    
    # deprecate
    p_dep = subparsers.add_parser("deprecate", help="Deprecate an agent")
    p_dep.add_argument("agent_id", help="Agent ID")
    
    # audit
    p_audit = subparsers.add_parser("audit", help="Show audit logs")
    p_audit.add_argument("--agent-id", help="Filter by agent ID")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 0
    
    commands = {
        "register": cmd_register,
        "list": cmd_list,
        "show": cmd_show,
        "update": cmd_update,
        "deprecate": cmd_deprecate,
        "audit": cmd_audit
    }
    
    return commands[args.command](args)


if __name__ == "__main__":
    sys.exit(main())