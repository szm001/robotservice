"""
配置模块
集中管理系统的配置参数
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class Config:
    """系统配置类"""
    
    # 服务器配置
    host: str = "localhost"
    port: int = 8765
    
    # WebSocket 配置
    ping_interval: int = 30  # 心跳包间隔（秒）
    ping_timeout: int = 10   # 心跳超时时间（秒）
    
    # 重连配置
    reconnect_delay: float = 1.0      # 初始重连延迟（秒）
    reconnect_max_delay: float = 60.0 # 最大重连延迟（秒）
    reconnect_multiplier: float = 2.0 # 重连延迟倍增系数
    max_reconnect_attempts: Optional[int] = None  # 最大重连尝试次数（None 为无限）
    
    # 日志配置
    log_level: str = "INFO"
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # 消息配置
    max_message_size: int = 1024 * 1024  # 最大消息大小（字节）
    message_encoding: str = "utf-8"
    
    @classmethod
    def from_dict(cls, data: dict) -> "Config":
        """从字典创建配置对象"""
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})
    
    def to_dict(self) -> dict:
        """将配置对象转换为字典"""
        return {
            field.name: getattr(self, field.name)
            for field in self.__dataclass_fields__.values()
        }
