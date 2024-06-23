import asyncio
import logging
import sys
from multiprocessing import Process
from typing import Callable, Dict

import msgspec
import zmq
import zmq.asyncio


class ZeroSubscriber:  # pragma: no cover
    def __init__(self, host: str = "127.0.0.1", port: int = 5558):
        self._host = host
        self._port = port

        self._ctx = zmq.Context.instance()
        self._topic_map: Dict[str, Callable] = {}

    def register_listener(self, topic: str, func: Callable):
        if not isinstance(func, Callable):  # type: ignore
            raise ValueError(f"topic should listen to function not {type(func)}")
        self._topic_map[topic] = func
        return func

    def run(self):
        processes = []
        try:
            processes = [
                Process(
                    target=Listener.spawn_listener_worker,
                    args=(topic, func),
                )
                for topic, func in self._topic_map.items()
            ]
            for prcs in processes:
                prcs.start()
            self._create_zmq_device()
        except KeyboardInterrupt:
            print("Caught KeyboardInterrupt, terminating workers")
            for prcs in processes:
                prcs.terminate()
        else:
            print("Normal termination")
            for prcs in processes:
                prcs.close()
        for prcs in processes:
            prcs.join()

    def _create_zmq_device(self):
        gateway = None
        backend = None
        try:
            gateway = self._ctx.socket(zmq.SUB)
            gateway.bind(f"tcp://*:{self._port}")
            gateway.setsockopt_string(zmq.SUBSCRIBE, "")

            logging.info("Starting server at %d", self._port)

            backend = self._ctx.socket(zmq.PUB)
            if sys.platform == "posix":
                backend.bind("ipc://backendworker")
            else:
                backend.bind("tcp://127.0.0.1:6667")

            zmq.device(zmq.FORWARDER, gateway, backend)

        except Exception as exc:  # pylint: disable=broad-except
            logging.error(exc)
            logging.error("bringing down zmq device")
        finally:
            if gateway is not None:
                gateway.close()
            if backend is not None:
                backend.close()
            self._ctx.term()


class Listener:  # pragma: no cover
    @classmethod
    def spawn_listener_worker(cls, topic, func):
        worker = cls(topic, func)
        asyncio.run(worker._create_worker())

    def __init__(self, topic, func):
        self._topic = topic
        self._func = func

    async def _create_worker(self):
        ctx = zmq.asyncio.Context()
        socket = ctx.socket(zmq.SUB)

        if sys.platform == "posix":
            socket.connect("ipc://backendworker")
        else:
            socket.connect("tcp://127.0.0.1:6667")

        socket.setsockopt_string(zmq.SUBSCRIBE, self._topic)
        logging.info("Starting listener for: %s", self._topic)

        while True:
            topic, msg = await socket.recv_multipart()
            if topic.decode() != self._topic:
                continue

            try:
                await self._func(msgspec.msgpack.decode(msg))
            except Exception as exc:  # pylint: disable=broad-except
                logging.error(exc)
