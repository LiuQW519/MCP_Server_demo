import subprocess
import json
import os
from typing import List, Dict, Any, Optional
from fastmcp import FastMCP

# ==================== 全局配置 ====================

DEBUG = os.getenv("MCP_DEBUG", "false").lower() == "true"

# ------------------- 公共错误码表（符合 MCP 规范）-------------------
ERROR_CODE = {
    0: "success",
    1001: "command not found or permission denied",
    1002: "command execution failed",
    1003: "failed to parse response",
    1004: "unexpected exception occurred",
    1005: "device not available or no matching hardware found"
}

# 初始化 MCP 服务
mcp = FastMCP(name="SystemHealthChecker")


# ==================== 内部工具函数 ====================

def _run_command(cmd: List[str], shell: bool = False) -> tuple:
    """
    执行系统命令，捕获输出与状态码
    :param cmd: 命令列表或字符串（shell=True时）
    :param shell: 是否启用 shell 执行
    :return: (stdout: str, stderr: str, returncode: int)
    """
    if DEBUG:
        print(f"[DEBUG] Executing: {' '.join(cmd) if isinstance(cmd, list) else cmd}")
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            shell=shell,
            timeout=3
        )
        stdout = result.stdout.strip()
        stderr = result.stderr.strip()
        if DEBUG and stdout:
            print(f"[DEBUG] STDOUT:\n{stdout}")
        if DEBUG and stderr:
            print(f"[DEBUG] STDERR:\n{stderr}")
        return stdout, stderr, result.returncode
    except Exception as e:
        if DEBUG:
            print(f"[DEBUG] Exception: {e}")
        return "", str(e), -1


def _make_response(code: int, data: Any = None, message: Optional[str] = None) -> str:
    """
    构造符合 MCP 规范的标准响应体，包含 structuredContent 和 outputSchema
    """
    if data is None:
        data = []
    msg = message or ERROR_CODE.get(code, "unknown error")

    # 构建 structuredContent
    structured_content = {
        "response": {
            "code": code,
            "message": msg,
            "data": data
        }
    }

    # outputSchema 可动态生成，此处简化为静态定义（实际可对接 Pydantic 或 JSON Schema）
    return json.dumps({
        "structuredContent": structured_content,
        "outputSchema": _get_output_schema_for_data(data)
    }, ensure_ascii=False, indent=2 if DEBUG else None)


def _get_output_schema_for_data(data: Any) -> Dict[str, Any]:
    """
    根据 data 自动生成简易 outputSchema（模拟真实场景）
    实际项目建议使用 pydantic 或 jsonschema 库进行校验
    """
    schema = {
        "type": "object",
        "properties": {
            "code": {"type": "number", "description": "接口返回码，0 表示成功"},
            "message": {"type": "string", "description": "接口返回信息"},
            "data": {
                "type": "array",
                "items": {"type": "object", "properties": {}, "required": [], "additionalProperties": True}
            }
        },
        "required": ["code", "message", "data"],
        "additionalProperties": False,
        "description": "接口返回体",
        "$schema": "http://json-schema.org/draft-07/schema#"
    }

    if not data:
        return schema

    sample = data[0]
    props = {}
    required = []

    for k, v in sample.items():
        props[k] = {"type": "string", "description": f"{k} 字段说明"}  # 实际应由业务定义
        required.append(k)

    schema["properties"]["data"]["items"]["properties"] = props
    schema["properties"]["data"]["items"]["required"] = required
    return schema


# ==================== MCP 工具接口（严格合规版）====================

