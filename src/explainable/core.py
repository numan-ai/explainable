import gzip
import inspect
import json
import time
import asyncio
import logging
import threading

from base64 import b64encode
from dataclasses import asdict, dataclass, field, is_dataclass
from typing import Any, Callable

import websockets


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


UPDATE_INTERVAL = 0.1
DEFAULT_CTX_NAME = "MAIN"
UNSET = object()


@dataclass
class Node:
    data: any
    object_id: int = 0
    widget: str = ""
    layer: str = "main"
    # don't set this
    node_id: str = ""
    default_x: float = 100.0
    default_y: float = 100.0

    def __post_init__(self) -> None:
        self.node_id = f"{self.layer}:{self.object_id}"


@dataclass
class TextNode(Node):
    widget: str = "text"


@dataclass
class NumberNode(Node):
    widget: str = "number"


@dataclass
class RowNode(Node):
    widget: str = "row"


@dataclass
class ColumnNode(Node):
    widget: str = "column"


@dataclass
class PixelNode(Node):
    widget: str = "pixel"


@dataclass
class LineChartNode(Node):
    widget: str = "linechart"


@dataclass
class Edge:
    edge_id: str
    node_start_id: str
    node_end_id: str
    data: Any = None
    line_width: float = 2.0
    line_color: str = '#fff'
    label_color: str = '#fff'


@dataclass
class Graph:
    nodes: list[Node] = field(default_factory=list)
    edges: list[Edge] = field(default_factory=list)
    nodes_by_id: dict[str, Node] = field(default_factory=dict)

    def add_node(self, node: Node) -> Node:
        if node.node_id in self.nodes_by_id:
            return self.nodes_by_id[node.node_id]
        self.nodes.append(node)
        self.nodes_by_id[node.node_id] = node
        return node
    
    def find_node(self, node_id: str) -> Node:
        return self.nodes_by_id[node_id]
    
    def connect(self, node1: Node, node2: Node, data: Any = None) -> Edge:
        edge = Edge(
            edge_id=f"{node1.node_id}-{node2.node_id}",
            node_start_id=node1.node_id,
            node_end_id=node2.node_id,
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


def collect_vis_state() -> bytes:
    if CONTEXT is None:
        raise RuntimeError("FRAME is None")
    
    data = DRAW_FUNCTION(CONTEXT)
    if is_dataclass(data):
        data = asdict(data)
    raw_data = json.dumps(data)
    compressed_data = gzip.compress(raw_data.encode())

    return compressed_data


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

    def set_ctx(self, name: str, value: inspect.FrameInfo):
        self._ctx_data[name] = value

    def has_ctx(self, name: str) -> bool:
        return name in self._ctx_data

    def get_ctx(self, name: str = DEFAULT_CTX_NAME) -> dict[str, Any]:
        try:
            return self._ctx_data[name].frame.f_locals
        except KeyError:
            return {}
        
    def get(self, name: str, ctx_name: str = DEFAULT_CTX_NAME, default: Any = UNSET) -> Any:
        return self.get_ctx(ctx_name).get(name, default)


CLIENTS: list[websockets.WebSocketServerProtocol] = []
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


async def _send_message_to_client(client: websockets.WebSocketServerProtocol, message: str | bytes) -> None:
    try:
        await client.send(message)
    except websockets.exceptions.ConnectionClosedError:
        _remove_client(client)
        logger.debug("Client disconnected")
    except websockets.exceptions.ConnectionClosedOK:
        _remove_client(client)
        logger.debug("Client disconnected")


async def _send_init_data():
    pass


async def _handle_client(websocket: websockets.WebSocketServerProtocol, path: str=None) -> None:
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

    await _send_init_data()

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
            else:
                raise ValueError(f"Unknown action: {data['action']}")
    except websockets.ConnectionClosed:
        _remove_client(websocket)
        logger.debug("Client disconnected")


async def _send_updates() -> None:
    while True:
        data = collect_vis_state()

        await _send_message_to_all(json.dumps({
            "type": "snapshot",
            "data": {
                "view_id": "view1",
                "structure": b64encode(data).decode(),
            }
        }))

        await asyncio.sleep(UPDATE_INTERVAL)


async def _main(host, port):
    async with websockets.serve(_handle_client, host, port) as server:
        logger.info(f"Server started at ws://{host}:{port}/")
        await _send_updates()


def _start_threaded_server(host, port) -> None:
    asyncio.run(_main(host, port))


def init(draw_func, update_interval: float = 0.1, wait_client=True, host="localhost", port=8120, silent=False) -> None:
    global UPDATE_INTERVAL
    set_draw_function(draw_func)
    # _start_threaded_server(host=host, port=port)
    UPDATE_INTERVAL = update_interval

    threading.Thread(target=_start_threaded_server, kwargs={
        "host": host,
        "port": port,
    }, daemon=True).start()

    while not CLIENTS and wait_client:
        time.sleep(0.1)

    if not silent:
        print("Visit https://explainable.numan.ai/ to see your data")
        # logger.info(f"Visit https://explainable.numan.ai/ to see your data")
