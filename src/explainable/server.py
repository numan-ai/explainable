import dataclasses
import time
import json
import queue
import asyncio
import logging
import threading

from dataclasses import asdict, dataclass

import websockets

from .display import DISPLAY_REGISTRY


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


@dataclass
class ObjectUpdate:
    type: str
    data: dict


@dataclass
class ServerConfig:
    enabled: bool = False
    paused: bool = False
    should_wait_clients: bool = True
    history_enabled: bool = True


CONFIG = ServerConfig()

UPDATES_QUEUE: queue.Queue[ObjectUpdate] = queue.Queue(maxsize=1000)
CLIENTS: list[websockets.WebSocketServerProtocol] = []
OBSERVED_OBJECTS: dict[str, any] = {}
NEW_CLIENT_LOCK = threading.Lock()


def _remove_client(client):
    print("Removing client")
    try:
        CLIENTS.remove(client)
    except ValueError:
        pass


async def _send_message(message: str) -> None:
    for client in CLIENTS.copy():
        try:
            await client.send(message)
        except websockets.exceptions.ConnectionClosedError:
            _remove_client(client)
            logger.debug("Client disconnected")
        except websockets.exceptions.ConnectionClosedOK:
            _remove_client(client)
            logger.debug("Client disconnected")


async def _send_init_data():
    display_config = {}
    for name, config in DISPLAY_REGISTRY.items():
        display_config[name] = asdict(config)

    from .core import serialize
    for view_id, (obj, widget) in OBSERVED_OBJECTS.items():
        _serialized = serialize(obj, path=view_id)
        _serialized_widget = None if widget is None else dataclasses.asdict(widget)
        
        for client in CLIENTS.copy():
            try:
                await client.send(json.dumps({
                    "type": "snapshot",
                    "data": {
                        "view_id": view_id,
                        "structure": _serialized,
                        "widget": _serialized_widget,
                    }
                }))
            except websockets.exceptions.ConnectionClosed:
                _remove_client(client)

    for client in CLIENTS.copy():
        try:
            await client.send(json.dumps({
                "type": "displayConfig",
                "data": display_config,
            }))
        except websockets.exceptions.ConnectionClosed:
            _remove_client(client)


async def _handle_client(websocket: websockets.WebSocketServerProtocol, path: str) -> None:
    global PAUSED
    logger.debug("Client connected")

    CLIENTS.append(websocket)

    # with NEW_CLIENT_LOCK:
    await _send_init_data()

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
        _remove_client(websocket)
        logger.debug("Client disconnected")


async def _send_updates() -> None:
    while not CLIENTS:
        await asyncio.sleep(0.1)

    while True:
        if UPDATES_QUEUE.empty():
            await asyncio.sleep(0.001)
            continue
        
        updates = []
        while not UPDATES_QUEUE.empty() and len(updates) < 200:
            message = UPDATES_QUEUE.get_nowait()

            if message.type == "__init__":
                await _send_init_data()
                continue

            updates.append(asdict(message))

        data = json.dumps(updates)

        # message = UPDATES_QUEUE.get()

        # if message.type == "__init__":
        #     with NEW_CLIENT_LOCK:
        #         await _send_init_data()
        #     continue

        # data = json.dumps(asdict(message))
        await _send_message(data)


async def _main(host, port):
    async with websockets.serve(_handle_client, host, port) as server:
        logger.info(f"Server started at ws://{host}:{port}/")
        await _send_updates()


def _start_threaded_server(host, port) -> None:
    asyncio.run(_main(host, port))


def init(wait_client=True, enable_history=True,host="localhost", port=8120) -> None:
    CONFIG.should_wait_clients = wait_client
    CONFIG.enabled = True
    CONFIG.paused = False
    CONFIG.history_enabled = enable_history

    threading.Thread(target=_start_threaded_server, kwargs={
        "host": host,
        "port": port,
    }, daemon=True).start()


def send_update(update_type: str, data: dict) -> None:
    while CONFIG.paused:
        time.sleep(0.1)
    
    while not CLIENTS and CONFIG.should_wait_clients:
        time.sleep(0.1)
    
    UPDATES_QUEUE.put(ObjectUpdate(type=update_type, data=data))


def force_update():
    pass