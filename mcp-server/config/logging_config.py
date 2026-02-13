"""日志配置模块"""
import os
import sys
import logging
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from pathlib import Path
from typing import Optional, Dict, Any
from config.settings import settings

class LogManager:
    """日志管理器"""
    
    # 日志级别映射
    LOG_LEVELS = {
        'debug': logging.DEBUG,
        'info': logging.INFO,
        'warning': logging.WARNING,
        'error': logging.ERROR,
        'critical': logging.CRITICAL
    }
    
    # 日志格式
    LOG_FORMATS = {
        'default': '%(asctime)s - %(name)s - %(levelname)s - [%(pathname)s:%(funcName)s:%(lineno)d] - %(message)s',
        'detailed': '%(asctime)s - %(name)s - %(levelname)s - [%(pathname)s:%(funcName)s:%(lineno)d] - %(message)s',
        'simple': '%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'
    }
    
    def __init__(self, app_name: str = "SystemHealthChecker"):
        """
        初始化日志管理器
        
        Args:
            app_name: 应用名称，用于日志记录器名称
        """
        self.app_name = app_name
        self.log_dir = Path("logs")
        self._setup_log_directory()
        
        # 从配置获取日志级别
        log_level = os.getenv("LOG_LEVEL", "info").lower()
        self.level = self.LOG_LEVELS.get(log_level, logging.INFO)
        
        # 是否启用调试模式
        self.debug_mode = settings.DEBUG
        
    def _setup_log_directory(self):
        """创建日志目录"""
        if not self.log_dir.exists():
            self.log_dir.mkdir(exist_ok=True)
    
    def get_logger(self, name: Optional[str] = None) -> logging.Logger:
        """
        获取配置好的日志记录器
        
        Args:
            name: 日志记录器名称，默认为应用名
            
        Returns:
            配置好的Logger实例
        """
        logger_name = name or self.app_name
        logger = logging.getLogger(logger_name)
        
        # 避免重复添加处理器
        if logger.handlers:
            return logger
        
        # 设置日志级别
        logger.setLevel(self.level)
        
        # 添加处理器
        self._add_handlers(logger)
        
        # 禁用传播到根日志记录器，避免第三方库日志
        logger.propagate = False
        
        return logger
    
    def _add_handlers(self, logger: logging.Logger):
        """为日志记录器添加处理器"""
        
        # 1. 控制台处理器
        console_handler = self._create_console_handler()
        logger.addHandler(console_handler)
        
        # 2. 应用日志文件处理器（按大小轮转）
        app_handler = self._create_file_handler(
            filename="app.log",
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,
            formatter='detailed'  # 使用详细格式
        )
        logger.addHandler(app_handler)
        
        # 3. 错误日志文件处理器（按时间轮转）
        error_handler = self._create_file_handler(
            filename="error.log",
            level=logging.ERROR,
            when='midnight',
            backupCount=30,
            formatter='detailed'  # 使用详细格式
        )
        logger.addHandler(error_handler)
        
        # 4. 调试日志文件处理器（仅在调试模式启用）
        if self.debug_mode:
            debug_handler = self._create_file_handler(
                filename="debug.log",
                level=logging.DEBUG,
                formatter='detailed'
            )
            logger.addHandler(debug_handler)
    
    def _create_console_handler(self) -> logging.Handler:
        """创建控制台处理器"""
        handler = logging.StreamHandler(sys.stdout)
        
        # 始终使用详细格式，包含文件、函数和行号信息
        formatter = logging.Formatter(
            self.LOG_FORMATS['detailed'],
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        handler.setFormatter(formatter)
        
        # 设置控制台处理器级别
        handler.setLevel(self.level)
        
        return handler
    
    def _create_file_handler(self, 
                            filename: str, 
                            level: Optional[int] = None,
                            formatter: str = 'default',
                            **kwargs) -> logging.Handler:
        """
        创建文件处理器
        
        Args:
            filename: 日志文件名
            level: 日志级别
            formatter: 日志格式名称
            **kwargs: 传递给RotatingFileHandler或TimedRotatingFileHandler的参数
            
        Returns:
            文件处理器
        """
        log_file = self.log_dir / filename
        
        # 根据参数决定使用哪种轮转方式
        if 'when' in kwargs:
            # 时间轮转
            handler = TimedRotatingFileHandler(
                log_file,
                **kwargs
            )
        else:
            # 大小轮转
            handler = RotatingFileHandler(
                log_file,
                **kwargs
            )
        
        # 设置格式
        fmt = logging.Formatter(
            self.LOG_FORMATS[formatter],
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        handler.setFormatter(fmt)
        
        # 设置级别
        if level is not None:
            handler.setLevel(level)
        
        return handler
    
    def configure_root_logger(self):
        """配置根日志记录器"""
        root_logger = logging.getLogger()
        # 根日志记录器保持默认级别（WARNING），避免第三方库的debug日志
        root_logger.setLevel(logging.WARNING)
        
        # 移除默认处理器
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
        
        # 添加控制台处理器，但只处理WARNING及以上级别的日志
        console_handler = self._create_console_handler()
        console_handler.setLevel(logging.WARNING)  # 根日志记录器只显示WARNING及以上
        root_logger.addHandler(console_handler)

# 全局日志管理器实例
log_manager = LogManager()

# 便捷函数
def get_logger(name: Optional[str] = None) -> logging.Logger:
    """获取日志记录器的便捷函数"""
    return log_manager.get_logger(name)

def setup_logging():
    """设置日志系统的便捷函数"""
    # 配置根日志记录器（只处理WARNING及以上级别的日志）
    log_manager.configure_root_logger()
    
    # 获取项目专用的日志记录器（使用环境变量设置的级别）
    logger = get_logger(__name__)
    logger.info("Logging system initialized")
    return logger