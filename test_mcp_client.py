"""MCP客戶端測試腳本."""

import asyncio
import json
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def test_mcp_client():
    """測試MCP客戶端連接."""
    print("=== MCP客戶端測試 ===")
    
    try:
        # 連接到MCP服務器
        server_params = StdioServerParameters(
            command="python",
            args=["mcp_server.py"]
        )
        
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                # 初始化連接
                await session.initialize()
                
                print("MCP連接成功！")
                
                # 列出可用資源
                print("\n=== 可用資源 ===")
                resources = await session.list_resources()
                for resource in resources:
                    print(f"- {resource.name}: {resource.description}")
                
                # 列出可用工具
                print("\n=== 可用工具 ===")
                tools = await session.list_tools()
                for tool in tools:
                    print(f"- {tool.name}: {tool.description}")
                
                # 測試搜尋文章工具
                print("\n=== 測試搜尋文章 ===")
                try:
                    result = await session.call_tool(
                        "search_articles",
                        {
                            "author": "mrp",
                            "limit": 5
                        }
                    )
                    print("搜尋結果:")
                    print(json.dumps(result, ensure_ascii=False, indent=2))
                except Exception as e:
                    print(f"搜尋失敗: {e}")
                
                # 測試作者活動分析工具
                print("\n=== 測試作者活動分析 ===")
                try:
                    result = await session.call_tool(
                        "analyze_author_activity",
                        {
                            "author": "mrp",
                            "days": 30
                        }
                    )
                    print("分析結果:")
                    print(json.dumps(result, ensure_ascii=False, indent=2))
                except Exception as e:
                    print(f"分析失敗: {e}")
                
    except Exception as e:
        print(f"MCP客戶端測試失敗: {e}")
        return False
    
    print("\n=== MCP客戶端測試完成 ===")
    return True


async def main():
    """主函數."""
    await test_mcp_client()


if __name__ == "__main__":
    asyncio.run(main())
