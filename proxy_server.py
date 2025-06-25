import json
import logging
import httpx
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse

app = FastAPI()

MCP_URL = "http://localhost:9000/mcp/"
MCP_SESSION_HEADER = "mcp-session-id"
MCP_HEADERS = {
    "Accept": "application/json, text/event-stream",
    "Content-Type": "application/json"
}

session_id_cache = None  # 存起初始化後的 session id

logging.basicConfig(level=logging.INFO)

async def initialize_mcp():
    global session_id_cache

    logging.info("\n⚙️  嘗試初始化 MCP server...")

    payload = {
        "jsonrpc": "2.0",
        "id": "flutter-proxy",
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {
                "name": "flutter-proxy",
                "version": "0.1"
            }
        }
    }

    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.post(MCP_URL, headers=MCP_HEADERS, json=payload)

        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail="初始化失敗")

        # 印出 headers
        logging.info("\nMCP Init Response Headers:")
        for key, value in response.headers.items():
            logging.info(f"   {key}: {value}")

        session_id = response.headers.get(MCP_SESSION_HEADER)
        if not session_id:
            raise HTTPException(status_code=500, detail="找不到 mcp-session-id")

        session_id_cache = session_id
        logging.info(f"\n✅ MCP session id: {session_id_cache}")

@app.post("/rest-mcp")
async def rest_mcp(request: Request):
    global session_id_cache
    
    req_json = await request.json()
    logging.info(f"\n💬 收到來自 Flutter 的請求：{req_json}")

    # 若沒有初始化過 MCP，就執行一次初始化
    if not session_id_cache:
        try:
            await initialize_mcp()
        except Exception as e:
            logging.error(f"❌ MCP 初始化失敗：{str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    method = req_json.get("action")
    params = req_json.get("data", {})

    # 若缺少 session_id，就自動補上
    if "session_id" not in params:
        params["session_id"] = session_id_cache

    payload = {
        "jsonrpc": "2.0",
        "id": "flutter-proxy",
        "method": "tools/call",
        "params": {
            "name": "hello_world",  # tool 名稱
            "input": params    # tool 的輸入參數
        }
    }

    logging.info(f"\n🚀 Proxy 要送出的 payload：{json.dumps(payload)}")

    async with httpx.AsyncClient(timeout=None) as client:
        headers = MCP_HEADERS.copy()
        if session_id_cache:
            headers["mcp-session-id"] = session_id_cache  # 🔑 加入 session id

        response = await client.post(MCP_URL, headers=headers, json=payload)

        if response.status_code != 200:
            logging.warning(f"⚠️ MCP 回應異常（{response.status_code}）：{response.text}")
            raise HTTPException(status_code=500, detail=response.text)

        try:
            logging.warning(f"⚠️ MCP 回應成功（{response.status_code}）：{response.text}")
            return JSONResponse(content=response.json())
        except Exception as e:
            logging.error(f"❌ 回應解析失敗：{str(e)}")
            raise HTTPException(status_code=500, detail=str(e))
