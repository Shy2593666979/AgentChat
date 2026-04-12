"""
Redis Session 管理器，对应 Java RedisSessionManager
L1: cachetools TTLCache (本地内存)
L2: Redis (分布式)
"""
import json
import socket
import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional
import redis.asyncio as aioredis
from cachetools import TTLCache

from agentchat.mcp_proxy.session.models import McpProxySession, ClientInfo, ClientCapabilities, SessionState


SESSION_TTL_SECONDS = 1800
SESSION_KEY_PREFIX = "mcp:session:"

def _session_to_dict(s: McpProxySession) -> dict:
    return {
        "session_id": s.session_id,
        "server_name": s.server_name,
        "environment": s.environment,
        "client_info": {"name": s.client_info.name, "version": s.client_info.version},
        "client_capabilities": {
            "supports_roots": s.client_capabilities.supports_roots,
            "supports_sampling": s.client_capabilities.supports_sampling,
            "supports_experimental": s.client_capabilities.supports_experimental,
        },
        "created_at": s.created_at.isoformat(),
        "last_accessed_at": s.last_accessed_at.isoformat(),
        "expires_at": s.expires_at.isoformat() if s.expires_at else None,
        "current_node_id": s.current_node_id,
        "backend_sessions": s.backend_sessions,
        "attributes": s.attributes,
        "state": s.state.value,
    }


def _dict_to_session(d: dict) -> McpProxySession:
    ci = d.get("client_info", {})
    cc = d.get("client_capabilities", {})
    return McpProxySession(
        session_id=d["session_id"],
        server_name=d["server_name"],
        environment=d.get("environment", "prod"),
        client_info=ClientInfo(name=ci.get("name", "unknown"), version=ci.get("version", "0.0.0")),
        client_capabilities=ClientCapabilities(
            supports_roots=cc.get("supports_roots", False),
            supports_sampling=cc.get("supports_sampling", False),
            supports_experimental=cc.get("supports_experimental", False),
        ),
        created_at=datetime.fromisoformat(d["created_at"]),
        last_accessed_at=datetime.fromisoformat(d["last_accessed_at"]),
        expires_at=datetime.fromisoformat(d["expires_at"]) if d.get("expires_at") else None,
        current_node_id=d.get("current_node_id", ""),
        backend_sessions=d.get("backend_sessions", {}),
        attributes=d.get("attributes", {}),
        state=SessionState(d.get("state", "CREATED")),
    )


class SessionManager:
    def __init__(self, redis_client: aioredis.Redis):
        self._redis = redis_client
        self._local: TTLCache = TTLCache(maxsize=1000, ttl=30)
        self._node_id = socket.gethostname()

    def _key(self, session_id: str) -> str:
        return f"{SESSION_KEY_PREFIX}{session_id}"

    async def create_session(
        self,
        server_name: str,
        environment: str,
        client_info: ClientInfo,
        capabilities: ClientCapabilities,
    ) -> McpProxySession:
        session_id = f"mcp-proxy-{uuid.uuid4().hex[:8]}"
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(seconds=SESSION_TTL_SECONDS)
        session = McpProxySession(
            session_id=session_id,
            server_name=server_name,
            environment=environment,
            client_info=client_info,
            client_capabilities=capabilities,
            created_at=now,
            last_accessed_at=now,
            expires_at=expires_at,
            current_node_id=self._node_id,
            state=SessionState.CREATED,
        )
        await self._save(session)
        return session

    async def get_session(self, session_id: str) -> Optional[McpProxySession]:
        # L1
        cached = self._local.get(session_id)
        if cached:
            return cached
        # L2
        raw = await self._redis.get(self._key(session_id))
        if not raw:
            return None
        session = _dict_to_session(json.loads(raw))
        self._local[session_id] = session
        return session

    async def touch_session(self, session_id: str) -> Optional[McpProxySession]:
        session = await self.get_session(session_id)
        if session:
            session.touch()
            await self._save(session)
        return session

    async def delete_session(self, session_id: str):
        await self._redis.delete(self._key(session_id))
        self._local.pop(session_id, None)

    async def exists_session(self, session_id: str) -> bool:
        if session_id in self._local:
            return True
        return bool(await self._redis.exists(self._key(session_id)))

    async def _save(self, session: McpProxySession):
        data = json.dumps(_session_to_dict(session))
        await self._redis.setex(self._key(session.session_id), SESSION_TTL_SECONDS, data)
        self._local[session.session_id] = session
