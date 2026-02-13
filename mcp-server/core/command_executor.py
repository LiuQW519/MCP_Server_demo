"""命令执行器模块"""
import subprocess
import logging
from typing import List, Tuple
from config.settings import settings
from config.logging_config import get_logger

class CommandExecutor:
    """命令执行器，封装系统命令执行逻辑"""
    
    def __init__(self, timeout: int = None):
        self.timeout = timeout or settings.COMMAND_TIMEOUT
        self.logger = get_logger(__name__)
        self.ssh_timeout = settings.SSH_TIMEOUT
        self.ssh_username = settings.SSH_USERNAME
        self.ssh_host = settings.SSH_HOST
        self.ssh_port = settings.SSH_PORT
    
    def execute(self, 
                cmd: List[str], 
                shell: bool = False) -> Tuple[str, str, int]:
        """
        执行系统命令
        
        Args:
            cmd: 命令列表或字符串
            shell: 是否启用shell执行
            
        Returns:
            (stdout, stderr, returncode)
        """
        # ssh远程执行
        self.logger.info(f"Executing command via SSH: {' '.join(cmd) if isinstance(cmd, list) else cmd}")
        ssh_pref = ['ssh', 
                   '-o', 'StrictHostKeyChecking=no', 
                   '-o', 'UserKnownHostsFile=/dev/null',
                   '-o', 'LogLevel=ERROR',
                   '-o',  f'ConnectTimeout={self.ssh_timeout}']
        ssh_usr = ['-p', f'{self.ssh_port}', f'{self.ssh_username}@{self.ssh_host}']
        # 为所有命令添加sudo前缀
        if isinstance(cmd, list):
            cmd = ssh_pref + ssh_usr + ['sudo'] + cmd
        else:
            cmd = ssh_pref + ssh_usr + ['sudo', cmd]
        
        self.logger.debug(f"Full SSH command: {' '.join(cmd) if isinstance(cmd, list) else cmd}")
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                shell=shell,
                timeout=self.timeout
            )
            
            stdout = result.stdout.strip()
            stderr = result.stderr.strip()
            
            self._log_output(stdout, stderr)
            
            if result.returncode == 0:
                self.logger.info(f"Command executed successfully with return code {result.returncode}")
            else:
                self.logger.warning(f"Command completed with non-zero return code {result.returncode}")
            
            return stdout, stderr, result.returncode
            
        except subprocess.TimeoutExpired as e:
            error_msg = f"Command timeout after {self.timeout}s"
            self.logger.error(error_msg)
            return "", error_msg, -1
        except Exception as e:
            error_msg = f"Command execution failed: {str(e)}"
            self.logger.error(error_msg)
            return "", error_msg, -1
    
    def _log_output(self, stdout: str, stderr: str):
        """记录输出日志"""
        if stdout:
            stdout_lines = stdout.splitlines()
            if len(stdout_lines) <= 10:  # 如果输出行数较少，完整记录
                self.logger.debug(f"STDOUT ({len(stdout_lines)} lines):")
                for line in stdout_lines:
                    self.logger.debug(f"  {line}")
            else:
                self.logger.debug(f"STDOUT ({len(stdout_lines)} lines, showing first 5):")
                for line in stdout_lines[:5]:
                    self.logger.debug(f"  {line}")
                self.logger.debug(f"... (truncated {len(stdout_lines)-10} lines) ...")
                self.logger.debug("STDOUT last 5 lines:")
                for line in stdout_lines[-5:]:
                    self.logger.debug(f"  {line}")
        
        if stderr:
            stderr_lines = stderr.splitlines()
            if len(stderr_lines) <= 5:
                self.logger.warning(f"STDERR ({len(stderr_lines)} lines):")
                for line in stderr_lines:
                    self.logger.warning(f"  {line}")
            else:
                self.logger.warning(f"STDERR ({len(stderr_lines)} lines, showing first 3):")
                for line in stderr_lines[:3]:
                    self.logger.warning(f"  {line}")
                self.logger.warning(f"... (truncated {len(stderr_lines)-6} lines) ...")
                self.logger.warning("STDERR last 3 lines:")
                for line in stderr_lines[-3:]:
                    self.logger.warning(f"  {line}")