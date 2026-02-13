"""配置管理模块"""
import os
from dataclasses import dataclass, field
from typing import Optional
from pathlib import Path

@dataclass
class AppSettings:
    """应用配置"""
    # 基础配置
    DEBUG: bool = field(default_factory=lambda: os.getenv("MCP_DEBUG", "false").lower() == "true")
    HOST: str = field(default_factory=lambda: os.getenv("MCP_HOST", "0.0.0.0"))
    PORT: int = field(default_factory=lambda: int(os.getenv("MCP_PORT", "6666")))
    TRANSPORT: str = field(default_factory=lambda: os.getenv("MCP_TRANSPORT", "sse"))
    
    # 命令执行配置
    COMMAND_TIMEOUT: int = field(default_factory=lambda: int(os.getenv("COMMAND_TIMEOUT", "3")))
    
    # SSH配置
    SSH_USERNAME: str = field(default_factory=lambda: os.getenv("SSH_USERNAME", "stor_user"))
    SSH_HOST: str = field(default_factory=lambda: os.getenv("SSH_HOST", "localhost"))
    SSH_PORT: int = field(default_factory=lambda: int(os.getenv("SSH_PORT", "22")))
    SSH_TIMEOUT: int = field(default_factory=lambda: int(os.getenv("SSH_TIMEOUT", "3")))
    
    # 日志配置
    LOG_LEVEL: str = field(default_factory=lambda: os.getenv("LOG_LEVEL", "info").lower())
    LOG_DIR: Path = field(default_factory=lambda: Path(os.getenv("LOG_DIR", "logs")))
    LOG_MAX_SIZE: int = field(default_factory=lambda: int(os.getenv("LOG_MAX_SIZE", "10485760")))  # 10MB
    LOG_BACKUP_COUNT: int = field(default_factory=lambda: int(os.getenv("LOG_BACKUP_COUNT", "5")))
    
    # 性能配置
    MAX_WORKERS: int = field(default_factory=lambda: int(os.getenv("MAX_WORKERS", "4")))
    
    @classmethod
    def from_env(cls) -> "AppSettings":
        """从环境变量创建配置实例"""
        return cls()
    
    def validate(self):
        """验证配置"""
        valid_log_levels = ['debug', 'info', 'warning', 'error', 'critical']
        if self.LOG_LEVEL not in valid_log_levels:
            raise ValueError(f"Invalid LOG_LEVEL: {self.LOG_LEVEL}. Must be one of {valid_log_levels}")
        
        if self.PORT < 1 or self.PORT > 65535:
            raise ValueError(f"Invalid PORT: {self.PORT}. Must be between 1 and 65535")
        
        if self.COMMAND_TIMEOUT < 1:
            raise ValueError(f"Invalid COMMAND_TIMEOUT: {self.COMMAND_TIMEOUT}. Must be positive")

settings = AppSettings.from_env()

# 验证配置
try:
    settings.validate()
except ValueError as e:
    import sys
    sys.stderr.write(f"Configuration error: {e}\n")
    exit(1)