"""
集成测试
测试服务器和客户端的完整交互流程
"""

import unittest
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from utils import Config, Message, MessageType
from server import WebSocketServer
from client import WebSocketClient


class TestIntegration(unittest.TestCase):
    """集成测试类"""
    
    def setUp(self):
        """测试前准备"""
        self.config = Config(
            host="localhost",
            port=8766,  # 使用不同端口避免冲突
            log_level="WARNING"
        )
        self.server = None
        self.server_task = None
    
    def tearDown(self):
        """测试后清理"""
        if self.server_task and not self.server_task.done():
            self.server_task.cancel()
    
    def test_message_creation_and_serialization(self):
        """测试消息创建和序列化"""
        msg = Message(type=MessageType.TEXT, content="test", sender="user1")
        json_str = msg.to_json()
        restored = Message.from_json(json_str)
        
        self.assertEqual(msg.type, restored.type)
        self.assertEqual(msg.content, restored.content)
        self.assertEqual(msg.sender, restored.sender)
    
    def test_config_initialization(self):
        """测试配置初始化"""
        config = Config()
        self.assertIsNotNone(config)
        self.assertEqual(config.port, 8765)
        
        custom_config = Config(host="test", port=9999)
        self.assertEqual(custom_config.host, "test")
        self.assertEqual(custom_config.port, 9999)
    
    def test_server_initialization(self):
        """测试服务器初始化"""
        server = WebSocketServer(self.config)
        self.assertIsNotNone(server)
        self.assertEqual(server.get_client_count(), 0)
    
    def test_client_initialization(self):
        """测试客户端初始化"""
        client = WebSocketClient(self.config)
        self.assertIsNotNone(client)
        self.assertFalse(client.is_connected)
        # _running 初始为 False，直到 connect() 被调用
        self.assertFalse(client.is_running)
    
    def test_message_types(self):
        """测试各种消息类型"""
        messages = [
            Message(type=MessageType.TEXT, content="hello"),
            Message(type=MessageType.JOIN, content="join", sender="user1"),
            Message(type=MessageType.LEAVE, content="leave", sender="user1"),
            Message(type=MessageType.ERROR, content="error"),
            Message(type=MessageType.HEARTBEAT, content="ping"),
        ]
        
        for msg in messages:
            json_str = msg.to_json()
            restored = Message.from_json(json_str)
            self.assertEqual(msg.type, restored.type)
            self.assertEqual(msg.content, restored.content)


class TestAsyncServerClient(unittest.TestCase):
    """异步服务器和客户端测试"""
    
    def test_server_start_stop(self):
        """测试服务器启动和停止"""
        config = Config(host="localhost", port=8767)
        server = WebSocketServer(config)
        
        async def run_test():
            # 启动服务器
            server_task = asyncio.create_task(server.start())
            
            # 等待一小段时间
            await asyncio.sleep(0.5)
            
            # 检查服务器是否运行
            self.assertTrue(server._running)
            
            # 停止服务器
            await server.stop()
            
            # 取消任务
            server_task.cancel()
            try:
                await server_task
            except asyncio.CancelledError:
                pass
        
        asyncio.run(run_test())
    
    def test_client_connect_disconnect(self):
        """测试客户端连接和断开"""
        config = Config(host="localhost", port=8768)
        client = WebSocketClient(config)
        
        async def run_test():
            # 不连接服务器，测试客户端状态
            self.assertFalse(client.is_connected)
            
            # 测试停止
            await client.stop()
            self.assertFalse(client.is_running)
        
        asyncio.run(run_test())


if __name__ == "__main__":
    unittest.main()
