# FastMCP Railway Server

一個部署在 Railway 上的簡潔 FastMCP 服務器。

## 功能特點

- 🚀 一鍵部署到 Railway
- 🛠️ 內建實用工具函數
- 📊 健康檢查端點
- 🔧 環境變數配置
- 📝 完整的 API 文件

## 本地開發

### 1. 克隆專案
\`\`\`bash
git clone <your-repo-url>
cd fastmcp-railway
\`\`\`

### 2. 安裝依賴
\`\`\`bash
pip install -r requirements.txt
\`\`\`

### 3. 運行服務器
\`\`\`bash
python main.py
\`\`\`

## Railway 部署

### 方法一：GitHub 整合
1. 將程式碼推送到 GitHub
2. 在 Railway 中連接 GitHub 倉庫
3. 選擇分支並部署

### 方法二：Railway CLI
\`\`\`bash
# 安裝 Railway CLI
npm install -g @railway/cli

# 登入
railway login

# 初始化專案
railway init

# 部署
railway up
\`\`\`

## 環境變數

在 Railway 控制台中設定：

- \`PORT\`: 服務器端口 (自動設定)
- \`RAILWAY_ENVIRONMENT\`: 環境標識
- \`LOG_LEVEL\`: 日誌級別 (INFO/DEBUG)

## API 使用

部署後，你的 MCP 服務器將可通過以下方式使用：

### 工具調用
- \`hello_world(name)\`: 問候功能
- \`calculate(expression)\`: 數學計算
- \`get_current_time(timezone)\`: 獲取時間
- \`health_check()\`: 健康檢查

### 資源存取
- \`text://server-status\`: 服務器狀態
- \`text://api-docs\`: API 文件

## 監控

- Railway 提供內建監控
- 健康檢查端點：\`/health\`
- 日誌可在 Railway 控制台查看
\`\`\`

## tests/test_server.py

```python
"""
FastMCP Server 測試
"""
import json
import pytest
from main import mcp

def test_hello_world():
    """測試問候功能"""
    result = mcp.tools["hello_world"].func("Alice")
    assert "Hello, Alice" in result
    assert "Railway" in result

def test_calculate():
    """測試計算功能"""
    result = mcp.tools["calculate"].func("2 + 3")
    assert "2 + 3 = 5" in result
    
    # 測試錯誤情況
    result = mcp.tools["calculate"].func("import os")
    assert "錯誤" in result

def test_get_server_info():
    """測試服務器資訊"""
    result = mcp.tools["get_server_info"].func()
    info = json.loads(result)
    assert info["server_name"] == "Railway MCP Server"
    assert "timestamp" in info

def test_echo_message():
    """測試回顯功能"""
    result = mcp.tools["echo_message"].func("Test", 2)
    lines = result.split("\n")
    assert len(lines) == 2
    assert "1. Test" in lines[0]
    assert "2. Test" in lines[1]

def test_format_json():
    """測試 JSON 格式化"""
    test_json = '{"name":"test","value":123}'
    result = mcp.tools["format_json"].func(test_json)
    formatted = json.loads(result)
    assert formatted["name"] == "test"
    assert formatted["value"] == 123

def test_health_check():
    """測試健康檢查"""
    result = mcp.tools["health_check"].func()
    health = json.loads(result)
    assert health["status"] == "healthy"

if __name__ == "__main__":
    pytest.main([__file__])