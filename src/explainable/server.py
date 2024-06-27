import asyncio
from dataclasses import asdict, dataclass
import json
import logging
import queue
import threading
import time

import websockets


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


@dataclass
class VisoUpdate:
    type: str
    data: dict


UPDATES_QUEUE: queue.Queue[VisoUpdate] = queue.Queue(maxsize=1000)
CLIENTS: list[websockets.WebSocketServerProtocol] = []
PAUSED: bool = False
SNAPSHOTS: dict[str, VisoUpdate] = {}
SHOULD_WAIT_CLIENTS: bool = True


def _remove_client(client):
    try:
        CLIENTS.remove(client)
    except ValueError:
        pass


async def _send_message(message: str) -> None:
    for client in CLIENTS:
        try:
            await client.send(message)
        except websockets.exceptions.ConnectionClosedError:
            _remove_client(client)
            logger.debug("Client disconnected")
        except websockets.exceptions.ConnectionClosedOK:
            _remove_client(client)
            logger.debug("Client disconnected")


async def _handle_client(websocket: websockets.WebSocketServerProtocol, path: str) -> None:
    global PAUSED
    logger.debug("Client connected")

    CLIENTS.append(websocket)

    for view_id in SNAPSHOTS:
        await websocket.send(json.dumps(asdict(SNAPSHOTS[view_id])))

    try:
        async for message in websocket:
            data = json.loads(message)
            logger.debug("< %s", data)
            if data["type"] == "pause":
                PAUSED = data["data"]
                await _send_message(json.dumps({
                    "type": data["request_id"],
                    "data": PAUSED,
                }))
                continue
            else:
                raise ValueError(f"Unknown action: {data['action']}")
    except websockets.ConnectionClosedError:
        logger.debug("Client disconnected")
        _remove_client(websocket)


async def _send_updates() -> None:
    global SNAPSHOTS

    while not CLIENTS:
        await asyncio.sleep(0.1)

    while True:
        if UPDATES_QUEUE.empty():
            await asyncio.sleep(0.1)
            continue
        
        message = UPDATES_QUEUE.get()

        if message.type == "snapshot":
            SNAPSHOTS[message.data['view_id']] = message
        
        data = json.dumps(asdict(message))
        await _send_message(data)


async def _main(host, port):
    async with websockets.serve(_handle_client, host, port) as server:
        logger.info(f"Server started at ws://{host}:{port}/")
        await _send_updates()


def _start_threaded_server(host, port) -> None:
    asyncio.run(_main(host, port))


def init(wait_client=True, host="localhost", port=8120) -> None:
    global SHOULD_WAIT_CLIENTS
    SHOULD_WAIT_CLIENTS = wait_client

    threading.Thread(target=_start_threaded_server, kwargs={
        "host": host,
        "port": port,
    }).start()


def send_update(update_type: str, data: dict) -> None:
    while PAUSED:
        time.sleep(0.1)
    
    while not CLIENTS and SHOULD_WAIT_CLIENTS:
        time.sleep(0.1)
    
    UPDATES_QUEUE.put(VisoUpdate(type=update_type, data=data))
