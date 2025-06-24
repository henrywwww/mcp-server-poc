# test_client.py
import asyncio
from fastmcp import Client

async def test_mcp_server():
    """测试 MCP 服务器的所有功能"""
    
    # 连接到服务器
    client = Client("https://web-production-f44b.up.railway.app/mcp")
    
    try:
        print("=== 连接到 MCP 服务器 ===")
        await client.connect()
        print("✅ 成功连接到服务器")
        
        # 获取可用的工具列表
        print("\n=== 获取可用工具 ===")
        tools = await client.list_tools()
        print(f"可用工具数量: {len(tools)}")
        for tool in tools:
            print(f"- {tool['name']}: {tool.get('description', '无描述')}")
        
        # 测试 add_numbers 工具
        print("\n=== 测试 add_numbers 工具 ===")
        result = await client.call_tool("add_numbers", {"a": 10, "b": 25})
        print(f"10 + 25 = {result}")
        
        # 测试 get_time 工具
        print("\n=== 测试 get_time 工具 ===")
        result = await client.call_tool("get_time", {})
        print(f"当前时间: {result}")
        
        # 测试 greet 工具（默认参数）
        print("\n=== 测试 greet 工具（默认中文）===")
        result = await client.call_tool("greet", {"name": "张三"})
        print(f"问候: {result}")
        
        # 测试 greet 工具（指定语言）
        print("\n=== 测试 greet 工具（英文）===")
        result = await client.call_tool("greet", {"name": "John", "language": "en"})
        print(f"问候: {result}")
        
        # 测试异步工具
        print("\n=== 测试 async_calculation 工具 ===")
        print("开始异步计算...")
        result = await client.call_tool("async_calculation", {"x": 5, "delay": 2.0})
        print(f"计算结果: {result}")
        
        # 测试错误处理
        print("\n=== 测试错误处理 ===")
        try:
            result = await client.call_tool("nonexistent_tool", {})
        except Exception as e:
            print(f"✅ 正确捕获错误: {e}")
        
        # 测试参数错误
        try:
            result = await client.call_tool("add_numbers", {"a": "not_a_number", "b": 5})
        except Exception as e:
            print(f"✅ 正确捕获参数错误: {e}")
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
    
    finally:
        await client.close()
        print("\n=== 测试完成 ===")

if __name__ == "__main__":
    print("开始测试 MCP 服务器...")
    asyncio.run(test_mcp_server())