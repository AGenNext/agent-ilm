"""
Audit Logging for Agent Identity Lifecycle Management
"""

import json
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum
from typing import Any, Optional
import uuid


class AuditEventType(Enum):
    AGENT_REGISTERED = "agent_registered"
    AGENT_UPDATED = "agent_updated"
    AGENT_DEPRECATED = "agent_deprecated"
    AGENT_RETIRED = "agent_retired"
    ROLE_ASSIGNED = "role_assigned"
    ROLE_REVOKED = "role_revoked"
    ACCESS_REVIEWED = "access_reviewed"
    IDENTITY_CREATED = "identity_created"
    IDENTITY_DELETED = "identity_deleted"


@dataclass
class AuditEvent:
    """Audit event record"""
    id: str
    timestamp: datetime
    event_type: AuditEventType
    agent_id: str
    actor: str
    action: str
    details: dict
    resource_id: Optional[str] = None
    status: str = "success"
    error_message: Optional[str] = None


class AuditLogger:
    """Audit logger for agent identity operations"""
    
    def __init__(self, log_file: str = "audit.log"):
        self.log_file = log_file
    
    def log(
        self,
        event_type: AuditEventType,
        agent_id: str,
        actor: str,
        action: str,
        details: Optional[dict] = None,
        resource_id: Optional[str] = None,
        status: str = "success",
        error_message: Optional[str] = None
    ) -> AuditEvent:
        """Log an audit event"""
        event = AuditEvent(
            id=str(uuid.uuid4()),
            timestamp=datetime.utcnow(),
            event_type=event_type,
            agent_id=agent_id,
            actor=actor,
            action=action,
            details=details or {},
            resource_id=resource_id,
            status=status,
            error_message=error_message
        )
        
        self._write(event)
        return event
    
    def _write(self, event: AuditEvent) -> None:
        """Write event to log file"""
        with open(self.log_file, "a") as f:
            f.write(json.dumps(asdict(event)) + "\n")
    
    def get_events(
        self,
        agent_id: Optional[str] = None,
        event_type: Optional[AuditEventType] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> list[AuditEvent]:
        """Query audit events"""
        events = []
        
        try:
            with open(self.log_file, "r") as f:
                for line in f:
                    data = json.loads(line)
                    
                    if agent_id and data["agent_id"] != agent_id:
                        continue
                    
                    if event_type and data["event_type"] != event_type.value:
                        continue
                    
                    event_time = datetime.fromisoformat(data["timestamp"].replace("Z", "+00:00"))
                    
                    if start_time and event_time < start_time:
                        continue
                    
                    if end_time and event_time > end_time:
                        continue
                    
                    events.append(AuditEvent(**data))
        except FileNotFoundError:
            pass
        
        return events
    
    def generate_report(self, start_date: datetime, end_date: datetime) -> dict:
        """Generate audit summary report"""
        events = self.get_events(start_time=start_date, end_time=end_date)
        
        summary = {
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            },
            "total_events": len(events),
            "by_type": {},
            "by_status": {},
            "agents": set()
        }
        
        for event in events:
            event_type = event.event_type.value
            summary["by_type"][event_type] = summary["by_type"].get(event_type, 0) + 1
            
            summary["by_status"][event.status] = summary["by_status"].get(event.status, 0) + 1
            
            summary["agents"].add(event.agent_id)
        
        summary["agents"] = list(summary["agents"])
        summary["unique_agents"] = len(summary["agents"])
        
        return summary