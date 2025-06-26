# proxy_server.py

import os
import asyncio
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastmcp import Client  # 正確的 client 類別

app = FastAPI()
MCP_SERVER_URL = os.getenv("MCP_SERVER_URL", "http://localhost:9000/mcp/")

# 建立 write-once 的 client 實例
client = Client(MCP_SERVER_URL)

async def get_client():
    # 確保 client 已連線
    if not client._transport or not client._transport.connected:
        await client.__aenter__()
    return client

@app.on_event("shutdown")
async def shutdown_event():
    # 關閉 client
    await client.__aexit__(None, None, None)

@app.post("/mcp-proxy")
async def mcp_proxy(request: Request):
    payload = await request.json()
    cl = await get_client()
    try:
        # 根據 payload 結構呼叫 call_tool 或 call_resource
        method = payload.get("method")
        params = payload.get("params", {})

        if method:
            result = await cl.call_tool(method, params)
        else:
            raise HTTPException(status_code=400, detail="Missing 'method'")

        return JSONResponse(content={"result": result})

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))