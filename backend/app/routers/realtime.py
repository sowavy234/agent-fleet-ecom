from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict, List

router = APIRouter()

# Simple in-memory room manager
rooms: Dict[str, List[WebSocket]] = {}


@router.websocket('/{room_id}')
async def ws_room(websocket: WebSocket, room_id: str):
    await websocket.accept()
    conns = rooms.setdefault(room_id, [])
    conns.append(websocket)
    try:
        while True:
            data = await websocket.receive_json()
            # expect messages: {type: 'chat'|'signal', from: email, payload: ...}
            # broadcast to other clients in room
            for ws in list(conns):
                if ws is websocket:
                    continue
                try:
                    await ws.send_json(data)
                except Exception:
                    try:
                        conns.remove(ws)
                    except Exception:
                        pass
    except WebSocketDisconnect:
        try:
            rooms[room_id].remove(websocket)
        except Exception:
            pass
    except Exception:
        try:
            rooms[room_id].remove(websocket)
        except Exception:
            pass
