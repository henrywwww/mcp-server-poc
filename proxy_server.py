import logging
import json
import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

# 初始化 FastAPI 應用
app = FastAPI()

# MCP server 的 streamable-http 位置
MCP_STREAM_URL = "http://localhost:9000/mcp/"

# 啟用 CORS（方便 Flutter App 呼叫）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生產環境請改成指定 origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 記錄格式
logging.basicConfig(level=logging.INFO)

# Flutter 來的資料格式
class RestMcpRequest(BaseModel):
    action: str
    data: dict

# 啟動時自動初始化 MCP Server
@app.on_event("startup")
async def initialize_mcp():
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

    async with httpx.AsyncClient(timeout=10) as client:
        try:
            logging.info("⚙️  初始化 MCP server...")
            resp = await client.post(
                MCP_STREAM_URL,
                headers={"Content-Type": "application/json"},
                json=init_payload
            )
            logging.info(f"✅ MCP 初始化成功：{resp.status_code} - {resp.text}")
        except Exception as e:
            logging.error(f"❌ MCP 初始化失敗：{e}")

# Flutter 呼叫轉發端點
@app.post("/rest-mcp")
async def rest_mcp(req: RestMcpRequest):
    logging.info("💬 收到來自 Flutter 的請求：%s", req)

    payload = {
        "jsonrpc": "2.0",
        "id": "proxy",
        "method": req.action,
        "params": req.data
    }

    logging.info("🚀 Proxy 要送出的 payload：%s", json.dumps(payload, ensure_ascii=False))

    async with httpx.AsyncClient(timeout=20) as client:
        try:
            response = await client.post(
                MCP_STREAM_URL,
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json, text/event-stream"
                },
                json=payload
            )

            if response.status_code != 200:
                raise HTTPException(status_code=response.status_code, detail=response.text)

            logging.info("✅ MCP Server 回應：%s", response.text)
            return json.loads(response.text)

        except Exception as e:
            logging.error("❌ 發生錯誤：%s", str(e))
            raise HTTPException(status_code=500, detail=str(e))