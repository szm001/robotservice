"""
命令行客户端模块
提供基于命令行的交互式 WebSocket 客户端
"""

import asyncio
import sys
from typing import Optional

try:
    from .utils import Config, setup_logger, Message, MessageType
    from .client import WebSocketClient
except ImportError:
    from utils import Config, setup_logger, Message, MessageType
    from client import WebSocketClient


class CommandProcessor:
    """命令处理器"""
    
    def __init__(self, client_app: "ChatClientApp"):
        self.client_app = client_app
        self.logger = setup_logger("CommandProcessor")
        
        # 注册命令
        self.commands = {
            "/help": self.cmd_help,
            "/quit": self.cmd_quit,
            "/exit": self.cmd_quit,
            "/connect": self.cmd_connect,
            "/disconnect": self.cmd_disconnect,
            "/status": self.cmd_status,
            "/nick": self.cmd_nick,
            "/clear": self.cmd_clear,
        }
    
    async def process(self, command: str) -> bool:
        """
        处理命令
        
        Args:
            command: 命令字符串
            
        Returns:
            True 如果应该继续运行，False 如果应该退出
        """
        parts = command.strip().split(maxsplit=1)
        if not parts:
            return True
        
        cmd = parts[0].lower()
        args = parts[1] if len(parts) > 1 else ""
        
        handler = self.commands.get(cmd)
        if handler:
            return await handler(args)
        else:
            # 不是命令，当作文本消息发送
            return await self.cmd_send_message(command)
    
    async def cmd_help(self, args: str) -> bool:
        """显示帮助信息"""
        print("\n=== 可用命令 ===")
        print("/help          - 显示帮助信息")
        print("/quit          - 退出客户端")
        print("/connect       - 连接到服务器")
        print("/disconnect    - 断开与服务器的连接")
        print("/status        - 显示连接状态")
        print("/nick <name>   - 设置用户名")
        print("/clear         - 清屏")
        print("其他输入       - 发送文本消息")
        print("==============\n")
        return True
    
    async def cmd_quit(self, args: str) -> bool:
        """退出客户端"""
        print("正在退出...")
        return False
    
    async def cmd_connect(self, args: str) -> bool:
        """连接到服务器"""
        if self.client_app.is_connected:
            print("已经连接到服务器")
        else:
            print("正在连接服务器...")
            # 主循环会处理重连
        return True
    
    async def cmd_disconnect(self, args: str) -> bool:
        """断开连接"""
        if self.client_app.is_connected:
            await self.client_app.disconnect()
            print("已断开连接")
        else:
            print("未连接到服务器")
        return True
    
    async def cmd_status(self, args: str) -> bool:
        """显示状态"""
        if self.client_app.is_connected:
            print(f"✓ 已连接")
            print(f"  服务器：{self.client_app.server_uri}")
            print(f"  用户名：{self.client_app.username}")
        else:
            print("✗ 未连接")
            print(f"  服务器：{self.client_app.server_uri}")
        return True
    
    async def cmd_nick(self, args: str) -> bool:
        """设置用户名"""
        if not args.strip():
            print(f"当前用户名：{self.client_app.username}")
        else:
            self.client_app.username = args.strip()
            print(f"用户名已设置为：{self.client_app.username}")
        return True
    
    async def cmd_clear(self, args: str) -> bool:
        """清屏"""
        # Windows
        if sys.platform == "win32":
            asyncio.create_subprocess_exec("cls", shell=True)
        # Unix-like
        else:
            asyncio.create_subprocess_exec("clear")
        return True
    
    async def cmd_send_message(self, message: str) -> bool:
        """发送消息"""
        if not self.client_app.is_connected:
            print("未连接到服务器，请先连接")
            return True
        
        message = message.strip()
        if not message:
            return True
        
        try:
            await self.client_app.send_message(message)
        except Exception as e:
            print(f"发送失败：{e}")
        
        return True


