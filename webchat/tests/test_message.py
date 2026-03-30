"""
消息模块单元测试
"""

import unittest
import json
from datetime import datetime

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.message import Message, MessageType, create_text_message, create_error_message, create_command_message


class TestMessageType(unittest.TestCase):
    """测试 MessageType 枚举"""
    
    def test_message_type_values(self):
        """测试消息类型值"""
        self.assertEqual(MessageType.TEXT.value, "text")
        self.assertEqual(MessageType.JOIN.value, "join")
        self.assertEqual(MessageType.LEAVE.value, "leave")
        self.assertEqual(MessageType.ERROR.value, "error")
        self.assertEqual(MessageType.HEARTBEAT.value, "heartbeat")
    
    def test_message_type_from_string(self):
        """测试从字符串创建消息类型"""
        self.assertEqual(MessageType("text"), MessageType.TEXT)
        self.assertEqual(MessageType("error"), MessageType.ERROR)


class TestMessage(unittest.TestCase):
    """测试 Message 类"""
    
    def test_create_message(self):
        """测试创建消息"""
        msg = Message(
            type=MessageType.TEXT,
            content="Hello, World!",
            sender="test_user"
        )
        
        self.assertEqual(msg.type, MessageType.TEXT)
        self.assertEqual(msg.content, "Hello, World!")
        self.assertEqual(msg.sender, "test_user")
        self.assertIsNotNone(msg.timestamp)
    
    def test_message_to_json(self):
        """测试消息序列化为 JSON"""
        msg = Message(
            type=MessageType.TEXT,
            content="Test message",
            sender="sender1"
        )
        
        json_str = msg.to_json()
        data = json.loads(json_str)
        
        self.assertEqual(data["type"], "text")
        self.assertEqual(data["content"], "Test message")
        self.assertEqual(data["sender"], "sender1")
        self.assertIn("timestamp", data)
    
    def test_message_from_json(self):
        """测试从 JSON 反序列化消息"""
        json_str = json.dumps({
            "type": "text",
            "content": "Test content",
            "sender": "user123",
            "timestamp": "2024-01-01T00:00:00",
            "metadata": {}
        })
        
        msg = Message.from_json(json_str)
        
        self.assertEqual(msg.type, MessageType.TEXT)
        self.assertEqual(msg.content, "Test content")
        self.assertEqual(msg.sender, "user123")
        self.assertEqual(msg.timestamp, "2024-01-01T00:00:00")
    
    def test_message_from_json_invalid_type(self):
        """测试从无效类型的 JSON 创建消息"""
        json_str = json.dumps({
            "type": "invalid_type",
            "content": "Test"
        })
        
        # 应该使用默认的 TEXT 类型
        msg = Message.from_json(json_str)
        self.assertEqual(msg.type, MessageType.TEXT)
    
    def test_message_str_representation(self):
        """测试消息的字符串表示"""
        msg = Message(
            type=MessageType.TEXT,
            content="Hello",
            sender="Alice"
        )
        
        self.assertEqual(str(msg), "[text] Alice: Hello")
    
    def test_message_with_metadata(self):
        """测试带元数据的消息"""
        msg = Message(
            type=MessageType.COMMAND,
            content="ping",
            sender="system",
            metadata={"retry": 3, "timeout": 30}
        )
        
        self.assertEqual(msg.metadata["retry"], 3)
        self.assertEqual(msg.metadata["timeout"], 30)


class TestMessageFactories(unittest.TestCase):
    """测试消息工厂函数"""
    
    def test_create_text_message(self):
        """测试创建文本消息"""
        msg = create_text_message("Hello", "Alice")
        
        self.assertEqual(msg.type, MessageType.TEXT)
        self.assertEqual(msg.content, "Hello")
        self.assertEqual(msg.sender, "Alice")
    
    def test_create_error_message(self):
        """测试创建错误消息"""
        msg = create_error_message("Connection failed", "server")
        
        self.assertEqual(msg.type, MessageType.ERROR)
        self.assertEqual(msg.content, "Connection failed")
        self.assertEqual(msg.sender, "server")
    
    def test_create_command_message(self):
        """测试创建命令消息"""
        msg = create_command_message("restart", {"delay": 5}, "admin")
        
        self.assertEqual(msg.type, MessageType.COMMAND)
        self.assertEqual(msg.content, "restart")
        self.assertEqual(msg.sender, "admin")
        self.assertEqual(msg.metadata["args"]["delay"], 5)
    
    def test_create_command_message_without_args(self):
        """测试创建无参数的命令消息"""
        msg = create_command_message("ping")
        
        self.assertEqual(msg.type, MessageType.COMMAND)
        self.assertEqual(msg.content, "ping")
        self.assertEqual(msg.metadata["args"], {})


class TestMessageRoundTrip(unittest.TestCase):
    """测试消息的序列化 - 反序列化往返"""
    
    def test_message_round_trip(self):
        """测试消息往返"""
        original = Message(
            type=MessageType.TEXT,
            content="Test content",
            sender="user1",
            metadata={"key": "value"}
        )
        
        # 序列化
        json_str = original.to_json()
        
        # 反序列化
        restored = Message.from_json(json_str)
        
        # 验证
        self.assertEqual(original.type, restored.type)
        self.assertEqual(original.content, restored.content)
        self.assertEqual(original.sender, restored.sender)
        self.assertEqual(original.metadata, restored.metadata)


if __name__ == "__main__":
    unittest.main()
