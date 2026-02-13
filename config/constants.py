"""常量定义模块"""
from enum import IntEnum

class ErrorCode(IntEnum):
    """错误码枚举"""
    SUCCESS = 0
    COMMAND_NOT_FOUND = 1001
    COMMAND_EXECUTION_FAILED = 1002
    PARSE_FAILED = 1003
    UNEXPECTED_EXCEPTION = 1004
    DEVICE_NOT_AVAILABLE = 1005

ERROR_MESSAGES = {
    ErrorCode.SUCCESS: "success",
    ErrorCode.COMMAND_NOT_FOUND: "command not found or permission denied",
    ErrorCode.COMMAND_EXECUTION_FAILED: "command execution failed",
    ErrorCode.PARSE_FAILED: "failed to parse response",
    ErrorCode.UNEXPECTED_EXCEPTION: "unexpected exception occurred",
    ErrorCode.DEVICE_NOT_AVAILABLE: "device not available or no matching hardware found"
}