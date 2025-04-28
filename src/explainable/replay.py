from base64 import b64encode
import gzip
import json
import sys
import asyncio
import logging

import websockets

from dataclasses import dataclass

from .core import read_log
from . import __version__


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler())


@dataclass
class ReplayConfig:
    file_path: str
    speed: float = 0.3
    idx: int = 0
    running: bool = True


async def _stream_log(config: ReplayConfig, ws: websockets.ServerConnection) -> None:
    lines = read_log(config.file_path)

    while True:
        try:
            await ws.send(json.dumps({
                "type": "snapshot",
                "data": {
                    "view_id": "view1",
                    "structure": b64encode(
                        lines[config.idx]
                    ).decode(),
                }
            }))
        except websockets.ConnectionClosed:
            logger.info("Connection closed")
            break
        if config.running:
            config.idx += 1

        await asyncio.sleep(config.speed)
        if config.idx >= len(lines):
            config.idx -= 1


async def _process_client_input(config: ReplayConfig, ws: websockets.ServerConnection) -> None:
    try:
        async for message in ws:
            data = json.loads(message)
            logger.info("< %s", message)

            if data["type"] == "replay-running":
                config.running = data["data"]
            
    except websockets.ConnectionClosed:
        logger.info("Connection closed")



async def replay_log(file_path: str, host: str = "localhost", port: int = 8120) -> None:
    async def handle_replay_client(ws: websockets.ServerConnection) -> None:
        await ws.send(json.dumps({
            "type": "init",
            "data": {
                "version": __version__,
                "type": "replay",
            },
        }))

        config = ReplayConfig(file_path=file_path)
        await asyncio.gather(
            _stream_log(config, ws),
            _process_client_input(config, ws),
        )

    async with websockets.serve(handle_replay_client, host, port) as server:
        logger.info(f"Server started at ws://{host}:{port}/")
        print("Visit https://explainable.numan.ai/replay/ to see your data")
        await asyncio.Future()


if __name__ == "__main__":
    file_name = sys.argv[1]
    asyncio.run(replay_log(file_name))
