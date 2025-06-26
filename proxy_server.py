# proxy_server.py

import os
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastmcp import Client
from fastmcp.types import BaseContent, ToolOutput

app = FastAPI()
MCP_SERVER_URL = os.getenv("MCP_SERVER_URL", "http://localhost:9000/mcp/")

@app.post("/mcp-proxy")
async def mcp_proxy(request: Request):
    try:
        payload = await request.json()
        method = payload.get("method")
        params = payload.get("params", {})

        if not method:
            raise HTTPException(status_code=400, detail="Missing 'method'")

        async with Client(MCP_SERVER_URL) as client:
            result = await client.call_tool(method, params)

        # ✅ 確保回傳內容可 JSON 序列化
        if isinstance(result, (BaseContent, ToolOutput)):
            result = result.model_dump()

        return JSONResponse(content={"result": result})

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))