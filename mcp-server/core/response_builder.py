"""响应构建器模块"""
import json
import logging
from typing import Any, Dict, Optional
from config.constants import ErrorCode, ERROR_MESSAGES
from config.settings import settings
from config.logging_config import get_logger

class ResponseBuilder:
    """MCP响应构建器"""
    
    def __init__(self):
        self.logger = get_logger(__name__)
    
    def build(self, 
              code: ErrorCode, 
              data: Any = None, 
              message: Optional[str] = None) -> str:
        """
        构建符合MCP规范的响应
        
        Args:
            code: 错误码
            data: 响应数据
            message: 自定义消息
            
        Returns:
            JSON格式的响应字符串
        """
        if data is None:
            data = []
        
        msg = message or ERROR_MESSAGES.get(code, "unknown error")
        
        structured_content = {
            "response": {
                "code": code.value,
                "message": msg,
                "data": data
            }
        }
        
        # 生成outputSchema
        output_schema = self._get_output_schema_for_data(data)
        
        response = {
            "structuredContent": structured_content,
            "outputSchema": output_schema
        }
        
        # 记录响应构建日志
        if code == ErrorCode.SUCCESS:
            self.logger.debug(f"Response built successfully with code {code.value}, data items: {len(data) if isinstance(data, list) else 1}")
        else:
            self.logger.warning(f"Response built with error code {code.value}: {msg}")
        
        indent = 2 if settings.DEBUG else None
        return json.dumps(response, ensure_ascii=False, indent=indent)
    
    def _get_output_schema_for_data(self, data: Any) -> Dict[str, Any]:
        """
        根据数据自动生成outputSchema
        
        Args:
            data: 响应数据
            
        Returns:
            JSON Schema字典
        """
        schema = {
            "type": "object",
            "properties": {
                "code": {
                    "type": "number", 
                    "description": "接口返回码，0表示成功"
                },
                "message": {
                    "type": "string", 
                    "description": "接口返回信息"
                },
                "data": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {},
                        "required": [],
                        "additionalProperties": True
                    }
                }
            },
            "required": ["code", "message", "data"],
            "additionalProperties": False,
            "description": "接口返回体",
            "$schema": "http://json-schema.org/draft-07/schema#"
        }
        
        if not data or not isinstance(data, list) or len(data) == 0:
            return schema
        
        # 使用第一个数据项作为样本生成字段定义
        sample = data[0]
        if not isinstance(sample, dict):
            return schema
        
        props = {}
        required = []
        
        for key, value in sample.items():
            # 根据值类型推断字段类型
            if isinstance(value, (int, float)):
                field_type = "number"
            elif isinstance(value, bool):
                field_type = "boolean"
            else:
                field_type = "string"
            
            props[key] = {
                "type": field_type,
                "description": f"{key}字段说明"
            }
            required.append(key)
        
        schema["properties"]["data"]["items"]["properties"] = props
        schema["properties"]["data"]["items"]["required"] = required
        
        return schema