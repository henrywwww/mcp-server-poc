import logging
import json
import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()
logging.basicConfig(level=logging.INFO)

# MCP server 設定
MCP_STREAM_URL = "http://localhost:9000/mcp/"
mcp_initialized = False

class RestMcpRequest(BaseModel):
    action: str
    data: dict

@app.post("/rest-mcp")
async def rest_mcp(req: RestMcpRequest):
    global mcp_initialized

    async with httpx.AsyncClient(timeout=None) as client:
        try:
            # ✅ 若尚未初始化，先送一次 initialize
            if not mcp_initialized:
                logging.info("⚙️  嘗試初始化 MCP server...")

                init_payload = {
                    "jsonrpc": "2.0",
                    "id": 0,
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

                init_headers = {
                    "Accept": "application/json, text/event-stream",
                    "Content-Type": "application/json"
                }

                init_response = await client.post(
                    MCP_STREAM_URL,
                    headers=init_headers,
                    json=init_payload
                )

                if init_response.status_code == 200:
                    logging.info("✅ MCP 初始化成功")
                    mcp_initialized = True
                else:
                    logging.warning(f"⚠️ MCP 初始化失敗（{init_response.status_code}）：{init_response.text}")
                    raise HTTPException(status_code=init_response.status_code, detail=init_response.text)

            # ✅ 轉送實際的 action 請求
            payload = {
                "jsonrpc": "2.0",
                "id": "proxy",
                "method": req.action,
                "params": req.data
            }

            logging.info("💬 收到來自 Flutter 的請求：%s", req.dict())
            logging.info("🚀 Proxy 要送出的 payload：%s", json.dumps(payload, ensure_ascii=False))

            response = await client.post(
                MCP_STREAM_URL,
                headers={
                    "Accept": "application/json, text/event-stream",
                    "Content-Type": "application/json"
                },
                json=payload
            )

            if response.status_code != 200:
                logging.warning("⚠️ MCP 回應異常（%s）：%s", response.status_code, response.text)
                raise HTTPException(status_code=response.status_code, detail=response.text)

            logging.info("✅ MCP Server 回應：%s", response.text)
            return json.loads(response.text)

        except Exception as e:
            logging.error("❌ 發生錯誤：%s", str(e))
            raise HTTPException(status_code=500, detail=str(e))