"""
消息模块
定义消息类型和消息结构
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional
import json


class MessageType(str, Enum):
    """消息类型枚举"""
    
    # 基础消息类型
    TEXT = "text"           # 文本消息
    JOIN = "join"           # 用户加入
    LEAVE = "leave"         # 用户离开
    ERROR = "error"         # 错误消息
    ACK = "ack"             # 确认消息
    
    # 可扩展的消息类型
    COMMAND = "command"     # 命令消息
    NOTIFICATION = "notification"  # 通知消息
    HEARTBEAT = "heartbeat"  # 心跳消息
    
    # 预留未来扩展
    FILE = "file"           # 文件消息（预留）
    IMAGE = "image"         # 图片消息（预留）
    VIDEO = "video"         # 视频消息（预留）


@dataclass
class Message:
    """
    消息数据结构
    
    Attributes:
        type: 消息类型
        content: 消息内容
        sender: 发送者标识
        timestamp: 时间戳
        metadata: 额外的元数据
    """
    
    type: MessageType
    content: Any
    sender: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    metadata: dict = field(default_factory=dict)
    
    def to_json(self) -> str:
        """
        将消息序列化为 JSON 字符串
        
        Returns:
            JSON 格式的消息字符串
        """
        return json.dumps({
            "type": self.type.value,
            "content": self.content,
            "sender": self.sender,
            "timestamp": self.timestamp,
            "metadata": self.metadata
        })
    
    @classmethod
    def from_json(cls, json_str: str) -> "Message":
        """
        从 JSON 字符串反序列化消息
        
        Args:
            json_str: JSON 格式的消息字符串
            
        Returns:
            Message 对象
            
        Raises:
            ValueError: 当 JSON 格式无效或消息类型不存在时
        """
        data = json.loads(json_str)
        
        try:
            message_type = MessageType(data["type"])
        except ValueError:
            # 对于未知的消息类型，使用 TEXT 作为默认类型
            message_type = MessageType.TEXT
        
        return cls(
            type=message_type,
            content=data.get("content"),
            sender=data.get("sender"),
            timestamp=data.get("timestamp", datetime.now().isoformat()),
            metadata=data.get("metadata", {})
        )
    
    def __str__(self) -> str:
        """返回消息的字符串表示"""
        return f"[{self.type.value}] {self.sender}: {self.content}"


def create_text_message(content: str, sender: Optional[str] = None) -> Message:
    """
    创建文本消息
    
    Args:
        content: 消息内容
        sender: 发送者标识
        
    Returns:
        Message 对象
    """
    return Message(type=MessageType.TEXT, content=content, sender=sender)


def create_error_message(error: str, sender: Optional[str] = None) -> Message:
    """
    创建错误消息
    
    Args:
        error: 错误信息
        sender: 发送者标识
        
    Returns:
        Message 对象
    """
    return Message(type=MessageType.ERROR, content=error, sender=sender)


def create_command_message(command: str, args: Optional[dict] = None, sender: Optional[str] = None) -> Message:
    """
    创建命令消息
    
    Args:
        command: 命令名称
        args: 命令参数
        sender: 发送者标识
        
    Returns:
        Message 对象
    """
    return Message(
        type=MessageType.COMMAND,
        content=command,
        sender=sender,
        metadata={"args": args or {}}
    )