class ChatClientApp:
    """
    聊天客户端应用
    
    提供命令行交互界面
    """
    
    def __init__(self, config: Optional[Config] = None):
        """
        初始化客户端应用
        
        Args:
            config: 配置对象
        """
        self.config = config or Config()
        self.logger = setup_logger("ChatClientApp", self.config.log_level)
        
        # WebSocket 客户端
        self.client = WebSocketClient(self.config)
        
        # 应用状态
        self.username = "user"
        self.server_uri = f"ws://{self.config.host}:{self.config.port}"
        self._running = False
        
        # 命令处理器
        self.command_processor = CommandProcessor(self)
        
        # 设置客户端回调
        self.client.on_connect(self._on_connect)
        self.client.on_disconnect(self._on_disconnect)
        self.client.on_message(self._on_message)
    
    def _on_connect(self):
        """连接成功回调"""
        print("\n✓ 已连接到服务器")
        print(f"  用户名：{self.username}")
        print("  输入 /help 查看可用命令\n")
    
    def _on_disconnect(self):
        """断开连接回调"""
        print("\n✗ 与服务器断开连接")
        print("  正在尝试重连...\n")
    
    def _on_message(self, message: Message):
        """收到消息回调"""
        # 格式化显示消息
        if message.type == MessageType.TEXT:
            print(f"[{message.timestamp}] {message.sender}: {message.content}")
        elif message.type == MessageType.JOIN:
            print(f"[{message.timestamp}] [系统] {message.content}")
        elif message.type == MessageType.LEAVE:
            print(f"[{message.timestamp}] [系统] {message.content}")
        elif message.type == MessageType.ERROR:
            print(f"[{message.timestamp}] [错误] {message.content}")
        else:
            print(f"[{message.timestamp}] [{message.type.value}] {message.content}")
    
    @property
    def is_connected(self) -> bool:
        """检查是否已连接"""
        return self.client.is_connected
    
    async def send_message(self, content: str):
        """
        发送消息
        
        Args:
            content: 消息内容
        """
        await self.client.send_text(content, sender=self.username)
    
    async def disconnect(self):
        """断开连接"""
        # 发送离开消息
        try:
            await self.client.send_leave(self.username)
        except Exception:
            pass
        
        await self.client.stop()
    
    async def _input_loop(self):
        """用户输入循环"""
        print("\n=== WebSocket 聊天客户端 ===")
        print(f"服务器：{self.server_uri}")
        print("输入 /help 查看可用命令\n")
        
        while self._running:
            try:
                # 获取用户输入
                if self.is_connected:
                    prompt = f"{self.username}> "
                else:
                    prompt = "(未连接) "
                
                # 使用 asyncio 的 run_in_executor 来避免阻塞
                loop = asyncio.get_event_loop()
                user_input = await loop.run_in_executor(
                    None, input, prompt
                )
                
                # 处理输入
                if user_input.strip():
                    should_continue = await self.command_processor.process(user_input)
                    if not should_continue:
                        break
                
            except EOFError:
                # 处理 Ctrl+D
                break
            except KeyboardInterrupt:
                # 处理 Ctrl+C
                print("\n中断信号")
                break
            except Exception as e:
                self.logger.error(f"输入处理错误：{e}")
        
        self._running = False
    
    async def run(self):
        """运行客户端应用"""
        self._running = True
        
        # 启动两个并发任务：连接和输入处理
        tasks = [
            asyncio.create_task(self.client.connect(self.server_uri)),
            asyncio.create_task(self._input_loop())
        ]
        
        try:
            # 等待任一任务完成
            done, pending = await asyncio.wait(
                tasks,
                return_when=asyncio.FIRST_COMPLETED
            )
            
            # 取消未完成的任务
            for task in pending:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
        
        except asyncio.CancelledError:
            self.logger.debug("应用被取消")
        except Exception as e:
            self.logger.error(f"应用错误：{e}", exc_info=True)
        finally:
            # 清理
            await self.client.stop()
            print("\n再见！")


def main():
    """主函数"""
    import argparse
    
    # 解析命令行参数
    parser = argparse.ArgumentParser(description="WebSocket 聊天客户端")
    parser.add_argument("--host", default="localhost", help="服务器主机地址")
    parser.add_argument("--port", type=int, default=8765, help="服务器端口")
    parser.add_argument("--nick", default="user", help="用户名")
    parser.add_argument("--log-level", default="INFO", help="日志级别")
    
    args = parser.parse_args()
    
    # 创建配置
    config = Config(
        host=args.host,
        port=args.port,
        log_level=args.log_level
    )
    
    # 创建并运行应用
    app = ChatClientApp(config)
    app.username = args.nick
    
    try:
        asyncio.run(app.run())
    except KeyboardInterrupt:
        print("\n已退出")


if __name__ == "__main__":
    main()
