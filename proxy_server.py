import os
import logging
from fastapi import FastAPI, Request
from fastmcp import Client
from fastapi.responses import JSONResponse

# 設定 Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("proxy-server")

# FastAPI 應用
app = FastAPI()

# MCP Server 位置
MCP_SERVER_URL = "http://localhost:9000/mcp/"

# 初始化 MCP Client（同步）
def get_client():
    logger.info(f"🚀 初始化 FastMCP Client，連線至：{MCP_SERVER_URL}")
    return Client(MCP_SERVER_URL)#, transport="streamable-http")

# /mcp-proxy endpoint
@app.post("/mcp-proxy")
async def mcp_proxy(request: Request):
    try:
        body = await request.json()
        logger.info(f"📥 收到 /mcp-proxy 請求")
        logger.info(f"✅ request body = {body}")

        method = body.get("method")
        params = body.get("params", {})

        # 初始化 Client 並呼叫 MCP
        cl = get_client()
        async with cl:
            result = await cl.call_tool(method, arguments=params)

        logger.info(f"✅ 回傳結果：{result}")
        return JSONResponse(content={"result": result})

    except Exception as e:
        logger.error(f"🔥 MCP proxy 錯誤：{e}", exc_info=True)
        return JSONResponse(content={"error": str(e)}, status_code=500)