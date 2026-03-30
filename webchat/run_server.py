"""
WebSocket 服务器启动脚本
"""

import asyncio
import argparse

try:
    from .server import WebSocketServer
    from .utils import Config
except ImportError:
    from server import WebSocketServer
    from utils import Config


async def run_server(config: Config):
    """
    运行 WebSocket 服务器
    
    Args:
        config: 服务器配置
    """
    server = WebSocketServer(config)
    
    try:
        await server.start()
    except KeyboardInterrupt:
        print("\n正在关闭服务器...")
        await server.stop()


def main():
    """主函数"""
    # 解析命令行参数
    parser = argparse.ArgumentParser(description="WebSocket 聊天服务器")
    parser.add_argument("--host", default="localhost", help="监听主机地址")
    parser.add_argument("--port", type=int, default=8765, help="监听端口")
    parser.add_argument("--log-level", default="INFO", help="日志级别")
    
    args = parser.parse_args()
    
    # 创建配置
    config = Config(
        host=args.host,
        port=args.port,
        log_level=args.log_level
    )
    
    print(f"=== WebSocket 聊天服务器 ===")
    print(f"监听地址：ws://{config.host}:{config.port}")
    print(f"日志级别：{config.log_level}")
    print("按 Ctrl+C 停止服务器\n")
    
    try:
        asyncio.run(run_server(config))
    except KeyboardInterrupt:
        print("\n服务器已关闭")


if __name__ == "__main__":
    main()
