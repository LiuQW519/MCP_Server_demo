import subprocess
import json
from typing import List, Dict, Any
from fastmcp import FastMCP

# 初始化 MCP 服务实例
mcp = FastMCP(name="DiskMonitorServer")

@mcp.tool
def check_disk_smart(device: str = "/dev/sda") -> str:
    """
    检查指定硬盘的 SMART 自检状态。
    
    Args:
        device (str): 要检查的硬盘设备路径，默认为 /dev/sda。
    
    Returns:
        str: 返回 SMART 自检结果，为 "PASSED" 或 "FAILED"。
    """
    try:
        # 使用 smartctl 命令查询 SMART 健康状态
        # 注意：此命令需要 root 权限或 sudo 配置
        result = subprocess.run(
            ["sudo", "smartctl", "-H", device],
            capture_output=True,
            text=True,
            check=False
        )
        output = result.stdout.lower()
        
        if "self-assessment test result: passed" in output:
            return "PASSED"
        elif "self-assessment test result: failed" in output:
            return "FAILED"
        else:
            # 如果命令输出无法解析，可能表示命令执行失败或输出格式不符
            return f"UNKNOWN or ERROR: {result.stderr[:100]}"
            
    except FileNotFoundError:
        return "ERROR: 'smartctl' command not found. Please install smartmontools."
    except Exception as e:
        return f"ERROR: {str(e)}"

@mcp.tool
def list_disks() -> List[Dict[str, Any]]:
    """
    执行 lsblk 命令查询服务器上的磁盘列表。
    
    Returns:
        List[Dict]: 返回一个字典列表，每个字典包含磁盘的名称、大小和类型等信息。
    """
    try:
        # 使用 lsblk 命令以 JSON 格式输出磁盘信息
        result = subprocess.run(
            ["lsblk", "-J", "-o", "NAME,SIZE,TYPE,MOUNTPOINT"],
            capture_output=True,
            text=True,
            check=True
        )
        data = json.loads(result.stdout)
        # 从返回的 JSON 中提取 blockdevices 列表
        disks = data.get("blockdevices", [])
        return disks
        
    except FileNotFoundError:
        return [{"error": "'lsblk' command not found."}]
    except json.JSONDecodeError:
        return [{"error": "Failed to parse lsblk output."}]
    except subprocess.CalledProcessError as e:
        return [{"error": f"lsblk command failed: {e.stderr[:100]}"}]
    except Exception as e:
        return [{"error": f"Unexpected error: {str(e)}"}]

if __name__ == "__main__":
    # 启动服务，使用 SSE 传输模式，监听所有网络接口的 6666 端口
    mcp.run(transport="sse", host="0.0.0.0", port=6666)