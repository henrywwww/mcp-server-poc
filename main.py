from fastapi import FastAPI, Request
from fastmcp import FastMCP

app = FastAPI()

mcp = FastMCP()  # 會自動讀取 env，初始化 OpenAI 連線

@app.post("/mcp")
async def handle_mcp(request: Request):
    query = await request.json()
    return mcp(query)

@app.get("/status")
def status():
return {"status": "ok"}