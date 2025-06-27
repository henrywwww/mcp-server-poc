import logging
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastmcp.client import Client
from fastmcp.prompts.prompt import TextContent
import asyncio

app = FastAPI()
logger = logging.getLogger("proxy-server")
logging.basicConfig(level=logging.INFO)

MCP_SERVER_URL = "http://localhost:9000/mcp/"
client: Client | None = None

# 初始化 FastMCP Client
async def get_client() -> Client:
    global client
    if client is None:
        logger.info(f"🚀 初始化 FastMCP Client，連線至：{MCP_SERVER_URL}")
        client = Client(base_url=MCP_SERVER_URL)
        await client.__aenter__()
    return client

@app.post("/mcp-proxy")
async def mcp_proxy(request: Request):
    logger.info("📥 收到 /mcp-proxy 請求")
    try:
        body = await request.json()
        logger.info(f"✅ request body = {body}")

        method = body.get("method")
        params = body.get("params", {})

        if not method:
            return JSONResponse(status_code=400, content={"error": "Missing method"})

        cl = await get_client()
        logger.info(f"📡 呼叫工具 {method} with {params}")

        result = await cl.call_tool(name=method, arguments=params)

        logger.info(f"✅ MCP 回傳：{result}")

        # 若為 TextContent 或 List[TextContent]，轉換為可序列化格式
        if isinstance(result, TextContent):
            logger.info("🔄 MCP 回傳為 TextContent，執行 model_dump()")
            result = result.model_dump()
        elif isinstance(result, list) and all(isinstance(r, TextContent) for r in result):
            logger.info("🔄 MCP 回傳為 TextContent 列表，執行每個 model_dump()")
            result = [r.model_dump() for r in result]

        logger.info("📤 回傳 JSON 給 client")
        return JSONResponse(content={"result": result})

    except Exception as e:
        logger.exception(f"🔥 MCP proxy 錯誤：{e}")
        return JSONResponse(status_code=500, content={"error": str(e)})