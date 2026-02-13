"""版本管理模块"""
from datetime import datetime

class VersionInfo:
    """版本信息类"""
    
    # 版本信息 - 从version.txt文件读取
    VERSION_FILE = "version.txt"
    
    def __init__(self):
        self._load_version_info()
    
    def _load_version_info(self):
        """从version.txt文件加载版本信息"""
        import os
        
        # 默认值
        self.APP_NAME = "智能问数MCP服务"
        self.DESCRIPTION = "H3C智能排障与智能问数系统"
        self.VERSION = "V1.0.0"
        self.BUILD_DATE = "2026.02.13:10:58"
        
        # 尝试从version.txt文件读取
        version_file_path = os.path.join(os.path.dirname(__file__), self.VERSION_FILE)
        
        if os.path.exists(version_file_path):
            try:
                with open(version_file_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line and '=' in line:
                            key, value = line.split('=', 1)
                            key = key.strip()
                            value = value.strip()
                            
                            if key == 'VERSION':
                                self.VERSION = value
                            elif key == 'BUILD_DATE':
                                self.BUILD_DATE = value
                            elif key == 'APP_NAME':
                                self.APP_NAME = value
                            elif key == 'DESCRIPTION':
                                self.DESCRIPTION = value
            except Exception:
                # 如果文件读取失败，使用默认值
                pass
    
    def get_version_info(self) -> str:
        """获取完整的版本信息"""
        return f"{self.APP_NAME} {self.VERSION} (Build: {self.BUILD_DATE})\
\n{self.DESCRIPTION}"
    
    def get_banner(self) -> str:
        """获取启动横幅"""
        banner = f"""
{'=' * 60}
{self.APP_NAME}
版本: {self.VERSION}
构建时间: {self.BUILD_DATE}
描述: {self.DESCRIPTION}
{'=' * 60}
"""
        return banner
    
    def print_startup_info(self):
        """打印启动信息"""
        print(self.get_banner())
        
        # 打印当前时间
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"启动时间: {current_time}")
        print()

# 版本信息实例
version_info = VersionInfo()