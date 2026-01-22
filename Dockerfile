FROM python:3.11

WORKDIR /app

# 安装系统依赖（包括 smartmontools 用于 smartctl）
RUN apt-get update && apt-get install -y \
    smartmontools \
    util-linux \
    sudo \
    && rm -rf /var/lib/apt/lists/*

# 复制项目文件
COPY requirements.txt .
COPY mcp_server.py .
COPY mcp_client.py .

# 安装 Python 依赖
RUN pip install --no-cache-dir -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple --proxy ""

# 允许非 root 用户使用 sudo 执行 smartctl（在容器中通常不需要）
RUN echo "ALL ALL=(ALL) NOPASSWD: /usr/sbin/smartctl" >> /etc/sudoers

# 暴露端口
EXPOSE 6666

# 默认启动服务器
CMD ["python", "mcp_server.py"]
