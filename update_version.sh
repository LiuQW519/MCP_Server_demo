#!/bin/bash
# 版本信息更新脚本

VERSION_FILE="mcp-server/config/version.txt"

# 显示当前版本信息
show_current_version() {
    if [ -f "$VERSION_FILE" ]; then
        echo "当前版本信息:"
        echo "=============="
        cat "$VERSION_FILE"
        echo ""
    else
        echo "版本文件不存在: $VERSION_FILE"
        echo ""
    fi
}

# 更新版本信息
update_version() {
    local version="$1"
    local build_date="$2"
    
    if [ -z "$version" ]; then
        echo "错误: 请提供版本号"
        echo "用法: $0 <版本号> [构建时间]"
        echo "示例: $0 V1.0.1 2026.02.13:11:30"
        exit 1
    fi
    
    # 如果没有提供构建时间，使用当前时间
    if [ -z "$build_date" ]; then
        build_date=$(date '+%Y.%m.%d:%H:%M')
    fi
    
    echo "更新版本信息:"
    echo "=============="
    echo "版本号: $version"
    echo "构建时间: $build_date"
    echo ""
    
    # 创建或更新版本文件
    cat > "$VERSION_FILE" << EOF
# 智能问数MCP服务版本信息
# 此文件用于管理版本信息，修改后无需重新编译代码

VERSION=$version
BUILD_DATE=$build_date
APP_NAME=智能问数MCP服务
DESCRIPTION=H3C智能排障与智能问数系统
EOF
    
    echo "版本信息已更新"
    echo ""
    show_current_version
}

# 主函数
main() {
    case "${1:-}" in
        "")
            show_current_version
            ;;
        "-h"|"--help")
            echo "版本管理工具"
            echo ""
            echo "用法:"
            echo "  $0                  显示当前版本信息"
            echo "  $0 <版本号> [时间]  更新版本信息"
            echo "  $0 -h, --help       显示帮助信息"
            echo ""
            echo "示例:"
            echo "  $0                          # 显示当前版本"
            echo "  $0 V1.0.1                   # 更新版本号为V1.0.1，使用当前时间"
            echo "  $0 V1.0.1 2026.02.13:11:30  # 更新版本号和构建时间"
            ;;
        *)
            update_version "$1" "$2"
            ;;
    esac
}

main "$@"