@mcp.tool
def getArpConfig() -> str:
    """
    ### 模块：网络配置检测
    ### 接口：ARP参数配置检查
    ### 功能简介：
    获取所有 InfiniBand 接口的 ARP 相关内核参数配置，用于判断是否存在 ARP 配置异常导致通信问题。
    支持多网卡环境，逐接口返回 disable_ipv6、arp_ignore 等关键配置项。

    ### 路径 / 方法：
    getArpConfig()

    ### 参数说明：
    无输入参数。

    ### 返回字段说明：
    | 字段名         | 类型   | 是否必填 | 示例值 | 详细描述 |
    |----------------|--------|----------|--------|----------|
    | interface      | string | 是       | ib9b-0 | IB 接口名称 |
    | disableIpv6    | string | 是       | "0"    | 是否禁用 IPv6（0:不禁用, 1:禁用） |
    | arpIgnore      | string | 是       | "2"    | ARP 忽略策略（0:不忽略, 1:只回应目标IP是本机的ARP, 2:只回应目标IP是本机且入口设备匹配的ARP） |
    | arpAnnounce    | string | 是       | "2"    | ARP 宣告策略（0:任意本地地址, 1:尽量使用目标子网的地址, 2:总是使用最佳本地地址） |
    | rpFilter       | string | 是       | "2"    | 反向路径过滤（0:关闭, 1:松散模式, 2:严格模式） |
    | arpFilter      | string | 是       | "0"    | 是否启用基于防火墙规则的 ARP 过滤（0:否, 1:是） |
    | arpNotify      | string | 是       | "1"    | 是否发送免费 ARP 通知（0:否, 1:是） |
    | arpAccept      | string | 是       | "0"    | 是否自动学习非请求 ARP（0:否, 1:是） |

    ### 请求示例：
    {}  # 无参数

    ### 响应示例：
    {
      "structuredContent": {
        "response": {
          "code": 0,
          "message": "success",
          "data": [
            {
              "interface": "ib9b-0",
              "disableIpv6": "0",
              "arpIgnore": "2",
              "arpAnnounce": "2",
              "rpFilter": "2",
              "arpFilter": "0",
              "arpNotify": "1",
              "arpAccept": "0"
            }
          ]
        }
      },
      "outputSchema": { ... }
    }

    ### 错误码与说明：
    | 错误码 | 说明 |
    |-------|------|
    | 0     | 成功 |
    | 1002  | ibdev2netdev 命令执行失败 |
    | 1003  | 解析 sysctl 输出失败 |
    """
    keys_map = {
        "disable_ipv6": "disableIpv6",
        "arp_ignore": "arpIgnore",
        "arp_announce": "arpAnnounce",
        "rp_filter": "rpFilter",
        "arp_filter": "arpFilter",
        "arp_notify": "arpNotify",
        "arp_accept": "arpAccept"
    }
    data = []

    # 获取接口列表
    stdout, stderr, ret = _run_command(["ibdev2netdev"])
    if ret != 0:
        return _make_response(1002, [], f"ibdev2netdev failed: {stderr}")

    for line in stdout.splitlines():
        parts = line.split(" ==> ")
        if len(parts) != 2:
            continue
        iface = parts[1].split()[0]

        entry = {"interface": iface}
        for raw_key, camel_key in keys_map.items():
            full_key = f"{iface}.{raw_key}"
            out, _, ret_sysctl = _run_command(["sysctl", "-a"])
            if ret_sysctl != 0:
                entry[camel_key] = ""
                continue
            found = False
            for l in out.splitlines():
                if l.startswith(full_key):
                    value = l.split(" = ", 1)[-1].strip()
                    entry[camel_key] = value
                    found = True
                    break
            if not found:
                entry[camel_key] = ""

        data.append(entry)

    return _make_response(0, data)


