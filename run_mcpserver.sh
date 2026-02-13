#!/bin/bash

# ============================================
# MCP Disk Monitor 启动脚本
# 功能：
# 1. 生成 SSH 密钥对（如果不存在）
# 2. 设置 SSH 权限
# 3. 检查并加载 MCP Monitor 镜像（如果不存在）
# 4. 启动 Docker 容器
# ============================================

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印带颜色的消息
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查是否以 root 用户运行
check_root() {
    if [[ $EUID -eq 0 ]]; then
        print_warning "脚本以 root 用户运行，请注意权限问题"
    fi
}

# 检查 Docker 是否安装
check_docker() {
    if ! command -v docker &> /dev/null; then
        print_error "Docker 未安装，请先安装 Docker"
        exit 1
    fi
    print_success "Docker 已安装"
}

# 检查 Docker 服务是否运行
check_docker_service() {
    if ! docker info &> /dev/null; then
        print_error "Docker 服务未运行，请启动 Docker 服务"
        exit 1
    fi
    print_success "Docker 服务正在运行"
}

# 生成 SSH 密钥
generate_ssh_key() {
    local ssh_dir="$HOME/.ssh"
    local private_key="$ssh_dir/id_rsa"
    local public_key="$ssh_dir/id_rsa.pub"
    local auth_keys="$ssh_dir/authorized_keys"
    
    # 创建 .ssh 目录（如果不存在）
    if [ ! -d "$ssh_dir" ]; then
        print_info "创建 .ssh 目录: $ssh_dir"
        mkdir -p "$ssh_dir"
    fi
    
    # 生成 SSH 密钥对（如果不存在）
    if [ ! -f "$private_key" ] || [ ! -f "$public_key" ]; then
        print_info "生成 SSH RSA 4096 密钥对..."
        ssh-keygen -t rsa -b 4096 -f "$private_key" -N "" -q
        print_success "SSH 密钥对已生成"
    else
        print_info "SSH 密钥对已存在，跳过生成"
    fi
    
    # 将公钥添加到 authorized_keys
    if [ ! -f "$auth_keys" ] || ! grep -q "$(cat "$public_key")" "$auth_keys" 2>/dev/null; then
        print_info "将公钥添加到 authorized_keys..."
        cat "$public_key" >> "$auth_keys"
        print_success "公钥已添加到 authorized_keys"
    else
        print_info "公钥已在 authorized_keys 中，跳过添加"
    fi
    
    # 设置正确的权限
    print_info "设置 SSH 目录和文件权限..."
    chmod 700 "$ssh_dir"
    chmod 600 "$private_key"
    chmod 644 "$public_key"
    chmod 600 "$auth_keys"
    print_success "权限设置完成"
    
    # 显示公钥信息
    print_info "SSH 公钥指纹:"
    ssh-keygen -lf "$public_key"
}

# 检查环境变量文件
check_env_file() {
    local env_file="run.env"
    
    if [ ! -f "$env_file" ]; then
        print_warning "环境变量文件 $env_file 不存在，创建示例文件..."
        
        cat > "$env_file" << EOF
# MCP Disk Monitor 环境变量配置
# SSH 用户名
SSH_USERNAME=root

# 日志级别 (debug, info, warning, error)
LOG_LEVEL=debug

# 其他配置
# MCP_SERVER_URL=http://localhost:8000
# API_KEY=your_api_key_here
# TIMEOUT=30
EOF
        
        print_info "已创建示例环境变量文件: $env_file"
        print_warning "请编辑 $env_file 文件以配置实际参数"
    else
        print_success "找到环境变量文件: $env_file"
    fi
}

# 检查 mcp-server 目录
check_mcp_server_dir() {
    local mcp_dir="./mcp-server"
    
    if [ ! -d "$mcp_dir" ]; then
        print_warning "mcp-server 目录不存在: $mcp_dir"
        print_info "创建 mcp-server 目录..."
        mkdir -p "$mcp_dir"
        print_success "已创建 mcp-server 目录"
        
        # 创建示例文件
        if [ ! -f "$mcp_dir/README.md" ]; then
            cat > "$mcp_dir/README.md" << EOF
# MCP Server 目录

此目录用于存放 MCP Server 相关文件。

请将您的 MCP Server 文件放在此目录中。
EOF
        fi
    else
        print_success "找到 mcp-server 目录: $mcp_dir"
    fi
}

