import json
import logging
import re

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
import httpx

app = FastAPI()

MCP_URL = "http://localhost:9000/mcp/"
MCP_HEADERS = {
    "accept": "application/json, text/event-stream",
    "content-type": "application/json"
}

# 儲存初始化後的 MCP session id 和 cookies
mcp_session_id = None
mcp_cookies = None


async def initialize_mcp():
    global mcp_session_id, mcp_cookies
    logging.info("\n\n⚙️ 嘗試初始化 MCP server...")

    init_payload = {
        "jsonrpc": "2.0",
        "id": "flutter-proxy",
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {
                "name": "flutter-proxy",
                "version": "0.1.0"
            }
        }
    }

    async with httpx.AsyncClient(timeout=10) as client:
        try:
            response = await client.post(MCP_URL, headers=MCP_HEADERS, json=init_payload)
            if response.status_code != 200:
                logging.warning(f"⚠️ MCP 初始化回應非 200：{response.status_code} {response.text}")
                return False

            # 儲存 mcp-session-id 與 cookies
            mcp_session_id = response.headers.get("mcp-session-id")
            mcp_cookies = response.cookies
            logging.info(f"✅ MCP session_id: {mcp_session_id}")
            logging.info(f"✅ MCP cookies: {mcp_cookies}")
            return True

        except Exception as e:
            logging.error(f"❌ MCP 初始化失敗：{e}")
            return False


@app.post("/rest-mcp")
async def rest_mcp(request: Request):
    global mcp_session_id, mcp_cookies

    body = await request.json()
    action = body.get("action")
    data = body.get("data", {})

    logging.info(f"\n\n💬 收到來自 Flutter 的請求：{body}")

    # 若尚未初始化，則執行初始化
    if not mcp_session_id:
        success = await initialize_mcp()
        if not success:
            raise HTTPException(status_code=500, detail="Failed to initialize MCP")

    # 構造 JSON-RPC payload
    payload = {
        "jsonrpc": "2.0",
        "id": "flutter-proxy",
        "method": "tools/call",
        "params": {
            "name": action,
            "arguments": "Henry"
        }
    }

    logging.info(f"\n\n🚀 Proxy 要送出的 payload：{json.dumps(payload)}")

    async with httpx.AsyncClient(timeout=10, cookies=mcp_cookies) as client:
        try:
            headers = MCP_HEADERS.copy()
            if mcp_session_id:
                headers["mcp-session-id"] = mcp_session_id

            response = await client.post(MCP_URL, headers=headers, json=payload)
            text = response.text
            logging.warning(f"⚠️ MCP 回應成功（{response.status_code}）：{text}")

            # 從 text/event-stream 抽出 data: {...}
            match = re.search(r'data:\s*(\{.*\})', text)
            if match:
                json_str = match.group(1)
                return JSONResponse(content=json.loads(json_str))

            raise HTTPException(status_code=500, detail="Failed to parse MCP response")

        except Exception as e:
            logging.error(f"❌ 發生錯誤：{e}")
            raise HTTPException(status_code=500, detail=str(e))
