import os
import logging
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastmcp.client import Client
from fastmcp.prompts.prompt import TextContent
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("proxy-server")

MCP_SERVER_URL = "http://localhost:9000/mcp/"
client: Client | None = None

# 初始化 FastMCP Client（使用 async factory）
async def get_client() -> Client:
    global client
    if client is None:
        logger.info(f"🚀 初始化 FastMCP Client，連線至：{MCP_SERVER_URL}")
        client = await Client.from_url(MCP_SERVER_URL)
    return client

@app.post("/mcp-proxy")
async def mcp_proxy(request: Request):
    try:
        logger.info("📥 收到 /mcp-proxy 請求")
        body = await request.json()
        logger.info(f"✅ request body = {body}")

        method = body.get("method")
        params = body.get("params", {})

        cl = await get_client()

        logger.info(f"📡 呼叫工具 {method} with {params}")
        result = await cl.call(method=method, params=params)
        logger.info(f"✅ MCP 回傳 = {result}")

        # 將 TextContent / ComplexOutput 等物件轉成 dict
        serialized_result = []
        for item in result:
            if hasattr(item, "model_dump"):
                serialized_result.append(item.model_dump())
            else:
                serialized_result.append(item)

        logger.info("📤 回傳 JSON 給 client")
        return JSONResponse(content={"result": serialized_result})

    except Exception as e:
        logger.exception(f"🔥 MCP proxy 錯誤：{e}")
        return JSONResponse(status_code=500, content={"error": str(e)})