@mcp.tool
def getLosslessNetworkConfig() -> str:
    """
    ### 模块：无损网络检测
    ### 接口：PFC与ECN配置查询
    ### 功能简介：
    获取每个 IB 接口的 PFC（优先级流控）和 ECN（显式拥塞通知）配置状态，用于诊断 RoCE 无损网络配置是否正确。

    ### 参数说明：
    无输入参数。

    ### 返回字段说明：
    | 字段名        | 类型   | 是否必填 | 示例值   | 详细描述 |
    |---------------|--------|----------|----------|----------|
    | interface     | string | 是       | ib9b-0   | IB 接口名称 |
    | pfcPriority   | string | 是       | "-1"     | PFC 启用的优先级，-1 表示未启用 |
    | pfcTrust      | string | 是       | "pcp"    | PFC 信任模式（pcp/dscp） |
    | pfcTsa        | string | 是       | "vendor" | TSA 算法（vendor/ets/etc） |
    | ecnEnable     | string | 是       | "10"     | ECN 使能位（取 traffic_class 寄存器低2位）|

    ### 响应示例：
    {
      "structuredContent": {
        "response": {
          "code": 0,
          "message": "success",
          "data": [
            {
              "interface": "ib9b-0",
              "pfcPriority": "-1",
              "pfcTrust": "pcp",
              "pfcTsa": "vendor",
              "ecnEnable": "00"
            }
          ]
        }
      },
      ...
    }
    """
    data = []
    stdout, _, ret = _run_command(["ibdev2netdev"])
    if ret != 0:
        return _make_response(1002, [], "Failed to get IB interfaces")

    for line in stdout.splitlines():
        parts = line.split(" ==> ")
        if len(parts) != 2:
            continue
        iface = parts[1].split()[0]
        device = parts[0].split()[0]  # mlx5_0

        entry = {"interface": iface}

        # === PFC via mlnx_qos ===
        pfc_out, _, pfc_ret = _run_command(["mlnx_qos", "-i", iface])
        if pfc_ret == 0:
            trust_state = pfc_tsa = ""
            pfc_enabled = []
            for l in pfc_out.splitlines():
                if "Priority trust state" in l:
                    trust_state = l.split(":")[-1].strip()
                elif "enabled" in l and "priority" not in l:
                    pfc_enabled = [i for i, v in enumerate(l.split()[1:]) if v == "1"]
                elif "tsa:" in l:
                    pfc_tsa = l.split("tsa:")[-1].strip()
            entry["pfcPriority"] = str(pfc_enabled[0]) if pfc_enabled else "-1"
            entry["pfcTrust"] = trust_state
            entry["pfcTsa"] = pfc_tsa
        else:
            entry.update({"pfcPriority": "", "pfcTrust": "", "pfcTsa": ""})

        # === ECN ===
        ecn_path = f"/sys/class/infiniband/{device}/tc/1/traffic_class"
        if os.path.exists(ecn_path):
            try:
                with open(ecn_path, 'r') as f:
                    val = int(f.read().strip())
                    entry["ecnEnable"] = bin(val)[-2:].zfill(2)
            except:
                entry["ecnEnable"] = "00"
        else:
            entry["ecnEnable"] = "00"

        data.append(entry)

    return _make_response(0, data)


@mcp.tool
def getPcieLinkSpeedForNic() -> str:
    """
    ### 模块：硬件链路检测
    ### 接口：网卡 PCIE 协商速率查询
    ### 功能简介：
    获取 IB 网卡对应的 PCIE 总线协商速率与宽度，用于判断是否存在降速问题。

    ### 返回字段说明：
    | 字段名     | 类型   | 是否必填 | 示例值                  | 详细描述 |
    |------------|--------|----------|-------------------------|----------|
    | interface  | string | 是       | ib9b-0                  | IB 接口名 |
    | busInfo    | string | 是       | "0000:9b:00.0"          | BDF 地址 |
    | lnkSta     | string | 是       | "Speed 16GT/s, Width x16" | 链路状态 |

    ### 响应示例：
    {
      "data": [{
        "interface": "ib9b-0",
        "busInfo": "0000:9b:00.0",
        "lnkSta": "Speed 16GT/s, Width x16"
      }]
    }
    """
    data = []
    stdout, _, ret = _run_command(["ibdev2netdev"])
    if ret != 0:
        return _make_response(1002, [], "No IB devices found")

    for line in stdout.splitlines():
        parts = line.split(" ==> ")
        if len(parts) != 2:
            continue
        iface = parts[1].split()[0]

        ethtool_out, _, et_ret = _run_command(["ethtool", "-i", iface])
        bdf = ""
        if et_ret == 0:
            for l in ethtool_out.splitlines():
                if "bus-info" in l:
                    bdf = l.split(":", 1)[1].strip()
                    break
        if not bdf:
            continue

        lspci_out, _, ls_ret = _run_command(["lspci", "-vvvs", bdf])
        lnksta = "N/A"
        if ls_ret == 0:
            for l in lspci_out.splitlines():
                if "LnkSta:" in l and "Speed" in l:
                    lnksta = l.split(":", 1)[1].strip()
                    break

        data.append({
            "interface": iface,
            "busInfo": bdf,
            "lnkSta": lnksta
        })

    return _make_response(0, data)


