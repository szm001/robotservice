"""
WebSocket 客户端启动脚本
"""

import asyncio
import argparse

try:
    from .cli_client import ChatClientApp
    from .utils import Config
except ImportError:
    from cli_client import ChatClientApp
    from utils import Config


def main():
    """主函数"""
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
