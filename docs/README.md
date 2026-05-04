# Agent Identity Lifecycle Management

**Version**: 0.1.0  
**Repository**: https://github.com/AGenNext/agent-ilm

## Overview

agent-ilm is a Python SDK for managing AI agent identities in Microsoft Entra ID. It provides tools for agent identity registration, lifecycle management, access governance, and audit logging.

## Why Agent Identity Management?

Every AI agent should have its own identity. In Microsoft environments, this means one service principal or managed identity per agent, with:

- **Explicit ownership** - Technical and business owners
- **Least-privilege permissions** - RBAC role assignments
- **Lifecycle controls** - Registration, updates, deprecation
- **Audit trails** - Compliance and accountability

## Installation

```bash
pip install agent-ilm
```

Or install from source:

```bash
git clone https://github.com/AGenNext/agent-ilm.git
cd agent-ilm
pip install -e .
```

## Quick Start

### Initialize the Identity Manager

```python
from agent_ilm import EntraIdentityManager, EntraConfig

# With tenant ID only (requires env vars for client credentials)
manager = EntraIdentityManager(tenant_id="your-tenant-id")

# Or with full configuration
config = EntraConfig(
    tenant_id="your-tenant-id",
    client_id="your-client-id",
    client_secret="your-client-secret"
)
manager = EntraIdentityManager(config=config)
```

### Register a New Agent

```python
from agent_ilm import RiskTier, DataClassification

agent = manager.register_agent(
    name="copilot-agent-sales",
    description="AI agent for sales analytics",
    owner="sales-team@company.com",
    sponsor="sales-director@company.com",
    risk_tier=RiskTier.MEDIUM,
    data_classification=DataClassification.INTERNAL,
    use_case="Sales data analysis and reporting"
)
```

### List All Agents

```python
agents = manager.list_agents()
for sp in agents:
    print(f"{sp['displayName']} - {sp['id']}")
```

### Deprecate an Agent

```python
manager.deprecate_agent(object_id="...")
```

## Using the Agent Registry

For in-memory tracking without Entra ID:

```python
from agent_ilm import AgentRegistry, Agent, AgentMetadata, RiskTier, DataClassification, AgentStatus

registry = AgentRegistry()

# Register an agent
metadata = AgentMetadata(
    owner="team@company.com",
    sponsor="director@company.com",
    use_case="Data processing",
    risk_tier=RiskTier.HIGH,
    data_classification=DataClassification.CONFIDENTIAL
)

agent = Agent(
    name="data-processor-agent",
    description="Process sensitive data",
    metadata=metadata
)

registered = registry.register(agent)
print(f"Registered: {registered.id}")

# List all agents
for a in registry.list_all():
    print(f"{a.name} - {a.status.value}")

# Deprecate an agent
registry.deprecate(agent.id)
```

## Audit Logging

```python
from agent_ilm import AuditLogger, AuditEventType
from datetime import datetime

logger = AuditLogger("audit.log")

# Log an event
logger.log(
    event_type=AuditEventType.AGENT_REGISTERED,
    agent_id="agent-123",
    actor="admin@company.com",
    action="register_agent",
    details={"name": "sales-agent", "risk_tier": "medium"}
)

# Query events
events = logger.get_events(agent_id="agent-123")

# Generate report
report = logger.generate_report(
    start_date=datetime(2024, 1, 1),
    end_date=datetime(2024, 12, 31)
)
```

## Configuration

### Environment Variables

- `ENTRA_TENANT_ID` - Microsoft Entra tenant ID
- `ENTRA_CLIENT_ID` - Application client ID
- `ENTRA_CLIENT_SECRET` - Application client secret

### Required Permissions

The application needs these Microsoft Graph permissions:

- `Application.ReadWrite.All` - Create service principals
- `Directory.ReadWrite.All` - Read directory data
- `RoleManagement.ReadWrite.Directory` - Assign roles

## Concepts

### Risk Tiers

| Tier | Description |
|------|-------------|
| `LOW` | Limited access, read-only operations |
| `MEDIUM` | Standard access, internal data |
| `HIGH` | Elevated access, sensitive data |
| `CRITICAL` | Full access, restricted data |

### Data Classifications

| Classification | Description |
|----------------|-------------|
| `PUBLIC` | Publicly available |
| `INTERNAL` | Internal company data |
| `CONFIDENTIAL` | Sensitive business data |
| `RESTRICTED` | Highly restricted data |

### Agent Status

| Status | Description |
|--------|-------------|
| `PENDING` | Awaiting approval |
| `ACTIVE` | Currently in use |
| `DEPRECATED` | Being phased out |
| `RETIRED` | No longer in use |

## Best Practices

### 1. Register Every Agent

Every AI agent should have its own identity. Don't share identities across agents.

### 2. Define Ownership

Each agent must have:
- **Technical owner** - Responsible for implementation
- **Business sponsor** - Accountable for use case

### 3. Apply Least Privilege

Grant only the permissions needed for the specific use case.

### 4. Monitor Activity

Use audit logging to track all identity operations.

### 5. Regular Reviews

Conduct periodic access reviews to identify:
- Unused identities
- Excessive permissions
- Orphaned accounts

## Related Resources

- [Microsoft Entra Agents](https://learn.microsoft.com/en-us/entra/security-copilot/entra-agents)
- [Agent Lifecycle Management](https://teamcopilot.nl/2026/03/14/managing-agent-identity-access-accountability/)
- [Microsoft Graph API](https://learn.microsoft.com/graph/use-the-api)

## License

MIT License - See LICENSE file for details.