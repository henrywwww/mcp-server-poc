from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastmcp.client import Client
from fastmcp.prompts.prompt import TextContent
import logging

app = FastAPI()

# 設定 logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("proxy-server")

# ✅ 修改成你的 MCP Server 實際位址（本機測試或 Railway 上）
MCP_SERVER_URL = "http://localhost:9000/mcp/"


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
        logger.info(f"🚀 初始化 FastMCP Client，連線至：{MCP_SERVER_URL}")
        async with Client(MCP_SERVER_URL) as client:
            logger.info(f"📡 呼叫工具 {method} with {params}")
            result = await client.call_tool(method, params)
            logger.info(f"✅ MCP 回傳：{result}")

        # 若為 TextContent，自動轉 dict
        if isinstance(result, TextContent):
            logger.info("🔄 MCP 回傳為 TextContent，執行 model_dump()")
            result = result.model_dump()

        logger.info("📤 回傳 JSON 給 client")
        return JSONResponse(content={"result": result})

    except Exception as e:
        logger.exception(f"🔥 MCP proxy 錯誤：{e}")
        return JSONResponse(content={"error": f"Proxy error: {str(e)}"}, status_code=500)


@app.get("/health")
async def health_check():
    return {"status": "ok"}