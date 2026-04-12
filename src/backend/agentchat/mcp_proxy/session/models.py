from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from enum import Enum
from typing import Any


class SessionState(str, Enum):
    CREATED = "CREATED"
    ACTIVE = "ACTIVE"
    EXPIRED = "EXPIRED"
    CLOSED = "CLOSED"


@dataclass
class ClientInfo:
    name: str = "unknown"
    version: str = "0.0.0"


@dataclass
class ClientCapabilities:
    supports_roots: bool = False
    supports_sampling: bool = False
    supports_experimental: bool = False


@dataclass
class McpProxySession:
    session_id: str
    server_name: str
    environment: str = "prod"
    client_info: ClientInfo = field(default_factory=ClientInfo)
    client_capabilities: ClientCapabilities = field(default_factory=ClientCapabilities)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_accessed_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: datetime | None = None
    current_node_id: str = ""
    backend_sessions: dict[str, str] = field(default_factory=dict)
    attributes: dict[str, Any] = field(default_factory=dict)
    state: SessionState = SessionState.CREATED

    def touch(self):
        self.last_accessed_at = datetime.now(timezone.utc)

    def is_expired(self) -> bool:
        if self.expires_at is None:
            return False
        return datetime.now(timezone.utc) > self.expires_at

    def is_active(self) -> bool:
        return self.state == SessionState.ACTIVE and not self.is_expired()
