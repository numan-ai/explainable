import gzip
import inspect
import json
import time
import asyncio
import logging
import threading

from base64 import b64encode
from dataclasses import asdict, dataclass, field, is_dataclass
from typing import Any, Callable, Optional

from .entities import Edge, Node

import websockets


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


UPDATE_INTERVAL = 0.1
DEFAULT_CTX_NAME = "MAIN"
UNSET = object()


@dataclass
class Graph:
    nodes: list[Node] = field(default_factory=list)
    edges: list[Edge] = field(default_factory=list)
    nodes_by_id: dict[str, Node] = field(default_factory=dict)

    def add_node(self, node: Node) -> Node:
        if node.object_id in self.nodes_by_id:
            return self.nodes_by_id[node.object_id]
        self.nodes.append(node)
        self.nodes_by_id[node.object_id] = node
        return node
    
    def find_node(self, object_id: str) -> Node:
        return self.nodes_by_id[object_id]
    
    def connect(self, node1: Node, node2: Node, data: Any = None) -> Edge:
        edge = Edge(
            edge_id=f"{node1.object_id}-{node2.object_id}",
            node_start_id=node1.object_id,
            node_end_id=node2.object_id,
            data=data,
        )
        self.edges.append(edge)
        return edge


def add_context(name: str = DEFAULT_CTX_NAME):
    CONTEXT.set_ctx(name, inspect.stack()[1])


DRAW_FUNCTION = None


def set_draw_function(func: Callable[[dict[str, dict]], dict[str, Any]]):
    global DRAW_FUNCTION
    DRAW_FUNCTION = func


def collect_vis_state() -> tuple[bytes, bool]:
    if CONTEXT is None:
        raise RuntimeError("FRAME is None")
    
    data = DRAW_FUNCTION(CONTEXT)

    if data is None:
        return None, False

    if is_dataclass(data):
        data = asdict(data)
    raw_data = json.dumps(data)
    compressed_data = gzip.compress(raw_data.encode())

    return compressed_data, True


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


class ContextManager:

    def __init__(self) -> None:
        self._ctx_data: dict[str, inspect.FrameInfo] = {}
        self._clickable_exclusive_data: dict[str, str] = {}

    def set_ctx(self, name: str, value: inspect.FrameInfo):
        self._ctx_data[name] = value

    def has_ctx(self, name: str) -> bool:
        return name in self._ctx_data

    def get_ctx(self, name: str = DEFAULT_CTX_NAME) -> dict[str, Any]:
        try:
            return self._ctx_data[name].frame.f_locals
        except KeyError:
            return {}
        
    def get(self, name: str, default: Any = UNSET, ctx_name: str = DEFAULT_CTX_NAME, ) -> Any:
        ctx = self.get_ctx(ctx_name)
        if default is UNSET:
            return ctx[name]
        return ctx.get(name, default)
    
    def get_clickable_exclusive(self, group: str) -> str:
        return str(self._clickable_exclusive_data.get(group, ""))
    
    def set_clickable_exclusive(self, group: str, value: str):
        self._clickable_exclusive_data[group] = value



CLIENTS: list[websockets.ServerConnection] = []
OBSERVED_OBJECTS: dict[str, Any] = {}
CONTEXT: ContextManager = ContextManager()


def _remove_client(client):
    try:
        CLIENTS.remove(client)
    except ValueError:
        pass


async def _send_message_to_all(message: str | bytes) -> None:
    for client in CLIENTS.copy():
        await _send_message_to_client(client, message)


async def _send_message_to_client(client: websockets.ServerConnection, message: str | bytes) -> None:
    try:
        await client.send(message)
    except websockets.exceptions.ConnectionClosedError:
        _remove_client(client)
        logger.debug("Client disconnected")
    except websockets.exceptions.ConnectionClosedOK:
        _remove_client(client)
        logger.debug("Client disconnected")


async def _handle_client(websocket: websockets.ServerConnection, path: str=None) -> None:
    from . import __version__

    global PAUSED
    logger.debug("Client connected")

    CLIENTS.append(websocket)

    await websocket.send(json.dumps({
        "type": "init",
        "data": {
            "version": __version__,
        },
    }))

    try:
        upd_selections = await websocket.recv()
    except websockets.ConnectionClosed:
        _remove_client(websocket)
        logger.debug("Client disconnected")
        return
    
    for key, value in json.loads(upd_selections)["data"]['selections'].items():
        CONTEXT.set_clickable_exclusive(key, value)

    try:
        async for message in websocket:
            data = json.loads(message)
            logger.debug("< %s", data)
            if data["type"] == "pause":
                CONFIG.paused = data["data"]
                await _send_message_to_all(json.dumps({
                    "type": data["request_id"],
                    "data": CONFIG.paused,
                }))
                continue
            elif data["type"] == "update_selections":
                for key, value in data["data"]['selections'].items():
                    CONTEXT.set_clickable_exclusive(key, value)
            else:
                raise ValueError(f"Unknown message type: {data['type']}")
    except websockets.ConnectionClosed:
        _remove_client(websocket)
        logger.debug("Client disconnected")


LOG: list[bytes] = []
UPDATES_TO_SEND = []


async def _send_updates() -> None:
    if UPDATE_INTERVAL is None:
        while True:
            upds = UPDATES_TO_SEND.copy()
            UPDATES_TO_SEND.clear()
            for upd in upds:
                await _send_update(upd)
            await asyncio.sleep(0.01)

    while True:
        data, ok = collect_vis_state()
        if not ok:
            await asyncio.sleep(UPDATE_INTERVAL)
            return
        await _send_update(data)
        
        await asyncio.sleep(UPDATE_INTERVAL)


async def _send_update(data):
    LOG.append(data)
    await _send_message_to_all(json.dumps({
        "type": "snapshot",
        "data": {
            "view_id": "view1",
            "structure": b64encode(data).decode(),
        }
    }))



def update() -> None:
    data, ok = collect_vis_state()
    if not ok:
        return
    UPDATES_TO_SEND.append(data)


def save_log(file_path: str) -> None:
    with open(file_path, "wb") as f:
        for data in LOG:
            f.write(data)
            f.write(b"!\n|\n!")


def read_log(file_path: str) -> list[bytes]:
    with open(file_path, "rb") as f:
        data = f.read()
    
    return data.split(b"!\n|\n!")


async def _main(host, port):
    async with websockets.serve(_handle_client, host, port) as server:
        logger.info(f"Server started at ws://{host}:{port}/")
        await _send_updates()


def _start_threaded_server(host, port) -> None:
    asyncio.run(_main(host, port))


def init(draw_func, update_interval: Optional[float] = 0.1, wait_client=True, host="localhost", port=8120, silent=False) -> None:
    global UPDATE_INTERVAL
    set_draw_function(draw_func)
    # _start_threaded_server(host=host, port=port)
    UPDATE_INTERVAL = update_interval

    threading.Thread(target=_start_threaded_server, kwargs={
        "host": host,
        "port": port,
    }, daemon=True).start()

    if not silent:
        print("Visit https://explainable.numan.ai/ to see your data")
        # logger.info(f"Visit https://explainable.numan.ai/ to see your data")

    while not CLIENTS and wait_client:
        time.sleep(0.1)

