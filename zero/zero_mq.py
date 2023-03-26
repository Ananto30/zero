import logging
from typing import Callable

import zmq

"""
If we want to replace the client-server patter with other implementation like Simple Pirate pattern,
implement the ZeroMQInterface class and replace the ZeroMQ with the new implementation instance.
"""


class ZeroMQInterface:
    def queue_device(
        self,
        host: str,
        port: int,
        device_comm_channel: str,
    ):
        """
        A queue_device maintains a queue to distribute the requests among the workers.

        Remember the queue device is blocking.

        Parameters
        ----------
        host: str
            The host where the queue device will bind.
            That means the host of the server.
        port: int
            The port where the queue device will bind.
            That means the port of the server.
        device_comm_channel: str
            The address where the queue device will bind.
            By default we use ipc for faster communication.
            But some os don't support ipc, in that case we use tcp.
        """
        raise NotImplementedError()

    def worker(
        self,
        device_comm_channel: str,
        worker_id: int,
        process_message: Callable,
    ):
        """
        A worker is a process that will handle the requests.

        Parameters
        ----------
        device_comm_channel: str
            The address where the queue device will bind.
            By default we use ipc for faster communication.
            But some os don't support ipc, in that case we use tcp.
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
        device_comm_channel: str,
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
            backend.bind(device_comm_channel)

            # details: https://learning-0mq-with-pyzmq.readthedocs.io/en/latest/pyzmq/devices/queue.html
            zmq.device(zmq.QUEUE, gateway, backend)

        except KeyboardInterrupt:
            logging.info("Caught KeyboardInterrupt, terminating workers")

        except Exception as e:
            logging.exception(e)
            logging.error("bringing down zmq device")

        finally:
            logging.info("closing zmq device")
            gateway.close() if gateway else None
            backend.close() if backend else None
            ctx.destroy() if ctx else None
            ctx.term() if ctx else None

    def worker(
        self,
        device_comm_channel: str,
        worker_id: int,
        process_message: Callable,
    ):
        ctx: zmq.Context = None  # type: ignore
        socket: zmq.Socket = None  # type: ignore

        try:
            ctx = zmq.Context.instance()
            socket = ctx.socket(zmq.DEALER)
            socket.connect(device_comm_channel)

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

        finally:
            logging.info("closing worker")
            socket.close() if socket else None
            ctx.destroy() if ctx else None
            ctx.term() if ctx else None


# IMPORTANT: register the imlementation here
ZeroMQ = ZeroMQPythonDevice()
