# Component Manifest

Agent ILM uses component manifests to describe SDK surfaces, CLI command groups, workflows, integrations, schemas, and policy modules in a machine-readable way.

Each cataloged component should include:

```text
catalog/<component-id>/component.json
```

Existing code can be migrated gradually. Normal validation warns about missing or incomplete catalog entries; strict validation enforces them.

## Required fields

| Field | Purpose |
| --- | --- |
| `schemaVersion` | Manifest schema version. Use `1.0.0`. |
| `id` | Stable lowercase component id. |
| `name` | Human-readable component name. |
| `version` | Component version. SemVer or date-based versions are accepted. |
| `description` | Short explanation of what the component provides. |
| `status` | One of `planned`, `experimental`, `active`, `maintenance`, or `deprecated`. |
| `kind` | Component type, such as `sdk`, `module`, `cli`, `workflow`, or `integration`. |
| `owner` | Owning team and optional contact. |
| `entrypoints` | Primary source path plus docs, tests, and examples. |
| `runtime` | Runtime language, version, package manager, and platforms. |
| `interfaces` | Python APIs, CLI commands, environment variables, and external APIs. |
| `dependencies` | Packages, APIs, identity providers, cloud services, or other components. |
| `security` | Data classification, auth requirements, roles, and secret names. |
| `operations` | Health checks, audit hooks, runbooks, and operational notes. |

## Example

```json
{
  "schemaVersion": "1.0.0",
  "id": "entra-identity-manager",
  "name": "Entra Identity Manager",
  "version": "0.1.0",
  "description": "Python SDK component for registering, listing, and managing AI agent identities in Microsoft Entra ID.",
  "status": "experimental",
  "kind": "sdk",
  "owner": {
    "team": "AGenNext",
    "github": "AGenNext"
  },
  "categories": ["agent-identity", "entra-id", "lifecycle", "sdk"],
  "entrypoints": {
    "primary": "agent_ilm/entra.py",
    "readme": "README.md",
    "docs": ["docs/component-manifest.md"],
    "tests": [],
    "examples": []
  },
  "runtime": {
    "language": "python",
    "minimumVersion": ">=3.10",
    "packageManager": "pip",
    "platforms": ["macos", "linux", "windows", "wsl"]
  },
  "interfaces": {
    "python": ["EntraIdentityManager"],
    "cli": ["agent-ilm"],
    "env": ["AZURE_TENANT_ID", "AZURE_CLIENT_ID", "AZURE_CLIENT_SECRET"],
    "externalApis": ["Microsoft Graph", "Microsoft Entra ID"]
  },
  "dependencies": [
    {
      "type": "package",
      "name": "requests",
      "required": true
    },
    {
      "type": "identity-provider",
      "name": "Microsoft Entra ID",
      "required": true
    }
  ],
  "security": {
    "dataClassification": "confidential",
    "authRequired": true,
    "roles": ["identity-admin", "application-admin"],
    "secrets": ["AZURE_CLIENT_SECRET"],
    "notes": "This component can create or update identity records and service principals. Use least-privilege Entra app permissions."
  },
  "operations": {
    "health": [],
    "audit": ["identity lifecycle operations should be logged"],
    "runbooks": [],
    "notes": "Rotate credentials and review agent ownership regularly."
  }
}
```

## Validation

Run migration-friendly validation:

```bash
python scripts/validate_catalog.py
```

Run strict validation:

```bash
python scripts/validate_catalog.py --strict
```

Build the generated catalog:

```bash
python scripts/build_catalog.py
```

This writes:

```text
catalog.json
```

## Best practices

- Keep component ids stable after publishing.
- Document all required Entra, Graph, and cloud permissions.
- List secrets by environment variable name only.
- Mark components that touch identity, authorization, credentials, or audit data as `confidential` or `restricted`.
- Add operational notes for credential rotation, deprovisioning, and access reviews.
- Use `deprecated` before removing a component from the catalog.
