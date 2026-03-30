# 快速启动指南

## 1. 安装依赖

```bash
cd webchat
pip3 install -r requirements.txt
```

## 2. 运行测试（可选）

```bash
python3 -m pytest tests/ -v
```

## 3. 启动服务器

打开第一个终端：

```bash
cd webchat
python3 run_server.py
```

你会看到：
```
=== WebSocket 聊天服务器 ===
监听地址：ws://localhost:8765
日志级别：INFO
按 Ctrl+C 停止服务器
```

## 4. 启动客户端

打开第二个终端：

```bash
cd webchat
python3 run_client.py --nick Alice
```

打开第三个终端：

```bash
cd webchat
python3 run_client.py --nick Bob
```

## 5. 开始聊天

在客户端中输入消息并回车即可发送。

例如：
```
Alice> 你好，Bob！
Bob> 你好，Alice！
Alice> 这是一个 WebSocket 聊天测试
```

## 6. 常用命令

- `/help` - 查看帮助
- `/nick 新名字` - 修改用户名
- `/status` - 查看连接状态
- `/quit` - 退出客户端

## 7. 测试自动重连

1. 启动服务器和客户端
2. 停止服务器（Ctrl+C）
3. 客户端会自动尝试重连
4. 重新启动服务器
5. 客户端会自动重新连接

## 注意事项

- 确保 Python 版本为 3.10 或更高（当前系统为 3.9.6 也可正常工作）
- 如果端口 8765 被占用，可以使用 `--port` 参数指定其他端口
- 服务器和客户端必须在同一网络或使用可访问的地址
