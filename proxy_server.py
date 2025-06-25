
import logging
import json
import httpx
from fastapi import FastAPI, Request, HTTPException
from pydantic import BaseModel
from typing import Optional

app = FastAPI()
MCP_STREAM_URL = "http://localhost:9000/mcp/"
SESSION_ID: Optional[str] = None

logging.basicConfig(level=logging.INFO)

class RestMcpRequest(BaseModel):
    action: str
    data: dict = {}

@app.post("/rest-mcp")
async def rest_mcp(request: Request):
    global SESSION_ID

    req_json = await request.json()
    logging.info("💬 收到來自 Flutter 的請求：%s", req_json)

    if SESSION_ID is None:
        logging.info("⚙️  嘗試初始化 MCP server...")
        async with httpx.AsyncClient(timeout=None) as client:
            try:
                init_response = await client.post(
                    MCP_STREAM_URL,
                    headers={
                        "Accept": "application/json, text/event-stream",
                        "Content-Type": "application/json"
                    },
                    json={
                        "jsonrpc": "2.0",
                        "id": 0,
                        "method": "initialize",
                        "params": {
                            "protocolVersion": "2024-11-05",
                            "capabilities": {},
                            "clientInfo": {
                                "name": "proxy-server",
                                "version": "1.0"
                            }
                        }
                    }
                )
                if init_response.status_code == 200:
                    try:
                        init_json = init_response.json()
                        if "result" in init_json and "session_id" in init_json["result"]:
                            SESSION_ID = init_json["result"]["session_id"]
                            logging.info("✅ MCP 初始化成功，取得 session_id: %s", SESSION_ID)
                        else:
                            logging.warning("⚠️ MCP 初始化回應中沒有 session_id")
                    except Exception as e:
                        logging.warning("⚠️ MCP 初始化回應 JSON 解析錯誤：%s", e)
                else:
                    logging.warning("⚠️ MCP 回應異常（%d）：%s", init_response.status_code, init_response.text)
            except Exception as e:
                logging.error("❌ MCP 初始化失敗：%s", e)

    action = req_json.get("action")
    data = req_json.get("data", {})

    if SESSION_ID and "session_id" not in data:
        data["session_id"] = SESSION_ID

    payload = {
        "jsonrpc": "2.0",
        "id": "proxy",
        "method": action,
        "params": data
    }

    logging.info("🚀 Proxy 要送出的 payload：%s", json.dumps(payload, ensure_ascii=False))

    async with httpx.AsyncClient(timeout=None) as client:
        try:
            response = await client.post(
                MCP_STREAM_URL,
                headers={
                    "Accept": "application/json, text/event-stream",
                    "Content-Type": "application/json"
                },
                json=payload
            )
            if response.status_code == 200:
                return response.json()
            else:
                logging.warning("⚠️ MCP 回應異常（%d）：%s", response.status_code, response.text)
                raise HTTPException(status_code=response.status_code, detail=response.text)
        except Exception as e:
            logging.error("❌ 發生錯誤：%s", str(e))
            raise HTTPException(status_code=500, detail=str(e))
