import asyncio
import json
from typing import Dict, Any, List
from langchain_mcp_adapters.client import MultiServerMCPClient
from mcp.types import TextContent


class MCPNetworkDiagClient:
    """
    MCP 客户端：用于测试网络与系统诊断类工具
    对接符合《MCP接口数据描述规范.docx》的真实服务器
    """

    def __init__(self, server_url: str = "http://182.200.206.53:6666/sse"):
        self.server_url = server_url
        self.server_name = "network-diag"  # 可按需调整

        # 创建 MultiServerMCPClient
        self.client = MultiServerMCPClient({
            self.server_name: {
                "url": server_url,
                "transport": "sse"
            }
        })

    async def connect(self):
        """连接服务器并列出可用工具"""
        print(f"🔗 连接到 MCP 服务器: {self.server_url}")
        try:
            tools = await self.client.get_tools(server_name=self.server_name)
            print(f"✅ 可用工具 ({len(tools)} 个):")
            for tool in tools:
                print(f"  - {tool.name}: {tool.description.split('###')[0].strip()}")
            return tools
        except Exception as e:
            print(f"❌ 连接失败: {e}")
            raise

    async def call_tool(self, tool_name: str) -> Any:
        """调用指定工具，并自动解析 structuredContent.response.data"""
        print(f"\n🔧 调用工具: {tool_name}")

        async with self.client.session(self.server_name) as session:
            try:
                tool_result = await session.call_tool(
                    name=tool_name,
                    arguments={}  # 所有工具无参数
                )

                if tool_result.isError:
                    print(f"❌ 工具调用错误: {tool_result.error}")
                    return None

                result_list = []
                for item in tool_result.content:
                    if isinstance(item, TextContent):
                        text = item.text.strip()
                        try:
                            json_obj = json.loads(text)
                            result_list.append(json_obj)
                        except json.JSONDecodeError:
                            result_list.append(text)
                    else:
                        result_list.append(str(item))

                print(f"📨 工具返回数量: {len(result_list)}")

                # 提取 structuredContent.response.data
                parsed_results = []
                for res in result_list:
                    if isinstance(res, dict):
                        data = (
                            res.get("structuredContent", {})
                            .get("response", {})
                            .get("data", [])
                        )
                        code = res.get("structuredContent", {}).get("response", {}).get("code", -1)
                        message = res.get("structuredContent", {}).get("response", {}).get("message", "unknown")

                        if code != 0:
                            print(f"⚠️ 接口返回异常: code={code}, message={message}")
                        else:
                            print(f"✅ 接口调用成功: 返回 {len(data)} 条记录")

                        parsed_results.extend(data)
                    else:
                        parsed_results.append(res)

                return parsed_results

            except Exception as e:
                print(f"❌ 调用异常: {e}")
                return None

    async def disconnect(self):
        """断开连接"""
        pass


def pretty_print_response(title: str, data: List[Dict], keys: List[str]):
    """通用格式化打印函数"""
    print(f"\n📊 {title}")
    print("-" * 60)
    if not data:
        print("  ⚠️ 未获取到数据")
        return

    for i, item in enumerate(data, 1):
        print(f"  [{i}]")
        for key in keys:
            value = item.get(key, "N/A")
            display_key = key.replace('_', ' ').replace('Pcie', 'PCIe').replace('Phy', 'PHY')
            display_key = ''.join([' ' + c if c.isupper() else c for c in display_key]).lstrip().title()
            print(f"      {display_key}: {value}")
        print("")


async def main():
    """主函数：测试所有 MCP 诊断工具"""
    client = MCPNetworkDiagClient()

    try:
        print("=" * 60)
        print("🚀 开始测试 MCP 网络诊断工具")
        print("=" * 60)

        # 1. 连接并列出工具
        tools = await client.connect()
        if not tools:
            print("❌ 无可用工具，退出测试")
            return

        print(f"\n🔍 共发现 {len(tools)} 个工具，开始逐项测试...")

        # ========================
        # 1. ARP 参数配置检查
        # ========================
        arp_data = await client.call_tool("getArpConfig")
        pretty_print_response(
            "1. ARP 参数配置",
            arp_data,
            ["interface", "disableIpv6", "arpIgnore", "arpAnnounce", "rpFilter", "arpFilter", "arpNotify", "arpAccept"]
        )

        # ========================
        # 2. 无损网络参数 (PFC & ECN)
        # ========================
        pfc_ecn_data = await client.call_tool("getLosslessNetworkConfig")
        pretty_print_response(
            "2. 无损网络参数",
            pfc_ecn_data,
            ["interface", "pfcPriority", "pfcTrust", "pfcTsa", "ecnEnable"]
        )

        # ========================
        # 3. 网卡 PCIe 协商速率
        # ========================
        pcie_data = await client.call_tool("getPcieLinkSpeedForNic")
        pretty_print_response(
            "3. 网卡 PCIe 协商速率",
            pcie_data,
            ["interface", "busInfo", "lnkSta"]
        )

        # ========================
        # 4. 网卡发送暂停帧统计
        # ========================
        tx_pause_data = await client.call_tool("getNicCongestionStatsTx")
        pretty_print_response(
            "4. 网卡发送暂停帧统计",
            tx_pause_data,
            ["interface", "txPauseCtrlPhy"]
        )

        # ========================
        # 5. 交换机接收暂停帧统计
        # ========================
        rx_pause_data = await client.call_tool("getSwitchCongestionStatsRx")
        pretty_print_response(
            "5. 交换机接收暂停帧统计",
            rx_pause_data,
            ["interface", "rxPauseCtrlPhy"]
        )

        # ========================
        # 6. NVMe 盘 PCIe 协商速率
        # ========================
        nvme_data = await client.call_tool("getNvmePcieLinkSpeed")
        pretty_print_response(
            "6. NVMe 盘 PCIe 协商速率",
            nvme_data,
            ["nvme", "busInfo", "lnkSta"]
        )

        # ========================
        # 7. CPU 使用率
        # ========================
        cpu_data = await client.call_tool("getCpuUsage")
        if cpu_data and isinstance(cpu_data, list):
            item = cpu_data[0]
            print(f"\n📈 7. CPU 使用率")
            print("-" * 40)
            print(f"   当前使用率: {item.get('cpuUsage', 'N/A')}%")
            print(f"   告警阈值: {item.get('cpuThreshold', 'N/A')}%")
        else:
            print(f"\n⚠️ 无法获取 CPU 使用率")

        # ========================
        # 8. 内存使用率
        # ========================
        mem_data = await client.call_tool("getMemoryUsage")
        if mem_data and isinstance(mem_data, list):
            item = mem_data[0]
            print(f"\n🧠 8. 内存使用率")
            print("-" * 40)
            print(f"   使用率: {item.get('memUsage', 'N/A')}%")
            print(f"   总量: {item.get('memTotal', 'N/A')} MB")
            print(f"   已用: {item.get('memUsed', 'N/A')} MB")
            print(f"   可用: {item.get('memAvailable', 'N/A')} MB")
            print(f"   告警阈值: {item.get('memThreshold', 'N/A')}%")
        else:
            print(f"\n⚠️ 无法获取内存使用率")

        print("\n✅ 所有工具测试完成！")

    except Exception as e:
        print(f"❌ 客户端运行出错: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await client.disconnect()
        print("\n🔚 测试结束")


if __name__ == "__main__":
    asyncio.run(main())