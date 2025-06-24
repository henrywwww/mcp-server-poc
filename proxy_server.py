
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import httpx
import json

app = FastAPI()

MCP_STREAM_URL = "http://localhost:9000/"  # 若兩服務都在同 Railway 項目，可設成 http://localhost:9000

class RestMcpRequest(BaseModel):
    action: str
    data: dict

@app.post("/rest-mcp")
async def rest_mcp(req: RestMcpRequest):
    async with httpx.AsyncClient(timeout=None) as client:
        try:
            response = await client.post(
                MCP_STREAM_URL,
                headers={
                    "Accept": "application/json, text/event-stream",
                    "Content-Type": "application/json"
                },
                json={
                    "jsonrpc": "2.0",
                    "id": "proxy",
                    "method": req.action,
                    "params": req.data
                }
            )

            if response.status_code != 200:
                raise HTTPException(status_code=response.status_code, detail=response.text)

            # result = ""
            # async for chunk in response.aiter_text():
            #     result += chunk
            result = response.text
            return json.loads(result)

        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
