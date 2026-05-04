#!/usr/bin/env python3
"""
Agent Identity Lifecycle Management CLI

A CLI tool for managing AI agent identities in Microsoft Entra ID.
Similar to Claude Code for developer productivity.
"""

import argparse
import sys
import os
from typing import Optional

from agent_ilm import AgentRegistry, Agent, AgentMetadata, RiskTier, DataClassification, AgentStatus
from agent_ilm import EntraIdentityManager, EntraConfig
from agent_ilm import AuditLogger, AuditEventType


class Context:
    """CLI context state"""
    
    def __init__(self):
        self.registry = AgentRegistry()
        self.audit = AuditLogger()
        self.manager: Optional[EntraIdentityManager] = None
    
    def init_manager(self, tenant_id: str, client_id: str = "", client_secret: str = "") -> None:
        """Initialize Entra ID manager"""
        self.manager = EntraIdentityManager(
            tenant_id=tenant_id,
            client_id=client_id or os.getenv("ENTRA_CLIENT_ID", ""),
            client_secret=client_secret or os.getenv("ENTRA_CLIENT_SECRET", "")
        )


# Global context
ctx = Context()


def cmd_register(args) -> int:
    """Register a new agent"""
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
        metadata=metadata
    )
    
    registered = ctx.registry.register(agent)
    
    # Audit log
    ctx.audit.log(
        event_type=AuditEventType.AGENT_REGISTERED,
        agent_id=registered.id,
        actor=args.owner,
        action="register_agent",
        details={"name": args.name, "risk_tier": args.risk_tier}
    )
    
    print(f"✓ Registered agent: {registered.name} (ID: {registered.id})")
    return 0


def cmd_list(args) -> int:
    """List all agents"""
    agents = ctx.registry.list_all()
    
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
    agent = ctx.registry.get(args.agent_id) or ctx.registry.get_by_name(args.agent_id)
    
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
    print(f"{'Created:':<20} {agent.created_at.isoformat()}")
    print(f"{'Updated:':<20} {agent.updated_at.isoformat()}")
    
    if agent.deprecated_at:
        print(f"{'Deprecated:':<20} {agent.deprecated_at.isoformat()}")
    
    return 0


def cmd_update(args) -> int:
    """Update an agent"""
    updates = {}
    
    if args.name:
        updates["name"] = args.name
    if args.description:
        updates["description"] = args.description
    if args.owner:
        updates["owner"] = args.owner
    if args.sponsor:
        updates["sponsor"] = args.sponsor
    
    agent = ctx.registry.update(args.agent_id, **updates)
    
    if not agent:
        print(f"Agent not found: {args.agent_id}")
        return 1
    
    ctx.audit.log(
        event_type=AuditEventType.AGENT_UPDATED,
        agent_id=agent.id,
        actor=updates.get("owner", "unknown"),
        action="update_agent",
        details=updates
    )
    
    print(f"✓ Updated agent: {agent.name}")
    return 0


def cmd_deprecate(args) -> int:
    """Deprecate an agent"""
    agent = ctx.registry.deprecate(args.agent_id)
    
    if not agent:
        print(f"Agent not found: {args.agent_id}")
        return 1
    
    ctx.audit.log(
        event_type=AuditEventType.AGENT_DEPRECATED,
        agent_id=agent.id,
        actor="cli",
        action="deprecate_agent"
    )
    
    print(f"✓ Deprecated agent: {agent.name}")
    return 0


def cmd_audit(args) -> int:
    """Show audit logs"""
    events = ctx.audit.get_events(
        agent_id=args.agent_id,
        start_time=args.start_time,
        end_time=args.end_time
    )
    
    if not events:
        print("No audit events found")
        return 0
    
    print(f"\n{'Timestamp':<28} {'Type':<22} {'Actor':<25} {'Status':<10}")
    print("-" * 90)
    
    for event in events:
        print(f"{event.timestamp.isoformat():<28} {event.event_type.value:<22} {event.actor:<25} {event.status:<10}")
    
    print(f"\nTotal: {len(events)} event(s)")
    return 0


def cmd_init(args) -> int:
    """Initialize configuration"""
    if not args.tenant_id:
        print("Error: --tenant-id is required")
        return 1
    
    ctx.init_manager(
        tenant_id=args.tenant_id,
        client_id=args.client_id,
        client_secret=args.client_secret
    )
    
    print(f"✓ Initialized for tenant: {args.tenant_id}")
    return 0


def main():
    parser = argparse.ArgumentParser(
        description="Agent Identity Lifecycle Management CLI",
        prog="agent-ilm"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # init
    p_init = subparsers.add_parser("init", help="Initialize configuration")
    p_init.add_argument("--tenant-id", required=True, help="Entra tenant ID")
    p_init.add_argument("--client-id", help="Application client ID")
    p_init.add_argument("--client-secret", help="Application client secret")
    
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
    p_audit.add_argument("--start-time", help="Start time (ISO format)")
    p_audit.add_argument("--end-time", help="End time (ISO format)")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 0
    
    commands = {
        "init": cmd_init,
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