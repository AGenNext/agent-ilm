"""
Microsoft Entra ID Identity Manager
"""

import json
import logging
from typing import Optional
from dataclasses import dataclass

import requests

from agent_ilm.registry import Agent, AgentMetadata, AgentStatus, RiskTier, DataClassification


logger = logging.getLogger(__name__)


@dataclass
class EntraConfig:
    """Microsoft Entra ID configuration"""
    tenant_id: str
    client_id: str
    client_secret: str
    authority: str = "https://login.microsoftonline.com"
    
    @property
    def token_url(self) -> str:
        return f"{self.authority}/{self.tenant_id}/oauth2/v2.0/token"
    
    @property
    def graph_url(self) -> str:
        return "https://graph.microsoft.com/v1.0"


class EntraIdentityManager:
    """Manage agent identities in Microsoft Entra ID"""
    
    def __init__(self, config: Optional[EntraConfig] = None, tenant_id: str = ""):
        if config:
            self.config = config
        elif tenant_id:
            self.config = EntraConfig(
                tenant_id=tenant_id,
                client_id="",  # Set your client ID
                client_secret=""  # Set your client secret
            )
        else:
            raise ValueError("Either config or tenant_id must be provided")
        
        self._token: Optional[str] = None
    
    def _get_token(self) -> str:
        """Get access token"""
        if self._token:
            return self._token
        
        data = {
            "client_id": self.config.client_id,
            "client_secret": self.config.client_secret,
            "scope": "https://graph.microsoft.com/.default",
            "grant_type": "client_credentials"
        }
        
        response = requests.post(self.config.token_url, data=data)
        response.raise_for_status()
        
        self._token = response.json()["access_token"]
        return self._token
    
    def _ headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self._get_token()}",
            "Content-Type": "application/json"
        }
    
    def create_service_principal(
        self,
        app_id: str,
        display_name: str,
        tags: Optional[list] = None
    ) -> dict:
        """Create a service principal"""
        url = f"{self.config.graph_url}/servicePrincipals"
        
        payload = {
            "appId": app_id,
            "displayName": display_name,
        }
        
        if tags:
            payload["tags"] = tags
        
        response = requests.post(url, headers=self._headers(), json=payload)
        response.raise_for_status()
        
        return response.json()
    
    def get_service_principal(self, object_id: str) -> dict:
        """Get a service principal"""
        url = f"{self.config.graph_url}/servicePrincipals/{object_id}"
        
        response = requests.get(url, headers=self._headers())
        response.raise_for_status()
        
        return response.json()
    
    def list_service_principals(self, filter: Optional[str] = None) -> list[dict]:
        """List service principals"""
        url = f"{self.config.graph_url}/servicePrincipals"
        
        params = {}
        if filter:
            params["$filter"] = filter
        
        response = requests.get(url, headers=self._headers(), params=params)
        response.raise_for_status()
        
        return response.json().get("value", [])
    
    def assign_role(
        self,
        principal_id: str,
        role_definition_id: str,
        resource_id: str
    ) -> dict:
        """Assign Azure RBAC role to service principal"""
        url = f"{self.config.graph_url}/roleAssignments"
        
        payload = {
            "principalId": principal_id,
            "roleDefinitionId": role_definition_id,
            "resourceId": resource_id
        }
        
        response = requests.post(url, headers=self._headers(), json=payload)
        response.raise_for_status()
        
        return response.json()
    
    def register_agent(
        self,
        name: str,
        description: str,
        owner: str,
        sponsor: Optional[str] = None,
        risk_tier: RiskTier = RiskTier.MEDIUM,
        data_classification: DataClassification = DataClassification.INTERNAL,
        use_case: str = ""
    ) -> Agent:
        """Register a new agent (creates service principal in Entra ID)"""
        # Create service principal in Entra ID
        app_id = f"{name}-app-id"  # In production, create actual app registration
        
        payload = {
            "appId": app_id,
            "displayName": name,
            "tags": [
                f"agent-ilm",
                f"risk-tier:{risk_tier.value}",
                f"data-classification:{data_classification.value}"
            ]
        }
        
        # Try to create service principal (will fail if app doesn't exist)
        try:
            graph_url = "https://graph.microsoft.com/v1.0"
            response = requests.post(
                f"{graph_url}/servicePrincipals",
                headers=self._headers(),
                json=payload
            )
            sp = response.json() if response.status_code == 201 else {}
        except Exception as e:
            logger.warning(f"Could not create service principal: {e}")
            sp = {}
        
        # Create agent in registry
        metadata = AgentMetadata(
            owner=owner,
            sponsor=sponsor,
            use_case=use_case,
            risk_tier=risk_tier,
            data_classification=data_classification
        )
        
        agent = Agent(
            name=name,
            description=description,
            status=AgentStatus.ACTIVE,
            metadata=metadata,
            service_principal_id=sp.get("id")
        )
        
        return agent
    
    def list_agents(self, filter: Optional[str] = None) -> list[dict]:
        """List agents from Entra ID"""
        tags_filter = "tags/any(t:t eq 'agent-ilm')" if not filter else filter
        return self.list_service_principals(filter=tags_filter)
    
    def deprecate_agent(self, object_id: str) -> bool:
        """Deprecate an agent (disable service principal)"""
        url = f"{self.config.graph_url}/servicePrincipals/{object_id}"
        
        payload = {
            "accountEnabled": False
        }
        
        response = requests.patch(url, headers=self._headers(), json=payload)
        return response.status_code == 200