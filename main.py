"""
Clean FastMCP Server for Railway Deployment
簡潔的 FastMCP 服務器，準備部署到 Railway
"""

import os
import json
import asyncio
from datetime import datetime
from typing import Dict, List, Optional
from fastmcp import FastMCP

# 初始化 FastMCP Server
mcp = FastMCP("production-server")

# 獲取環境變數
PORT = 8080#int(os.getenv("PORT", 8080))
ENVIRONMENT = "development"#os.getenv("RAILWAY_ENVIRONMENT", "development")

# 基本工具函數
@mcp.tool()
def hello_world(name: str = "World") -> str:
    """簡單的問候工具
    
    Args:
        name: 要問候的名字
        
    Returns:
        問候訊息
    """
    return f"Hello, {name}! 來自 Railway 的 FastMCP Server"

@mcp.tool()
def get_server_info() -> str:
    """獲取服務器資訊
    
    Returns:
        服務器狀態和環境資訊
    """
    info = {
        "server_name": "Railway MCP Server",
        "environment": ENVIRONMENT,
        "timestamp": datetime.now().isoformat(),
        "port": PORT,
        "status": "running"
    }
    return json.dumps(info, ensure_ascii=False, indent=2)

@mcp.tool()
def calculate(expression: str) -> str:
    """安全的數學計算器
    
    Args:
        expression: 數學表達式 (僅支援基本運算)
        
    Returns:
        計算結果
    """
    try:
        # 安全的表達式驗證
        allowed_chars = set('0123456789+-*/.() ')
        if not all(c in allowed_chars for c in expression):
            return "錯誤: 包含不允許的字符"
        
        # 避免複雜表達式
        if len(expression) > 100:
            return "錯誤: 表達式過長"
            
        result = eval(expression)
        return f"{expression} = {result}"
    except ZeroDivisionError:
        return "錯誤: 除零錯誤"
    except Exception as e:
        return f"錯誤: {str(e)}"

@mcp.tool()
def echo_message(message: str, repeat: int = 1) -> str:
    """回顯訊息工具
    
    Args:
        message: 要回顯的訊息
        repeat: 重複次數 (最多5次)
        
    Returns:
        重複的訊息
    """
    if repeat > 5:
        repeat = 5
    if repeat < 1:
        repeat = 1
        
    return "\n".join([f"{i+1}. {message}" for i in range(repeat)])

@mcp.tool()
def get_current_time(timezone: str = "UTC") -> str:
    """獲取當前時間
    
    Args:
        timezone: 時區 (UTC/Asia/Taipei)
        
    Returns:
        當前時間字串
    """
    now = datetime.now()
    
    if timezone == "Asia/Taipei":
        # 簡單的時區轉換 (UTC+8)
        from datetime import timedelta
        now = now + timedelta(hours=8)
        tz_info = "Asia/Taipei (UTC+8)"
    else:
        tz_info = "UTC"
    
    return f"當前時間: {now.strftime('%Y-%m-%d %H:%M:%S')} ({tz_info})"

@mcp.tool()
def format_json(json_string: str) -> str:
    """格式化 JSON 字串
    
    Args:
        json_string: 要格式化的 JSON 字串
        
    Returns:
        格式化後的 JSON
    """
    try:
        data = json.loads(json_string)
        return json.dumps(data, ensure_ascii=False, indent=2)
    except json.JSONDecodeError as e:
        return f"JSON 格式錯誤: {str(e)}"

# 資源定義
@mcp.resource("text://server-status")
def get_server_status():
    """服務器狀態資源"""
    status = {
        "service": "FastMCP Server",
        "version": "1.0.0",
        "deployed_on": "Railway",
        "environment": ENVIRONMENT,
        "uptime": "Available via Railway",
        "endpoints": [
            "hello_world",
            "get_server_info", 
            "calculate",
            "echo_message",
            "get_current_time",
            "format_json"
        ]
    }
    return json.dumps(status, ensure_ascii=False, indent=2)

