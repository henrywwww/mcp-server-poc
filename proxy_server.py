
import json
import logging
import httpx
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
import asyncio

app = FastAPI()
logging.basicConfig(level=logging.INFO)

MCP_STREAM_URL = "http://localhost:9000/mcp/"
SESSION_ID = None
mcp_cookies = None
class RestMcpRequest(BaseModel):
    action: str
    data: dict

async def initialize_mcp() -> str:
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            logging.info("⚙️  嘗試初始化 MCP server...")
            init_response = await client.post(
                MCP_STREAM_URL,
                headers={
                    "Accept": "application/json, text/event-stream",
                    "Content-Type": "application/json"
                },
                json={
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
            )
            
            
            session_text = ""
            mcp_cookies = init_response.cookies

            logging.info("✅ MCP cookies: %s", mcp_cookies)

            logging.info("🧾 MCP Init Response Headers:")
            for key, value in init_response.headers.items():
                logging.info("   %s: %s", key, value)
            async for chunk in init_response.aiter_text():
                session_text += chunk
                logging.info("✅ MCP 初始化成功，session_text: %s", session_text)
                
                break  # 只讀第一段初始化即可

            
            

            
            return ""
        except Exception as e:
            logging.warning("⚠️ MCP 初始化失敗：%s", str(e))
            raise HTTPException(status_code=500, detail=str(e))

@app.post("/rest-mcp")
async def rest_mcp(request: Request):
    global SESSION_ID

    payload = await request.json()
    logging.info("💬 收到來自 Flutter 的請求：%s", payload)

    if SESSION_ID is None:
        try:
            SESSION_ID = await initialize_mcp()
        except HTTPException as e:
            raise e

    action = payload.get("action")
    data = payload.get("data", {})
    data["session_id"] = SESSION_ID  # 自動補上 session_id

    request_payload = {
        "jsonrpc": "2.0",
        "id": "proxy",
        "method": action,
        "params": data
    }

    logging.info("🚀 Proxy 要送出的 payload：%s", json.dumps(request_payload))

    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.post(
            MCP_STREAM_URL,
            headers={
                "Accept": "application/json, text/event-stream",
                "Content-Type": "application/json"
            },
            cookies=mcp_cookies,
            json=request_payload
        )

        if response.status_code != 200:
            logging.warning("⚠️ MCP 回應異常（%s）：%s", response.status_code, response.text)
            raise HTTPException(status_code=500, detail=f"{response.status_code}: {response.text}")

        result = ""
        async for chunk in response.aiter_text():
            result += chunk
            break

        logging.info("✅ MCP 回應：%s", result)
        return json.loads(result)
