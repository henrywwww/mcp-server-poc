import asyncio
import json
import logging
from typing import Any, Dict, List, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
import httpx
import os

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 全局HTTP客户端和MCP服务器配置
http_client: Optional[httpx.AsyncClient] = None
# MCP_SERVER_URL = os.getenv("MCP_SERVER_URL", "https://web-production-f44b.up.railway.app/mcp/")
MCP_SERVER_URL = "http://localhost:9000/mcp/"#os.getenv("MCP_SERVER_URL", "https://web-production-f44b.up.railway.app/mcp/")
# Pydantic模型
class MCPRequest(BaseModel):
    method: str = Field(..., description="MCP方法名")
    params: Optional[Dict[str, Any]] = Field(default=None, description="方法参数")

class MCPResponse(BaseModel):
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None
    message: Optional[str] = None

class ToolCallRequest(BaseModel):
    tool_name: str = Field(..., description="工具名称")
    arguments: Optional[Dict[str, Any]] = Field(default=None, description="工具参数")

class ResourceRequest(BaseModel):
    uri: str = Field(..., description="资源URI")

# 安全认证
security = HTTPBearer()

async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """验证Bearer token"""
    token = credentials.credentials
    # 这里可以实现你的token验证逻辑
    # 例如验证JWT token或查询数据库
    expected_token = os.getenv("AUTH_TOKEN", "your-secret-token")
    if not token or token != expected_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return token

async def call_mcp_server(method: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
    """调用MCP服务器的HTTP API"""
    global http_client
    
    if not http_client:
        raise HTTPException(status_code=503, detail="HTTP客户端未初始化")
    
    # 构建JSON-RPC请求
    request_data = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": method,
        "params": params or {}
    }
    
    try:
        response = await http_client.post(
            MCP_SERVER_URL,
            json=request_data,
            timeout=30.0
        )
        response.raise_for_status()
        
        result = response.json()
        
        # 检查JSON-RPC错误
        if "error" in result:
            raise Exception(f"MCP服务器错误: {result['error']}")
        
        return result.get("result", {})
        
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="MCP服务器请求超时")
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=502, detail=f"MCP服务器返回错误: {e.response.status_code}")
    except Exception as e:
        logger.error(f"调用MCP服务器失败: {e}")
        raise HTTPException(status_code=500, detail=f"调用MCP服务器失败: {str(e)}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    global http_client
    
    try:
        # 启动时创建HTTP客户端
        logger.info("正在初始化HTTP客户端...")
        
        http_client = httpx.AsyncClient(
            timeout=httpx.Timeout(30.0),
            limits=httpx.Limits(max_keepalive_connections=5, max_connections=10)
        )
        
        # 测试连接到MCP服务器
        try:
            test_response = await http_client.get(MCP_SERVER_URL.rstrip('/'))
            logger.info(f"MCP服务器连接测试成功，状态码: {test_response.status_code}")
        except Exception as e:
            logger.warning(f"MCP服务器连接测试失败: {e}")
        
        logger.info("HTTP客户端初始化成功")
        yield
        
    except Exception as e:
        logger.error(f"初始化HTTP客户端失败: {e}")
        yield
    finally:
        # 关闭时清理连接
        if http_client:
            try:
                await http_client.aclose()
                logger.info("HTTP客户端已关闭")
            except Exception as e:
                logger.error(f"关闭HTTP客户端时出错: {e}")

# 创建FastAPI应用
app = FastAPI(
    title="MCP代理服务器",
    description="将REST API请求转发到MCP服务器",
    version="1.0.0",
    lifespan=lifespan
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境中应该设置具体的域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """健康检查端点"""
    return {"message": "MCP代理服务器运行正常", "status": "healthy"}

@app.get("/health")
async def health_check():
    """详细的健康检查"""
    global http_client
    
    http_status = "initialized" if http_client else "not_initialized"
    
    # 测试MCP服务器连接
    mcp_status = "unknown"
    try:
        if http_client:
            test_response = await http_client.get(
                MCP_SERVER_URL.rstrip('/'),
                timeout=5.0
            )
            mcp_status = "connected" if test_response.status_code == 200 else f"error_{test_response.status_code}"
    except Exception as e:
        mcp_status = f"error: {str(e)[:50]}"
    
    return {
        "status": "healthy",
        "http_client": http_status,
        "mcp_server": mcp_status,
        "mcp_url": MCP_SERVER_URL,
        "timestamp": asyncio.get_event_loop().time()
    }

@app.get("/tools", dependencies=[Depends(verify_token)])
async def list_tools() -> MCPResponse:
    """获取可用工具列表"""
    try:
        result = await call_mcp_server("tools/list")
        
        return MCPResponse(
            success=True,
            data=result.get("tools", []),
            message="成功获取工具列表"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取工具列表失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取工具列表失败: {str(e)}")

@app.post("/tools/call", dependencies=[Depends(verify_token)])
async def call_tool(request: ToolCallRequest) -> MCPResponse:
    """调用工具"""
    try:
        params = {
            "name": request.tool_name,
            "arguments": request.arguments or {}
        }
        result = await call_mcp_server("tools/call", params)
        
        return MCPResponse(
            success=True,
            data=result,
            message=f"成功调用工具: {request.tool_name}"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"调用工具失败: {e}")
        return MCPResponse(
            success=False,
            error=str(e),
            message=f"调用工具失败: {request.tool_name}"
        )

@app.get("/resources", dependencies=[Depends(verify_token)])
async def list_resources() -> MCPResponse:
    """获取可用资源列表"""
    try:
        result = await call_mcp_server("resources/list")
        
        return MCPResponse(
            success=True,
            data=result.get("resources", []),
            message="成功获取资源列表"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取资源列表失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取资源列表失败: {str(e)}")

@app.post("/resources/read", dependencies=[Depends(verify_token)])
async def read_resource(request: ResourceRequest) -> MCPResponse:
    """读取资源"""
    try:
        params = {"uri": request.uri}
        result = await call_mcp_server("resources/read", params)
        
        return MCPResponse(
            success=True,
            data=result,
            message=f"成功读取资源: {request.uri}"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"读取资源失败: {e}")
        return MCPResponse(
            success=False,
            error=str(e),
            message=f"读取资源失败: {request.uri}"
        )

@app.post("/mcp/call", dependencies=[Depends(verify_token)])
async def call_mcp_method(request: MCPRequest) -> MCPResponse:
    """通用MCP方法调用"""
    try:
        result = await call_mcp_server(request.method, request.params)
        
        return MCPResponse(
            success=True,
            data=result,
            message=f"成功调用方法: {request.method}"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"调用MCP方法失败: {e}")
        return MCPResponse(
            success=False,
            error=str(e),
            message=f"调用方法失败: {request.method}"
        )

# 错误处理
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return {
        "success": False,
        "error": exc.detail,
        "status_code": exc.status_code
    }

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    logger.error(f"未处理的异常: {exc}")
    return {
        "success": False,
        "error": "内部服务器错误",
        "message": str(exc)
    }

# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run(
#         "main:app",
#         host="0.0.0.0",
#         port=8000,
#         reload=True,
#         log_level="info"
#     )