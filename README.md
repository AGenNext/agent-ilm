# Agent Identity Lifecycle Management (agent-ilm)

Python SDK for managing AI agent identities in Microsoft Entra ID.

## Overview

This library provides tools for managing AI agent identities, including:
- Agent identity registration and lifecycle management
- Microsoft Entra ID integration
- Access review automation
- Audit logging and compliance

## Installation

```bash
pip install agent-ilm
```

## Quick Start

```python
from agent_ilm import AgentRegistry, EntraIdentityManager

# Initialize the identity manager
manager = EntraIdentityManager(tenant_id="your-tenant-id")

# Register a new agent
agent = manager.register_agent(
    name="copilot-agent-sales",
    description="AI agent for sales analytics",
    owner="sales-team@company.com",
    risk_tier="medium",
    data_classification="internal"
)

# List all registered agents
agents = manager.list_agents()
```

## Features

- **Agent Registry**: Track all agents with metadata (owners, sponsors, use cases)
- **Identity Management**: Create/update/deprecate service principals
- **Access Governance**: Azure RBAC, Conditional Access integration
- **Audit Logging**: Complete audit trail for compliance