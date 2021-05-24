import asyncio
import logging
import sys
from multiprocessing import Process

import msgpack
import zmq
import zmq.asyncio
import zmq.asyncio

logging.basicConfig(format='%(asctime)s | %(threadName)s | %(process)d | %(module)s : %(message)s', datefmt='%d-%b-%y %H:%M:%S', level=logging.INFO)


class ZeroSubscriber:
    def __init__(self, port=5558):
        self.__topic_map = {}
        self.__port = port

    def register_listener(self, topic, func):
        self.__topic_map[topic] = func

    def run(self):
        processes = []
        try:
            for topic in self.__topic_map:
                p = Process(target=Listener.spawn_listener_worker, args=(topic, self.__topic_map[topic]))
                processes.append(p)

            [prcs.start() for prcs in processes]
            self._create_zmq_device()
        except KeyboardInterrupt:
            print("Caught KeyboardInterrupt, terminating workers")
            [prcs.terminate() for prcs in processes]
        else:
            print("Normal termination")
            [prcs.close() for prcs in processes]
        [prcs.join() for prcs in processes]

    def _create_zmq_device(self):
        try:
            ctx = zmq.Context()

            gateway = ctx.socket(zmq.SUB)
            gateway.bind(f"tcp://*:{self.__port}")
            gateway.setsockopt_string(zmq.SUBSCRIBE, "")

            logging.info(f"Starting server at {self.__port}")

            backend = ctx.socket(zmq.PUB)
            if sys.platform == "posix":
                backend.bind("ipc://backendworker")
            else:
                backend.bind("tcp://127.0.0.1:6667")

            zmq.device(zmq.FORWARDER, gateway, backend)

        except Exception as e:
            logging.error(e)
            logging.error("bringing down zmq device")
        finally:
            pass
            gateway.close()
            backend.close()
            ctx.term()


class Listener:

    @classmethod
    def spawn_listener_worker(cls, topic, func):
        worker = Listener(topic, func)
        asyncio.run(worker.create_worker())

    def __init__(self, topic, func):
        self.__topic = topic
        self.__func = func

    async def create_worker(self):
        ctx = zmq.asyncio.Context()
        socket = ctx.socket(zmq.SUB)

        if sys.platform == "posix":
            socket.connect("ipc://backendworker")
        else:
            socket.connect("tcp://127.0.0.1:6667")

        socket.setsockopt_string(zmq.SUBSCRIBE, self.__topic)
        logging.info(f"Starting listener for: {self.__topic}")

        while True:
            topic, msg = await socket.recv_multipart()
            # logging.info(f"received rpc call: {rpc.decode()} | {msg}")
            try:
                await self._handle_msg(msgpack.unpackb(msg))
            except Exception as e:
                logging.error(e)

    async def _handle_msg(self, msg):
        try:
            return await self.__func(msg)
        except Exception as e:
            logging.error(e)
