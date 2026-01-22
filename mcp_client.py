import asyncio
import json
from typing import Dict, Any, List
from langchain_mcp_adapters.client import MultiServerMCPClient
from mcp.types import TextContent

class DiskMonitorClient:
    """
    使用 MultiServerMCPClient 的 MCP 客户端
    """
    
    def __init__(self, server_url: str = "http://localhost:6666/sse"):
        self.server_url = server_url
        self.server_name = "disk-monitor"
        
        # 创建 MultiServerMCPClient
        self.client = MultiServerMCPClient({
            self.server_name: {
                "url": server_url,
                "transport": "sse"
            }
        })
        
    async def connect(self):
        """连接服务器"""
        print(f"连接到 MCP 服务器: {self.server_url}")
        
        # 获取工具列表
        tools = await self.client.get_tools(server_name=self.server_name)
        print(f"可用工具: {[tool.name for tool in tools]}")
        
        return tools
        
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any] = None) -> Any:
        """调用服务器工具"""
        if arguments is None:
            arguments = {}
            
        print(f"\n调用工具: {tool_name}")
        print(f"参数: {arguments}")
        
        async with self.client.session(self.server_name) as session:
            # 调用工具
            tool_result = await session.call_tool(
                name=tool_name, 
                arguments=arguments
            )
            
            # 处理结果
            if tool_result.isError:
                print(f"工具调用错误: {tool_result}")
                return None
                
            # 提取文本内容
            result_list = []
            for item in tool_result.content:
                if isinstance(item, TextContent):
                    text = item.text
                    try:
                        # 尝试解析为 JSON
                        json_obj = json.loads(text)
                        result_list.append(json_obj)
                    except json.JSONDecodeError:
                        # 如果不是 JSON，保持为文本
                        result_list.append(text)
            
            print(f"工具返回类型: {type(result_list)}")
            print(f"工具返回长度: {len(result_list)}")
            
            return result_list
            
    async def list_tools(self):
        """列出所有可用工具"""
        async with self.client.session(self.server_name) as session:
            tool_list = await session.list_tools()
            return tool_list.tools
            
    async def disconnect(self):
        """断开连接"""
        # MultiServerMCPClient 会自动管理连接
        pass

def format_disk_info(disks: List[Dict]) -> str:
    """格式化磁盘信息以便阅读"""
    if not disks:
        return "没有找到磁盘信息"
    
    output = []
    
    def format_device(device: Dict, indent: int = 0):
        """递归格式化设备树"""
        prefix = "  " * indent
        name = device.get('name', '未知')
        size = device.get('size', '未知')
        dev_type = device.get('type', '未知')
        mountpoint = device.get('mountpoint') or '(未挂载)'
        
        # 主设备信息
        device_line = f"{prefix}├─ {name} ({dev_type}, {size})"
        if mountpoint and mountpoint != '(未挂载)':
            device_line += f" [挂载点: {mountpoint}]"
        output.append(device_line)
        
        # 子设备（分区）
        children = device.get('children', [])
        for i, child in enumerate(children):
            child_prefix = "  " * (indent + 1)
            last_child = (i == len(children) - 1)
            connector = "└─" if last_child else "├─"
            
            child_name = child.get('name', '未知')
            child_size = child.get('size', '未知')
            child_type = child.get('type', '未知')
            child_mount = child.get('mountpoint') or '(未挂载)'
            
            child_line = f"{child_prefix}{connector} {child_name} ({child_type}, {child_size})"
            if child_mount and child_mount != '(未挂载)':
                child_line += f" [挂载点: {child_mount}]"
            output.append(child_line)
            
            # 如果有孙设备（如 LVM 逻辑卷）
            grandchildren = child.get('children', [])
            for grandchild in grandchildren:
                format_device(grandchild, indent + 2)
    
    # 处理所有顶级设备
    for i, disk in enumerate(disks):
        if 'error' in disk:
            output.append(f"错误: {disk['error']}")
            continue
            
        if i > 0:
            output.append("")  # 设备间空行
        
        format_device(disk, 0)
    
    return "\n".join(output)

async def main():
    """主函数：测试 MCP 服务器工具"""
    client = DiskMonitorClient()
    
    try:
        # 1. 连接到服务器
        print("="*50)
        print("连接到 MCP 服务器...")
        print("="*50)
        
        tools = await client.connect()
        print(f"找到 {len(tools)} 个工具:")
        for tool in tools:
            print(f"  - {tool.name}: {tool.description}")
        
        # 2. 测试 list_disks 工具
        print("\n" + "="*50)
        print("测试 list_disks 工具...")
        print("="*50)
        
        disks_result = await client.call_tool("list_disks")
        
        if disks_result:
            print(f"\nlist_disks 响应类型: {type(disks_result)}")
            
            # 处理响应
            if isinstance(disks_result, list) and len(disks_result) > 0:
                # 第一个元素可能是工具响应
                first_result = disks_result[0]
                
                if isinstance(first_result, dict):
                    # 如果是字典，尝试获取 blockdevices
                    disks = first_result.get('blockdevices', [])
                    if not disks and isinstance(first_result, dict):
                        # 或者直接就是磁盘列表
                        disks = first_result
                elif isinstance(first_result, str):
                    # 如果是字符串，尝试解析为JSON
                    try:
                        parsed = json.loads(first_result)
                        if isinstance(parsed, dict):
                            disks = parsed.get('blockdevices', [])
                        else:
                            disks = parsed
                    except:
                        disks = []
                else:
                    disks = first_result
                
                if isinstance(disks, list):
                    print(f"\n找到 {len(disks)} 个磁盘设备:")
                    print("-" * 40)
                    
                    # 格式化显示
                    formatted = format_disk_info(disks)
                    print(formatted)
                else:
                    print(f"磁盘信息格式不正确: {type(disks)}")
                    print(f"内容: {disks}")
            else:
                print(f"响应格式: {disks_result}")
        else:
            print("获取磁盘列表失败")
        
        # 3. 测试 check_disk_smart 工具
        print("\n" + "="*50)
        print("测试 check_disk_smart 工具...")
        print("="*50)
        
        # 检查 /dev/sda
        smart_result = await client.call_tool(
            "check_disk_smart", 
            {"device": "/dev/sda"}
        )
        
        if smart_result:
            print(f"/dev/sda 的 SMART 状态:")
            if isinstance(smart_result, list) and len(smart_result) > 0:
                result = smart_result[0]
                if isinstance(result, dict):
                    print(json.dumps(result, indent=2, ensure_ascii=False))
                else:
                    print(result)
            else:
                print(smart_result)
        else:
            print("检查 SMART 状态失败")
            
            
    except Exception as e:
        print(f"客户端错误: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        # 断开连接
        await client.disconnect()
        print("\n程序结束")

if __name__ == "__main__":
    # 运行客户端
    asyncio.run(main())
