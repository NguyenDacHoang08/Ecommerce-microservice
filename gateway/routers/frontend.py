"""
Frontend catch-all router.

Proxies everything that didn't match an /api/v1/ route to the React/Next.js
frontend dev server, including WebSocket upgrade headers for hot-reload.
"""

import httpx
from fastapi import APIRouter, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import Response
from proxy import proxy_request
import config
import asyncio

router = APIRouter()
_BASE = config.FRONTEND_URL


@router.api_route(
    "/{path:path}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"],
)
async def frontend_proxy(path: str, request: Request) -> Response:
    upstream_path = f"/{path}" if path else "/"
    return await proxy_request(request, _BASE, upstream_path)


@router.websocket("/{path:path}")
async def frontend_ws_proxy(path: str, websocket: WebSocket):
    """
    WebSocket proxy to forward hot-reload / live connections from the
    frontend dev server (e.g. Vite HMR, Next.js Fast Refresh).
    """
    import websockets
    await websocket.accept()

    upstream_ws_url = _BASE.replace("http://", "ws://").replace("https://", "wss://")
    upstream_ws_url = f"{upstream_ws_url.rstrip('/')}/{path}"
    qs = websocket.url.query
    if qs:
        upstream_ws_url = f"{upstream_ws_url}?{qs}"

    # Filter out hop-by-hop headers
    headers = {}
    for k, v in websocket.headers.items():
        if k.lower() not in ["connection", "upgrade", "host"]:
            headers[k] = v

    try:
        async with websockets.connect(upstream_ws_url, extra_headers=headers) as upstream:
            async def client_to_upstream():
                try:
                    while True:
                        data = await websocket.receive()
                        if "text" in data:
                            await upstream.send(data["text"])
                        elif "bytes" in data:
                            await upstream.send(data["bytes"])
                        elif data.get("type") == "websocket.disconnect":
                            break
                except Exception:
                    pass

            async def upstream_to_client():
                try:
                    while True:
                        message = await upstream.recv()
                        if isinstance(message, bytes):
                            await websocket.send_bytes(message)
                        else:
                            await websocket.send_text(message)
                except Exception:
                    pass

            # Run both relay loops concurrently
            await asyncio.gather(client_to_upstream(), upstream_to_client())
    except Exception:
        pass
    finally:
        # Fallback: close gracefully
        try:
            await websocket.close()
        except Exception:
            pass
