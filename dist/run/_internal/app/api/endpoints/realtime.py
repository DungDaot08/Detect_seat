# app/api/endpoints/realtime.py
from fastapi import APIRouter, WebSocket
import json

router = APIRouter()
connected_clients: list[WebSocket] = []

@router.websocket("/ws/updates")
async def websocket_updates(websocket: WebSocket):
    await websocket.accept()
    connected_clients.append(websocket)
    print("🔌 Client kết nối WebSocket")

    try:
        while True:
            await websocket.receive_text()  # giữ kết nối
    except Exception as e:
        print("⚠️ Client mất kết nối WebSocket:", e)
    finally:
        connected_clients.remove(websocket)
        print("❌ Client ngắt kết nối WebSocket")


async def notify_frontend(data: dict):
    """Gửi dữ liệu đến tất cả client đang kết nối WebSocket"""
    message = json.dumps(data)
    for client in connected_clients.copy():
        try:
            await client.send_text(message)
        except:
            connected_clients.remove(client)
