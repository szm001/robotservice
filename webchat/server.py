"""
WebSocket 服务器模块
实现基于 websockets 库的 WebSocket 服务器
"""

import asyncio
import websockets
from typing import Dict, Set, Optional, Callable
import json

try:
    from .utils import Config, setup_logger, Message, MessageType
    from websockets.server import WebSocketServerProtocol
except ImportError:
    from utils import Config, setup_logger, Message, MessageType
    from websockets.legacy.server import WebSocketServerProtocol


class WebSocketServer:
    """
    WebSocket 服务器类
    
    提供稳定的 WebSocket 连接服务，支持多客户端连接和消息广播
    """
    
    def __init__(self, config: Optional[Config] = None):
        """
        初始化服务器
        
        Args:
            config: 服务器配置，使用默认配置如果未提供
        """
        self.config = config or Config()
        self.logger = setup_logger("WebSocketServer", self.config.log_level)
        
        # 连接的客户端集合
        self.clients: Set[WebSocketServerProtocol] = set()
        # 客户端信息映射
        self.client_info: Dict[WebSocketServerProtocol, dict] = {}
        
        # 消息处理器
        self.message_handlers: Dict[MessageType, Callable] = {}
        
        # 服务器状态
        self._server = None
        self._running = False
        
        # 注册默认处理器
        self._register_default_handlers()
    
    def _register_default_handlers(self):
        """注册默认的消息处理器"""
        self.message_handlers[MessageType.TEXT] = self._handle_text_message
        self.message_handlers[MessageType.JOIN] = self._handle_join_message
        self.message_handlers[MessageType.LEAVE] = self._handle_leave_message
        self.message_handlers[MessageType.HEARTBEAT] = self._handle_heartbeat
    
    def register_handler(self, message_type: MessageType, handler: Callable):
        """
        注册自定义消息处理器
        
        Args:
            message_type: 消息类型
            handler: 处理函数，签名为 handler(server, websocket, message)
        """
        self.message_handlers[message_type] = handler
        self.logger.info(f"已注册 {message_type.value} 类型的消息处理器")
    
    async def _handle_text_message(self, websocket: WebSocketServerProtocol, message: Message):
        """处理文本消息 - 广播给所有客户端"""
        self.logger.info(f"收到来自 {message.sender} 的文本消息：{message.content}")
        await self.broadcast(message, exclude=websocket)
    
    async def _handle_join_message(self, websocket: WebSocketServerProtocol, message: Message):
        """处理用户加入消息"""
        self.logger.info(f"用户 {message.sender} 加入聊天")
        join_notification = Message(
            type=MessageType.JOIN,
            content=f"{message.sender} 已加入",
            sender="system"
        )
        await self.broadcast(join_notification)
    
    async def _handle_leave_message(self, websocket: WebSocketServerProtocol, message: Message):
        """处理用户离开消息"""
        self.logger.info(f"用户 {message.sender} 离开聊天")
        leave_notification = Message(
            type=MessageType.LEAVE,
            content=f"{message.sender} 已离开",
            sender="system"
        )
        await self.broadcast(leave_notification, exclude=websocket)
    
    async def _handle_heartbeat(self, websocket: WebSocketServerProtocol, message: Message):
        """处理心跳消息"""
        heartbeat_response = Message(
            type=MessageType.HEARTBEAT,
            content="pong",
            sender="server"
        )
        await self.send_to(websocket, heartbeat_response)
    
    async def handler(self, websocket: WebSocketServerProtocol):
        """
        WebSocket 连接处理器
        
        Args:
            websocket: WebSocket 连接对象
        """
        # 添加客户端到集合
        self.clients.add(websocket)
        self.client_info[websocket] = {
            "connected_at": asyncio.get_event_loop().time(),
            "message_count": 0
        }
        
        self.logger.info(f"新客户端连接，当前连接数：{len(self.clients)}")
        
        try:
            # 发送欢迎消息
            welcome = Message(
                type=MessageType.TEXT,
                content="欢迎连接到 WebSocket 服务器！",
                sender="server"
            )
            await self.send_to(websocket, welcome)
            
            # 处理消息
            async for raw_message in websocket:
                try:
                    # 解析消息
                    message = Message.from_json(raw_message)
                    self.logger.debug(f"收到消息：{message}")
                    
                    # 更新统计
                    self.client_info[websocket]["message_count"] += 1
                    
                    # 调用对应的处理器
                    handler = self.message_handlers.get(message.type)
                    if handler:
                        await handler(websocket, message)
                    else:
                        self.logger.warning(f"未找到 {message.type} 类型的处理器")
                        # 默认当作文本消息处理
                        await self._handle_text_message(websocket, message)
                
                except json.JSONDecodeError as e:
                    self.logger.error(f"消息解析错误：{e}")
                    error_msg = create_error_message(f"无效的消息格式：{str(e)}", "server")
                    await self.send_to(websocket, error_msg)
                
                except Exception as e:
                    self.logger.error(f"处理消息时出错：{e}", exc_info=True)
                    error_msg = create_error_message(f"服务器错误：{str(e)}", "server")
                    await self.send_to(websocket, error_msg)
        
        except websockets.exceptions.ConnectionClosed as e:
            self.logger.info(f"客户端连接关闭：{e.code} - {e.reason}")
        
        finally:
            # 移除客户端
            self.clients.remove(websocket)
            if websocket in self.client_info:
                del self.client_info[websocket]
            
            self.logger.info(f"客户端断开连接，当前连接数：{len(self.clients)}")
    
    async def broadcast(self, message: Message, exclude: Optional[WebSocketServerProtocol] = None):
        """
        广播消息给所有连接的客户端
        
        Args:
            message: 要广播的消息
            exclude: 要排除的客户端（可选）
        """
        if not self.clients:
            self.logger.debug("没有客户端可接收消息")
            return
        
        message_json = message.to_json()
        
        # 创建发送任务
        tasks = []
        for client in self.clients.copy():
            if client != exclude:
                tasks.append(self._safe_send(client, message_json))
        
        # 并发发送
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            failed = sum(1 for r in results if isinstance(r, Exception))
            if failed:
                self.logger.warning(f"广播失败：{failed}/{len(tasks)} 个客户端")
    
    async def send_to(self, websocket: WebSocketServerProtocol, message: Message):
        """
        发送消息给指定客户端
        
        Args:
            websocket: 目标客户端
            message: 要发送的消息
        """
        try:
            await websocket.send(message.to_json())
            self.logger.debug(f"已发送消息给客户端：{message}")
        except websockets.exceptions.ConnectionClosed:
            self.logger.warning("尝试发送到已关闭的连接")
        except Exception as e:
            self.logger.error(f"发送消息失败：{e}")
    
    async def _safe_send(self, websocket: WebSocketServerProtocol, message: str):
        """
        安全的发送消息，捕获异常
        
        Args:
            websocket: 目标客户端
            message: 消息字符串
        """
        try:
            await websocket.send(message)
        except websockets.exceptions.ConnectionClosed:
            self.logger.debug("客户端已断开，跳过发送")
        except Exception as e:
            self.logger.error(f"发送失败：{e}")
            raise e
    
    async def start(self):
        """启动服务器"""
        self._running = True
        
        self._server = await websockets.serve(
            self.handler,
            self.config.host,
            self.config.port,
            ping_interval=self.config.ping_interval,
            ping_timeout=self.config.ping_timeout,
            max_size=self.config.max_message_size
        )
        
        self.logger.info(f"WebSocket 服务器已启动：ws://{self.config.host}:{self.config.port}")
        
        # 等待服务器关闭
        await self._server.wait_closed()
    
    async def stop(self):
        """停止服务器"""
        self._running = False
        
        if self._server:
            self._server.close()
            await self._server.wait_closed()
        
        # 关闭所有客户端连接
        close_tasks = []
        for client in self.clients.copy():
            close_tasks.append(client.close(1001, "服务器关闭"))
        
        if close_tasks:
            await asyncio.gather(*close_tasks, return_exceptions=True)
        
        self.logger.info("WebSocket 服务器已停止")
    
    def get_client_count(self) -> int:
        """获取当前连接的客户端数量"""
        return len(self.clients)
    
    def get_client_stats(self) -> dict:
        """获取客户端统计信息"""
        return {
            "total_clients": len(self.clients),
            "clients": [
                {
                    "connected_duration": asyncio.get_event_loop().time() - info["connected_at"],
                    "message_count": info["message_count"]
                }
                for info in self.client_info.values()
            ]
        }


# 便捷函数
def create_error_message(error: str, sender: Optional[str] = None) -> Message:
    """创建错误消息的便捷函数"""
    return Message(type=MessageType.ERROR, content=error, sender=sender)