# 检查并加载 MCP Monitor 镜像
check_and_load_image() {
    local image_name="mcp_monitor"
    
    # 检查镜像是否存在
    if docker image inspect "$image_name" &> /dev/null; then
        print_success "MCP Monitor 镜像已存在，跳过加载"
        return 0
    fi
    
    print_warning "MCP Monitor 镜像不存在，准备加载..."
    
    # 动态查找最新的镜像包
    local tar_file=$(find . -maxdepth 1 -name "mcp_monitor*.tar" -type f | sort -V | tail -n 1)
    
    if [ -z "$tar_file" ]; then
        print_error "未找到任何 MCP Monitor 镜像包 (*.tar)"
        print_info "请确保当前目录下存在 mcp_monitor*.tar 文件"
        exit 1
    fi
    
    print_info "找到最新的镜像包: $tar_file"
    
    # 加载镜像
    print_info "开始加载镜像包: $tar_file"
    if docker load -i "$tar_file"; then
        print_success "镜像加载成功"
        
        # 验证镜像是否加载成功
        if docker image inspect "$image_name" &> /dev/null; then
            print_success "MCP Monitor 镜像验证成功"
        else
            print_warning "镜像加载完成，但未找到预期的镜像名称 '$image_name'"
            print_info "已加载的镜像列表:"
            docker images | grep -i mcp || true
            
            # 尝试从加载的镜像中获取实际镜像名称
            local loaded_images=$(docker images --format "table {{.Repository}}" | grep -v REPOSITORY | grep -i mcp || true)
            if [ -n "$loaded_images" ]; then
                print_info "检测到以下 MCP 相关镜像，请检查是否需要更新镜像名称:"
                echo "$loaded_images"
            fi
        fi
    else
        print_error "镜像加载失败"
        exit 1
    fi
}

# 启动 Docker 容器
start_docker_container() {
    print_info "启动 MCP Monitor 容器..."
    
    local container_name="mcp_monitor_$(date +%s)"
    
    docker run -it \
        --name "$container_name" \
        -v "$HOME/.ssh/id_rsa:/root/.ssh/id_rsa:ro" \
        --env-file run.env \
        --entrypoint="" \
        --add-host=host.docker.internal:host-gateway \
        --network=host \
        mcp_monitor /bin/bash
    
    # 容器退出后的清理
    print_info "容器已停止，正在清理..."
    docker rm "$container_name" 2>/dev/null || true
    print_success "清理完成"
}

# 主函数
main() {
    print_info "开始执行 MCP Disk Monitor 启动脚本..."
    print_info "当前时间: $(date)"
    print_info "工作目录: $(pwd)"
    echo ""
    
    # 执行检查
    check_root
    check_docker
    check_docker_service
    
    echo ""
    print_info "步骤 1/4: 设置 SSH 密钥..."
    generate_ssh_key
    
    echo ""
    print_info "步骤 2/4: 检查环境变量文件..."
    check_env_file
    
    echo ""
    print_info "步骤 3/4: 检查 mcp-server 目录..."
    check_mcp_server_dir
    
    echo ""
    print_info "步骤 4/4: 检查并加载 MCP Monitor 镜像..."
    check_and_load_image
    
    echo ""
    print_info "步骤 5/5: 启动 Docker 容器..."
    echo "============================================"
    start_docker_container
}

# 显示使用说明
show_usage() {
    echo "用法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  -h, --help     显示此帮助信息"
    echo "  -s, --setup    仅进行环境设置，不启动容器"
    echo "  -c, --clean    清理旧的容器和镜像"
    echo ""
    echo "示例:"
    echo "  $0             完整执行（默认）"
    echo "  $0 --setup     仅设置环境"
    echo "  $0 --clean     清理旧容器"
}

# 清理函数
cleanup() {
    print_info "清理旧的 MCP Disk Monitor 容器..."
    
    # 停止并删除所有名为 mcp_monitor-* 的容器
    local containers=$(docker ps -a --filter "name=mcp_monitor_" --format "{{.Names}}" 2>/dev/null || true)
    
    if [ -n "$containers" ]; then
        print_info "找到以下容器需要清理:"
        echo "$containers"
        
        for container in $containers; do
            print_info "停止容器: $container"
            docker stop "$container" 2>/dev/null || true
            
            print_info "删除容器: $container"
            docker rm "$container" 2>/dev/null || true
        done
        
        print_success "容器清理完成"
    else
        print_info "没有找到需要清理的容器"
    fi
    
    # 可选：清理未使用的镜像
    read -p "是否清理未使用的 Docker 镜像？(y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_info "清理未使用的镜像..."
        docker image prune -f
        print_success "镜像清理完成"
    fi
}

# 仅设置环境
setup_only() {
    print_info "仅进行环境设置..."
    
    check_root
    check_docker
    check_docker_service
    
    generate_ssh_key
    check_env_file
    check_mcp_server_dir
    check_and_load_image
    
    print_success "环境设置完成！"
    print_info "要启动容器，请运行: $0"
}

# 解析命令行参数
if [[ $# -gt 0 ]]; then
    case $1 in
        -h|--help)
            show_usage
            exit 0
            ;;
        -s|--setup)
            setup_only
            exit 0
            ;;
        -c|--clean)
            cleanup
            exit 0
            ;;
        *)
            print_error "未知选项: $1"
            show_usage
            exit 1
            ;;
    esac
fi

# 执行主函数
main
