"""
「数知」智能学习平台 - 本地代理服务
用于将前端请求转发到远程服务器上的智能体系统

使用方法:
    python proxy_server.py

前端配置:
    VITE_API_BASE_URL=http://localhost:5000
"""

import asyncio
import json
import logging
from typing import Optional, Dict, Any
from contextlib import asynccontextmanager

import httpx
import websockets
import fastapi
from fastapi import FastAPI, Request, Response, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ==================== 配置区域 ====================

# 服务器地址配置
# 已配置为: https://tg6v6v36r5.coze.site
SERVER_BASE_URL = "https://tg6v6v36r5.coze.site"

# 超时配置
TIMEOUT_CONFIG = httpx.Timeout(
    connect=10.0,      # 连接超时
    read=60.0,        # 读取超时
    write=30.0,       # 写入超时
    pool=30.0         # 连接池超时
)

# ==================== FastAPI应用 ====================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    logger.info(f"🚀 代理服务启动，连接到: {SERVER_BASE_URL}")
    logger.info("📝 前端请配置: VITE_API_BASE_URL=http://localhost:5000")
    yield
    logger.info("👋 代理服务关闭")

app = FastAPI(
    title="数知智能学习平台 - 本地代理",
    description="将请求转发到远程智能体系统",
    version="1.0.0",
    lifespan=lifespan
)

# CORS配置 - 允许前端访问
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # Vite默认端口
        "http://127.0.0.1:3000",
        "http://localhost:5173",   # Vite备选端口
        "*"                        # 生产环境可限制
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==================== 代理核心逻辑 ====================

async def forward_request(
    method: str,
    path: str,
    headers: Dict[str, str],
    params: Optional[Dict] = None,
    body: Optional[bytes] = None
) -> httpx.Response:
    """
    转发请求到远程服务器
    
    Args:
        method: HTTP方法 (GET, POST, etc.)
        path: 请求路径
        headers: 请求头
        params: 查询参数
        body: 请求体
    
    Returns:
        httpx.Response: 服务器响应
    """
    # 构建目标URL
    target_url = f"{SERVER_BASE_URL}{path}"
    
    # 清理headers
    cleaned_headers = {}
    exclude_headers = {"host", "content-length"}
    for key, value in headers.items():
        if key.lower() not in exclude_headers:
            cleaned_headers[key] = value
    
    logger.info(f"📤 转发请求: {method} {target_url}")
    
    async with httpx.AsyncClient(timeout=TIMEOUT_CONFIG) as client:
        response = await client.request(
            method=method,
            url=target_url,
            headers=cleaned_headers,
            params=params,
            content=body,
            follow_redirects=True
        )
    
    logger.info(f"📥 收到响应: {response.status_code}")
    return response


# ==================== 代理路由 ====================

@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"])
async def proxy(path: str, request: Request):
    """
    通用代理路由 - 捕获所有请求并转发到远程服务器
    """
    try:
        # 获取请求信息
        body = await request.body()
        params = dict(request.query_params)
        headers = dict(request.headers)
        
        # 转发请求
        response = await forward_request(
            method=request.method,
            path=f"/{path}",
            headers=headers,
            params=params,
            body=body if body else None
        )
        
        # 返回响应
        return Response(
            content=response.content,
            status_code=response.status_code,
            headers=dict(response.headers),
            media_type=response.headers.get("content-type")
        )
        
    except httpx.TimeoutException as e:
        logger.error(f"⏰ 请求超时: {e}")
        raise HTTPException(status_code=504, detail="请求超时，请稍后重试")
    except httpx.ConnectError as e:
        logger.error(f"🔌 连接失败: {e}")
        raise HTTPException(status_code=502, detail="无法连接到服务器")
    except Exception as e:
        logger.error(f"❌ 未知错误: {e}")
        raise HTTPException(status_code=500, detail=f"代理服务错误: {str(e)}")


# ==================== WebSocket代理 ====================

@app.websocket("/ws/{path:path}")
async def websocket_proxy(websocket: fastapi.WebSocket, path: str):
    """
    WebSocket代理 - 转发WebSocket连接到远程服务器
    """
    import websockets
    
    # 构建目标URL (WebSocket)
    ws_scheme = "wss" if SERVER_BASE_URL.startswith("https") else "ws"
    server_host = SERVER_BASE_URL.replace("https://", "").replace("http://", "")
    target_url = f"{ws_scheme}://{server_host}/ws/{path}"
    
    await websocket.accept()
    logger.info(f"🔗 WebSocket代理: {websocket.client} -> {target_url}")
    
    try:
        async with websockets.connect(target_url) as remote_ws:
            logger.info(f"✅ WebSocket连接建立: {target_url}")
            
            async def forward_to_remote():
                """从本地转发到远程"""
                try:
                    while True:
                        data = await websocket.receive_text()
                        await remote_ws.send(data)
                except Exception:
                    pass
            
            async def forward_to_local():
                """从远程转发到本地"""
                try:
                    while True:
                        data = await remote_ws.recv()
                        if isinstance(data, str):
                            await websocket.send_text(data)
                        else:
                            await websocket.send_bytes(data)
                except Exception:
                    pass
            
            # 并发执行两个转发任务
            await asyncio.gather(
                forward_to_remote(),
                forward_to_local()
            )
            
    except websockets.exceptions.WebSocketException as e:
        logger.error(f"❌ WebSocket连接失败: {e}")
    except Exception as e:
        logger.error(f"❌ WebSocket错误: {e}")
    finally:
        await websocket.close()


# ==================== 健康检查 ====================

@app.get("/health")
async def health_check():
    """健康检查接口"""
    try:
        # 检查到服务器的连接
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{SERVER_BASE_URL}/health")
            server_status = "healthy" if response.status_code == 200 else "unhealthy"
    except Exception:
        server_status = "unreachable"
    
    return {
        "status": "ok",
        "proxy": "running",
        "server": server_status,
        "server_url": SERVER_BASE_URL
    }


@app.get("/")
async def root():
    """根路径 - 显示代理信息"""
    return {
        "name": "数知智能学习平台 - 本地代理",
        "version": "1.0.0",
        "status": "running",
        "server_url": SERVER_BASE_URL,
        "endpoints": {
            "proxy": "/*",
            "websocket": "/ws/*",
            "health": "/health"
        },
        "frontend_config": {
            "VITE_API_BASE_URL": "http://localhost:5000",
            "VITE_WS_URL": "ws://localhost:5000"
        }
    }


# ==================== 启动服务 ====================

def main():
    """启动代理服务"""
    print("""
╔══════════════════════════════════════════════════════════╗
║                                                          ║
║          「数知」智能学习平台 - 本地代理服务              ║
║                                                          ║
║  🏃 服务地址: http://localhost:5000                      ║
║  🔗 转发目标: {}                       ║
║                                                          ║
║  📝 前端环境变量配置:                                   ║
║     VITE_API_BASE_URL=http://localhost:5000            ║
║     VITE_WS_URL=ws://localhost:5000                    ║
║                                                          ║
╚══════════════════════════════════════════════════════════╝
    """.format(SERVER_BASE_URL[:40] + "..." if len(SERVER_BASE_URL) > 40 else SERVER_BASE_URL))
    
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=5000,
        log_level="info",
        reload=False  # 本地开发不需要热重载
    )


if __name__ == "__main__":
    main()
