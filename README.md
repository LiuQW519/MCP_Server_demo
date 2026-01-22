# MCP Disk Monitor Server

[![Docker Build Status](https://img.shields.io/docker/build/mcp-disk-monitor)](https://hub.docker.com/r/yourusername/mcp-disk-monitor)
[![Python Version](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

一个基于Model Context Protocol (MCP)的磁盘监控服务器Docker镜像，提供磁盘SMART状态检查和磁盘列表查询功能。

## 📋 目录

- [概述](#概述)
- [功能特性](#功能特性)
- [快速开始](#快速开始)
  - [前提条件](#前提条件)
  - [构建镜像](#构建镜像)
  - [运行容器](#运行容器)
- [使用方法](#使用方法)
  - [MCP服务器API](#mcp服务器api)
  - [客户端测试](#客户端测试)
- [项目结构](#项目结构)
- [配置说明](#配置说明)
- [高级用法](#高级用法)
  - [自定义端口](#自定义端口)
  - [持久化存储](#持久化存储)
  - [安全配置](#安全配置)
- [故障排除](#故障排除)
- [贡献指南](#贡献指南)
- [许可证](#许可证)

## 概述

本项目展示了如何从零开始构建一个基于MCP协议的磁盘监控服务器。MCP（Model Context Protocol）是一种新兴的协议，允许AI模型通过标准化的方式与外部工具和服务进行交互。

这个项目包含：

- 一个完整的MCP服务器实现
- 磁盘监控工具（SMART状态检查、磁盘列表查询， 并不完善，仅做调用test使用）
- Python客户端测试工具
- Docker容器化部署方案

## 功能特性

### 🚀 MCP服务器端

- 提供RESTful API接口
- 支持SSE（Server-Sent Events）传输模式
- 监听所有网络接口，便于远程访问

### 💾 磁盘监控工具(并不完善，仅做调用test使用)

- **`check_disk_smart`**: 检查硬盘SMART自检状态
  - 支持指定硬盘设备路径
  - 返回"PASSED"、"FAILED"或错误信息
- **`list_disks`**: 查询服务器磁盘列表信息
  - 使用lsblk命令获取详细信息
  - 返回JSON格式的磁盘和设备树信息

### 🔧 客户端工具

- 完整的Python客户端实现
- 支持异步调用
- 自动重连和错误处理
- 友好的命令行输出格式

### 🐳 容器化部署

- 完整的Docker镜像构建方案
- 最小化依赖安装
- 安全配置选项
- 健康检查支持

## 快速开始

### 前提条件

1. **操作系统**: Linux系统（已在EulerOS 2.x/22.03 LTS测试）
2. **Docker**: 已安装并运行的Docker服务
3. **Python**: 3.11+（仅客户端需要）

### 构建镜像

1. 克隆项目：

```bash
git clone https://github.com/yourusername/mcp-disk-monitor.git
cd mcp-disk-monitor
```

2. 构建Docker镜像：

```bash
docker build -t mcp-disk-monitor .
```

### 运行容器

启动MCP服务器容器：

```bash
docker run -d \
  --name mcp-server \
  -p 6666:6666 \
  --restart unless-stopped \
  mcp-disk-monitor
```

验证容器状态：

```bash
docker ps | grep mcp-server
```

查看服务器日志：

```bash
docker logs mcp-server
```

## 使用方法

### MCP服务器API

服务器启动后，可以通过以下方式访问：

- **SSE端点**: `http://localhost:6666/sse`
- **工具列表**: 通过MCP协议自动发现

### 客户端测试

运行内置的Python客户端进行测试：

注意，非localhost需修改代码里的请求IP部分

```bash
python mcp_client.py
```

示例输出：

```
==================================================
连接到 MCP 服务器...
==================================================
连接到 MCP 服务器: http://localhost:6666/sse
可用工具: ['check_disk_smart', 'list_disks']
找到 2 个工具:
  - check_disk_smart: 检查指定硬盘的 SMART 自检状态。
  - list_disks: 执行 lsblk 命令查询服务器上的磁盘列表。

==================================================
测试 list_disks 工具...
==================================================
找到 8 个磁盘设备:
----------------------------------------
├─ sda (disk, 447.1G)
  ├─ md126 (raid1, 424.8G)
    ├─ md126p1 (part, 600M)
    ├─ md126p2 (part, 1G)
    ├─ md126p3 (part, 423.2G)
  └─ md127 (None, 0B)
```

## 项目结构

```
mcp-disk-monitor/
├── Dockerfile              # Docker构建配置
├── requirements.txt        # Python依赖列表
├── mcp_server.py          # MCP服务器实现
├── mcp_client.py          # Python客户端测试工具
├── README.md              # 项目说明文档
└── LICENSE                # 许可证文件
```

## 配置说明

### Dockerfile配置项

| 配置项   | 默认值               | 说明             |
| -------- | -------------------- | ---------------- |
| 基础镜像 | python:3.11          | Python运行时环境 |
| 工作目录 | /app                 | 应用安装目录     |
| 暴露端口 | 6666                 | MCP服务端口      |
| 启动命令 | python mcp_server.py | 默认启动命令     |

### 环境变量

| 变量名 | 默认值  | 说明           |
| ------ | ------- | -------------- |
| PORT   | 6666    | 服务器监听端口 |
| HOST   | 0.0.0.0 | 服务器绑定地址 |

## 高级用法

### 自定义端口

如果需要使用不同的端口，可以修改映射：

```bash
docker run -d \
  --name mcp-server \
  -p 8888:6666 \
  mcp-disk-monitor
```

然后在客户端中指定新端口：

```python
client = DiskMonitorClient(server_url="http://localhost:8888/sse")
```

### 持久化存储

如果需要保存监控数据，可以挂载卷：

```bash
docker run -d \
  --name mcp-server \
  -p 6666:6666 \
  -v $(pwd)/data:/app/data \
  mcp-disk-monitor
```

### 安全配置

1. **使用非root用户运行**（推荐）：

```bash
docker run -d \
  --name mcp-server \
  -p 6666:6666 \
  --user 1000:1000 \
  mcp-disk-monitor
```

2. **限制资源使用**：

```bash
docker run -d \
  --name mcp-server \
  -p 6666:6666 \
  --memory=512m \
  --cpus=1 \
  mcp-disk-monitor
```

### 日志查看

查看详细的服务器日志：

```bash
docker logs -f mcp-server
```

进入容器调试：

```bash
docker exec -it mcp-server /bin/bash
```

## 相关链接

- [Model Context Protocol 官方文档](https://modelcontextprotocol.io/)
- [FastMCP 框架](https://github.com/fastmcp/fastmcp)
- [Docker 官方文档](https://docs.docker.com/)

---

**注意**: 本项目主要用于演示和学习目的。在生产环境中使用时，请确保进行充分的安全评估和测试。

如有问题或建议，请提交 [Issue](https://github.com/yourusername/mcp-disk-monitor/issues) 或通过邮件联系。
