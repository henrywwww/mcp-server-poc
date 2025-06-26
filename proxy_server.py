# proxy_server.py

import os
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastmcp import Client  # FastMCP 的官方 Client 類別

app = FastAPI()

MCP_SERVER_URL = os.getenv("MCP_SERVER_URL", "http://localhost:9000/mcp/")

@app.post("/mcp-proxy")
async def mcp_proxy(request: Request):
    try:
        # 從前端獲取 JSON payload
        payload = await request.json()
        method = payload.get("method")
        params = payload.get("params", {})

        if not method:
            raise HTTPException(status_code=400, detail="Missing 'method'")

        # 正確用法：每次都透過 async with 建立 Client
        async with Client(MCP_SERVER_URL) as client:
            result = await client.call_tool(method, params)

        return JSONResponse(content={"result": result})

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))