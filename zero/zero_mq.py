import logging
import os
from typing import Callable

import zmq

"""
If we want to replace the client-server patter with other implementation like Simple Pirate pattern,
implement the ZeroMQInterface class and replace the ZeroMQ with the new implementation instance.
"""


class ZeroMQInterface:
    def queue_device(
        self,
        worker_ipc: str,
        worker_port: int,
        host: str,
        port: int,
    ):
        """
        A queue_device maintains a queue to distribute the requests among the workers.

        Remember the queue device is blocking.

        Parameters
        ----------
        worker_ipc: str
            The address where all worker will connect.
            By default we use ipc for faster communication.
            But some os don't support ipc, in that case we use tcp and need the worker_port.
        worker_port: int
            It is used if ipc is not supported by os.
        host: str
            The host address where the device will listen from clients.
        port: int
            The port where the device will listen from clients.
        """
        raise NotImplementedError()

    def worker(
        self,
        worker_ipc: str,
        worker_port: int,
        worker_id: int,
        process_message: Callable,
    ):
        """
        A worker is a process that will handle the requests.

        Parameters
        ----------
        worker_ipc: str
            The address where all worker will connect.
            By default we use ipc for faster communication.
            But some os don't support ipc, in that case we use tcp and need the worker_port.
        worker_port: int
            It is used if ipc is not supported by os.
        worker_id: int
            The id of the worker.
        process_message: Callable
            The function that will process the message.
            It takes the rpc method name and msg in parameters as bytes and should return the reply in bytes.

            def process_message(rpc: bytes, msg: bytes) -> bytes:
                ...
        """
        raise NotImplementedError()


class ZeroMQPythonDevice(ZeroMQInterface):
    def queue_device(
        self,
        host: str,
        port: int,
        worker_ipc: str,
        worker_port: int,
    ):
        ctx: zmq.Context = None  # type: ignore
        gateway: zmq.Socket = None  # type: ignore
        backend: zmq.Socket = None  # type: ignore

        try:
            ctx = zmq.Context.instance()
            gateway = ctx.socket(zmq.ROUTER)
            gateway.bind(f"tcp://{host}:{port}")
            logging.info(f"Starting server at {host}:{port}")
            backend = ctx.socket(zmq.DEALER)

            if os.name == "posix":
                backend.bind(f"ipc://{worker_ipc}")
            else:
                backend.bind(f"tcp://127.0.0.1:{worker_port}")

            # details: https://learning-0mq-with-pyzmq.readthedocs.io/en/latest/pyzmq/devices/queue.html
            zmq.device(zmq.QUEUE, gateway, backend)

        except KeyboardInterrupt:
            logging.info("Caught KeyboardInterrupt, terminating workers")

        except Exception as e:
            logging.exception(e)
            logging.error("bringing down zmq device")

        finally:
            gateway.close() if gateway else None
            backend.close() if backend else None
            ctx.destroy() if ctx else None
            ctx.term() if ctx else None

    def worker(
        self,
        worker_ipc: str,
        worker_port: int,
        worker_id: int,
        process_message: Callable,
    ):
        ctx: zmq.Context = None  # type: ignore
        socket: zmq.Socket = None  # type: ignore

        try:
            ctx = zmq.Context.instance()
            socket: zmq.Socket = ctx.socket(zmq.DEALER)

            if os.name == "posix":
                socket.connect(f"ipc://{worker_ipc}")
            else:
                socket.connect(f"tcp://127.0.0.1:{worker_port}")

            logging.info(f"Starting worker: {worker_id}")

            while True:
                frames = socket.recv_multipart()
                if len(frames) != 2:
                    logging.error(f"invalid message received: {frames}")
                    continue

                ident, data = frames
                response = process_message(data)
                socket.send_multipart([ident, response], zmq.DONTWAIT)

        except KeyboardInterrupt:
            logging.info("shutting down worker")

        except Exception as e:
            logging.exception(e)


# IMPORTANT: register the imlementation here
ZeroMQ = ZeroMQPythonDevice()