@mcp.tool
def getNicCongestionStatsTx() -> str:
    """
    ### 模块：拥塞检测
    ### 接口：网卡发送方向暂停帧统计
    ### 返回字段说明：
    | 字段名             | 类型   | 是否必填 | 示例值 | 详细描述 |
    |--------------------|--------|----------|--------|----------|
    | interface          | string | 是       | ib9b-0 | 接口名 |
    | txPauseCtrlPhy     | string | 是       | "0"    | 发送的物理层暂停帧数量 |

    ### 响应示例：
    { "data": [{ "interface": "ib9b-0", "txPauseCtrlPhy": "0" }] }
    """
    data = []
    stdout, _, ret = _run_command(["ibdev2netdev"])
    if ret != 0:
        return _make_response(1002, [], "No interfaces")

    for line in stdout.splitlines():
        parts = line.split(" ==> ")
        if len(parts) != 2:
            continue
        iface = parts[1].split()[0]

        out, _, ret_code = _run_command(["ethtool", "-S", iface])
        tx_pause = "0"
        if ret_code == 0:
            for l in out.splitlines():
                if "tx_pause_ctrl_phy" in l:
                    tx_pause = l.split(":")[-1].strip()
                    break

        data.append({
            "interface": iface,
            "txPauseCtrlPhy": tx_pause
        })

    return _make_response(0, data)


@mcp.tool
def getSwitchCongestionStatsRx() -> str:
    """
    ### 模块：拥塞检测
    ### 接口：交换机接收方向暂停帧统计
    ### 返回字段说明：
    | 字段名             | 类型   | 是否必填 | 示例值 | 详细描述 |
    |--------------------|--------|----------|--------|----------|
    | interface          | string | 是       | ib9b-0 | 接口名 |
    | rxPauseCtrlPhy     | string | 是       | "0"    | 接收的物理层暂停帧数量 |

    ### 响应示例：
    { "data": [{ "interface": "ib9b-0", "rxPauseCtrlPhy": "0" }] }
    """
    data = []
    stdout, _, ret = _run_command(["ibdev2netdev"])
    if ret != 0:
        return _make_response(1002, [], "No interfaces")

    for line in stdout.splitlines():
        parts = line.split(" ==> ")
        if len(parts) != 2:
            continue
        iface = parts[1].split()[0]

        out, _, ret_code = _run_command(["ethtool", "-S", iface])
        rx_pause = "0"
        if ret_code == 0:
            for l in out.splitlines():
                if "rx_pause_ctrl_phy" in l:
                    rx_pause = l.split(":")[-1].strip()
                    break

        data.append({
            "interface": iface,
            "rxPauseCtrlPhy": rx_pause
        })

    return _make_response(0, data)