@mcp.resource("text://api-docs")
def get_api_docs():
    """API 文件資源"""
    docs = """
# FastMCP Server API 文件

## 可用工具

### hello_world(name: str)
- 功能: 簡單問候
- 參數: name - 要問候的名字
- 範例: hello_world("Alice")

### get_server_info()
- 功能: 獲取服務器資訊
- 參數: 無
- 返回: 服務器狀態 JSON

### calculate(expression: str)
- 功能: 安全數學計算
- 參數: expression - 數學表達式
- 範例: calculate("2 + 3 * 4")

### echo_message(message: str, repeat: int)
- 功能: 回顯訊息
- 參數: 
  - message: 訊息內容
  - repeat: 重複次數 (1-5)

### get_current_time(timezone: str)
- 功能: 獲取當前時間
- 參數: timezone - UTC 或 Asia/Taipei

### format_json(json_string: str)
- 功能: 格式化 JSON
- 參數: json_string - JSON 字串
"""
    return docs

# 健康檢查端點
@mcp.tool()
def health_check() -> str:
    """健康檢查
    
    Returns:
        服務健康狀態
    """
    health_status = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "environment": ENVIRONMENT,
        "port": PORT,
        "message": "FastMCP Server is running on Railway"
    }
    return json.dumps(health_status, ensure_ascii=False)

# Railway 特定配置
def setup_railway_config():
    """設定 Railway 特定配置"""
    print(f"🚀 FastMCP Server starting on Railway")
    print(f"📍 Environment: {ENVIRONMENT}")
    print(f"🔌 Port: {PORT}")
    print(f"⏰ Started at: {datetime.now().isoformat()}")

# 假交易資料（可日後替換為資料庫）
fake_transactions = {
    "user123": [
        {
            "date": "2025-06-19 14:32",
            "amount": -2500,
            "target": "王小明",
            "type": "轉帳",
            "note": "房租"
        },
        {
            "date": "2025-06-18 10:05",
            "amount": 15000,
            "target": "公司入帳",
            "type": "薪資",
            "note": "六月份薪資"
        },
        {
            "date": "2025-06-16 09:21",
            "amount": -800,
            "target": "統一超商",
            "type": "消費",
            "note": "早餐"
        }
    ]
}

@mcp.tool()
def get_transactions(user_id: str) -> str:
    """查詢交易紀錄
    
    Args:
        user_id: 使用者 ID
        
    Returns:
        該使用者的交易紀錄清單
    """
    records = fake_transactions.get(user_id)
    if not records:
        return f"找不到使用者 {user_id} 的交易紀錄"

    result = []
    for tx in records:
        result.append(
            f"{tx['date']}｜{tx['type']}｜{tx['target']}｜{tx['amount']}元｜備註：{tx['note']}"
        )
    return "\n".join(result)

# 匯率假資料
fake_rates = {
    "USD_TWD": 32.5,
    "EUR_TWD": 35.8,
    "JPY_TWD": 0.21
}

@mcp.tool()
def get_exchange_rate(base: str = "USD", target: str = "TWD") -> str:
    """匯率查詢
    
    Args:
        base: 原始幣別
        target: 目標幣別
        
    Returns:
        匯率資訊
    """
    key = f"{base.upper()}_{target.upper()}"
    rate = fake_rates.get(key)
    if not rate:
        return f"目前不支援 {base} 對 {target} 的匯率查詢"
    
    return f"📈 匯率查詢：1 {base.upper()} = {rate} {target.upper()}（假資料）"

if __name__ == "__main__":
    setup_railway_config()
    
    print("\n🛠️  Available Tools:")
    print("   - hello_world: 問候工具")
    print("   - get_server_info: 服務器資訊")
    print("   - calculate: 數學計算器")
    print("   - echo_message: 訊息回顯")
    print("   - get_current_time: 當前時間")
    print("   - format_json: JSON 格式化")
    print("   - health_check: 健康檢查")
    
    print("\n📚 Available Resources:")
    print("   - text://server-status: 服務器狀態")
    print("   - text://api-docs: API 文件")
    
    print(f"\n🎯 Server ready! Running on port {PORT}")
    
    # 啟動 MCP Server
    # mcp.run(
    #     transport="sse", host="127.0.0.1", port=8080
    # )
    mcp.run(
        transport="streamable-http",
        host="0.0.0.0",  # 允許外部訪問
        port=8080,
        log_level="debug"
    )
