from typing import List, Set
from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware


class WhitelistChecker:
    """白名单检查器类，负责路径匹配逻辑"""

    def __init__(self, whitelist_paths: List[str]):
        self.exact_paths: Set[str] = set()
        self.prefix_paths: List[str] = []

        # 解析和分类白名单路径
        for path in whitelist_paths:
            if path.endswith('/*'):  # 前缀匹配
                self.prefix_paths.append(path.rstrip('/*'))
            elif path.endswith('*'):  # 通配符匹配
                self.prefix_paths.append(path.rstrip('*'))
            else:  # 精确匹配
                self.exact_paths.add(path)

    def is_whitelisted(self, path: str) -> bool:
        """检查路径是否在白名单中"""
        # 优先检查精确匹配
        if path in self.exact_paths:
            return True

        # 检查前缀匹配
        return any(path.startswith(prefix) for prefix in self.prefix_paths)


class WhitelistMiddleware(BaseHTTPMiddleware):
    """白名单检查中间件类"""

    def __init__(self, app, whitelist_paths: List[str]):
        super().__init__(app)
        self.whitelist_checker = WhitelistChecker(whitelist_paths)

    async def dispatch(self, request: Request, call_next):
        """处理请求的核心方法"""
        request.state.is_whitelisted = self.whitelist_checker.is_whitelisted(request.url.path)
        response = await call_next(request)
        return response