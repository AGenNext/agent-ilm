"""Schema.org-compatible identity-aware decision graph events.

Every resource in the graph is identity-bearing: agents, tools, workflows,
memories, policies, evidence, decisions, outcomes, and even external resources
can be represented as subjects with stable identifiers, tenant ownership,
trust domain, authority level, and optional DID/VC metadata.
"""

from __future__ import annotations

import hashlib
import json
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

ResourceKind = Literal[
    "agent",
    "model",
    "tool",
    "workflow",
    "memory",
    "policy",
    "decision",
    "evidence",
    "task",
    "action",
    "outcome",
    "evaluation",
    "human",
    "tenant",
    "organization",
    "runtime",
    "kernel",
    "external",
]

AGENT_CONTEXT: dict[str, Any] = {
    "schema": "https://schema.org/",
    "agent": "https://agennext.ai/schema/agent#",
    "sec": "https://w3id.org/security#",
    "did": "https://www.w3.org/ns/did#",
    "IdentitySubject": "agent:IdentitySubject",
    "ResourceIdentity": "agent:ResourceIdentity",
    "Decision": "agent:Decision",
    "Agent": "agent:Agent",
    "Model": "agent:Model",
    "Tool": "agent:Tool",
    "Workflow": "agent:Workflow",
    "Memory": "agent:Memory",
    "Policy": "agent:Policy",
    "Evidence": "agent:Evidence",
    "Risk": "agent:Risk",
    "Constraint": "agent:Constraint",
    "Assumption": "agent:Assumption",
    "Action": "agent:Action",
    "Outcome": "agent:Outcome",
    "Evaluation": "agent:Evaluation",
    "hasIdentity": {"@id": "agent:hasIdentity", "@type": "@id"},
    "ownedByTenant": {"@id": "agent:ownedByTenant", "@type": "@id"},
    "belongsToTrustDomain": {"@id": "agent:belongsToTrustDomain", "@type": "@id"},
    "hasAuthorityLevel": {"@id": "agent:hasAuthorityLevel", "@type": "@id"},
    "hasPermission": {"@id": "agent:hasPermission", "@type": "@id"},
    "madeBy": {"@id": "agent:madeBy", "@type": "@id"},
    "usedModel": {"@id": "agent:usedModel", "@type": "@id"},
    "forTask": {"@id": "agent:forTask", "@type": "@id"},
    "usedTool": {"@id": "agent:usedTool", "@type": "@id"},
    "detectedRisk": {"@id": "agent:detectedRisk", "@type": "@id"},
    "followedConstraint": {"@id": "agent:followedConstraint", "@type": "@id"},
    "madeAssumption": {"@id": "agent:madeAssumption", "@type": "@id"},
    "selectedAction": {"@id": "agent:selectedAction", "@type": "@id"},
    "evaluatedBy": {"@id": "agent:evaluatedBy", "@type": "@id"},
    "producedOutcome": {"@id": "agent:producedOutcome", "@type": "@id"},
    "parentDecision": {"@id": "agent:parentDecision", "@type": "@id"},
    "revisesDecision": {"@id": "agent:revisesDecision", "@type": "@id"},
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def slug(value: str) -> str:
    return "".join(ch if ch.isalnum() or ch in "_.-" else "_" for ch in value.strip().lower())


def iri(kind: str, value: str) -> str:
    return f"agent:{kind}/{slug(value)}"


@dataclass(frozen=True)
class ResourceIdentity:
    """Identity metadata for any resource in the agent graph."""

    resource_id: str
    resource_kind: ResourceKind
    tenant_id: str | None = None
    trust_domain: str | None = None
    authority_level: str | None = None
    owner: str | None = None
    subject: str | None = None
    did: str | None = None
    credential_ids: list[str] = field(default_factory=list)
    permissions: list[str] = field(default_factory=list)
    lifecycle_status: str = "active"
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def node_id(self) -> str:
        return iri(self.resource_kind, self.resource_id)

    @property
    def identity_id(self) -> str:
        return iri("identity", f"{self.resource_kind}_{self.resource_id}")

    def to_jsonld(self) -> dict[str, Any]:
        return {
            "@id": self.identity_id,
            "@type": "ResourceIdentity",
            "schema:identifier": self.resource_id,
            "agent:resourceKind": self.resource_kind,
            "agent:subject": self.subject or self.node_id,
            "ownedByTenant": iri("tenant", self.tenant_id) if self.tenant_id else None,
            "belongsToTrustDomain": iri("trust_domain", self.trust_domain) if self.trust_domain else None,
            "hasAuthorityLevel": iri("authority", self.authority_level) if self.authority_level else None,
            "agent:owner": self.owner,
            "did:id": self.did,
            "sec:credential": self.credential_ids,
            "hasPermission": [iri("permission", permission) for permission in self.permissions],
            "agent:lifecycleStatus": self.lifecycle_status,
            "agent:metadata": self.metadata,
        }


def identity_node(identity: ResourceIdentity, node_type: str, properties: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        "@id": identity.node_id,
        "@type": node_type,
        "hasIdentity": identity.to_jsonld(),
        **(properties or {}),
    }


@dataclass(frozen=True)
class DecisionGraphEvent:
    agent: ResourceIdentity
    model: ResourceIdentity
    task: ResourceIdentity
    selected_action: str
    decision_id: str = field(default_factory=lambda: f"dec_{uuid.uuid4().hex[:12]}")
    task_name: str = "Decision"
    confidence: float = 0.0
    requires_human_review: bool = False
    assumptions: list[str] = field(default_factory=list)
    constraints: list[dict[str, Any]] = field(default_factory=list)
    risks: list[dict[str, Any]] = field(default_factory=list)
    evidence: list[dict[str, Any]] = field(default_factory=list)
    tools: list[ResourceIdentity] = field(default_factory=list)
    evaluation: dict[str, Any] | None = None
    outcome: dict[str, Any] | None = None
    parent_decision_id: str | None = None
    revises_decision_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_jsonld(self) -> dict[str, Any]:
        decision_identity = ResourceIdentity(
            resource_id=self.decision_id,
            resource_kind="decision",
            tenant_id=self.agent.tenant_id,
            trust_domain=self.agent.trust_domain,
            owner=self.agent.owner,
            lifecycle_status="recorded",
        )
        doc = identity_node(
            decision_identity,
            "Decision",
            {
                "@context": AGENT_CONTEXT,
                "schema:name": self.task_name,
                "schema:dateCreated": utc_now(),
                "madeBy": identity_node(self.agent, "Agent"),
                "usedModel": identity_node(self.model, "Model"),
                "forTask": identity_node(self.task, "Task"),
                "parentDecision": iri("decision", self.parent_decision_id) if self.parent_decision_id else None,
                "revisesDecision": iri("decision", self.revises_decision_id) if self.revises_decision_id else None,
                "madeAssumption": [
                    {
                        "@id": iri("assumption", f"{self.decision_id}_{index}"),
                        "@type": "Assumption",
                        "schema:text": text,
                    }
                    for index, text in enumerate(self.assumptions)
                ],
                "followedConstraint": [
                    {
                        "@id": iri("constraint", item["name"]),
                        "@type": "Constraint",
                        "schema:text": item.get("text", item["name"]),
                        "agent:priority": item.get("priority", "medium"),
                        "agent:status": item.get("status", "followed"),
                    }
                    for item in self.constraints
                ],
                "detectedRisk": [
                    {
                        "@id": iri("risk", item["name"]),
                        "@type": "Risk",
                        "schema:name": item["name"],
                        "agent:severity": item.get("severity", "medium"),
                        "agent:likelihood": item.get("likelihood", 0.0),
                        "agent:status": item.get("status", "detected"),
                    }
                    for item in self.risks
                ],
                "usedTool": [identity_node(tool, "Tool") for tool in self.tools],
                "selectedAction": {
                    "@id": iri("action", f"{self.decision_id}_{self.selected_action}"),
                    "@type": "Action",
                    "schema:name": self.selected_action,
                    "agent:confidence": self.confidence,
                    "agent:requiresHumanReview": self.requires_human_review,
                },
                "evaluatedBy": self.evaluation,
                "producedOutcome": self.outcome,
                "agent:metadata": self.metadata,
            },
        )
        canonical = json.dumps(doc, sort_keys=True, separators=(",", ":"))
        doc["agent:contentHash"] = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
        return doc


class DecisionGraphLogger:
    def __init__(self, log_file: str = "decision_graph.jsonl") -> None:
        self.log_file = Path(log_file)
        self.log_file.parent.mkdir(parents=True, exist_ok=True)

    def log(self, event: DecisionGraphEvent) -> dict[str, Any]:
        document = event.to_jsonld()
        with self.log_file.open("a", encoding="utf-8") as file:
            file.write(json.dumps(document, ensure_ascii=False) + "\n")
        return document

    def get_events(self) -> list[dict[str, Any]]:
        if not self.log_file.exists():
            return []
        with self.log_file.open("r", encoding="utf-8") as file:
            return [json.loads(line) for line in file if line.strip()]

    def log_identity_resource(self, identity: ResourceIdentity, node_type: str = "IdentitySubject") -> dict[str, Any]:
        document = {
            "@context": AGENT_CONTEXT,
            **identity_node(identity, node_type, {"schema:dateCreated": utc_now()}),
        }
        with self.log_file.open("a", encoding="utf-8") as file:
            file.write(json.dumps(document, ensure_ascii=False) + "\n")
        return document
