
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import httpx
import json
import logging

app = FastAPI()

MCP_STREAM_URL = "http://localhost:9000/mcp/"  # 若兩服務都在同 Railway 項目，可設成 http://localhost:9000

# 設定 log 格式
logging.basicConfig(level=logging.INFO)

class RestMcpRequest(BaseModel):
    action: str
    data: dict


initialized = False  # 記錄是否已初始化

@app.post("/rest-mcp")
async def rest_mcp(req: RestMcpRequest):
    global initialized
    async with httpx.AsyncClient(timeout=None) as client:
        try:
            # 第一次請求前初始化 MCP Server
            if not initialized:
                init_payload = {
                    "jsonrpc": "2.0",
                    "id": 0,
                    "method": "initialize",
                    "params": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {},
                        "clientInfo": {
                            "name": "flutter-proxy",
                            "version": "1.0.0"
                        }
                    }
                }
                logging.info("⚙️  初始化 MCP server...")
                init_response = await client.post(
                    MCP_STREAM_URL,
                    headers={
                        "Accept": "application/json, text/event-stream",
                        "Content-Type": "application/json"
                    },
                    json=init_payload
                )
                if init_response.status_code != 200:
                    raise HTTPException(status_code=init_response.status_code, detail=init_response.text)
                initialized = True
                logging.info("✅ MCP 初始化成功")

            # 接著處理正常的業務請求
            payload = {
                "jsonrpc": "2.0",
                "id": "proxy",
                "method": req.action,
                "params": req.data
            }
            logging.info("🚀 Proxy 要送出的 payload：%s", json.dumps(payload))

            response = await client.post(
                MCP_STREAM_URL,
                headers={
                    "Accept": "application/json, text/event-stream",
                    "Content-Type": "application/json"
                },
                json=payload
            )

            if response.status_code != 200:
                raise HTTPException(status_code=response.status_code, detail=response.text)

            logging.info("✅ MCP Server 回應：%s", response.text)

            return response.json()

        except Exception as e:
            logging.error("❌ 發生錯誤：%s", str(e))
            raise HTTPException(status_code=500, detail=str(e))