@mcp.tool
def getNvmePcieLinkSpeed() -> str:
    """
    ### 模块：存储硬件检测
    ### 接口：NVMe盘 PCIE 协商速率
    ### 返回字段说明：
    | 字段名     | 类型   | 是否必填 | 示例值                  | 详细描述 |
    |------------|--------|----------|-------------------------|----------|
    | nvme       | string | 是       | nvme0                   | NVMe 设备名 |
    | busInfo    | string | 是       | "0000:17:00.0"          | BDF 地址 |
    | lnkSta     | string | 是       | "Speed 16GT/s, Width x4"| 链路状态 |

    ### 响应示例：
    { "data": [{ "nvme": "nvme0", "busInfo": "0000:17:00.0", "lnkSta": "Speed 16GT/s, Width x4" }] }
    """
    data = []
    out, err, ret = _run_command(["nvme", "list"])
    if ret != 0:
        return _make_response(1002, [], f"nvme list failed: {err}")

    devices = []
    for line in out.splitlines():
        if "/dev/nvme" in line:
            dev_name = line.split("/dev/")[1].split("n")[0]
            if dev_name not in devices:
                devices.append(dev_name)

    for dev in devices:
        addr_path = f"/sys/class/nvme/{dev}/address"
        if not os.path.exists(addr_path):
            continue
        try:
            with open(addr_path, 'r') as f:
                bdf = f.read().strip()
        except:
            continue

        lspci_out, _, ret_code = _run_command(["lspci", "-vvvs", bdf])
        lnksta = "N/A"
        if ret_code == 0:
            for l in lspci_out.splitlines():
                if "LnkSta:" in l and "Speed" in l:
                    lnksta = l.split(":", 1)[1].strip()
                    break
                elif "Speed Downgraded" in l:
                    lnksta = "Speed Downgraded"
                    break

        data.append({
            "nvme": dev,
            "busInfo": bdf,
            "lnkSta": lnksta
        })

    return _make_response(0, data)


@mcp.tool
def getCpuUsage() -> str:
    """
    ### 模块：系统资源检测
    ### 接口：CPU 使用率查询
    ### 返回字段说明：
    | 字段名         | 类型   | 是否必填 | 示例值 | 详细描述 |
    |----------------|--------|----------|--------|----------|
    | cpuUsage       | string | 是       | "1.7"  | CPU 使用率百分比 |
    | cpuThreshold   | string | 是       | "80"   | 告警阈值（固定） |

    ### 响应示例：
    { "data": [{ "cpuUsage": "1.7", "cpuThreshold": "80" }] }
    """
    out, err, ret = _run_command("top -bn1 | grep 'Cpu(s)' | awk '{print $2}'", shell=True)
    if ret != 0:
        return _make_response(1002, [], f"top failed: {err}")

    try:
        usage = f"{float(out.strip()):.1f}"
    except:
        return _make_response(1003, [], "Parse CPU usage failed")

    return _make_response(0, [{
        "cpuUsage": usage,
        "cpuThreshold": "80"
    }])


@mcp.tool
def getMemoryUsage() -> str:
    """
    ### 模块：系统资源检测
    ### 接口：内存使用率查询
    ### 返回字段说明：
    | 字段名           | 类型   | 是否必填 | 示例值  | 详细描述 |
    |------------------|--------|----------|---------|----------|
    | memUsage         | string | 是       | "67.0"  | 内存使用率百分比 |
    | memTotal         | string | 是       | "31250" | 总内存(MB) |
    | memUsed          | string | 是       | "21442" | 已用内存(MB) |
    | memAvailable     | string | 是       | "9808"  | 可用内存(MB) |
    | memThreshold     | string | 是       | "80"    | 告警阈值 |

    ### 响应示例：
    { "data": [{ "memUsage": "67.0", "memTotal": "31250", "memUsed": "21442", "memAvailable": "9808", "memThreshold": "80" }] }
    """
    out, err, ret = _run_command(["free", "-m"])
    if ret != 0:
        return _make_response(1002, [], f"free failed: {err}")

    try:
        lines = out.splitlines()
        for line in lines:
            if line.startswith("Mem:"):
                parts = line.split()
                total = int(parts[1])
                used = int(parts[2])
                available = int(parts[6]) if len(parts) > 6 else 0
                usage = round((used / total) * 100, 1)
                break
        else:
            return _make_response(1003, [], "No Mem line")
    except Exception as e:
        return _make_response(1003, [], f"Parse error: {str(e)}")

    return _make_response(0, [{
        "memUsage": str(usage),
        "memTotal": str(total),
        "memUsed": str(used),
        "memAvailable": str(available),
        "memThreshold": "80"
    }])


# ==================== 主程序入口 ====================
if __name__ == "__main__":
    print("🚀 H3C MCP Server (Fully Compliant Edition) Starting...")
    print(f"🔧 DEBUG Mode: {'ENABLED' if DEBUG else 'DISABLED'}")
    mcp.run(transport="sse", host="0.0.0.0", port=6666)