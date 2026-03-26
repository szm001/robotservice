"""
WebSocket 客户端模块
实现基于 websockets 库的 WebSocket 客户端，支持自动重连
"""

import asyncio
import websockets
from typing import Optional, Callable, Dict, Any
import json

try:
    from .utils import Config, setup_logger, Message, MessageType
    from websockets.client import WebSocketClientProtocol
except ImportError:
    from utils import Config, setup_logger, Message, MessageType
    from websockets.legacy.client import WebSocketClientProtocol


class WebSocketClient:
    """
    WebSocket 客户端类
    
    提供稳定的 WebSocket 连接，支持自动重连和消息处理
    """
    
    def __init__(self, config: Optional[Config] = None):
        """
        初始化客户端
        
        Args:
            config: 客户端配置，使用默认配置如果未提供
        """
        self.config = config or Config()
        self.logger = setup_logger("WebSocketClient", self.config.log_level)
        
        # WebSocket 连接
        self._websocket: Optional[WebSocketClientProtocol] = None
        
        # 连接状态
        self._connected = False
        self._running = False
        self._reconnect_attempts = 0
        
        # 消息处理器
        self.message_handlers: Dict[MessageType, Callable] = {}
        
        # 消息队列（用于重连后发送）
        self._pending_messages: list = []
        
        # 回调函数
        self._on_connect: Optional[Callable] = None
        self._on_disconnect: Optional[Callable] = None
        self._on_message: Optional[Callable] = None
        
        # 注册默认处理器
        self._register_default_handlers()
    
    def _register_default_handlers(self):
        """注册默认的消息处理器"""
        self.message_handlers[MessageType.TEXT] = self._handle_text_message
        self.message_handlers[MessageType.HEARTBEAT] = self._handle_heartbeat
        self.message_handlers[MessageType.ERROR] = self._handle_error_message
    
    def _handle_text_message(self, message: Message):
        """处理文本消息"""
        self.logger.info(f"收到文本消息：{message}")
        if self._on_message:
            self._on_message(message)
    
    def _handle_heartbeat(self, message: Message):
        """处理心跳响应"""
        self.logger.debug("收到心跳响应")
    
    def _handle_error_message(self, message: Message):
        """处理错误消息"""
        self.logger.error(f"收到服务器错误：{message.content}")
        if self._on_message:
            self._on_message(message)
    
    def register_handler(self, message_type: MessageType, handler: Callable):
        """
        注册自定义消息处理器
        
        Args:
            message_type: 消息类型
            handler: 处理函数，签名为 handler(message)
        """
        self.message_handlers[message_type] = handler
        self.logger.info(f"已注册 {message_type.value} 类型的消息处理器")
    
    def on_connect(self, callback: Optional[Callable] = None):
        """
        设置连接成功回调
        
        Args:
            callback: 回调函数，签名为 callback()
        """
        self._on_connect = callback
    
    def on_disconnect(self, callback: Optional[Callable] = None):
        """
        设置断开连接回调
        
        Args:
            callback: 回调函数，签名为 callback()
        """
        self._on_disconnect = callback
    
    def on_message(self, callback: Optional[Callable] = None):
        """
        设置收到消息回调（默认回调，当没有特定处理器时调用）
        
        Args:
            callback: 回调函数，签名为 callback(message)
        """
        self._on_message = callback
    
    async def connect(self, uri: Optional[str] = None):
        """
        连接到 WebSocket 服务器
        
        Args:
            uri: WebSocket 服务器 URI，如果未提供则使用配置中的 host 和 port
        """
        if uri is None:
            uri = f"ws://{self.config.host}:{self.config.port}"
        
        self._running = True
        self._reconnect_attempts = 0
        
        await self._connect_with_retry(uri)
    
    async def _connect_with_retry(self, uri: str):
        """
        带重试的连接
        
        Args:
            uri: WebSocket 服务器 URI
        """
        while self._running:
            try:
                self.logger.info(f"尝试连接到 {uri}")
                
                self._websocket = await websockets.connect(
                    uri,
                    ping_interval=self.config.ping_interval,
                    ping_timeout=self.config.ping_timeout,
                    max_size=self.config.max_message_size
                )
                
                self._connected = True
                self._reconnect_attempts = 0
                
                self.logger.info("已成功连接到 WebSocket 服务器")
                
                # 调用连接回调
                if self._on_connect:
                    self._on_connect()
                
                # 发送待处理的消息
                await self._flush_pending_messages()
                
                # 开始接收消息
                await self._receive_messages()
                
            except (ConnectionRefusedError, OSError, websockets.exceptions.InvalidHandshake) as e:
                self.logger.error(f"连接失败：{e}")
                self._connected = False
                
                # 调用断开回调
                if self._on_disconnect:
                    self._on_disconnect()
                
                # 检查是否需要重连
                if not self._should_reconnect():
                    self.logger.error("达到最大重连尝试次数，停止重连")
                    break
                
                # 计算重连延迟（指数退避）
                delay = min(
                    self.config.reconnect_delay * (self.config.reconnect_multiplier ** self._reconnect_attempts),
                    self.config.reconnect_max_delay
                )
                
                self.logger.info(f"将在 {delay:.1f} 秒后重连（尝试 {self._reconnect_attempts}）")
                await asyncio.sleep(delay)
                
                self._reconnect_attempts += 1
            
            except websockets.exceptions.ConnectionClosed as e:
                self.logger.warning(f"连接关闭：{e.code} - {e.reason}")
                self._connected = False
                
                # 调用断开回调
                if self._on_disconnect:
                    self._on_disconnect()
                
                # 检查是否需要重连
                if not self._should_reconnect():
                    break
                
                # 计算重连延迟
                delay = min(
                    self.config.reconnect_delay * (self.config.reconnect_multiplier ** self._reconnect_attempts),
                    self.config.reconnect_max_delay
                )
                
                self.logger.info(f"将在 {delay:.1f} 秒后重连（尝试 {self._reconnect_attempts}）")
                await asyncio.sleep(delay)
                
                self._reconnect_attempts += 1
        
        self.logger.info("客户端已停止")
    
    async def _receive_messages(self):
        """接收并处理消息"""
        if not self._websocket:
            return
        
        try:
            async for raw_message in self._websocket:
                if not self._running:
                    break
                
                try:
                    # 解析消息
                    message = Message.from_json(raw_message)
                    self.logger.debug(f"收到消息：{message}")
                    
                    # 调用对应的处理器
                    handler = self.message_handlers.get(message.type)
                    if handler:
                        if asyncio.iscoroutinefunction(handler):
                            await handler(message)
                        else:
                            handler(message)
                    else:
                        self.logger.warning(f"未找到 {message.type} 类型的处理器")
                        # 默认处理
                        self._handle_text_message(message)
                
                except json.JSONDecodeError as e:
                    self.logger.error(f"消息解析错误：{e}")
        
        except asyncio.CancelledError:
            self.logger.debug("消息接收被取消")
        except Exception as e:
            self.logger.error(f"接收消息时出错：{e}", exc_info=True)
    
    async def _flush_pending_messages(self):
        """发送待处理的消息"""
        while self._pending_messages and self._connected:
            message = self._pending_messages.pop(0)
            try:
                await self.send(message)
                self.logger.debug(f"已发送待处理消息：{message}")
            except Exception as e:
                self.logger.error(f"发送待处理消息失败：{e}")
                self._pending_messages.insert(0, message)
                break
    
    def _should_reconnect(self) -> bool:
        """
        判断是否应该重连
        
        Returns:
            True 如果应该重连，否则 False
        """
        if not self._running:
            return False
        
        if self.config.max_reconnect_attempts is None:
            return True
        
        return self._reconnect_attempts < self.config.max_reconnect_attempts
    
    async def send(self, message: Message):
        """
        发送消息
        
        Args:
            message: 要发送的消息
            
        Raises:
            ConnectionError: 当未连接时
        """
        if not self._connected or not self._websocket:
            self.logger.warning("未连接，消息已加入待发送队列")
            self._pending_messages.append(message)
            raise ConnectionError("未连接到服务器")
        
        try:
            message_json = message.to_json()
            await self._websocket.send(message_json)
            self.logger.debug(f"已发送消息：{message}")
        except websockets.exceptions.ConnectionClosed:
            self.logger.warning("连接已关闭，消息发送失败")
            self._connected = False
            self._pending_messages.append(message)
            raise
        except Exception as e:
            self.logger.error(f"发送消息失败：{e}")
            raise
    
    async def send_text(self, content: str, sender: Optional[str] = None):
        """
        发送文本消息
        
        Args:
            content: 消息内容
            sender: 发送者标识
        """
        message = Message(type=MessageType.TEXT, content=content, sender=sender)
        await self.send(message)
    
    async def send_join(self, sender: str):
        """
        发送加入消息
        
        Args:
            sender: 用户标识
        """
        message = Message(type=MessageType.JOIN, content="join", sender=sender)
        await self.send(message)
    
    async def send_leave(self, sender: str):
        """
        发送离开消息
        
        Args:
            sender: 用户标识
        """
        message = Message(type=MessageType.LEAVE, content="leave", sender=sender)
        await self.send(message)
    
    async def send_heartbeat(self):
        """发送心跳消息"""
        message = Message(type=MessageType.HEARTBEAT, content="ping", sender="client")
        await self.send(message)
    
    async def stop(self):
        """停止客户端并关闭连接"""
        self.logger.info("正在停止客户端...")
        
        self._running = False
        
        if self._websocket:
            try:
                await self._websocket.close(1000, "客户端关闭")
            except Exception as e:
                self.logger.warning(f"关闭连接时出错：{e}")
        
        self._connected = False
        self._websocket = None
        
        self.logger.info("客户端已停止")
    
    @property
    def is_connected(self) -> bool:
        """检查是否已连接"""
        return self._connected
    
    @property
    def is_running(self) -> bool:
        """检查是否正在运行"""
        return self._running
