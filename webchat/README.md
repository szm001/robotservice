# WebSocket 客户端与服务器通讯系统

一个基于 Python 和 WebSocket 技术构建的完整实时双向通信系统。

## 功能特性

### 核心技术
- ✅ 基于标准 WebSocket 协议 (RFC 6455) 实现双向实时通信
- ✅ 服务器端使用 Python `websockets` 库
- ✅ 客户端采用 Python 命令行界面
- ✅ 兼容 Python 3.10 及以上版本

### 核心功能
- ✅ 稳定的 WebSocket 连接
- ✅ 自动重连机制（指数退避算法）
- ✅ 文本消息实时双向传输
- ✅ 连接状态监控与错误处理
- ✅ 多客户端支持与消息广播

### 扩展特性
- ✅ 模块化架构设计
- ✅ 可扩展的消息类型系统
- ✅ 心跳检测机制
- ✅ 用户加入/离开通知
- ✅ 命令处理系统

## 目录结构

```
webchat/
├── __init__.py           # 包初始化
├── utils/                # 公共工具模块
│   ├── __init__.py
│   ├── config.py         # 配置管理
│   ├── logger.py         # 日志系统
│   └── message.py        # 消息类型与结构
├── server.py             # WebSocket 服务器模块
├── client.py             # WebSocket 客户端模块
├── cli_client.py         # 命令行交互界面
├── run_server.py         # 服务器启动脚本
├── run_client.py         # 客户端启动脚本
├── requirements.txt      # 依赖包列表
├── tests/                # 单元测试
│   ├── __init__.py
│   ├── test_message.py   # 消息模块测试
│   ├── test_config.py    # 配置模块测试
│   └── test_integration.py # 集成测试
└── README.md             # 说明文档
```

## 安装说明

### 1. 环境要求
- Python 3.10 或更高版本
- pip 包管理器

### 2. 安装依赖

```bash
cd webchat
pip install -r requirements.txt
```

### 3. 验证安装

```bash
python -m pytest tests/
```

## 使用方法

### 启动服务器

```bash
# 使用默认配置（localhost:8765）
python -m webchat.run_server

# 自定义主机和端口
python -m webchat.run_server --host 0.0.0.0 --port 9000

# 设置日志级别
python -m webchat.run_server --log-level DEBUG
```

**服务器参数说明：**
- `--host`: 监听主机地址（默认：localhost）
- `--port`: 监听端口（默认：8765）
- `--log-level`: 日志级别（默认：INFO）

### 启动客户端

```bash
# 使用默认配置连接到本地服务器
python -m webchat.run_client

# 连接到远程服务器
python -m webchat.run_client --host 192.168.1.100 --port 9000

# 设置用户名
python -m webchat.run_client --nick Alice

# 完整示例
python -m webchat.run_client --host localhost --port 8765 --nick Bob --log-level DEBUG
```

**客户端参数说明：**
- `--host`: 服务器主机地址（默认：localhost）
- `--port`: 服务器端口（默认：8765）
- `--nick`: 用户名（默认：user）
- `--log-level`: 日志级别（默认：INFO）

## 客户端命令

连接到服务器后，可以使用以下命令：

| 命令 | 说明 |
|------|------|
| `/help` | 显示帮助信息 |
| `/quit` 或 `/exit` | 退出客户端 |
| `/connect` | 连接到服务器 |
| `/disconnect` | 断开与服务器的连接 |
| `/status` | 显示连接状态 |
| `/nick <name>` | 设置用户名 |
| `/clear` | 清屏 |
| 其他输入 | 发送文本消息 |

## 消息类型

系统支持以下消息类型：

- **TEXT**: 普通文本消息
- **JOIN**: 用户加入通知
- **LEAVE**: 用户离开通知
- **ERROR**: 错误消息
- **ACK**: 确认消息
- **COMMAND**: 命令消息
- **NOTIFICATION**: 通知消息
- **HEARTBEAT**: 心跳消息

