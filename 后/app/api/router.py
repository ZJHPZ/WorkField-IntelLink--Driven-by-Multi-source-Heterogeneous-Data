"""顶层路由聚合 —— 所有 /api/* 子路由在此挂载。"""

from __future__ import annotations

from fastapi import APIRouter

from app.api import graph, positions, metrics, match, enterprise, personal

api_router = APIRouter()

api_router.include_router(graph.router, tags=["图谱"])
api_router.include_router(positions.router, tags=["岗位"])
api_router.include_router(metrics.router, tags=["指标"])
api_router.include_router(match.router, tags=["匹配"])
api_router.include_router(enterprise.router, prefix="/enterprise", tags=["企业工作台"])
api_router.include_router(personal.router, prefix="/personal", tags=["个人工作台"])
