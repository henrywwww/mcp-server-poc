from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastmcp.client import Client
from fastmcp.utilities.types import BaseContent, ToolOutput
import logging

app = FastAPI()

# 初始化 log 設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("proxy-server")

MCP_SERVER_URL = "http://localhost:9000/mcp/"  # 改成你的 MCP URL

@app.post("/mcp-proxy")
async def mcp_proxy(request: Request):
    logger.info("📥 收到 /mcp-proxy 請求")

    try:
        body = await request.json()
        logger.info(f"✅ request body = {body}")
    except Exception as e:
        logger.error(f"❌ 無法解析 JSON body: {e}")
        return JSONResponse(content={"error": "Invalid JSON body"}, status_code=400)

    method = body.get("method")
    params = body.get("params", {})

    if not method:
        logger.warning("⚠️ 缺少 method 參數")
        return JSONResponse(content={"error": "Missing method"}, status_code=400)

    try:
        logger.info(f"🚀 初始化 fastmcp client，目標伺服器：{MCP_SERVER_URL}")
        async with Client(MCP_SERVER_URL) as client:
            logger.info(f"📡 呼叫 MCP 工具: {method}，參數: {params}")
            result = await client.call_tool(method, params)
            logger.info(f"✅ MCP 回傳結果：{result}")

        # 處理回傳格式
        if isinstance(result, (BaseContent, ToolOutput)):
            logger.info("🛠 轉換 MCP 回傳結果為 dict")
            result = result.model_dump()

        return JSONResponse(content={"result": result})

    except Exception as e:
        logger.exception(f"🔥 發生 proxy 錯誤：{e}")
        return JSONResponse(content={"error": f"Proxy error: {str(e)}"}, status_code=500)