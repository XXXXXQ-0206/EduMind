"""
WebSocket 工具函数
管理 WebSocket 连接和消息广播
"""
from typing import Set, Dict, Any, Optional
from fastapi import WebSocket
import asyncio
import json


class ConnectionManager:
    """WebSocket 连接管理器"""

    def __init__(self):
        # 每个会话 ID 对应的活动连接集合
        self.active_connections: Dict[str, Set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, session_id: str):
        """连接 WebSocket"""
        # WebSocket 已经在路由中被接受，这里不需要再次 accept

        if session_id not in self.active_connections:
            self.active_connections[session_id] = set()

        self.active_connections[session_id].add(websocket)

    def disconnect(self, websocket: WebSocket, session_id: str):
        """断开 WebSocket 连接"""
        if session_id in self.active_connections:
            self.active_connections[session_id].discard(websocket)

            # 如果没有连接了，删除会话
            if not self.active_connections[session_id]:
                del self.active_connections[session_id]

    async def send_message(
        self, message: Dict[str, Any], session_id: str
    ):
        """向指定会话的所有连接发送消息"""
        if session_id not in self.active_connections:
            print(f"[DEBUG] No active connections for session {session_id}")
            return

        # 复制连接集，避免在迭代时修改
        connections = list(self.active_connections[session_id])
        print(f"[DEBUG] Sending message to {len(connections)} connection(s): {message.get('type')}")

        for connection in connections:
            try:
                await connection.send_json(message)
                print(f"[DEBUG] Message sent successfully")
            except Exception as e:
                # 发送失败，移除连接
                print(f"[ERROR] Failed to send message: {type(e).__name__}: {e!r}")
                self.disconnect(connection, session_id)

    async def broadcast(
        self, message: Dict[str, Any], session_id: str
    ):
        """广播消息（send_message 的别名）"""
        await self.send_message(message, session_id)

    def get_connection_count(self, session_id: str) -> int:
        """获取指定会话的连接数"""
        return len(self.active_connections.get(session_id, set()))


# 全局连接管理器实例
manager = ConnectionManager()


async def emit_to_all(
    connections: Optional[Set[WebSocket]],
    message: Dict[str, Any],
):
    """向所有连接发送消息（兼容原 Node.js 版本）"""
    if not connections:
        return

    for connection in list(connections):
        try:
            await connection.send_json(message)
        except Exception:
            # 静默失败
            pass


def send_sync(
    websocket: WebSocket,
    message: Dict[str, Any],
):
    """同步发送消息（用于非异步上下文）"""
    try:
        # FastAPI 的 send_json 是异步的，这里需要在事件循环中调用
        loop = asyncio.get_event_loop()
        loop.create_task(websocket.send_json(message))
    except Exception:
        pass