## 配置选项

可以通过 `Config` 类自定义系统行为：

```python
from utils import Config

config = Config(
    host="localhost",
    port=8765,
    ping_interval=30,        # 心跳间隔（秒）
    ping_timeout=10,         # 心跳超时（秒）
    reconnect_delay=1.0,     # 初始重连延迟（秒）
    reconnect_max_delay=60.0, # 最大重连延迟（秒）
    reconnect_multiplier=2.0, # 重连延迟倍增系数
    max_reconnect_attempts=None, # 最大重连尝试次数（None 为无限）
    log_level="INFO",
    max_message_size=1048576, # 最大消息大小（字节）
)
```

## 自动重连机制

客户端实现了智能重连机制：

1. **指数退避**: 重连延迟按指数增长（1s, 2s, 4s, 8s...）
2. **最大延迟**: 重连延迟不超过 60 秒
3. **可配置**: 可设置最大重连尝试次数
4. **消息队列**: 重连期间发送的消息会被缓存

## 扩展开发

### 添加自定义消息处理器

**服务器端：**

```python
from webchat.server import WebSocketServer
from webchat.utils import MessageType, Message

async def handle_custom_message(websocket, message):
    """处理自定义消息"""
    print(f"收到自定义消息：{message.content}")
    # 处理逻辑...

server = WebSocketServer()
server.register_handler(MessageType.COMMAND, handle_custom_message)
```

**客户端：**

```python
from webchat.client import WebSocketClient
from webchat.utils import MessageType

async def handle_custom_message(message):
    """处理自定义消息"""
    print(f"收到：{message.content}")

client = WebSocketClient()
client.register_handler(MessageType.COMMAND, handle_custom_message)
```

### 添加新的消息类型

```python
from webchat.utils import MessageType

# 扩展消息类型（在 message.py 中定义）
class MessageType(str, Enum):
    # ... 现有类型 ...
    CUSTOM = "custom"  # 新增类型
```

## 运行测试

```bash
# 运行所有测试
python -m pytest tests/ -v

# 运行特定测试文件
python -m pytest tests/test_message.py -v

# 运行测试并显示覆盖率
python -m pytest tests/ --cov=webchat --cov-report=html
```

## 示例场景

### 场景 1：本地聊天测试

终端 1 - 启动服务器：
```bash
python -m webchat.run_server
```

终端 2 - 启动客户端 1：
```bash
python -m webchat.run_client --nick Alice
```

终端 3 - 启动客户端 2：
```bash
python -m webchat.run_client --nick Bob
```

### 场景 2：网络稳定性测试

1. 启动服务器
2. 启动客户端并建立连接
3. 停止服务器
4. 观察客户端自动重连
5. 重启服务器
6. 客户端自动恢复连接

## 技术细节

### 协议规范
- 遵循 WebSocket 协议 RFC 6455
- 支持 WebSocket 心跳（ping/pong）
- JSON 格式消息编码

### 安全性
- 支持消息大小限制（防止 DoS）
- 连接超时检测
- 错误处理与日志记录

### 性能优化
- 异步 I/O 操作
- 并发消息广播
- 连接池管理

## 常见问题

### Q: 客户端无法连接服务器？
A: 检查以下几点：
1. 服务器是否已启动
2. 主机地址和端口是否正确
3. 防火墙是否阻止连接
4. 查看日志输出获取详细错误信息

### Q: 如何修改默认端口？
A: 使用 `--port` 参数启动服务器和客户端

### Q: 客户端断线后会自动重连吗？
A: 是的，客户端默认启用自动重连机制

### Q: 如何查看调试信息？
A: 使用 `--log-level DEBUG` 参数启动服务器或客户端

## 许可证

本项目采用 MIT 许可证。

## 贡献

欢迎提交 Issue 和 Pull Request！

## 联系方式

如有问题或建议，请通过 Issue 联系我们。
